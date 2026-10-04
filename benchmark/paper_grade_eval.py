from __future__ import annotations
import json, math, random, statistics, sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from pwm.belief_governance import DecisionAwareBeliefGate, PersonalizationAction, counterfactual_personalization_regret
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType,MemoryStatus
NOW='2000-06-01T12:00:00+00:00'

@dataclass(frozen=True)
class Case:
    id:str; split:str; family:str; memory:MemoryRecord; context:str|None; conflict:bool; gold_action:PersonalizationAction
    @property
    def should_use(self): return self.gold_action==PersonalizationAction.USE

def mem(*,confidence=.9,source=SourceType.EXPLICIT,context=None,valid_until=None,status=MemoryStatus.ACTIVE,verified=False):
    return MemoryRecord(user_id='u',subject='user',predicate='food.preference',value='likes sushi',memory_type=MemoryType.PREFERENCE,source_type=source,confidence=confidence,source_event_ids=['evt'],context_scope=context,valid_until=valid_until,status=status,user_verified=verified)

def build_cases():
    out=[]
    families=['valid_explicit','valid_observed','stale','context_mismatch','weak_inferred','unresolved_conflict','inactive','medium_authority']
    for fam in families:
      for i in range(80):
        split='dev' if i<40 else 'test'
        j=i if split=='dev' else i-40
        if fam=='valid_explicit': c=Case(f'{fam}-{i}',split,fam,mem(confidence=.82+(j%8)*.02,verified=j%5==0),'dining',False,PersonalizationAction.USE)
        elif fam=='valid_observed': c=Case(f'{fam}-{i}',split,fam,mem(confidence=.84+(j%6)*.025,source=SourceType.OBSERVED),'dining',False,PersonalizationAction.USE)
        elif fam=='stale': c=Case(f'{fam}-{i}',split,fam,mem(confidence=.94+(j%3)*.02,valid_until='1999-12-01T00:00:00+00:00'),'dining',False,PersonalizationAction.ABSTAIN)
        elif fam=='context_mismatch': c=Case(f'{fam}-{i}',split,fam,mem(confidence=.92+(j%4)*.02,context='work'),'friends',False,PersonalizationAction.ABSTAIN)
        elif fam=='weak_inferred': c=Case(f'{fam}-{i}',split,fam,mem(confidence=.46+(j%8)*.035,source=SourceType.INFERRED),'dining',False,PersonalizationAction.ABSTAIN)
        elif fam=='unresolved_conflict': c=Case(f'{fam}-{i}',split,fam,mem(confidence=.90+(j%5)*.02),'dining',True,PersonalizationAction.ASK)
        elif fam=='inactive': c=Case(f'{fam}-{i}',split,fam,mem(confidence=.97,status=MemoryStatus.SUPERSEDED),'dining',False,PersonalizationAction.ABSTAIN)
        else: c=Case(f'{fam}-{i}',split,fam,mem(confidence=.56+(j%7)*.025,source=SourceType.EXPLICIT),'dining',False,PersonalizationAction.ASK)
        out.append(c)
    return out

def expired(m): return bool(m.valid_until and m.valid_until < NOW)

def retrieval_only(c): return PersonalizationAction.USE if c.memory.status==MemoryStatus.ACTIVE else PersonalizationAction.ABSTAIN

def confidence_only(c):
    return PersonalizationAction.USE if c.memory.status==MemoryStatus.ACTIVE and c.memory.confidence>=.78 else PersonalizationAction.ABSTAIN

def provenance_only(c):
    return PersonalizationAction.USE if c.memory.status==MemoryStatus.ACTIVE and c.memory.source_type in {SourceType.EXPLICIT,SourceType.OBSERVED} else PersonalizationAction.ABSTAIN

def temporal_context(c):
    if c.memory.status!=MemoryStatus.ACTIVE or expired(c.memory): return PersonalizationAction.ABSTAIN
    if c.memory.context_scope and c.context and c.memory.context_scope.lower()!=c.context.lower(): return PersonalizationAction.ABSTAIN
    return PersonalizationAction.USE

def metadata_score(c):
    if c.memory.status!=MemoryStatus.ACTIVE: return PersonalizationAction.ABSTAIN
    s=c.memory.confidence + (.08 if c.memory.source_type==SourceType.EXPLICIT else 0) - (.18 if c.memory.source_type==SourceType.INFERRED else 0) + (.12 if c.memory.user_verified else 0)
    if s>=.78:return PersonalizationAction.USE
    if s>=.52:return PersonalizationAction.ASK
    return PersonalizationAction.ABSTAIN

