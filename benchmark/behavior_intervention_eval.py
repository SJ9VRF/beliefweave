from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from benchmark.paper_grade_eval import build_cases,beliefweave,retrieval_only
from pwm.belief_governance import PersonalizationAction,memory_intervention_fidelity

def render(action, memory_present=True):
    if not memory_present:return 'Here are several dinner options based on your current request.'
    if action==PersonalizationAction.USE:return 'Since you like sushi, I would prioritize a sushi restaurant that fits the current request.'
    if action==PersonalizationAction.ASK:return 'I have an older or uncertain preference that may be relevant. Should I use it for this recommendation?'
    return 'Here are several dinner options based on your current request.'

def eval_policy(cases,fn):
    rows=[];causal=[];changed=[];expected_changed=[];exact=[]
    for c in cases:
        a=fn(c); y=render(a,True); y0=render(PersonalizationAction.ABSTAIN,False); ch=y!=y0
        rows.append({'id':c.id,'family':c.family,'gold_action':c.gold_action.value,'gold_personalization_causal':c.should_use,'gold_behavior_should_change':c.gold_action!=PersonalizationAction.ABSTAIN,'action':a.value,'changed_after_memory_removal':ch,'response':y,'counterfactual_without_memory':y0})
        causal.append(c.should_use);changed.append(a==PersonalizationAction.USE);expected_changed.append(c.gold_action!=PersonalizationAction.ABSTAIN);exact.append(a==c.gold_action)
    false_influence=sum((not g) and ch for g,ch in zip(causal,changed))/len(cases)
    missed=sum(g and not ch for g,ch in zip(causal,changed))/len(cases)
    behavior_changed=[r['changed_after_memory_removal'] for r in rows]
    return {'exact_action_accuracy':sum(exact)/len(exact),'personalization_intervention_fidelity':memory_intervention_fidelity(causal,changed),'behavior_intervention_fidelity':memory_intervention_fidelity(expected_changed,behavior_changed),'false_personalization_influence_rate':false_influence,'missed_personalization_influence_rate':missed,'rows':rows}

def main():
    cases=[c for c in build_cases() if c.split=='test']
    r={'benchmark':'ControlledResponseIntervention','n':len(cases),'beliefweave':eval_policy(cases,beliefweave),'retrieval_only':eval_policy(cases,retrieval_only),'scientific_boundary':'Deterministic response renderer isolates causal memory influence. It is not an LLM response-quality evaluation.'}
    (ROOT/'results'/'behavior_intervention.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='rows'} if isinstance(v,dict) else v for k,v in r.items()},indent=2))
if __name__=='__main__':main()
