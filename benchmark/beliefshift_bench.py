from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from pwm.belief_governance import DecisionAwareBeliefGate,PersonalizationAction,counterfactual_personalization_regret,memory_intervention_fidelity
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType,MemoryStatus
NOW='2000-06-01T12:00:00+00:00'
def mem(confidence=.95,source=SourceType.EXPLICIT,context=None,valid_until=None,status=MemoryStatus.ACTIVE,verified=False):
    return MemoryRecord(user_id='u',subject='user',predicate='food.preference',value='likes sushi',memory_type=MemoryType.PREFERENCE,source_type=source,confidence=confidence,source_event_ids=['evt_x'],context_scope=context,valid_until=valid_until,status=status,user_verified=verified)
def cases():
    out=[]
    for i in range(40):out.append((f'valid-{i}',mem(confidence=.88+(i%5)*.02,verified=i%3==0),'dining',True,False))
    for i in range(30):out.append((f'stale-{i}',mem(valid_until='2000-01-01T00:00:00+00:00'),'dining',False,False))
    for i in range(30):out.append((f'context-{i}',mem(context='work'),'friends',False,False))
    for i in range(30):out.append((f'weak-{i}',mem(confidence=.50+(i%5)*.02,source=SourceType.INFERRED),'dining',False,False))
    for i in range(30):out.append((f'conflict-{i}',mem(confidence=.93),'dining',False,True))
    for i in range(20):out.append((f'medium-{i}',mem(confidence=.60,source=SourceType.EXPLICIT),'dining',False,False))
    return out
def evaluate():
    gate=DecisionAwareBeliefGate();gold=[];pred=[];baseline=[];rows=[]
    for cid,m,ctx,should_use,conflict in cases():
        d=gate.decide(m,context=ctx,now=NOW,unresolved_conflict=conflict)
        gold.append(should_use);pred.append(d.action);baseline.append(PersonalizationAction.USE if m.status==MemoryStatus.ACTIVE else PersonalizationAction.ABSTAIN)
        rows.append({'id':cid,'gold_should_use':should_use,'action':d.action.value,'score':d.score,'reason':d.reason})
    changed=[a==PersonalizationAction.USE for a in pred]
    return {'benchmark':'BeliefShiftBench','n':len(rows),'beliefweave':{'decision_success_rate':sum((g==(a==PersonalizationAction.USE)) for g,a in zip(gold,pred))/len(gold),'counterfactual_personalization_regret':counterfactual_personalization_regret(gold,pred),'false_personalization_rate':sum((not g) and a==PersonalizationAction.USE for g,a in zip(gold,pred))/len(gold),'use_precision':sum(g and a==PersonalizationAction.USE for g,a in zip(gold,pred))/max(1,sum(a==PersonalizationAction.USE for a in pred)),'intervention_fidelity':memory_intervention_fidelity(gold,changed)},'retrieval_only_baseline':{'decision_success_rate':sum((g==(a==PersonalizationAction.USE)) for g,a in zip(gold,baseline))/len(gold),'counterfactual_personalization_regret':counterfactual_personalization_regret(gold,baseline),'false_personalization_rate':sum((not g) and a==PersonalizationAction.USE for g,a in zip(gold,baseline))/len(gold)},'scientific_boundary':'Controlled synthetic governance benchmark; not a real-user or SOTA claim.','rows':rows}
if __name__=='__main__':
    r=evaluate();(ROOT/'results'/'beliefshift_bench.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
