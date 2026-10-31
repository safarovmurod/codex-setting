import json
import os
from pathlib import Path
import subprocess
import sys

home=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
descriptor=home/'codex-setting.json'
if not descriptor.is_file():raise SystemExit('codex-setting насб нест; аввал Install.ps1-ро иҷро кун, шеф.')
config=json.loads(descriptor.read_text(encoding='utf-8'))
root=Path(config['root'])
if not root.is_absolute() or not (root/'installation.json').is_file():raise SystemExit('Installation unavailable.')
result=subprocess.run([config['python'],str(root/'app/runner.py'),'--install-root',str(root),*sys.argv[1:]],
    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
raise SystemExit(result.returncode)
