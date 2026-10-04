from __future__ import annotations
import importlib.metadata as md, json, platform, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
wanted=['personal-world-model','scikit-learn','joblib','fastapi','pydantic','uvicorn','pytest','pytest-cov','httpx','matplotlib','setuptools']
items=[]
for name in wanted:
    try: version=md.version(name)
    except md.PackageNotFoundError: continue
    items.append({'name':name,'version':version,'purl':f'pkg:pypi/{name}@{version}'})
print(json.dumps({'format':'CycloneDX-inspired minimal inventory','python':sys.version.split()[0],'platform':platform.platform(),'components':items},indent=2,sort_keys=True))
