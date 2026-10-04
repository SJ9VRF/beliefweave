from __future__ import annotations
import json, platform, sys
from importlib.metadata import version, PackageNotFoundError
import importlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
packages=['scikit-learn','joblib','fastapi','pydantic','uvicorn','pytest','pytest-cov','httpx','matplotlib','setuptools','wheel']
versions={}
for name in packages:
    try: versions[name]=version(name)
    except PackageNotFoundError:
        try:
            mod=importlib.import_module(name.replace('-', '_'))
            versions[name]=getattr(mod,'__version__',None)
        except Exception:
            versions[name]=None
out={
  'python': sys.version.split()[0],
  'platform': platform.platform(),
  'packages': versions,
  'note': 'Environment snapshot for the validated release; not a cross-platform lockfile.'
}
(ROOT/'results'/'dependency_snapshot.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
md=['# Dependency Snapshot','',f"- Python: `{out['python']}`",f"- Platform: `{out['platform']}`",'', 'Validated package versions:','']
md += [f"- `{k}`: `{v}`" for k,v in versions.items()]
md += ['', '> This is a validated-environment snapshot, not a universal lockfile. The package metadata keeps compatible lower bounds for portability.', '']
(ROOT/'DEPENDENCY_SNAPSHOT.md').write_text('\n'.join(md))
print(json.dumps(out, indent=2))