def beliefweave(c, ut=.78, at=.52): return DecisionAwareBeliefGate(ut,at).decide(c.memory,context=c.context,now=NOW,unresolved_conflict=c.conflict).action

def oracle(c): return c.gold_action

def auth_score(c, features=None):
    features=set(features or {'time','context','provenance','verification','conflict','status'})
    if 'status' in features and c.memory.status!=MemoryStatus.ACTIVE:return 0.0
    if 'time' in features and expired(c.memory):return 0.0
    if 'context' in features and c.memory.context_scope and c.context and c.memory.context_scope.lower()!=c.context.lower():return .05
    if 'conflict' in features and c.conflict:return .5
    s=float(c.memory.confidence)
    if 'provenance' in features:
        if c.memory.source_type==SourceType.INFERRED:s-=.18
        elif c.memory.source_type==SourceType.EXPLICIT:s+=.08
    if 'verification' in features and c.memory.user_verified:s+=.12
    return max(1e-6,min(1-1e-6,s))

def cost_policy(c, fp=2.0, miss=1.0, ask=.25, features=None):
    p=auth_score(c,features)
    losses={PersonalizationAction.USE:(1-p)*fp, PersonalizationAction.ABSTAIN:p*miss, PersonalizationAction.ASK:ask}
    return min(losses,key=losses.get)

def metrics(cases, acts, fp_cost=2, miss_cost=1, ask_cost=.25):
    gold=[c.should_use for c in cases]; use=[a==PersonalizationAction.USE for a in acts]
    tp=sum(g and u for g,u in zip(gold,use)); tn=sum((not g) and (not u) for g,u in zip(gold,use)); fp=sum((not g) and u for g,u in zip(gold,use)); fn=sum(g and (not u) for g,u in zip(gold,use))
    return {'n':len(cases),'exact_action_accuracy':sum(a==c.gold_action for c,a in zip(cases,acts))/len(cases),'binary_use_accuracy':(tp+tn)/len(cases),'cpr':counterfactual_personalization_regret(gold,acts,false_personalization_cost=fp_cost,missed_personalization_cost=miss_cost,ask_cost=ask_cost),'false_personalization_rate':fp/len(cases),'use_precision':tp/max(tp+fp,1),'use_recall':tp/max(tp+fn,1),'ask_rate':sum(a==PersonalizationAction.ASK for a in acts)/len(acts),'abstain_rate':sum(a==PersonalizationAction.ABSTAIN for a in acts)/len(acts)}

def bootstrap_ci(cases, fn, metric='cpr', B=1000, seed=19):
    rng=random.Random(seed); vals=[]; n=len(cases)
    for _ in range(B):
        sample=[cases[rng.randrange(n)] for _ in range(n)]; acts=[fn(c) for c in sample]; vals.append(metrics(sample,acts)[metric])
    vals.sort(); return [vals[int(.025*B)], vals[min(B-1,int(.975*B))]]

def mcnemar(cases, fn_a, fn_b):
    b=c=0
    for x in cases:
        aok=(fn_a(x)==x.gold_action); bok=(fn_b(x)==x.gold_action)
        if aok and not bok:b+=1
        elif bok and not aok:c+=1
    if b+c==0:return {'b':b,'c':c,'exact_two_sided_p':1.0}
    n=b+c; k=min(b,c); p=2*sum(math.comb(n,i)*(0.5**n) for i in range(k+1)); return {'b':b,'c':c,'exact_two_sided_p':min(1.0,p)}

