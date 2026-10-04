from __future__ import annotations
import json, random, statistics, sys
from dataclasses import dataclass
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from pwm.belief_governance import DecisionAwareBeliefGate, DecisionAwareBeliefGateV2, PersonalizationAction
from pwm.memory.schema import MemoryRecord, MemoryType, SourceType, MemoryStatus
NOW='2000-06-01T12:00:00+00:00'

@dataclass(frozen=True)
class SpecCase:
    case_id:str; family:str; memory:MemoryRecord; context:str|None; conflict:bool; gold:PersonalizationAction; rationale:str

PREDICATES=['food.preference','travel.preference','work.constraint','communication.style','exercise.preference','music.preference']
VALUES=['likes sushi','prefers aisle seats','no meetings after 5','prefers concise replies','likes morning workouts','likes jazz']
TYPES=[MemoryType.PREFERENCE,MemoryType.PREFERENCE,MemoryType.CONSTRAINT,MemoryType.STYLE,MemoryType.PREFERENCE,MemoryType.PREFERENCE]


def rec(seed:int, *, conf:float=.9, source:SourceType=SourceType.EXPLICIT, context:str|None=None,
        valid_from:str|None=None, valid_until:str|None=None, status:MemoryStatus=MemoryStatus.ACTIVE,
        verified:bool=False, privacy_level:str='normal')->MemoryRecord:
    i=seed%len(PREDICATES)
    return MemoryRecord(user_id='u',subject='user',predicate=PREDICATES[i],value=VALUES[i],memory_type=TYPES[i],
        source_type=source,confidence=conf,source_event_ids=[f'evt-{seed}'],context_scope=context,
        valid_from=valid_from,valid_until=valid_until,status=status,user_verified=verified,privacy_level=privacy_level)


def build(seed:int=0, per_family:int=24):
    rng=random.Random(seed); cases=[]
    def add(family, maker, gold, rationale):
        for j in range(per_family):
            m,ctx,conflict=maker(j)
            cases.append(SpecCase(f'{family}-{seed}-{j}',family,m,ctx,conflict,gold,rationale))
    # Compositions deliberately absent from BeliefShiftBench-v2.
    add('future_not_yet_valid', lambda j:(rec(j,conf=.92,valid_from='2001-01-01T00:00:00+00:00'), 'dining', False), PersonalizationAction.ABSTAIN, 'A future-effective belief must not affect current behavior.')
    add('scoped_memory_context_unknown', lambda j:(rec(j,conf=.94,context='work'), None, False), PersonalizationAction.ASK, 'A scoped belief cannot safely personalize when current context is unknown.')
    add('synthetic_high_confidence', lambda j:(rec(j,conf=.96,source=SourceType.SYNTHETIC), 'dining', False), PersonalizationAction.ABSTAIN, 'Synthetic/generated evidence is not user-grounded authority.')
    add('implicit_medium_confidence', lambda j:(rec(j,conf=.68,source=SourceType.IMPLICIT), 'dining', False), PersonalizationAction.ASK, 'Implicit evidence at moderate confidence warrants clarification.')
    add('verified_inferred', lambda j:(rec(j,conf=.72,source=SourceType.INFERRED,verified=True), 'dining', False), PersonalizationAction.ASK, 'Verification raises authority, but an inferred belief at this boundary remains clarification-worthy.')
    add('explicit_low_confidence', lambda j:(rec(j,conf=.38,source=SourceType.EXPLICIT), 'dining', False), PersonalizationAction.ABSTAIN, 'Low-confidence explicit evidence should not drive personalization.')
    add('observed_boundary', lambda j:(rec(j,conf=.74+(j%3)*.01,source=SourceType.OBSERVED), 'dining', False), PersonalizationAction.ASK, 'Observed evidence near the decision boundary should trigger clarification.')
    add('conflict_plus_context_match', lambda j:(rec(j,conf=.98,source=SourceType.EXPLICIT,context='friends'), 'friends', True), PersonalizationAction.ASK, 'An unresolved contradiction dominates otherwise strong matching evidence.')
    add('expired_and_verified', lambda j:(rec(j,conf=.99,verified=True,valid_until='1999-01-01T00:00:00+00:00'), 'dining', False), PersonalizationAction.ABSTAIN, 'Verification does not revive expired evidence.')
    add('superseded_high_confidence', lambda j:(rec(j,conf=.99,status=MemoryStatus.SUPERSEDED), 'dining', False), PersonalizationAction.ABSTAIN, 'Superseded evidence must not influence behavior.')
    add('valid_explicit_unscoped', lambda j:(rec(j,conf=.86+(j%4)*.02,source=SourceType.EXPLICIT), rng.choice(['dining','travel','work']), False), PersonalizationAction.USE, 'High-confidence explicit unscoped evidence is safe to use.')
    add('valid_observed_unscoped', lambda j:(rec(j,conf=.86+(j%4)*.02,source=SourceType.OBSERVED), rng.choice(['dining','travel','work']), False), PersonalizationAction.USE, 'High-confidence repeated observation is usable under this benchmark policy.')
    return cases


def eval_cases(cases, gate_cls=DecisionAwareBeliefGate):
    gate=gate_cls()
    rows=[]
    for c in cases:
        d=gate.decide(c.memory,context=c.context,now=NOW,unresolved_conflict=c.conflict)
        rows.append((c,d.action,d.reason,d.score))
    n=len(rows); acc=sum(pred==c.gold for c,pred,_,_ in rows)/n
    fam={}
    for f in sorted({c.family for c,_,_,_ in rows}):
        rr=[x for x in rows if x[0].family==f]
        fam[f]={
            'n':len(rr),
            'accuracy':sum(pred==c.gold for c,pred,_,_ in rr)/len(rr),
            'gold_action':rr[0][0].gold.value,
            'predicted_action_counts':{a.value:sum(pred==a for _,pred,_,_ in rr) for a in PersonalizationAction},
            'rationale':rr[0][0].rationale,
        }
    return acc,fam


def main():
    seeds=list(range(10)); seed_acc=[]; all_family={}
    for s in seeds:
        cases=build(seed=s)
        acc,fam=eval_cases(cases,DecisionAwareBeliefGate); seed_acc.append(acc)
        for k,v in fam.items(): all_family.setdefault(k,[]).append(v['accuracy'])
    patch_acc=[]
    for s in seeds:
        a,_=eval_cases(build(seed=s),DecisionAwareBeliefGateV2); patch_acc.append(a)
    out={
        'suite':'BeliefShift Unseen-Composition Challenge',
        'role':'post-hoc adversarial challenge; not used for parameter tuning and not included in the primary held-out claim',
        'seeds':seeds,
        'cases_per_seed':len(build(0)),
        'total_decisions':sum(len(build(s)) for s in seeds),
        'mean_exact_action_accuracy':statistics.mean(seed_acc),
        'std_exact_action_accuracy_across_seeds':statistics.pstdev(seed_acc),
        'seed_accuracies':seed_acc,
        'family_accuracy_mean':{k:statistics.mean(v) for k,v in sorted(all_family.items())},
        'challenge_informed_patch_mean_accuracy':statistics.mean(patch_acc),
        'challenge_informed_patch_note':'The V2 gate was written after observing these failures; its score is a regression result, not independent generalization evidence.',
        'interpretation':'This suite deliberately introduces structural combinations absent from BeliefShiftBench-v2. Failures are evidence about specification coverage, not grounds to retune the frozen primary test.',
    }
    p=ROOT/'results'/'unseen_composition.json'; p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
