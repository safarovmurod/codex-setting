from __future__ import annotations

import copy
import json
from pathlib import Path
import tomllib


def toml_dump(value: dict) -> str:
    """Small TOML writer for the standard scalar/table/array types in Codex config."""
    lines = []
    key = lambda s: json.dumps(s, ensure_ascii=False)

    def scalar(v):
        if isinstance(v, bool): return str(v).lower()
        if isinstance(v, (str, int, float)): return json.dumps(v, ensure_ascii=False, allow_nan=False)
        if isinstance(v, list): return '['+', '.join(scalar(x) for x in v)+']'
        if isinstance(v, dict): return '{'+', '.join(key(k)+' = '+scalar(x) for k,x in v.items())+'}'
        raise ValueError('UNSUPPORTED_TOML_TYPE')

    def emit(table, path=(), header=True):
        if path and header: lines.append('['+'.'.join(key(p) for p in path)+']')
        for k,v in table.items():
            if not isinstance(v, dict): lines.append(key(k)+' = '+scalar(v))
        for k,v in table.items():
            if isinstance(v, dict):
                lines.append(''); emit(v, (*path,k))
    emit(value)
    result='\n'.join(lines)+'\n'
    if tomllib.loads(result) != value: raise ValueError('TOML_ROUNDTRIP_FAILED')
    return result


def merge(base, desired):
    result=copy.deepcopy(base)
    for k,v in desired.items():
        result[k]=merge(result[k],v) if isinstance(v,dict) and isinstance(result.get(k),dict) else copy.deepcopy(v)
    return result


def expand(value, replacements):
    if isinstance(value,str):
        for k,v in replacements.items(): value=value.replace('${'+k+'}',str(v).replace('\\','/'))
        return value
    if isinstance(value,list): return [expand(x,replacements) for x in value]
    if isinstance(value,dict): return {expand(k,replacements):expand(v,replacements) for k,v in value.items()}
    return value


def desired_config(profile, user_home: Path, documents: Path):
    return expand(profile['config'],{'USERPROFILE':user_home,'DOCUMENTS':documents})
