import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_mobile_plugin', ROOT / 'tools/build_mobile_plugin.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class MobilePluginTests(unittest.TestCase):
    def test_committed_plugin_matches_pc_rules(self):
        expected = build.files()
        target = ROOT / 'plugins/shef-rules'
        actual = {p.relative_to(target).as_posix(): p.read_bytes().decode('utf-8') for p in target.rglob('*') if p.is_file()}
        self.assertEqual(sorted(actual), sorted(expected), 'run: python tools/build_mobile_plugin.py')
        for rel, text in expected.items():
            self.assertEqual(actual[rel], text, rel + ' is stale; run: python tools/build_mobile_plugin.py')

    def test_rules_skill_has_pc_rules_without_host_paths(self):
        rules = build.files()['skills/shef-rules/SKILL.md']
        self.assertTrue(rules.startswith('---\nname: shef-rules\n'))
        for needle in ('«шеф»', 'ANALYZE → VERIFY → EXPLAIN → FIX', 'Сабаб аниқ тасдиқ нашудааст'):
            self.assertIn(needle, rules)
        for host_only in ('C:/Users/safar', 'D:/User/CodexAutoStart', '## Codex: Spec Kit'):
            self.assertNotIn(host_only, rules)

    def test_frontend_skill_carries_current_agreement(self):
        out = build.files()
        self.assertIn('name: shef-frontend', out['skills/shef-frontend/SKILL.md'])
        pc = (ROOT / 'payload/skills/mansur-frontend-mentor/references/current-agreement.md').read_bytes().decode('utf-8').replace('\r\n', '\n')
        self.assertEqual(out['skills/shef-frontend/references/current-agreement.md'], pc)

    def test_manifest_and_archive_have_no_private_data(self):
        manifest = json.loads(build.files()['plugin.json'])
        self.assertEqual(manifest['name'], 'shef-rules')
        self.assertEqual(manifest['extensions']['com.openai']['interface']['capabilities'], ['skills'])
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'plugin'
            build.write(target)
            archive = Path(d) / 'p.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                for p in target.rglob('*'):
                    if p.is_file():
                        z.write(p, p.relative_to(target).as_posix())
            names = zipfile.ZipFile(archive).namelist()
        self.assertIn('plugin.json', names)
        self.assertFalse([n for n in names if not n.endswith(('.md', '.yaml', '.json'))])


if __name__ == '__main__':
    unittest.main()
