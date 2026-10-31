from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from codex_setting.runtime import Runtime


class RuntimeUpdateTests(unittest.TestCase):
    def test_persistent_watcher_rediscovers_a_replaced_backend(self):
        runtime=Runtime.__new__(Runtime)
        runtime.backend=SimpleNamespace(codex_exe=Path('old.exe'),app_identity=lambda:None)
        runtime._last_discovery=0;runtime._home=Path('owner');runtime._discover=lambda:Path('new.exe')
        runtime._backend_type=lambda home,exe:SimpleNamespace(codex_exe=exe,app_identity=lambda:{'server':'current'},loaded=lambda thread,identity:'loaded')
        with patch('codex_setting.runtime.time.monotonic',return_value=100):
            self.assertTrue(runtime.ready('exact-thread'))
        self.assertEqual(runtime.backend.codex_exe,Path('new.exe'))
    def test_unavailable_discovery_keeps_dispatch_closed(self):
        runtime=Runtime.__new__(Runtime)
        runtime.backend=SimpleNamespace(app_identity=lambda:None)
        runtime._last_discovery=0
        def failed():raise RuntimeError('not available')
        runtime._discover=failed
        with patch('codex_setting.runtime.time.monotonic',return_value=100):self.assertFalse(runtime.ready('exact-thread'))

if __name__=='__main__':unittest.main()
