from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json,tempfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
from pwm.engine import PersonalMemoryEngine

def ts(days): return (datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(days=days)).isoformat()
def main():
 rows=[json.loads(x) for x in Path('benchmark/data/hard_scenarios_360.jsonl').read_text().splitlines() if x.strip()]
 ok=0; by={}
 for r in rows:
  cat=r['category']; passed=False
  with tempfile.TemporaryDirectory() as td:
   e=PersonalMemoryEngine(Path(td) / 'x.db', enable_ml=True); uid=r['id']
   turns=r['turns']
   for j,t in enumerate(turns):
    if isinstance(t,dict): e.ingest(uid,t['text'],context=t.get('context'),timestamp=ts(j))
    else: e.ingest(uid,t,timestamp=ts(j))
   allm=e.memories.list_all(uid); active=e.memories.list_active(uid,now=ts(10))
   if cat=='preference_reversal': passed=(len(active)==1 and active[0].predicate=='dislikes')
   elif cat=='context_dependence': passed=(len(active)==2)
   elif cat=='temporary_state': passed=(len(e.memories.list_active(uid,now=ts(10)))==1 and len(e.memories.list_active(uid,now=ts(40)))==0)
   elif cat=='explicit_correction': passed=(len(active)==1 and active[0].predicate=='dislikes' and active[0].user_verified)
   elif cat=='third_party_attribution': passed=(len(allm)==0)
   elif cat=='multilingual': passed=(len(active)==1 and active[0].predicate=='likes' and active[0].value.lower()==r['expected']['value'].lower())
  ok+=int(passed); by.setdefault(cat,[0,0]); by[cat][0]+=int(passed); by[cat][1]+=1
 out={'overall_accuracy':ok/len(rows),'n_scenarios':len(rows),'by_category':{k:{'accuracy':a/b,'n':b} for k,(a,b) in by.items()},'note':'Template-generated hard scenarios; deterministic engineering validation.'}
 Path('results/hard_scenarios.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)); print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
