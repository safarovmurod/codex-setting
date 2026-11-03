import hashlib
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from codex_setting.installation import install,uninstall,doctor,finalize_plugin_config
from codex_setting.preferences import toml_dump

class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.source=self.base/'source';self.user=self.base/'owner';self.dest=self.base/'installed'
        (self.source/'payload/skills/example').mkdir(parents=True);(self.source/'skills/autorun/agents').mkdir(parents=True);(self.source/'profiles').mkdir()
        (self.source/'payload/AGENTS.md').write_text('owner instructions',encoding='utf-8');(self.source/'payload/skills/example/SKILL.md').write_text('example')
        (self.source/'skills/autorun/SKILL.md').write_text('explicit autorun');(self.source/'skills/autorun/agents/openai.yaml').write_text('policy:\n  allow_implicit_invocation: false\n')
        self.profile={'config':{'model':'gpt-6.1-sol','skills':{'config':[{'path':'${USERPROFILE}/.agents/skills/example/SKILL.md','enabled':False}]},'desktop':{'projectlessWorkspaceRoot':'${DOCUMENTS}/Codex'}}}
        (self.source/'profiles/owner.json').write_text(json.dumps(self.profile))
        hashes={p.relative_to(self.source/'payload').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.source/'payload').rglob('*') if p.is_file()}
        (self.source/'profiles/payload-sha256.json').write_text(json.dumps(hashes))
    def tearDown(self):self.temp.cleanup()
    def run_install(self):return install(self.source,self.dest,self.user,self.user/'Documents')
    def test_fresh_install_writes_real_destinations(self):
        result=self.run_install();self.assertTrue(result['files_ok'])
        cfg=tomllib.loads((self.user/'.codex/config.toml').read_text())
        self.assertNotIn('${',json.dumps(cfg));self.assertFalse(cfg['skills']['config'][0]['enabled'])
        self.assertTrue((self.user/'.agents/skills/example/SKILL.md').is_file());self.assertTrue((self.user/'.agents/skills/autorun/SKILL.md').is_file())
        self.assertEqual(result['chatgpt_personalization']['status'],'needs_ui_verification')
    def test_repeat_install_no_duplicate_entries_and_backup_restores_original(self):
        (self.user/'.codex').mkdir(parents=True);cfg=self.user/'.codex/config.toml'
        original=b'model="old"\n[unrelated]\nkeep=true\n';cfg.write_bytes(original)
        self.run_install();first=json.loads((self.dest/'installation.json').read_text());self.run_install();second=json.loads((self.dest/'installation.json').read_text())
        self.assertEqual(first['host_id'],second['host_id']);self.assertEqual(len(first['files']),len(second['files']))
        self.assertTrue(tomllib.loads(cfg.read_text())['unrelated']['keep'])
        self.assertFalse(uninstall(self.dest)['conflicts']);self.assertEqual(cfg.read_bytes(),original)
    def test_install_keeps_existing_model_choices(self):
        (self.user/'.codex').mkdir(parents=True)
        (self.user/'.codex/config.toml').write_text(toml_dump({'model':'gpt-6.1-terra','model_reasoning_effort':'ultra','service_tier':'priority'}),encoding='utf-8')
        self.run_install();cfg=tomllib.loads((self.user/'.codex/config.toml').read_text())
        self.assertEqual(cfg['model'],'gpt-6.1-terra');self.assertEqual(cfg['model_reasoning_effort'],'ultra');self.assertEqual(cfg['service_tier'],'priority')
    def test_uninstall_preserves_later_owner_edits(self):
        self.run_install();p=self.user/'.codex/AGENTS.md';p.write_text('later owner change')
        result=uninstall(self.dest);self.assertIn(str(p),result['conflicts']);self.assertEqual(p.read_text(),'later owner change')
    def test_hash_failure_changes_no_destination(self):
        (self.source/'payload/AGENTS.md').write_text('tampered')
        with self.assertRaises(ValueError):self.run_install()
        self.assertFalse((self.user/'.codex/AGENTS.md').exists())
    def test_repair_restores_missing_file(self):
        self.run_install();p=self.user/'.agents/skills/example/SKILL.md';p.unlink()
        self.assertFalse(doctor(self.dest)['files_ok']);self.assertTrue(self.run_install()['files_ok'])
    def test_plugin_receipt_preserves_original_backup(self):
        (self.user/'.codex').mkdir(parents=True);cfg=self.user/'.codex/config.toml'
        original=b'model="old"\n';cfg.write_bytes(original)
        self.run_install();before=cfg.read_bytes()
        changed=tomllib.loads(before.decode());changed['plugins']={'autorun@codex-setting':{'enabled':True}}
        changed['marketplaces']={'codex-setting':{'source':str(self.dest/'app'),'source_type':'local'}}
        cfg.write_text(toml_dump(changed),encoding='utf-8')
        self.assertFalse(doctor(self.dest)['files_ok'])
        finalize_plugin_config(self.dest,before)
        self.assertTrue(doctor(self.dest)['files_ok'])
        self.assertFalse(uninstall(self.dest)['conflicts']);self.assertEqual(cfg.read_bytes(),original)
    def test_plugin_receipt_refuses_unrelated_changes(self):
        self.run_install();cfg=self.user/'.codex/config.toml';before=cfg.read_bytes()
        changed=tomllib.loads(before.decode());changed['plugins']={'autorun@codex-setting':{'enabled':True}}
        changed['marketplaces']={'codex-setting':{'source':str(self.dest/'app'),'source_type':'local'}};changed['unrelated']={'modified':True}
        cfg.write_text(toml_dump(changed),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'UNRELATED_CONFIG_CHANGE'):finalize_plugin_config(self.dest,before)
        self.assertFalse(doctor(self.dest)['files_ok'])
    def test_plugin_receipt_rejects_wrong_marketplace(self):
        self.run_install();cfg=self.user/'.codex/config.toml';before=cfg.read_bytes()
        changed=tomllib.loads(before.decode());changed['plugins']={'autorun@codex-setting':{'enabled':True}}
        changed['marketplaces']={'codex-setting':{'source':str(self.base/'foreign'),'source_type':'local'}}
        cfg.write_text(toml_dump(changed),encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'PLUGIN_MARKETPLACE_WRONG_ROOT'):finalize_plugin_config(self.dest,before)
    def test_agents_paths_are_remapped_without_changing_snapshot(self):
        snapshot=ROOT/'payload/AGENTS.md'
        data=snapshot.read_bytes()
        (self.source/'payload/AGENTS.md').write_bytes(data)
        path=self.source/'profiles/payload-sha256.json'
        hashes=json.loads(path.read_text())
        hashes['AGENTS.md']=hashlib.sha256(data).hexdigest()
        path.write_text(json.dumps(hashes))
        self.assertTrue(self.run_install()['files_ok'])
        actual=(self.user/'.codex/AGENTS.md').read_text(encoding='utf-8')
        self.assertIn((self.user/'.agents/skills').as_posix(),actual)
        self.assertIn((self.user/'.codex/AGENTS.md').as_posix(),actual)
        self.assertIn((self.dest/'recovery').as_posix(),actual)
        self.assertNotIn('`D:/User/CodexAutoStart`',actual)
        self.assertNotIn('`C:/Users/safar/.agents/skills`',actual)
        self.assertNotIn('`C:/Users/safar/.codex/AGENTS.md`',actual)
        self.assertEqual(snapshot.read_bytes(),data)
        self.assertEqual((self.source/'payload/AGENTS.md').read_bytes(),data)
        self.assertTrue(self.run_install()['files_ok'])
        self.assertEqual((self.user/'.codex/AGENTS.md').read_text(encoding='utf-8'),actual)
    def test_real_snapshot_hashes_all_match(self):
        hashes=json.loads((ROOT/'profiles/payload-sha256.json').read_text())
        for rel,expected in hashes.items():self.assertEqual(hashlib.sha256((ROOT/'payload'/rel).read_bytes()).hexdigest(),expected,rel)
        profile=json.loads((ROOT/'profiles/owner.json').read_text(encoding='utf-8'))
        self.assertEqual(len(profile['personal_skills']),34);self.assertEqual(len(profile['config']['skills']['config']),6)
    def test_real_config_roundtrip(self):
        profile=json.loads((ROOT/'profiles/owner.json').read_text(encoding='utf-8'))
        self.assertEqual(tomllib.loads(toml_dump(profile['config'])),profile['config'])
    def test_payload_does_not_ship_credentials_or_databases(self):
        for p in (ROOT/'payload').rglob('*'):
            if p.is_file():self.assertNotIn(p.name.lower(),['auth.json','state.json','cookies.json']);self.assertNotIn(p.suffix.lower(),['.sqlite','.db','.pem','.key'])

if __name__=='__main__':unittest.main()
