"""Owner-invoked preference export. Only explicit files/keys; no auth/session copies."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import tomllib

ROOT=Path(__file__).resolve().parents[1]
PORTABLE={'project_doc_max_bytes','model','model_reasoning_effort','service_tier','desktop','windows','skills','features','memories','tui'}
DEVICE_DESKTOP={'projectlessWorkspaceRoot','git-worktree-root','microphoneInputDeviceId','open-in-target-preferences'}
IGNORED_DIRS={'.git','__pycache__','node_modules','.venv','.cache'}
# Removed 2026-11-03 by owner decision: unknown third-party browser binary; stays disabled in config if a copy remains.
EXCLUDED_SKILLS={'autoglm-browser-agent'}
FORBIDDEN={'auth.json','credentials.json','cookies.json','state.json','.env'}
EXTS={'.md','.py','.ps1','.sh','.ts','.tsx','.js','.mjs','.cjs','.json','.yaml','.yml','.toml','.txt','.html','.css','.svg','.png','.jpg','.jpeg','.webp','.csv','.gitignore'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--codex-home',type=Path,required=True);p.add_argument('--skills',type=Path,required=True);p.add_argument('--plugin-audit',type=Path,required=True);a=p.parse_args()
    cfg=tomllib.loads((a.codex_home/'config.toml').read_text(encoding='utf-8-sig'))
    portable={k:copy.deepcopy(v) for k,v in cfg.items() if k in PORTABLE}
    records=[]
    def classify(value,path=()):
        if isinstance(value,dict):
            for k,v in value.items():classify(v,(*path,k))
        elif isinstance(value,list):
            for i,v in enumerate(value):classify(v,(*path,str(i)))
        else:
            top=path[0]
            status='portable' if top in PORTABLE else 'runtime_regenerated' if top in ['notify','marketplaces','mcp_servers'] else 'machine_local'
            field='.'.join(path)
            if top=='projects':field='projects.<existing-local-project>.'+path[-1]
            if top=='desktop' and len(path)>1 and path[1] in DEVICE_DESKTOP:status='device_remapped'
            records.append({'source':'config.toml','key':field,'disposition':status,'destination':'config.toml' if status=='portable' else 'target host discovery / existing local setting','verification':'doctor read-back'})
    classify(cfg)
    desktop=portable.get('desktop',{})
    desktop['projectlessWorkspaceRoot']='${DOCUMENTS}/Codex'
    desktop['git-worktree-root']='${DOCUMENTS}/Codex/worktrees'
    desktop['microphoneInputDeviceId']='communications'
    # A value referencing Explorer is a preference; machine/account identifiers are not carried.
    for item in portable.get('skills',{}).get('config',[]):
        item['path']='${USERPROFILE}/.agents/skills/'+Path(item['path']).parent.name+'/SKILL.md'
    # SDK/pipe env and notification helpers are deliberately rediscovered on the destination.
    agents=(a.codex_home/'AGENTS.md').read_text(encoding='utf-8-sig')
    if '<!-- CODEX-SETTING-VOICE -->' not in agents:agents+='\n<!-- CODEX-SETTING-VOICE -->\n## Гапзании одӣ\nБа шеф бо тоҷикии одии Душанбе ҷавоб деҳ: кӯтоҳ, равон ва амалӣ. Ҷумлаҳои адабӣ, таърифи зиёдатӣ ва дарси напурсидаро илова накун. Калимаи техникиро вақте лозим аст, сода фаҳмон. Натиҷаи насанҷидаро «тайёр» нагӯй.\n<!-- END-CODEX-SETTING-VOICE -->\n'
    out=ROOT/'payload';(out/'skills').mkdir(parents=True,exist_ok=True)
    (out/'AGENTS.md').write_text(agents,encoding='utf-8')
    names=[];excluded=[]
    for skill in sorted(a.skills.iterdir()):
        if not skill.is_dir() or not (skill/'SKILL.md').is_file() or skill.name in EXCLUDED_SKILLS:continue
        names.append(skill.name)
        for f in skill.rglob('*'):
            rel=f.relative_to(skill)
            if any(v in IGNORED_DIRS for v in rel.parts) or not f.is_file():continue
            if f.is_symlink():raise ValueError('SKILL_SYMLINK_REQUIRES_REVIEW:'+str(rel))
            if f.name.lower() in FORBIDDEN or f.suffix.lower() in ['.sqlite','.db','.pem','.key'] or f.name.startswith('.env'):
                raise ValueError('PRIVATE_SKILL_FILE_REFUSED:'+str(rel))
            if f.suffix.lower() not in EXTS and f.name not in ['LICENSE','NOTICE','.gitignore']:
                excluded.append(skill.name+'/'+rel.as_posix());continue
            data=f.read_bytes()
            if re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{35,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)',data):
                raise ValueError('POSSIBLE_SECRET_REFUSED:'+str(rel))
            dst=out/'skills'/skill.name/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    if excluded:raise ValueError('REVIEW_UNSUPPORTED_SKILL_FILES:'+json.dumps(excluded))
    if len(names)!=34:raise ValueError('EXPECTED_34_PERSONAL_SKILLS:'+str(len(names)))
    audit=json.loads(a.plugin_audit.read_text(encoding='utf-8'))
    plugins=[{k:p.get(k) for k in ['name','id','displayName','enabled','marketplace','installPolicy']} for p in audit['plugins'] if p['installed']]
    profile={'schema':1,'config':portable,'personal_skills':names,'plugins_manual':plugins,
             'removed_plugins':['Metricool','AnyPDF','Adobe Express','TinyFish','PostHog','Sentry','Tailscale','Cloud Environment','Canva','Descript','Gmail','Google Calendar']}
    (ROOT/'profiles').mkdir(exist_ok=True)
    (ROOT/'profiles'/'owner.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'profiles'/'settings-map.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    hashes={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    (ROOT/'profiles'/'payload-sha256.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps({'personal_skills':len(names),'payload_files':len(hashes),'settings_classified':len(records),'plugins_manual':len(plugins)}))

if __name__=='__main__':main()
