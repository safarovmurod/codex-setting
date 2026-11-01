from pathlib import Path
import sys,tempfile,unittest,uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from codex_setting.watcher import Watcher


class WatcherTests(unittest.TestCase):
    def test_connected_chat_without_task_is_watched_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def unavailable():calls.append(True);raise RuntimeError('app closed')
            watcher=Watcher(Path(tmp),'host',unavailable)
            watcher.store.connect('host',str(uuid.uuid4()),1)
            self.assertEqual(watcher.tick()['status'],'waiting_for_host_runtime')
            self.assertEqual(len(calls),1)
    def test_empty_consent_keeps_watcher_alive_without_runtime_or_quota(self):
        with tempfile.TemporaryDirectory() as tmp:
            def forbidden():raise AssertionError('Idle must not initialize runtime or probe quota')
            watcher=Watcher(Path(tmp),'host',forbidden)
            self.assertEqual(watcher.tick()['status'],'idle')
            self.assertTrue((Path(tmp)/'watcher-status.json').is_file())
    def test_app_unavailable_at_logon_does_not_kill_watcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def unavailable():calls.append(True);raise RuntimeError('app closed')
            watcher=Watcher(Path(tmp),'host',unavailable)
            watcher.store.arm('host',str(uuid.uuid4()),'goal-hash','1')
            self.assertEqual(watcher.tick()['status'],'waiting_for_host_runtime')
            self.assertEqual(watcher.tick()['status'],'waiting_for_host_runtime')
            self.assertEqual(len(calls),2)

if __name__=='__main__':unittest.main()
