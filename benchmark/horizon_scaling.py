from __future__ import annotations
import json,tempfile,time,statistics,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from pwm.events.store import EventStore
from pwm.memory.store import MemoryStore
from pwm.memory.schema import Event,MemoryRecord,MemoryType,SourceType,MemoryStatus
from pwm.belief_governance import DecisionAwareBeliefGate

def run_horizon(turns):
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/'scale.sqlite'; es=EventStore(db); ms=MemoryStore(db); gate=DecisionAwareBeliefGate(); base=datetime(2000,1,1,tzinfo=timezone.utc)
        event_lat=[]; memory_lat=[]; gate_lat=[]; last_by_key={}
        for t in range(turns):
            ts=(base+timedelta(minutes=t)).isoformat(); ev=Event(user_id='u',raw_text='ordinary interaction',timestamp=ts)
            st=time.perf_counter();es.add(ev);event_lat.append((time.perf_counter()-st)*1000)
            # 2% of turns produce a durable preference update; every second update supersedes prior value for same slot.
            if t%50==0:
                key=f'slot{(t//50)%25}'; value=f'value{t//50}'; m=MemoryRecord(user_id='u',subject='user',predicate=key,value=value,memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_ids=[ev.id],created_at=ts,updated_at=ts)
                st=time.perf_counter(); ms.add(m); old=last_by_key.get(key)
                if old:ms.supersede(old,m.id)
                last_by_key[key]=m.id;memory_lat.append((time.perf_counter()-st)*1000)
                st=time.perf_counter();gate.decide(m,context='general',now=ts);gate_lat.append((time.perf_counter()-st)*1000)
        active=ms.list_active('u',now=(base+timedelta(minutes=turns)).isoformat()); allm=ms.list_all('u')
        dup=len(active)-len({m.predicate for m in active})
        def p95(xs): return sorted(xs)[max(0,int(.95*len(xs))-1)] if xs else 0
        return {'turns':turns,'event_rows':turns,'memory_rows':len(allm),'active_memories':len(active),'active_duplicate_single_value_slots':dup,'mean_event_write_ms':statistics.mean(event_lat),'p95_event_write_ms':p95(event_lat),'mean_memory_update_ms':statistics.mean(memory_lat) if memory_lat else 0,'p95_memory_update_ms':p95(memory_lat),'mean_gate_ms':statistics.mean(gate_lat) if gate_lat else 0,'p95_gate_ms':p95(gate_lat)}

def main():
    rows=[run_horizon(n) for n in [10,100,1000,10000]]
    r={'benchmark':'MemoryCoreHorizonScaling','rows':rows,'scientific_boundary':'Local SQLite memory-core stress test with 2% durable-memory rate. This isolates persistence/update/gating scale; it is not end-to-end LLM latency.'}
    (ROOT/'results'/'horizon_scaling.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
