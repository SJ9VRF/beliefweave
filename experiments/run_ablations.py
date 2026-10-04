from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json,random
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime,timezone,timedelta
from pwm.engine import PersonalMemoryEngine

@dataclass
class AppendOnly:
 items:list
 def __init__(self): self.items=[]
 def ingest(self,text,context,day): self.items.append((text.lower(),context,day))
 def old_retired(self,item): return not any(c=='food' and t==f'i love {item}.' for t,c,d in self.items)
 def temp_expired(self,item,day): return False

@dataclass
class LatestPredicate:
 items:dict
 def __init__(self): self.items={}
 def ingest(self,text,context,day):
  t=text.lower()
  if t.startswith('i love '): self.items[(context,'likes')]=(t[7:].rstrip('.'),day)
  if 'i dislike ' in t: self.items[(context,'dislikes')]=(t.split('i dislike ',1)[1].rstrip('.'),day)
  if "i'm avoiding " in t: self.items[(context,'avoids')]=(t.split("i'm avoiding ",1)[1].replace(' this month','').rstrip('.'),day)
 def old_retired(self,item):
  x=self.items.get(('food','likes')); return not (x and x[0]==item)
 def temp_expired(self,item,day): return False

def iso(day): return (datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(days=day)).isoformat()
def run(n=200):
 rng=random.Random(4); foods=['sushi','ramen','pasta','tacos']; systems={'append_only':[0,0],'latest_predicate':[0,0],'full_pwm':[0,0]}
 expiry={'append_only':[0,0],'latest_predicate':[0,0],'full_pwm':[0,0]}
 for i in range(n):
  food=rng.choice(foods)
  a=AppendOnly(); l=LatestPredicate()
  a.ingest(f'I love {food}.','food',0); l.ingest(f'I love {food}.','food',0)
  a.ingest(f'Actually, I dislike {food}.','food',10); l.ingest(f'Actually, I dislike {food}.','food',10)
  systems['append_only'][0]+=a.old_retired(food); systems['append_only'][1]+=1
  systems['latest_predicate'][0]+=l.old_retired(food); systems['latest_predicate'][1]+=1
  import tempfile
  with tempfile.TemporaryDirectory() as td:
   e=PersonalMemoryEngine(Path(td) / 'x.db', enable_ml=True); e.ingest('u',f'I love {food}.',context='food',timestamp=iso(0)); e.ingest('u',f'Actually, I dislike {food}.',context='food',timestamp=iso(10)); active=e.memories.list_active('u',now=iso(10)); good=not any(m.predicate=='likes' and m.value.lower()==food for m in active); systems['full_pwm'][0]+=good; systems['full_pwm'][1]+=1
   e2=PersonalMemoryEngine(Path(td) / 'y.db', enable_ml=True); e2.ingest('u',f"I'm avoiding {food} this month.",context='food',timestamp=iso(0)); good_exp=len(e2.memories.list_active('u',now=iso(40)))==0; expiry['full_pwm'][0]+=good_exp; expiry['full_pwm'][1]+=1
  for k,obj in [('append_only',a),('latest_predicate',l)]: expiry[k][0]+=obj.temp_expired(food,40); expiry[k][1]+=1
 out={'n_cases':n,'reversal_retirement_accuracy':{k:a/b for k,(a,b) in systems.items()},'temporary_expiry_accuracy':{k:a/b for k,(a,b) in expiry.items()},'note':'Controlled ablation over deterministic baselines.'}
 Path('results/ablations.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
if __name__=='__main__': run()
