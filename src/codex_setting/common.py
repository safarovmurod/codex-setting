from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

PRODUCT = 'codex-setting'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8-sig'))


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.codex-setting-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save_json(path: Path, data):
    atomic_write(path, (json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def no_links(path: Path):
    for p in (path, *path.parents):
        if p.exists() and (p.is_symlink() or getattr(p.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('LINKED_PATH_REFUSED: '+str(p))


def confined(base: Path, relative: str) -> Path:
    base = base.resolve()
    target = base.joinpath(relative).absolute()
    if target == base or not target.is_relative_to(base) or '..' in Path(relative).parts:
        raise ValueError('PATH_ESCAPE')
    no_links(target)
    return target


@contextlib.contextmanager
def file_lock(path: Path, timeout=10):
    """OS-released lock; survives crashes without leaving a permanently held flag."""
    path.parent.mkdir(parents=True, exist_ok=True)
    no_links(path)
    stream = path.open('a+b')
    stream.seek(0, 2)
    if stream.tell() == 0:
        stream.write(b'0'); stream.flush()
    end = time.monotonic()+timeout
    locked = False
    try:
        while not locked:
            try:
                stream.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                if time.monotonic() >= end:
                    raise TimeoutError('LOCK_BUSY') from None
                time.sleep(.05)
        yield
    finally:
        if locked:
            stream.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()