def calibration(cases):
    ps=[min(1-1e-6,max(1e-6,auth_score(c))) for c in cases]; ys=[1.0 if c.should_use else 0.0 for c in cases]; n=len(ys)
    brier=sum((p-y)**2 for p,y in zip(ps,ys))/n
    nll=-sum(y*math.log(p)+(1-y)*math.log(1-p) for p,y in zip(ps,ys))/n
    def ece(equal_count=False,bins=10):
        pairs=sorted(zip(ps,ys)) if equal_count else list(zip(ps,ys)); total=0.0
        if equal_count:
            groups=[pairs[i*n//bins:(i+1)*n//bins] for i in range(bins)]
        else:
            groups=[[(p,y) for p,y in pairs if (i/bins)<=p<((i+1)/bins) or (i==bins-1 and p==1)] for i in range(bins)]
        for g in groups:
            if not g:continue
            conf=sum(p for p,_ in g)/len(g); acc=sum(y for _,y in g)/len(g); total+=len(g)/n*abs(conf-acc)
        return total
    return {'brier':brier,'nll':nll,'ece_10':ece(False),'adaptive_ece_10':ece(True)}

def risk_coverage(cases):
    out=[]
    for th in [round(.40+i*.025,3) for i in range(24)]:
        accepted=[c for c in cases if auth_score(c)>=th]; fp=sum(not c.should_use for c in accepted)
        out.append({'threshold':th,'coverage':len(accepted)/len(cases),'risk_false_use':fp/max(1,len(accepted)),'use_precision':sum(c.should_use for c in accepted)/max(1,len(accepted))})
    return out

def component_ablations(cases):
    full={'time','context','provenance','verification','conflict','status'}; out={}
    for drop in [None,'time','context','provenance','verification','conflict','status']:
        feats=full if drop is None else full-{drop}; acts=[cost_policy(c,features=feats) for c in cases]
        key='full_cost_sensitive' if drop is None else f'no_{drop}'
        out[key]=metrics(cases,acts)
        fam={}
        for family in sorted(set(c.family for c in cases)):
            cs=[c for c in cases if c.family==family]; fam[family]=metrics(cs,[cost_policy(c,features=feats) for c in cs])['exact_action_accuracy']
        out[key]['family_accuracy']=fam
    return out

def main():
    all_cases=build_cases(); test=[c for c in all_cases if c.split=='test']; dev=[c for c in all_cases if c.split=='dev']
    systems={
      'retrieval_only':retrieval_only,'confidence_only':confidence_only,'provenance_only':provenance_only,
      'temporal_context':temporal_context,'metadata_score_no_hard_veto':metadata_score,
      'cost_sensitive_authority':cost_policy,'beliefweave':beliefweave,'oracle':oracle}
    res={'benchmark':'BeliefShiftBench-v2','construction':'author-constructed deterministic metadata stress test with frozen dev/test split','n_total':len(all_cases),'n_dev':len(dev),'n_test':len(test),'systems':{},'family_breakdown':{}}
    for name,fn in systems.items():
        m=metrics(test,[fn(c) for c in test]); m['cpr_95ci']=bootstrap_ci(test,fn,'cpr'); m['exact_action_accuracy_95ci']=bootstrap_ci(test,fn,'exact_action_accuracy'); res['systems'][name]=m
    for fam in sorted(set(c.family for c in test)):
        cs=[c for c in test if c.family==fam];res['family_breakdown'][fam]={name:metrics(cs,[fn(c) for c in cs]) for name,fn in systems.items()}
    res['paired_test_vs_temporal_context']=mcnemar(test,beliefweave,temporal_context)
    res['paired_test_vs_metadata_score']=mcnemar(test,beliefweave,metadata_score)
    res['calibration']=calibration(test);res['risk_coverage']=risk_coverage(test);res['component_ablations']=component_ablations(test)
    res['threshold_sweep']=[]
    for ut in [round(.65+i*.025,3) for i in range(13)]:
      for at in [round(.35+i*.025,3) for i in range(13)]:
        if at>=ut:continue
        fn=lambda c,ut=ut,at=at:beliefweave(c,ut,at); res['threshold_sweep'].append({'use_threshold':ut,'ask_threshold':at,**metrics(test,[fn(c) for c in test])})
    res['cost_sensitivity']=[]
    for fp in [1,2,4,8]:
      for miss in [.5,1,2]:
       for ask in [.05,.1,.25,.5,1]:
        fn=lambda c,fp=fp,miss=miss,ask=ask:cost_policy(c,fp,miss,ask)
        res['cost_sensitivity'].append({'false_personalization_cost':fp,'missed_personalization_cost':miss,'ask_cost':ask,**metrics(test,[fn(c) for c in test],fp,miss,ask)})
    res['scientific_boundary']='Held-out within an author-constructed synthetic benchmark. This reduces tuning leakage but does not replace independent benchmark, external model, or human evaluation.'
    (ROOT/'results'/'paper_grade_eval.json').write_text(json.dumps(res,indent=2))
    # freeze split manifest without project date
    manifest={'benchmark':'BeliefShiftBench-v2','test_ids':[c.id for c in test],'n_test':len(test)}
    (ROOT/'benchmark'/'beliefshift_v2_test_manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'n_test':len(test),'systems':res['systems'],'calibration':res['calibration'],'paired':res['paired_test_vs_temporal_context']},indent=2))
if __name__=='__main__':main()
