import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from codex_setting.installation import finalize_plugin_config
CODEX=shutil.which('codex.exe')
POWERSHELL=shutil.which('pwsh.exe')

@unittest.skipUnless(os.name=='nt' and CODEX and POWERSHELL,'Windows, PowerShell 7 and Codex CLI required')
class PluginRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name)
        self.home=self.base/'owner/.codex';self.home.mkdir(parents=True)
        self.app=self.base/'app';self.app.mkdir()
        shutil.copytree(ROOT/'.agents/plugins',self.app/'.agents/plugins')
        shutil.copytree(ROOT/'plugins/autorun',self.app/'plugins/autorun')
        self.env=dict(os.environ,CODEX_HOME=str(self.home))
    def tearDown(self):self.temp.cleanup()
    def register(self,app=None):
        q=lambda s:"'"+str(s).replace("'","''")+"'"
        cmd='& '+q(ROOT/'scripts/Register-AutorunPlugin.ps1')+' -CodexExe '+q(CODEX)+' -AppRoot '+q(app or self.app)+' | ConvertTo-Json -Compress'
        result=subprocess.run([POWERSHELL,'-NoProfile','-NonInteractive','-Command',cmd],env=self.env,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(result.stdout)
    def test_fresh_repeat_and_conflicting_marketplace(self):
        config=self.home/'config.toml';config.write_text('model = "gpt-5"\n',encoding='utf-8');before=config.read_bytes()
        marker={'product':'codex-setting','user_home':str(self.home.parent),'files':{str(config):{'installed_sha256':hashlib.sha256(before).hexdigest()}}}
        (self.base/'installation.json').write_text(json.dumps(marker),encoding='utf-8')
        first=self.register();self.assertEqual(first['status'],'installed',first)
        actual=tomllib.loads(config.read_text(encoding='utf-8'))
        self.assertEqual(actual.pop('plugins'),{'autorun@codex-setting':{'enabled':True}})
        marketplace=actual.pop('marketplaces')['codex-setting']
        self.assertEqual(marketplace['source_type'],'local')
        self.assertEqual(Path(marketplace['source'].removeprefix('\\\\?\\')).resolve(),self.app.resolve())
        self.assertEqual(actual,{'model':'gpt-5'})
        self.assertEqual(finalize_plugin_config(self.base,before)['status'],'plugin_receipt_verified')
        again=self.register();self.assertEqual(again['status'],'present',again)
        conflict=self.register(self.base/'other');self.assertEqual(conflict['status'],'conflict',conflict)
        self.assertEqual(self.register()['status'],'present')

if __name__=='__main__':unittest.main()
