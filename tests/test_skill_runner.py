import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SkillRunnerTests(unittest.TestCase):
    def test_hidden_child_preserves_output_errors_arguments_and_exit_code(self):
        helper=Path(__file__).resolve().parents[1]/'skills/autorun/scripts/run.py'
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);root=base/'installation';home=base/'codex'
            (root/'app').mkdir(parents=True);home.mkdir()
            (root/'installation.json').write_text('{}')
            (home/'codex-setting.json').write_text(json.dumps({'root':str(root),'python':sys.executable}))
            (root/'app/runner.py').write_text(
                'import json,sys\nprint(json.dumps(sys.argv[3:]))\n'
                'print("expected error",file=sys.stderr)\nsys.exit(3)\n')
            env=dict(os.environ,CODEX_HOME=str(home))
            result=subprocess.run([sys.executable,str(helper),'autorun','status'],
                                  env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,3)
            self.assertEqual(json.loads(result.stdout),['autorun','status'])
            self.assertIn('expected error',result.stderr)
