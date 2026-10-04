from __future__ import annotations

import json
import statistics
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pwm.engine import PersonalMemoryEngine
from pwm.integrity import audit_database


def run(workers:int=12, ops_per_worker:int=40) -> dict:
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/'concurrency.sqlite'
        engine=PersonalMemoryEngine(db)
        lat=[]; errors=[]
        def worker(i:int):
            user=f'u{i}'
            local=[]
            for j in range(ops_per_worker):
                t=time.perf_counter()
                try:
                    engine.ingest(user, f'I prefer concise answer format {j}.', context='work')
                    if j % 7 == 0:
                        engine.governed_recall(user,'answer style concise',limit=3,context='work')
                except Exception as exc:
                    errors.append({'worker':i,'op':j,'type':type(exc).__name__,'message':str(exc)[:200]})
                local.append((time.perf_counter()-t)*1000)
            return local
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs=[pool.submit(worker,i) for i in range(workers)]
            for f in as_completed(futs): lat.extend(f.result())
        audit=audit_database(db)
        counts={f'u{i}':len(engine.events.list_for_user(f'u{i}',limit=None)) for i in range(workers)}
        sorted_lat=sorted(lat)
        def pct(p):
            if not sorted_lat:return 0.0
            return sorted_lat[min(len(sorted_lat)-1,int((len(sorted_lat)-1)*p))]
        return {
            'suite':'Concurrent Ingest/Recall Integrity Stress',
            'workers':workers,
            'ops_per_worker':ops_per_worker,
            'expected_ingests':workers*ops_per_worker,
            'observed_ingests':sum(counts.values()),
            'error_count':len(errors),
            'errors':errors[:20],
            'integrity_ok':audit['ok'],
            'integrity_error_count':audit['error_count'],
            'per_user_event_count_min':min(counts.values()),
            'per_user_event_count_max':max(counts.values()),
            'latency_ms':{
                'median':statistics.median(lat) if lat else 0.0,
                'p95':pct(.95),
                'p99':pct(.99),
            },
            'boundary':'Single-process multi-threaded SQLite stress. This is not a distributed or multi-process production load test.'
        }


def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=12);ap.add_argument('--ops-per-worker',type=int,default=40);ap.add_argument('--out',default='results/concurrency_integrity.json');a=ap.parse_args()
    r=run(a.workers,a.ops_per_worker);Path(a.out).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
