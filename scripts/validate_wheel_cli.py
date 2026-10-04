from __future__ import annotations
import json, os, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WHEELS=sorted((ROOT/'dist').glob('beliefweave-*.whl'))
if not WHEELS: raise SystemExit('no wheel found')
wheel=WHEELS[-1]
with zipfile.ZipFile(wheel) as z:
    eps=[n for n in z.namelist() if n.endswith('entry_points.txt')]
    if not eps: raise SystemExit('wheel missing entry_points.txt')
    entry=z.read(eps[0]).decode()
    if 'pwm = pwm.cli:main' not in entry: raise SystemExit('pwm console entrypoint missing')
with tempfile.TemporaryDirectory(prefix='pwm-wheel-target-') as td:
    target=Path(td)/'site'
    subprocess.run([sys.executable,'-m','pip','install','--no-deps','--target',str(target),str(wheel)],check=True,stdout=subprocess.DEVNULL)
    env=dict(os.environ); env['PYTHONPATH']=str(target)
    code='''\nimport json,importlib.metadata as md\nfrom pwm.cli import _doctor_payload,_demo_payload,_benchmark_payload\np={"version":md.version("beliefweave"),"doctor":_doctor_payload("/tmp/pwm-wheel-doctor.db"),"demo":_demo_payload(),"benchmark":_benchmark_payload()}\nprint(json.dumps(p))\n'''
    out=subprocess.check_output([sys.executable,'-c',code],env=env,text=True,cwd='/tmp')
    payload=json.loads(out)
    ok=(payload['doctor']['ok'] and payload['benchmark']['pass_rate']==1.0 and payload['demo']['hard_forget_ok'])
    result={'ok':ok,'wheel':wheel.name,'entrypoint':'pwm = pwm.cli:main','validation':payload}
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if ok else 1)
