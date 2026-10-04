from __future__ import annotations
import json,sys
from pathlib import Path
from dataclasses import dataclass
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from pwm.belief_governance import DecisionAwareBeliefGate,PersonalizationAction,counterfactual_personalization_regret
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType,MemoryStatus
NOW='2000-06-01T12:00:00+00:00'
@dataclass(frozen=True)
class Case: id:str; family:str; memory:MemoryRecord; context:str|None; conflict:bool; should_use:bool
def mem(*,confidence=.9,source=SourceType.EXPLICIT,context=None,valid_until=None,status=MemoryStatus.ACTIVE,verified=False):
    return MemoryRecord(user_id='u',subject='user',predicate='food.preference',value='likes sushi',memory_type=MemoryType.PREFERENCE,source_type=source,confidence=confidence,source_event_ids=['evt'],context_scope=context,valid_until=valid_until,status=status,user_verified=verified)
def cases():
    out=[]
    for i in range(25):out.append(Case(f'valid-explicit-{i}','valid_explicit',mem(confidence=.84+(i%5)*.03,verified=i%4==0),'dining',False,True))
    for i in range(25):out.append(Case(f'valid-observed-{i}','valid_observed',mem(confidence=.82+(i%4)*.04,source=SourceType.OBSERVED),'dining',False,True))
    for i in range(25):out.append(Case(f'stale-{i}','stale',mem(confidence=.99,valid_until='1999-01-01T00:00:00+00:00'),'dining',False,False))
    for i in range(25):out.append(Case(f'context-{i}','context_mismatch',mem(confidence=.99,context='work'),'friends',False,False))
    for i in range(25):out.append(Case(f'weak-{i}','weak_inferred',mem(confidence=.55+(i%4)*.03,source=SourceType.INFERRED),'dining',False,False))
    for i in range(25):out.append(Case(f'conflict-{i}','unresolved_conflict',mem(confidence=.99),'dining',True,False))
    for i in range(25):out.append(Case(f'inactive-{i}','inactive',mem(confidence=.99,status=MemoryStatus.SUPERSEDED),'dining',False,False))
    for i in range(25):out.append(Case(f'medium-{i}','medium_authority',mem(confidence=.62,source=SourceType.EXPLICIT),'dining',False,False))
    return out
def retrieval_only(c):return PersonalizationAction.USE if c.memory.status==MemoryStatus.ACTIVE else PersonalizationAction.ABSTAIN
def confidence_only(c):
    if c.memory.status!=MemoryStatus.ACTIVE:return PersonalizationAction.ABSTAIN
    return PersonalizationAction.USE if c.memory.confidence>=.78 else PersonalizationAction.ABSTAIN
def provenance_only(c):
    if c.memory.status!=MemoryStatus.ACTIVE:return PersonalizationAction.ABSTAIN
    return PersonalizationAction.USE if c.memory.source_type in {SourceType.EXPLICIT,SourceType.OBSERVED} else PersonalizationAction.ABSTAIN
def temporal_context(c):
    if c.memory.status!=MemoryStatus.ACTIVE:return PersonalizationAction.ABSTAIN
    if c.memory.valid_until and c.memory.valid_until<NOW:return PersonalizationAction.ABSTAIN
    if c.memory.context_scope and c.context and c.memory.context_scope.lower()!=c.context.lower():return PersonalizationAction.ABSTAIN
    return PersonalizationAction.USE
def metrics(gold,acts):
    use=[a==PersonalizationAction.USE for a in acts];tp=sum(g and u for g,u in zip(gold,use));fp=sum((not g) and u for g,u in zip(gold,use));fn=sum(g and not u for g,u in zip(gold,use))
    return {'cpr':counterfactual_personalization_regret(gold,acts),'false_personalization_rate':fp/len(gold),'use_precision':tp/max(tp+fp,1),'use_recall':tp/max(tp+fn,1),'ask_rate':sum(a==PersonalizationAction.ASK for a in acts)/len(acts),'abstain_rate':sum(a==PersonalizationAction.ABSTAIN for a in acts)/len(acts)}
def evaluate():
    cs=cases();gold=[c.should_use for c in cs];g=DecisionAwareBeliefGate();systems={'retrieval_only':[retrieval_only(c) for c in cs],'confidence_only':[confidence_only(c) for c in cs],'provenance_only':[provenance_only(c) for c in cs],'temporal_context_gate':[temporal_context(c) for c in cs],'beliefweave':[g.decide(c.memory,context=c.context,now=NOW,unresolved_conflict=c.conflict).action for c in cs]}
    sweep=[]
    for ut in [.70,.75,.78,.80,.85,.90]:
      for at in [.45,.50,.52,.55,.60]:
       if at>=ut:continue
       gg=DecisionAwareBeliefGate(ut,at); aa=[gg.decide(c.memory,context=c.context,now=NOW,unresolved_conflict=c.conflict).action for c in cs]; sweep.append({'use_threshold':ut,'ask_threshold':at,**metrics(gold,aa)})
    r={'benchmark':'AuthorityAblationBench','n':len(cs),'systems':{k:metrics(gold,v) for k,v in systems.items()},'threshold_sweep':sweep,'scientific_boundary':'Controlled synthetic mechanism-isolation benchmark; not real-user utility or cross-paper SOTA.'}
    (ROOT/'results'/'authority_ablation.json').write_text(json.dumps(r,indent=2));return r
if __name__=='__main__':print(json.dumps(evaluate(),indent=2))
