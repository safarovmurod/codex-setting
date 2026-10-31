from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time

from .common import load_json, digest


def native_codex():
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',
        '(Get-Command codex.exe -ErrorAction Stop).Source'],capture_output=True,text=True,
        timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if result.returncode or not result.stdout.strip(): raise RuntimeError('CODEX_NATIVE_NOT_FOUND')
    p=Path(result.stdout.strip())
    if not p.is_absolute() or not p.is_file() or p.name.lower()!='codex.exe': raise RuntimeError('INVALID_CODEX_NATIVE')
    return p


class Runtime:
    def __init__(self,install_root: Path,codex_home: Path):
        recovery=install_root/'recovery'
        # Original verifier checks archive digest, every release file, source blobs and owner.
        control=recovery/'scripts'/'recovery-control.py'
        import importlib.util
        spec=importlib.util.spec_from_file_location('codex_setting_upstream_verifier',control)
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        config,_,source,_=module.validate_layout(recovery/'recovery.json')
        if Path(config['codexHome']).resolve()!=codex_home.resolve(): raise RuntimeError('WRONG_CODEX_HOME')
        sys.dont_write_bytecode=True
        sys.path.insert(0,str(source))
        from codex_auto_resume.codex import LocalSource
        from codex_auto_resume.codex.transport import Backend
        from codex_auto_resume import config as upstream
        from codex_auto_resume.codex.pairing import app_engines
        self._discover=lambda:upstream.discover_codex_exe(None,lambda p:Backend(codex_home,p)._compatible(),running=app_engines)
        self._backend_type=Backend;self._home=codex_home;self._last_discovery=0
        exe=self._discover()
        self.backend=Backend(codex_home,exe)
        self.source=LocalSource(codex_home)

    def ready(self,thread):
        identity=self.backend.app_identity()
        if not identity and time.monotonic()-self._last_discovery>=30:
            self._last_discovery=time.monotonic()
            try:
                exe=self._discover()
                if Path(exe)!=self.backend.codex_exe:
                    self.backend=self._backend_type(self._home,exe)
                    identity=self.backend.app_identity()
            except Exception:pass
        return bool(identity and self.backend.loaded(thread,identity)=='loaded')

    def doctor(self,thread=None):
        result={'engine':self.backend.engine_checks(),'app_running':bool(self.backend.app_identity())}
        if thread:
            result.update(thread_eligible=self.source.taken(thread,frozenset()),
                          thread_loaded=self.ready(thread), projection=self.source.projection(thread))
            latest=self.source.latest(thread)
            result['latest_status']=latest.get('status') if latest else None
        result['quota']=self.backend.usage()
        return result
