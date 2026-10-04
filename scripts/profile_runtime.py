#!/usr/bin/env python3
from __future__ import annotations
import json, os, statistics, tempfile, time, tracemalloc
from pathlib import Path
import psutil
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from pwm.engine import PersonalMemoryEngine

N=int(os.environ.get('PWM_PROFILE_N','400'))
queries=['food preference','current goal','what should I remember','music preference']
texts=['I love sushi.','My goal is to publish a paper.','I like jazz.','I prefer concise answers.','Actually, I dislike sushi.']
proc=psutil.Process(); rss0=proc.memory_info().rss
tracemalloc.start(); ingest_ms=[]; recall_ms=[]
with tempfile.TemporaryDirectory(prefix='pwm-profile-') as td:
  e=PersonalMemoryEngine(Path(td) / 'profile.db', enable_ml=True)
  for i in range(N):
    t0=time.perf_counter(); e.ingest('profile-user',texts[i%len(texts)],context='profile'); ingest_ms.append((time.perf_counter()-t0)*1000)
    if i%4==0:
      q=queries[(i//4)%len(queries)]; t0=time.perf_counter(); e.recall('profile-user',q,limit=5,context='profile'); recall_ms.append((time.perf_counter()-t0)*1000)
  db_bytes=(Path(td)/'profile.db').stat().st_size
current, peak=tracemalloc.get_traced_memory(); tracemalloc.stop(); rss1=proc.memory_info().rss
pct=lambda xs,p: sorted(xs)[min(len(xs)-1,max(0,int(len(xs)*p)-1))]
result={
 'environment_note':'Single-process local prototype profile; not a production benchmark.',
 'interactions':N,'recalls':len(recall_ms),
 'ingest_ms':{'median':statistics.median(ingest_ms),'p95':pct(ingest_ms,.95),'max':max(ingest_ms)},
 'recall_ms':{'median':statistics.median(recall_ms),'p95':pct(recall_ms,.95),'max':max(recall_ms)},
 'rss_delta_bytes':rss1-rss0,'tracemalloc_peak_bytes':peak,'db_bytes':db_bytes,
}
out=ROOT/'results'/'runtime_profile.json'; out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2))
