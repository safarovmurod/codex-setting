"""Fail before publication on unsafe paths, credentials or changed owner payload."""
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
hashes=json.loads((root/'profiles/payload-sha256.json').read_text())
for rel,expected in hashes.items():
 p=root/'payload'/rel
 assert p.resolve().is_relative_to((root/'payload').resolve())
 assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected,rel
bad=[]
pattern=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{35,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)')
for p in root.rglob('*'):
 if not p.is_file() or any(x in {'.git','__pycache__','.venv','work'} for x in p.relative_to(root).parts):continue
 rel=p.relative_to(root).as_posix()
 if p.is_symlink() or p.name.lower() in {'auth.json','cookies.json','credentials.json'} or p.suffix.lower() in {'.sqlite','.db','.key','.pem'} or p.name.startswith('.env'):
  bad.append(rel);continue
 if pattern.search(p.read_bytes()):bad.append(rel)
assert not bad,'RELEASE_REFUSED: '+', '.join(bad)
print('Release scan PASS; '+str(len(hashes))+' owner payload hashes verified.')
