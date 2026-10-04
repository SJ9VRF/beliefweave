from __future__ import annotations
import json, random, statistics, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from benchmark.paper_grade_eval import Case, mem, metrics, retrieval_only, confidence_only, temporal_context, metadata_score, beliefweave, cost_policy
from pwm.belief_governance import PersonalizationAction
from pwm.memory.schema import SourceType,MemoryStatus

FAMILIES=('valid_explicit','valid_observed','stale','context_mismatch','weak_inferred','unresolved_conflict','inactive','medium_authority')
SYSTEMS={'retrieval_only':retrieval_only,'confidence_only':confidence_only,'temporal_context':temporal_context,'metadata_score_no_hard_veto':metadata_score,'cost_sensitive_authority':cost_policy,'beliefweave':beliefweave}

def build(seed:int,n_per_family:int=50):
    rng=random.Random(seed); out=[]
    for fam in FAMILIES:
        for i in range(n_per_family):
            if fam=='valid_explicit': c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.80,.99),source=SourceType.EXPLICIT,verified=rng.random()<.2),rng.choice(['dining','travel','friends']),False,PersonalizationAction.USE)
            elif fam=='valid_observed': c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.82,.99),source=SourceType.OBSERVED),rng.choice(['dining','travel','friends']),False,PersonalizationAction.USE)
            elif fam=='stale': c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.80,.99),valid_until='1999-12-01T00:00:00+00:00'),rng.choice(['dining','travel']),False,PersonalizationAction.ABSTAIN)
            elif fam=='context_mismatch':
                left,right=rng.choice([('work','friends'),('travel','home'),('gym','work')]); c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.80,.99),context=left),right,False,PersonalizationAction.ABSTAIN)
            elif fam=='weak_inferred': c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.28,.58),source=SourceType.INFERRED),rng.choice(['dining','travel']),False,PersonalizationAction.ABSTAIN)
            elif fam=='unresolved_conflict': c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.75,.99),source=SourceType.EXPLICIT),rng.choice(['dining','travel']),True,PersonalizationAction.ASK)
            elif fam=='inactive': c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.85,.99),status=rng.choice([MemoryStatus.SUPERSEDED,MemoryStatus.ARCHIVED,MemoryStatus.EXPIRED])),rng.choice(['dining','travel']),False,PersonalizationAction.ABSTAIN)
            else: c=Case(f'{fam}-{seed}-{i}','stress',fam,mem(confidence=rng.uniform(.58,.68),source=SourceType.EXPLICIT),rng.choice(['dining','travel']),False,PersonalizationAction.ASK)
            out.append(c)
    rng.shuffle(out); return out

def main():
    seeds=list(range(30)); per={name:[] for name in SYSTEMS}; fam={name:{f:[] for f in FAMILIES} for name in SYSTEMS}
    for s in seeds:
        cases=build(s)
        for name,fn in SYSTEMS.items():
            m=metrics(cases,[fn(c) for c in cases]); per[name].append(m)
            for f in FAMILIES:
                cs=[c for c in cases if c.family==f]; fam[name][f].append(metrics(cs,[fn(c) for c in cs])['exact_action_accuracy'])
    out={'suite':'stochastic metadata stability','seeds':seeds,'cases_per_seed':len(build(0)),'total_decisions_per_system':len(seeds)*len(build(0)),'systems':{}}
    for name,rows in per.items():
        out['systems'][name]={
            'exact_action_accuracy_mean':statistics.mean(r['exact_action_accuracy'] for r in rows),
            'exact_action_accuracy_std':statistics.pstdev(r['exact_action_accuracy'] for r in rows),
            'cpr_mean':statistics.mean(r['cpr'] for r in rows),
            'cpr_std':statistics.pstdev(r['cpr'] for r in rows),
            'false_personalization_rate_mean':statistics.mean(r['false_personalization_rate'] for r in rows),
            'family_accuracy_mean':{f:statistics.mean(fam[name][f]) for f in FAMILIES},
        }
    out['boundary']='Synthetic stochastic metadata perturbations within pre-specified label-safe ranges; not a substitute for user/model variation.'
    (ROOT/'results'/'stochastic_stability.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
