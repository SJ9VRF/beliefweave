from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from benchmark.paper_grade_eval import build_cases,NOW
from pwm.belief_governance import DecisionAwareBeliefGate,PersonalizationAction
from pwm.memory.schema import MemoryStatus,SourceType

class Mutant:
    def __init__(self,name):self.name=name;self.base=DecisionAwareBeliefGate()
    def decide(self,c):
        m=c.memory
        if self.name=='no_status':
            # clone behavior while bypassing lifecycle by temporarily forcing active
            old=m.status; m.status=MemoryStatus.ACTIVE
            try:return self.base.decide(m,context=c.context,now=NOW,unresolved_conflict=c.conflict).action
            finally:m.status=old
        if self.name=='no_time': return self.base.decide(m,context=c.context,now=None,unresolved_conflict=c.conflict).action
        if self.name=='no_context': return self.base.decide(m,context=None,now=NOW,unresolved_conflict=c.conflict).action
        if self.name=='no_conflict': return self.base.decide(m,context=c.context,now=NOW,unresolved_conflict=False).action
        if self.name=='no_provenance':
            # neutralize source adjustments via OBSERVED
            old=m.source_type;m.source_type=SourceType.OBSERVED
            try:return self.base.decide(m,context=c.context,now=NOW,unresolved_conflict=c.conflict).action
            finally:m.source_type=old
        if self.name=='always_use_active': return PersonalizationAction.USE if m.status==MemoryStatus.ACTIVE else PersonalizationAction.ABSTAIN
        raise KeyError(self.name)

def main():
    test=[c for c in build_cases() if c.split=='test']
    base=DecisionAwareBeliefGate(); base_pred=[base.decide(c.memory,context=c.context,now=NOW,unresolved_conflict=c.conflict).action for c in test]
    base_acc=sum(p==c.gold_action for p,c in zip(base_pred,test))/len(test)
    rows={}; killed=0
    for name in ['no_status','no_time','no_context','no_conflict','no_provenance','always_use_active']:
        mu=Mutant(name); pred=[mu.decide(c) for c in test]; acc=sum(p==c.gold_action for p,c in zip(pred,test))/len(test)
        changed=sum(p!=b for p,b in zip(pred,base_pred)); kill=acc<base_acc-1e-12; killed+=int(kill)
        rows[name]={'exact_action_accuracy':acc,'delta_vs_base':acc-base_acc,'changed_decisions':changed,'killed':kill}
    out={'suite':'Benchmark Mutation Adequacy','benchmark':'BeliefShiftBench-v2 frozen test','base_accuracy':base_acc,'n_mutants':len(rows),'mutants_killed':killed,'mutation_score':killed/len(rows),'mutants':rows,
         'interpretation':'Fault injection checks whether the benchmark detects removal of semantically important decision mechanisms. Mutation score is benchmark adequacy evidence, not model generalization evidence.'}
    (ROOT/'results'/'mutation_adequacy.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
