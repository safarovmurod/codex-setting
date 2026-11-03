"""Build the account plugin «Шеф Rules» from the same files the PC uses.

Codex on Android Remote runs on the Windows host and already reads AGENTS.md and skills there.
A cloud chat without the host sees only account plugins, so this plugin carries the same rules:
- skills/shef-rules: payload/AGENTS.md without the Windows-host-only sections;
- skills/shef-frontend: the mentor skill and its current agreement.
Run after changing payload/AGENTS.md or the mentor skill; a test fails if plugins/shef-rules is stale.
Usage: python tools/build_mobile_plugin.py [--zip DIR]
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = 'shef-rules'
HOST_ONLY = ('## Codex: Spec Kit', '## Codex: skills, пути и recovery')
VERSION_BASE = '1.0'


def lf(path):
    return path.read_bytes().decode('utf-8').replace('\r\n', '\n')


def strip_host_sections(text):
    lines, keep = [], True
    for line in text.split('\n'):
        if line.startswith('## '):
            keep = not line.startswith(HOST_ONLY)
        if keep:
            lines.append(line)
    return '\n'.join(lines).rstrip().rstrip('-').rstrip() + '\n'


def files():
    agents = strip_host_sections(lf(ROOT / 'payload/AGENTS.md'))
    agents = agents.replace('Для любой frontend/React-задачи прочитай его перед работой.',
                            'В этом plugin он называется `shef-frontend`. Для любой frontend/React-задачи прочитай его перед работой.')
    rules = ('---\nname: shef-rules\n'
             'description: Personal rules of «шеф» for every request in any chat — Dushanbe Tajik style, abbreviations, '
             'no decisions for him, error and fact formats, verification. Read first in every conversation, '
             'including phone and cloud chats.\n---\n\n' + agents)
    mentor = lf(ROOT / 'payload/skills/mansur-frontend-mentor/SKILL.md')
    head, body = mentor.split('\n---\n', 1)
    head = head.replace('name: mansur-frontend-mentor', 'name: shef-frontend')
    body = body.replace('Общие правила — в глобальном AGENTS.md.', 'Общие правила — в skill `shef-rules` (или глобальном AGENTS.md на ПК).')
    body = body.split('\nОстальные references')[0].rstrip() + '\n'
    out = {
        'skills/shef-rules/SKILL.md': rules,
        'skills/shef-rules/agents/openai.yaml': 'interface:\n  display_name: "Шеф Rules"\n  short_description: "Қоидаҳои шахсии шеф барои ҳар чат"\npolicy:\n  allow_implicit_invocation: true\n',
        'skills/shef-frontend/SKILL.md': head + '\n---\n' + body,
        'skills/shef-frontend/references/current-agreement.md': lf(ROOT / 'payload/skills/mansur-frontend-mentor/references/current-agreement.md'),
        'skills/shef-frontend/agents/openai.yaml': 'interface:\n  display_name: "Шеф Frontend"\n  short_description: "Frontend-договор: stack, UI, код, API, дарс"\npolicy:\n  allow_implicit_invocation: true\n',
    }
    digest = hashlib.sha256(json.dumps(out, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    manifest = {
        '$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
        'name': PLUGIN,
        'version': VERSION_BASE + '.' + str(int(digest[:6], 16)),
        'description': 'Personal rules of «шеф» for phone and cloud chats; built from the PC AGENTS.md and mentor skill.',
        'author': {'name': 'codex-setting'},
        'repository': 'https://github.com/safarovmurod/codex-setting',
        'extensions': {'com.openai': {'interface': {
            'displayName': 'Шеф Rules',
            'shortDescription': 'Қоидаҳои ПК дар телефон ва cloud',
            'longDescription': 'Ҳамон қоидаҳои AGENTS.md ва скилли frontend-и ПК барои чатҳои телефон ва cloud. Аз ҳамин репо худкор сохта мешавад.',
            'developerName': 'codex-setting',
            'category': 'Productivity',
            'capabilities': ['skills'],
        }}},
    }
    out['plugin.json'] = json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'
    return out


def write(target):
    if target.exists():
        shutil.rmtree(target)
    for rel, text in files().items():
        p = target / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode('utf-8'))


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--zip', type=Path, help='also write <DIR>/shef-rules-<version>.zip for Upload plugin archive')
    args = a.parse_args()
    target = ROOT / 'plugins' / PLUGIN
    write(target)
    version = json.loads((target / 'plugin.json').read_text(encoding='utf-8'))['version']
    print('plugins/' + PLUGIN, version)
    if args.zip:
        args.zip.mkdir(parents=True, exist_ok=True)
        archive = args.zip / f'{PLUGIN}-{version}.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(target.rglob('*')):
                if p.is_file():
                    z.write(p, p.relative_to(target).as_posix())
        print(archive)


if __name__ == '__main__':
    main()
