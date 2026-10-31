"""Portable adapter for the pinned Standard recovery engine. Never reads auth.json."""
from __future__ import annotations

import argparse
from contextlib import closing
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import uuid
import zipfile

PRODUCT = "CodexAutoStart.Recovery"
VERSION = "0.6.17"
ARCHIVE = "CodexAutoResume-v0.6.17-win-x64.zip"
DIGEST = "601e8081272a6c5b942ac465ca5d92938eca75007da24fa51cff4b7a6f130d16"


class RecoveryError(RuntimeError):
    pass


def read_json(file: Path):
    try:
        return json.loads(file.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        raise RecoveryError("INVALID_CONFIG") from error


def same_path(left, right):
    def canonical(value):
        text = str(Path(value).absolute())
        if os.name == "nt":
            # Expand 8.3 names without following MSIX redirection or reparse points.
            import ctypes
            from ctypes import wintypes
            expand = ctypes.WinDLL("kernel32", use_last_error=True).GetLongPathNameW
            expand.argtypes = (wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD)
            expand.restype = wintypes.DWORD
            buffer = ctypes.create_unicode_buffer(32768)
            length = expand(text, buffer, len(buffer))
            if 0 < length < len(buffer):
                text = buffer.value
        return os.path.normcase(text)
    return canonical(left) == canonical(right)


def no_links(file: Path):
    for candidate in (file, *file.parents):
        if candidate.exists():
            info = candidate.lstat()
            if candidate.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                raise RecoveryError("LINKED_PATH_REFUSED")


def sha256(file: Path):
    with file.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def current_sid():
    if os.name != "nt":
        raise RecoveryError("WINDOWS_REQUIRED")
    command = Path(os.environ["SystemRoot"]) / "System32" / "whoami.exe"
    result = subprocess.run([str(command), "/user", "/fo", "csv", "/nh"], capture_output=True,
                            text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW,
                            check=True)
    rows = list(csv.reader(io.StringIO(result.stdout)))
    if len(rows) != 1 or len(rows[0]) != 2 or not rows[0][1].startswith("S-1-"):
        raise RecoveryError("OWNER_UNAVAILABLE")
    return rows[0][1]


def validate_layout(config_file: Path, *, sid=None, verify_package=True):
    config_file = config_file.absolute()
    no_links(config_file)
    root = config_file.parent
    if not same_path(root, root.resolve()):
        raise RecoveryError("REDIRECTED_ROOT_USE_INSTALLROOT_OUTSIDE_LOCALAPPDATA")
    if config_file.name != "recovery.json":
        raise RecoveryError("INVALID_CONFIG_LOCATION")
    config = read_json(config_file)
    no_links(root / "installation.json")
    marker = read_json(root / "installation.json")
    if (config.get("schemaVersion") != 1 or marker.get("schemaVersion") != 1
            or config.get("product") != PRODUCT or marker.get("product") != PRODUCT
            or marker.get("upstreamVersion") != VERSION or marker.get("archiveSha256") != DIGEST
            or marker.get("ownerSid") != (sid or current_sid())):
        raise RecoveryError("INSTALLATION_OWNER_MISMATCH")
    expected = {"installRoot": root, "packageRoot": root / "package", "stateRoot": root / "state"}
    for name, value in expected.items():
        if not isinstance(config.get(name), str) or not same_path(config[name], value):
            raise RecoveryError("INVALID_CONFIG_PATH")
        no_links(value)
    for name in ("codexExe", "codexHome"):
        if not isinstance(config.get(name), str) or not Path(config[name]).is_absolute():
            raise RecoveryError("INVALID_CODEX_PATH")
        no_links(Path(config[name]))
    native = Path(config["codexExe"])
    if native.name.lower() != "codex.exe" or not Path(config["codexHome"]).is_dir():
        raise RecoveryError("CODEX_UNAVAILABLE")
    state, codex_home = Path(config["stateRoot"]), Path(config["codexHome"])
    if same_path(state, codex_home) or codex_home in state.parents or state in codex_home.parents:
        raise RecoveryError("STATE_MUST_BE_SEPARATE")
    package = Path(config["packageRoot"])
    runtime = package / "payload" / "runtime"
    source = package / "payload" / "app" / "src"
    if verify_package:
        archive_file = root / ARCHIVE
        no_links(archive_file)
        if not archive_file.is_file() or sha256(archive_file) != DIGEST:
            raise RecoveryError("PACKAGE_DIGEST_MISMATCH")
        no_links(root / "upstream.json")
        meta = read_json(root / "upstream.json")
        if meta.get("sha256") != DIGEST or meta.get("version") != VERSION:
            raise RecoveryError("PACKAGE_METADATA_MISMATCH")
        # Every shipped file stays byte-for-byte intact, including the embedded runtime.
        with zipfile.ZipFile(archive_file) as bundle:
            entries = {entry.filename.replace("\\", "/"): entry for entry in bundle.infolist()}
            published_files = {name for name, entry in entries.items() if not entry.is_dir()}
            for relative in published_files:
                target = package / Path(relative)
                no_links(target)
                if not target.is_file():
                    raise RecoveryError("PACKAGE_INCOMPLETE")
                published = bundle.read(entries[relative])
                actual = target.read_bytes()
                if hashlib.sha256(actual).digest() != hashlib.sha256(published).digest():
                    raise RecoveryError("PACKAGE_FILE_CHANGED")
                if relative.startswith("payload/app/") and relative[len("payload/app/"):] in meta["sourceGitBlobs"]:
                    git_path = relative[len("payload/app/"):]
                    # Windows release builds use CRLF; Git stores these text files as LF.
                    normalized = actual.replace(b"\r\n", b"\n")
                    blob = b"blob " + str(len(normalized)).encode("ascii") + b"\0" + normalized
                    if hashlib.sha1(blob).hexdigest() != meta["sourceGitBlobs"][git_path]:
                        raise RecoveryError("SOURCE_COMMIT_MISMATCH")
            # Imports may create .pyc files; extra source/native import hooks are refused.
            for target in package.rglob("*"):
                no_links(target)
                relative = target.relative_to(package)
                if target.is_file() and target.suffix.lower() == ".pyc" and "__pycache__" not in relative.parts and relative.as_posix() not in published_files:
                    raise RecoveryError("UNEXPECTED_PACKAGE_BYTECODE")
                if target.is_file() and target.suffix.lower() in (".py", ".pyd", ".dll", ".exe", ".zip", ".pth", "._pth"):
                    if relative.as_posix() not in published_files:
                        raise RecoveryError("UNEXPECTED_PACKAGE_CODE")
    return config, state, source, runtime


def backup_state(source: Path, destination: Path):
    no_links(source)
    no_links(destination)
    if destination.exists() or same_path(source, destination) or source in destination.parents:
        raise RecoveryError("INVALID_BACKUP_LOCATION")
    destination.mkdir(parents=True)
    if not source.exists():
        return
    for item in source.rglob("*"):
        no_links(item)
        if item.name.lower() == "auth.json":
            raise RecoveryError("CREDENTIAL_BACKUP_REFUSED")
        target = destination / item.relative_to(source)
        if item.is_dir():
            target.mkdir(exist_ok=True)
        elif item.name.endswith(("-wal", "-shm")):
            continue
        elif item.suffix.lower() in (".sqlite", ".sqlite3", ".db"):
            target.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(item.as_uri() + "?mode=ro", uri=True, timeout=15)) as original:
                with closing(sqlite3.connect(target)) as copy:
                    original.backup(copy)
                    copy.execute("pragma journal_mode=delete")
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("command", choices=("verify", "initialize", "status", "settings", "doctor",
                        "pending", "observe", "activate", "disable", "cancel", "run", "stop", "backup", "configure"))
    parser.add_argument("--thread")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    config, state, source, _runtime = validate_layout(args.config)
    # Existing Codex sign-in remains on this machine. No cache is copied or opened here.
    os.environ["CODEX_HOME"] = config["codexHome"]
    # Let the pinned engine discover and pair the active official desktop backend.
    # A desktop update may remove the installer-time binary; never keep driving it.
    os.environ.pop("CODEX_AUTO_RESUME_CODEX_EXE", None)
    # Never load a pre-existing cache or write bytecode into the intact release payload.
    sys.dont_write_bytecode = True
    sys.pycache_prefix = str(state / (".bytecode-" + uuid.uuid4().hex))
    sys.path.insert(0, str(source))
    from codex_auto_resume.control import Control
    from codex_auto_resume.cli import main as engine_main
    control = Control(str(state))
    cli = ["--home", str(state), "--codex-home", config["codexHome"]]
    if args.command == "verify":
        result = {"packageVerified": True, "upstreamVersion": VERSION, "credentialsCopied": False}
    elif args.command == "initialize":
        # Reinstallation preserves previous choices and pending recoveries.
        if (state / "config" / "settings.json").exists():
            result = {"preservedExistingSettings": True}
        else:
            control.update_settings({
                "notifications": False, "show_tray": False, "observe_only": True,
                "recover_usage_limit": True, "recover_network_transient": False,
                "recover_timeout": False, "recover_rate_limit_transient": False,
                "recover_server_5xx": False, "recover_stream_interrupted": False,
                "detection_lookback_hours": 0, "keep_awake": "on_ac", "keep_awake_hours": "h6",
                "continuation_style": "custom", "custom_message_mode": "global",
                "custom_message": "Продолжай: кори нотамомро аз ҷои қатъшуда дар ҳамин чат давом деҳ. Қоидаҳо ва маҳдудиятҳои қаблиро риоя кун; кори анҷомшударо такрор накун.",
            })
            control.set_enabled(False)
            result = {"initialized": True, "observeOnly": True, "enabled": False}
    elif args.command == "backup":
        if args.destination is None:
            raise RecoveryError("BACKUP_DESTINATION_REQUIRED")
        backup_state(state, args.destination.absolute())
        result = {"stateBackedUp": True}
    elif args.command in ("status", "settings", "pending"):
        result = {"status": control.get_status} if args.command == "status" else {"settings": control.get_settings} if args.command == "settings" else {"pending": control.list_pending}
        result = {key: value() for key, value in result.items()}
    elif args.command == "observe":
        control.update_settings({"observe_only": True})
        result = {"observeOnly": True}
    elif args.command == "activate":
        control.update_settings({"observe_only": False})
        control.set_enabled(True)
        result = {"observeOnly": False, "enabled": True}
    elif args.command == "disable":
        control.set_enabled(False)
        result = {"enabled": False}
    elif args.command == "configure":
        changes = json.load(sys.stdin)
        if not isinstance(changes, dict):
            raise RecoveryError("SETTINGS_OBJECT_REQUIRED")
        result = {"settings": control.update_settings(changes)}
    elif args.command == "cancel":
        if not args.thread:
            raise RecoveryError("THREAD_REQUIRED")
        result = control.cancel_thread(args.thread)
    else:
        return engine_main(cli + [args.command] + (["--once"] if args.command == "run" and args.once else []))
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as error:
        code = str(error) if isinstance(error, RecoveryError) else "RECOVERY_CONTROL_FAILED"
        print(json.dumps({"ok": False, "code": code}), file=sys.stderr)
        raise SystemExit(1)
