from __future__ import annotations
import json, sys
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from pwm.belief_governance import DecisionAwareBeliefGateV2, DecisionAwareBeliefGateV3, PersonalizationAction
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType,MemoryStatus
NOW='2000-06-01T12:00:00+00:00'
RANK={PersonalizationAction.ABSTAIN:0,PersonalizationAction.ASK:1,PersonalizationAction.USE:2}

def base(conf=.85, source=SourceType.EXPLICIT, context=None, verified=False, status=MemoryStatus.ACTIVE, valid_from=None, valid_until=None):
    return MemoryRecord(user_id='u',subject='user',predicate='food.preference',value='likes sushi',memory_type=MemoryType.PREFERENCE,
        source_type=source,confidence=conf,source_event_ids=['evt'],context_scope=context,user_verified=verified,status=status,
        valid_from=valid_from,valid_until=valid_until)

def act(g,m,ctx='dining',conflict=False):
    return g.decide(m,context=ctx,now=NOW,unresolved_conflict=conflict).action

def evaluate_gate(gate_name,g):
    checks=[]
    def record(name, ok, detail): checks.append({'invariant':name,'pass':bool(ok),'detail':detail})
    confs=[.2,.35,.5,.6,.72,.78,.84,.9,.98]
    sources=[SourceType.EXPLICIT,SourceType.IMPLICIT,SourceType.INFERRED,SourceType.OBSERVED]
    for s in sources:
        for verified in [False,True]:
            prev=None
            for c in confs:
                a=act(g,base(c,s,verified=verified))
                if prev is not None: record('confidence_monotonicity', RANK[a]>=RANK[prev], f'{s.value}/{verified}: {prev.value}->{a.value} at {c}')
                prev=a
    for s in sources:
        for c in confs:
            a0=act(g,base(c,s,verified=False)); a1=act(g,base(c,s,verified=True))
            record('verification_non_decreasing',RANK[a1]>=RANK[a0],f'{s.value}/{c}: {a0.value}->{a1.value}')
    for c in confs:
        ae=act(g,base(c,SourceType.EXPLICIT)); ai=act(g,base(c,SourceType.INFERRED))
        record('explicit_not_below_inferred',RANK[ae]>=RANK[ai],f'{c}: {ae.value} vs {ai.value}')
    transforms=[
        ('expired', lambda m: replace(m,valid_until='1999-01-01T00:00:00+00:00'), 'dining', False),
        ('future', lambda m: replace(m,valid_from='2001-01-01T00:00:00+00:00'), 'dining', False),
        ('superseded', lambda m: replace(m,status=MemoryStatus.SUPERSEDED), 'dining', False),
        ('deleted', lambda m: replace(m,status=MemoryStatus.DELETED), 'dining', False),
        ('archived', lambda m: replace(m,status=MemoryStatus.ARCHIVED), 'dining', False),
        ('context_mismatch', lambda m: replace(m,context_scope='work'), 'friends', False),
        ('conflict', lambda m:m, 'dining', True),
        ('synthetic', lambda m: replace(m,source_type=SourceType.SYNTHETIC), 'dining', False),
    ]
    for c in [.55,.7,.82,.95]:
        m=base(c); a0=act(g,m)
        for name,fn,ctx,conflict in transforms:
            a1=act(g,fn(m),ctx,conflict)
            record(f'{name}_non_increasing',RANK[a1]<=RANK[a0],f'{c}: {a0.value}->{a1.value}')
            record(f'{name}_never_use',a1!=PersonalizationAction.USE,f'{c}: {a1.value}')
    for c in confs:
        m=base(c,context='Work'); a0=act(g,m,'Work'); a1=act(g,m,'work')
        record('context_case_invariant',a0==a1,f'{c}: {a0.value}/{a1.value}')
    for c in [.82,.9,.98]:
        m=base(c,valid_from=NOW,valid_until=NOW); a=act(g,m)
        record('temporal_boundary_inclusive',a==PersonalizationAction.USE,f'{c}: {a.value}')
    failed=[x for x in checks if not x['pass']]; by={}
    for x in checks:
        z=by.setdefault(x['invariant'],{'n':0,'passed':0}); z['n']+=1; z['passed']+=int(x['pass'])
    return {'gate':gate_name,'n_checks':len(checks),'n_failed':len(failed),'pass_rate':1-len(failed)/max(1,len(checks)),
            'by_invariant':{k:{**v,'pass_rate':v['passed']/v['n']} for k,v in sorted(by.items())},'failures':failed[:100]}

def main():
    results=[evaluate_gate('DecisionAwareBeliefGateV2',DecisionAwareBeliefGateV2()),evaluate_gate('DecisionAwareBeliefGateV3',DecisionAwareBeliefGateV3())]
    out={'suite':'Authority Metamorphic Invariants','gates':results,'all_pass':all(x['n_failed']==0 for x in results),
         'interpretation':'Property-based audit over transformations that should preserve or monotonically reduce personalization authority; not a substitute for user-level downstream evaluation.'}
    (ROOT/'results'/'metamorphic_authority.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
