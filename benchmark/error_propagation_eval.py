from __future__ import annotations
import json,sys
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from benchmark.paper_grade_eval import build_cases,beliefweave
from pwm.belief_governance import PersonalizationAction
from pwm.memory.schema import SourceType,MemoryStatus

def acc(cases,fn):return sum(fn(c)==c.gold_action for c in cases)/len(cases)
def main():
    cs=[c for c in build_cases() if c.split=='test']; base=acc(cs,beliefweave); rows=[]
    perturb={
      'extractor_source_corruption': lambda c: replace(c,memory=replace(c.memory,source_type=SourceType.EXPLICIT,confidence=max(.9,c.memory.confidence))),
      'state_status_corruption': lambda c: replace(c,memory=replace(c.memory,status=MemoryStatus.ACTIVE,valid_until=None)),
      'context_loss': lambda c: replace(c,context=None,memory=replace(c.memory,context_scope=None)),
      'conflict_loss': lambda c: replace(c,conflict=False),
    }
    for name,tx in perturb.items():
        pcs=[tx(c) for c in cs]; a=acc(pcs,beliefweave);rows.append({'fault':name,'decision_accuracy':a,'delta_from_clean':a-base})
    # Authority-stage and generation-stage forced errors are measured directly.
    forced_use=sum(c.gold_action==PersonalizationAction.USE for c in cs)/len(cs)
    generation_flip=0.0 # every correct authority decision is inverted at rendering stage
    rows.extend([{'fault':'authority_forced_use','decision_accuracy':forced_use,'delta_from_clean':forced_use-base},{'fault':'generation_inverts_authority','decision_accuracy':generation_flip,'delta_from_clean':generation_flip-base}])
    r={'benchmark':'ControlledFaultInjection','n':len(cs),'clean_decision_accuracy':base,'faults':rows,'scientific_boundary':'Synthetic fault injection diagnoses error propagation; it is not an empirical estimate of production fault frequencies.'}
    (ROOT/'results'/'error_propagation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
if __name__=='__main__':main()
