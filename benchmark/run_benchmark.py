from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json,tempfile,time,statistics
from pathlib import Path
from pwm.engine import PersonalMemoryEngine
from pwm.simulation import LongitudinalUserGenerator

class NaiveMemory:
 def __init__(self): self.items=[]
 def ingest(self,text,context): self.items.append((text.lower(),context))
 def last_liked_food(self):
  likes=[t[7:].rstrip('.') for t,c in self.items if c=='food' and t.startswith('i love ')]
  return likes[-1] if likes else None
 def still_claims_like(self,item): return any(c=='food' and t==f'i love {item.lower()}.' for t,c in self.items)

def run(n_users=20,n_turns=100):
 g=LongitudinalUserGenerator(seed=101)
 final_world=[]; final_naive=[]; reversal_world=[]; reversal_naive=[]; stale=[]; latencies=[]; active_counts=[]
 for ui in range(n_users):
  user=f'b{ui:04d}'; traj=g.trajectory(user,n_turns)
  with tempfile.TemporaryDirectory() as td:
   e=PersonalMemoryEngine(Path(td) / 'b.db', enable_ml=True); naive=NaiveMemory(); initial_food=traj[0].ground_truth['food_like']
   for turn in traj:
    t0=time.perf_counter(); e.ingest(user,turn.text,context=turn.context,timestamp=turn.timestamp); latencies.append((time.perf_counter()-t0)*1000); naive.ingest(turn.text,turn.context)
    if turn.kind=='drift' and turn.text.lower().startswith('actually, i dislike'):
     active=e.memories.list_active(user,now=turn.timestamp)
     world_still_likes=any(m.context_scope=='food' and m.predicate=='likes' and m.value.lower()==initial_food.lower() for m in active)
     reversal_world.append(int(not world_still_likes)); reversal_naive.append(int(not naive.still_claims_like(initial_food)))
   now=traj[-1].timestamp; active=e.memories.list_active(user,now=now); active_counts.append(len(active)); gt=traj[-1].ground_truth['food_like']
   world_food=[m.value.lower() for m in active if m.context_scope=='food' and m.predicate=='likes']
   final_world.append(int(gt.lower() in world_food)); final_naive.append(int((naive.last_liked_food() or '').lower()==gt.lower()))
   stale_food=[m for m in active if m.context_scope=='food' and m.predicate=='likes' and m.value.lower()!=gt.lower()]
   stale.append(len(stale_food))
 result={
  'benchmark':'MemWorldBench controlled longitudinal slice','n_users':n_users,'n_turns_per_user':n_turns,'interactions':n_users*n_turns,
  'final_current_food_accuracy':{'personal_world_model':sum(final_world)/len(final_world),'naive_append_only':sum(final_naive)/len(final_naive)},
  'preference_reversal_old_belief_retirement_accuracy':{'personal_world_model':sum(reversal_world)/len(reversal_world),'naive_append_only':sum(reversal_naive)/len(reversal_naive)},
  'mean_active_stale_food_memories':statistics.mean(stale),'mean_ingest_latency_ms':statistics.mean(latencies),'p95_ingest_latency_ms':sorted(latencies)[int(.95*len(latencies))-1],'mean_active_memory_count':statistics.mean(active_counts),
  'note':'Synthetic controlled benchmark; engineering validation only, not evidence of performance on real users.'}
 Path('results').mkdir(exist_ok=True); Path('results/benchmark.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); return result
if __name__=='__main__': run()
