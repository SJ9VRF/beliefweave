from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json,tempfile,time,random
from pathlib import Path
from datetime import datetime,timezone,timedelta
from pwm.engine import PersonalMemoryEngine
ROOT=Path(__file__).resolve().parents[1]
random.seed(13)
PREF=['sushi','jazz','tea','running','quiet cafes','window seats']
GOALS=['publish a paper','learn French','run a marathon','finish my thesis']

def main(users=20,turns=100):
    start=time.perf_counter(); ingested=0; retrievals=0; stale=0
    with tempfile.TemporaryDirectory() as d:
      e=PersonalMemoryEngine(Path(d) / 'stress.sqlite', enable_ml=True)
      base=datetime(2026,1,1,tzinfo=timezone.utc)
      for u in range(users):
        uid=f'u{u}'
        for t in range(turns):
          ts=(base+timedelta(days=t)).isoformat()
          if t%40==0:
            item=random.choice(PREF); text=f'I love {item}.'
          elif t%40==20:
            item=random.choice(PREF); text=f'Actually, I dislike {item}.'
          elif t%25==0:
            text=f'My goal is to {random.choice(GOALS)}.'
          elif t%33==0:
            text='I am avoiding raw fish this month.'
          else:
            text='Explain attention mechanisms.'
          e.ingest(uid,text,timestamp=ts); ingested+=1
          if t%50==0:
            e.recall(uid,'What do you know about my preferences?',limit=3,now=ts); retrievals+=1
        # structural invariant: no exact active likes/dislikes contradiction for same value.
        active=e.memories.list_active(uid,now=(base+timedelta(days=turns)).isoformat())
        likes={m.value.lower() for m in active if m.predicate=='likes'}; dislikes={m.value.lower() for m in active if m.predicate=='dislikes'}
        stale+=len(likes&dislikes)
    elapsed=time.perf_counter()-start
    res={'users':users,'turns_per_user':turns,'interactions':ingested,'retrieval_calls':retrievals,'elapsed_seconds':elapsed,'interactions_per_second':ingested/elapsed,'active_exact_contradictions':stale,'pass':stale==0}
    (ROOT/'results'/'stress_test.json').write_text(json.dumps(res,indent=2)); print(json.dumps(res,indent=2))
if __name__=='__main__':main()
