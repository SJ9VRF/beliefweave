from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

DATASETS={
  'longmemeval_oracle':{
    'url':'https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_oracle.json',
    'filename':'longmemeval_oracle.json',
    'sha256':'821a2034d219ab45846873dd14c14f12cfe7776e73527a483f9dac095d38620c',
    'license':'MIT',
  },
  'locomo10':{
    'url':'https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json',
    'filename':'locomo10.json',
    'sha256':'79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4',
    'license':'upstream dataset terms; do not redistribute without checking current upstream license',
  },
  'personamem_questions_32k':{
    'url':'https://huggingface.co/datasets/bowen-upenn/PersonaMem-v1/resolve/main/questions_32k.csv',
    'filename':'questions_32k.csv','sha256':None,'license':'MIT',
  },
  'personamem_contexts_32k':{
    'url':'https://huggingface.co/datasets/bowen-upenn/PersonaMem-v1/resolve/main/shared_contexts_32k.jsonl',
    'filename':'shared_contexts_32k.jsonl','sha256':None,'license':'MIT',
  },
}

def sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out-dir',default='external_data');ap.add_argument('--only',action='append',choices=sorted(DATASETS));ap.add_argument('--manifest',default='results/external_fetch_manifest.json');a=ap.parse_args()
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True);keys=a.only or list(DATASETS);rows=[]
    for key in keys:
        spec=DATASETS[key];dst=out/spec['filename']
        try:
            if not dst.exists():urllib.request.urlretrieve(spec['url'],dst)
            digest=sha(dst);ok=spec['sha256'] in {None,digest}
            rows.append({'dataset':key,'path':str(dst),'bytes':dst.stat().st_size,'sha256':digest,'expected_sha256':spec['sha256'],'verified':ok,'license':spec['license']})
            if not ok:raise RuntimeError(f'checksum mismatch for {key}')
        except Exception as e:
            rows.append({'dataset':key,'path':str(dst),'verified':False,'error':f'{type(e).__name__}: {e}','license':spec['license']})
    manifest={'datasets':rows,'all_verified':all(x.get('verified') for x in rows),'note':'Third-party raw bytes are fetched into an external_data directory and are not vendored into the BeliefWeave release.'}
    Path(a.manifest).parent.mkdir(parents=True,exist_ok=True);Path(a.manifest).write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
