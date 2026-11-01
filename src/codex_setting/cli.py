from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sys
import time

from .common import file_lock, load_json
from .installation import doctor,install,uninstall,finalize_plugin_config


def main(argv=None):
    p=argparse.ArgumentParser(prog='codex-setting')
    p.add_argument('--install-root',type=Path,required=True)
    p.add_argument('--codex-home',type=Path)
    sub=p.add_subparsers(dest='command',required=True)
    setup=sub.add_parser('install');setup.add_argument('--source',type=Path,required=True);setup.add_argument('--user-home',type=Path,required=True);setup.add_argument('--documents',type=Path,required=True)
    for name in ['doctor','status','uninstall']:sub.add_parser(name)
    sub.add_parser('finalize-plugin-config')
    live=sub.add_parser('runtime-doctor');live.add_argument('--thread',default=os.environ.get('CODEX_THREAD_ID'))
    watch=sub.add_parser('watch');watch.add_argument('--once',action='store_true')
    ar=sub.add_parser('autorun');ar.add_argument('action',choices=['on','off','status','complete']);ar.add_argument('--thread',default=os.environ.get('CODEX_THREAD_ID'));ar.add_argument('--explicit',action='store_true');ar.add_argument('--goal');ar.add_argument('--task');ar.add_argument('--evidence',type=Path)
    a=p.parse_args(argv);root=a.install_root.resolve()
    try:
        if a.command=='install':result=install(a.source,root,a.user_home,a.documents)
        elif a.command=='finalize-plugin-config':
            encoded=sys.stdin.buffer.readline(4000001)
            if len(encoded)>4000000:raise ValueError('PLUGIN_CONFIG_BASELINE_TOO_LARGE')
            result=finalize_plugin_config(root,base64.b64decode(encoded.strip(),validate=True))
        elif a.command in ['doctor','status']:result=doctor(root)
        elif a.command=='uninstall':result=uninstall(root)
        else:
            from .runtime import Runtime
            from .autorun import Controller,thread_id
            marker=load_json(root/'installation.json')
            if not marker or marker.get('product')!='codex-setting':raise ValueError('NO_OWNED_INSTALLATION')
            home=a.codex_home or Path(marker['user_home'])/'.codex'
            if a.command=='watch':
                from .watcher import Watcher
                watcher=Watcher(root,marker['host_id'],lambda:Runtime(root,home))
                with file_lock(root/'watcher.lock',timeout=.1):
                    while True:
                        result=watcher.tick()
                        if a.once:break
                        time.sleep(30)
                print(json.dumps(result,ensure_ascii=True));return
            local_action=a.command=='autorun' and a.action in ['off','status','complete']
            if local_action:
                runtime=None
                if a.action!='status':
                    try:runtime=Runtime(root,home)
                    except Exception:pass  # Revoking consent cannot depend on the desktop/runtime being available.
            else:runtime=Runtime(root,home)
            if a.command=='runtime-doctor':result=runtime.doctor(a.thread)
            else:
                controller=Controller(root/'state',marker['host_id'],runtime)
                if a.command=='watch':
                    with file_lock(root/'watcher.lock',timeout=.1):
                        while True:
                            result=controller.tick()
                            if a.once:break
                            time.sleep(30)
                else:
                    if not a.thread:raise ValueError('CURRENT_THREAD_ID_REQUIRED')
                    thread_id(a.thread)
                    if a.action=='on':
                        if a.thread!=os.environ.get('CODEX_THREAD_ID'):raise ValueError('ONLY_THE_CURRENT_THREAD_CAN_BE_ARMED')
                        result=controller.arm(a.thread,a.goal or '',a.explicit)
                    elif a.action=='off':result=controller.off(a.thread)
                    elif a.action=='complete':
                        if not a.evidence or a.evidence.stat().st_size>128000:raise ValueError('BOUNDED_EVIDENCE_FILE_REQUIRED')
                        result=controller.complete(a.thread,a.task,load_json(a.evidence))
                    else:result={'task':controller.store.task(marker['host_id'],a.thread),'attempts':controller.store.attempts(marker['host_id'],a.thread)}
        # Status is content-free. JSON uses ASCII escapes on Windows legacy terminals.
        if isinstance(result,dict) and 'files' in result:
            result=dict(result);files=result.pop('files')
            result['file_issues']=[f for f in files if f['status']!='ok']
        print(json.dumps(result,ensure_ascii=True,indent=2))
    except (ValueError,RuntimeError,OSError,TimeoutError) as error:
        print(json.dumps({'ok':False,'error':str(error)},ensure_ascii=True),file=sys.stderr)
        raise SystemExit(1)

if __name__=='__main__':main()
