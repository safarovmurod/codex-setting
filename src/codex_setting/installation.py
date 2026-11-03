from __future__ import annotations

import json
import os
from pathlib import Path
import time
import tomllib
import uuid

from .common import PRODUCT, atomic_write, confined, digest, file_lock, load_json, no_links, save_json
from .preferences import desired_config, merge, toml_dump


def render_agents(data: bytes, user_home: Path, root: Path) -> bytes:
    """Map known source-host instruction paths without changing the snapshot."""
    value = data.decode('utf-8')
    replacements = {
        'C:/Users/safar/.agents/skills': (user_home/'.agents/skills').as_posix(),
        'C:/Users/safar/.codex/AGENTS.md': (user_home/'.codex/AGENTS.md').as_posix(),
        'D:/User/CodexAutoStart': (root/'recovery').as_posix(),
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    return value.encode('utf-8')


def install(source: Path, root: Path, user_home: Path, documents: Path):
    for path in (root,user_home/'.codex',user_home/'.agents/skills'):no_links(path)
    profile=load_json(source/'profiles/owner.json')
    hashes=load_json(source/'profiles/payload-sha256.json')
    # Validate every byte before touching any destination.
    for rel,expected in hashes.items():
        if digest(confined(source/'payload',rel).read_bytes())!=expected: raise ValueError('PAYLOAD_HASH_MISMATCH:'+rel)
    root.mkdir(parents=True,exist_ok=True)
    with file_lock(root/'install.lock'):
        marker=load_json(root/'installation.json',{})
        if marker and marker.get('product')!=PRODUCT: raise ValueError('FOREIGN_INSTALLATION')
        marker.setdefault('product',PRODUCT);marker.setdefault('host_id',str(uuid.uuid4()))
        marker.setdefault('files',{});marker.setdefault('settings_backup',{})
        backup=root/'backups/files';backup.mkdir(parents=True,exist_ok=True)
        candidates={}
        for rel in hashes:
            target=user_home/'.codex/AGENTS.md' if rel=='AGENTS.md' else confined(user_home/'.agents',rel)
            data=confined(source/'payload',rel).read_bytes()
            candidates[target]=render_agents(data,user_home,root) if rel=='AGENTS.md' else data
        for file in (source/'skills').rglob('*'):
            if file.is_file():
                target=confined(user_home/'.agents/skills',file.relative_to(source/'skills').as_posix())
                candidates[target]=file.read_bytes()
        cfg_file=user_home/'.codex/config.toml'
        old=tomllib.loads(cfg_file.read_text(encoding='utf-8-sig')) if cfg_file.exists() else {}
        desired=desired_config(profile,user_home,documents)
        # An existing target's device choices are already valid for that target.
        for k in ['projectlessWorkspaceRoot','git-worktree-root','microphoneInputDeviceId','open-in-target-preferences']:
            if k in old.get('desktop',{}):desired.setdefault('desktop',{})[k]=old['desktop'][k]
        # Model, effort and tier are the owner's account choices; never roll them back.
        for k in ['model','model_reasoning_effort','service_tier']:
            if k in old:desired[k]=old[k]
        candidates[cfg_file]=toml_dump(merge(old,desired)).encode('utf-8')
        descriptor=user_home/'.codex/codex-setting.json'
        python=root/'recovery/package/payload/runtime/python.exe'
        candidates[descriptor]=(json.dumps({'schema':1,'root':str(root),'python':str(python)},indent=2)+'\n').encode()
        for target,data in candidates.items():
            no_links(target)
            key=str(target)
            if key not in marker['files']:
                existed=target.exists();name=digest(key.encode())+'.bak'
                if existed:atomic_write(backup/name,target.read_bytes())
                marker['files'][key]={'existed':existed,'backup':name,'installed_sha256':None}
            marker['files'][key]['installed_sha256']=digest(data)
        # Journal the rollback before first destination mutation.
        save_json(root/'installation.json',marker)
        for target,data in candidates.items():
            if not target.exists() or target.read_bytes()!=data:atomic_write(target,data)
        marker.update(version='1.0.0',user_home=str(user_home),documents=str(documents),updated_at=time.time())
        save_json(root/'installation.json',marker)
        report=doctor(root)
        save_json(root/'install-report.json',report)
        return report


def doctor(root):
    marker=load_json(root/'installation.json',{})
    if marker.get('product')!=PRODUCT:return {'installed':False,'error':'NO_OWNED_INSTALLATION'}
    files=[]
    for name,entry in marker.get('files',{}).items():
        p=Path(name)
        status='ok' if p.is_file() and digest(p.read_bytes())==entry['installed_sha256'] else 'changed_or_missing'
        files.append({'path':name,'status':status})
    user=Path(marker.get('user_home',str(Path.home())))
    config=user/'.codex/config.toml'
    runtime='not_generated'
    if config.exists():
        cfg=tomllib.loads(config.read_text(encoding='utf-8-sig'))
        command=cfg.get('mcp_servers',{}).get('node_repl',{}).get('command')
        if command and Path(command).is_file():runtime='present'
    return {'installed':True,'files_ok':bool(files) and all(f['status']=='ok' for f in files),
            'file_count':len(files),'files':files,'node_repl_runtime':runtime,
            'chatgpt_personalization':load_json(root/'personalization-evidence.json',{'status':'needs_ui_verification'}),
            'android':load_json(root/'android-evidence.json',{'status':'needs_owner_pairing_and_live_test'})}


def finalize_plugin_config(root: Path, before: bytes):
    """Accept only the explicit local AUTORUN enablement into the install receipt."""
    with file_lock(root/'install.lock'):
        marker=load_json(root/'installation.json',{})
        if marker.get('product')!=PRODUCT:raise ValueError('NO_OWNED_INSTALLATION')
        config=Path(marker['user_home'])/'.codex/config.toml'
        no_links(config)
        entry=marker.get('files',{}).get(str(config))
        if not entry or entry['installed_sha256']!=digest(before):raise ValueError('PLUGIN_CONFIG_BASELINE_CHANGED')
        after=config.read_bytes()
        old=tomllib.loads(before.decode('utf-8-sig'));new=tomllib.loads(after.decode('utf-8-sig'))
        new_plugin=new.get('plugins',{}).get('autorun@codex-setting')
        if new_plugin != {'enabled':True}:raise ValueError('PLUGIN_CONFIG_NOT_ENABLED')
        marketplace=new.get('marketplaces',{}).get('codex-setting')
        if not isinstance(marketplace,dict) or set(marketplace)!={'source','source_type'} or marketplace['source_type']!='local':raise ValueError('PLUGIN_MARKETPLACE_NOT_LOCAL')
        actual=str(marketplace['source'])
        if actual.startswith('\\\\?\\'):actual=actual[4:]
        expected=str(root/'app')
        # realpath, not abspath: Windows hands out 8.3 short names that name the same folder.
        if os.path.normcase(os.path.realpath(actual))!=os.path.normcase(os.path.realpath(expected)):raise ValueError('PLUGIN_MARKETPLACE_WRONG_ROOT')
        old_marketplace=old.get('marketplaces',{}).get('codex-setting')
        if old_marketplace is not None and old_marketplace!=marketplace:raise ValueError('PLUGIN_MARKETPLACE_CHANGED')
        # Ignore only the requested plugin and its verified marketplace entries.
        for data in (old,new):
            plugins=data.get('plugins',{})
            plugins.pop('autorun@codex-setting',None)
            if not plugins:data.pop('plugins',None)
            markets=data.get('marketplaces',{})
            markets.pop('codex-setting',None)
            if not markets:data.pop('marketplaces',None)
        if old!=new:raise ValueError('UNRELATED_CONFIG_CHANGE_DURING_PLUGIN_INSTALL')
        entry['installed_sha256']=digest(after)
        save_json(root/'installation.json',marker)
        return {'status':'plugin_receipt_verified'}


def uninstall(root):
    marker=load_json(root/'installation.json',{})
    if marker.get('product')!=PRODUCT:raise ValueError('NO_OWNED_INSTALLATION')
    conflicts=[];restored=0
    with file_lock(root/'install.lock'):
        for name,item in marker['files'].items():
            p=Path(name);no_links(p)
            if p.exists() and digest(p.read_bytes())!=item['installed_sha256']:
                conflicts.append(name);continue
            if item['existed']:
                atomic_write(p,confined(root/'backups/files',item['backup']).read_bytes())
            elif p.exists():p.unlink()
            restored+=1
        save_json(root/'uninstall-report.json',{'restored':restored,'conflicts':conflicts})
    return {'restored':restored,'conflicts':conflicts,'retained':'Backups and own recovery receipts remain for review.'}
