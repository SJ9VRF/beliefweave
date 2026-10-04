from __future__ import annotations
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import json,tempfile,random
from pathlib import Path
from pwm.engine import PersonalMemoryEngine
from pwm.observations.learned_router import LearnedObservationRouter
from pwm.memory.schema import MemoryRecord,Observation,MemoryType,SourceType,ConflictType
from pwm.world_model.hybrid_conflict import HybridConflictResolver

ROOT=Path(__file__).resolve().parents[1]
random.seed(101)
OOD={
 'PREFERENCE':['When I get to choose, {v} is usually my pick.','I gravitate toward {v}.','I would take {v} over the alternatives.'],
 'GOAL':['A target I am pursuing is to {v}.','I am setting out to {v}.','The outcome I am working toward is to {v}.'],
 'CONSTRAINT':['Keep {v} off the table for me.','{v} is something I need to avoid.','Please treat {v} as a restriction.'],
 'COMMITMENT':['I promised myself I would {v}.','I am on the hook to {v}.','I still owe it to myself to {v}.'],
 'ROUTINE':['It is typical for me to {v}.','On most days, I end up {v}.','A recurring habit of mine is to {v}.'],
 'NONE':['My colleague says I love {v}.','Suppose I loved {v}; what then?','Can you explain {v}?','She told me she prefers {v}.']
}
VALS=['sushi','quiet cafes','jazz','morning workouts','French','tea']

def eval_router():
    r=LearnedObservationRouter(ROOT/'results'/'observation_router.joblib')
    total=correct=0; by={}
    for label,temps in OOD.items():
        c=n=0
        for t in temps:
            for v in VALS:
                pred=r.route(t.format(v=v)).label; n+=1; total+=1; c+=pred==label; correct+=pred==label
        by[label]={'correct':c,'total':n,'accuracy':c/n}
    # selective-prediction curve: abstain below confidence threshold
    selective={}
    for th in (0.50,0.60,0.70,0.80,0.90):
        kept=good=0
        for label,temps in OOD.items():
            for t in temps:
                for v in VALS:
                    z=r.route(t.format(v=v))
                    if z.confidence>=th:
                        kept+=1; good+=z.label==label
        selective[str(th)]={'coverage':kept/total,'accuracy':(good/kept if kept else None),'n':kept}
    return {'accuracy':correct/total,'total':total,'by_label':by,'selective':selective}

def eval_conflict():
    h=HybridConflictResolver(ROOT/'results'/'conflict_model.joblib')
    cases=[]
    # Unrelated pairs must stay NONE even if lexical overlap exists.
    for item in VALS:
        old=MemoryRecord(user_id='u',subject='user',predicate='likes',value=item,memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_ids=['e'])
        obs=Observation(subject='user',attribute='goal',value=f'learn about {item}',memory_type=MemoryType.GOAL,source_type=SourceType.EXPLICIT,confidence=.9,source_event_id='e2')
        cases.append((h.classify(old,obs),ConflictType.NONE))
    # True reversals.
    for item in VALS:
        old=MemoryRecord(user_id='u',subject='user',predicate='likes',value=item,memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_ids=['e'])
        obs=Observation(subject='user',attribute='dislikes',value=item,memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_id='e2')
        cases.append((h.classify(old,obs),ConflictType.PREFERENCE_DRIFT))
    return {'accuracy':sum(a==b for a,b in cases)/len(cases),'total':len(cases),'errors':[{'pred':a.value,'gold':b.value} for a,b in cases if a!=b]}

def eval_engine_adversarial():
    scenarios=[
      ('third_party',['My friend says I love sushi.'],0),
      ('roleplay',['Pretend that I like jazz for this roleplay.'],0),
      ('unrelated',['I am a big fan of quiet cafes.','My goal is to publish a paper.'],2),
      ('reversal',['I love sushi.','Actually, I dislike sushi.'],1),
      ('context',['I prefer formal tone.','I prefer casual tone.'],2),
    ]
    out=[]
    for name,turns,expected_active in scenarios:
      with tempfile.TemporaryDirectory() as d:
        e=PersonalMemoryEngine(Path(d) / 'db.sqlite', enable_ml=True)
        for j,t in enumerate(turns):
            e.ingest('u',t,timestamp=f'2000-01-{j+1:02d}T00:00:00+00:00')
        active=e.memories.list_active('u',now='2000-01-10T00:00:00+00:00')
        out.append({'name':name,'pass':len(active)==expected_active,'active':[m.to_dict() for m in active]})
    return {'passed':sum(x['pass'] for x in out),'total':len(out),'scenarios':out}

def main():
    res={'ood_router':eval_router(),'hybrid_conflict':eval_conflict(),'engine_adversarial':eval_engine_adversarial()}
    (ROOT/'results'/'ood_robustness.json').write_text(json.dumps(res,indent=2)); print(json.dumps({'ood_router_accuracy':res['ood_router']['accuracy'],'ood_router_n':res['ood_router']['total'],'hybrid_conflict_accuracy':res['hybrid_conflict']['accuracy'],'engine_adversarial':f"{res['engine_adversarial']['passed']}/{res['engine_adversarial']['total']}"},indent=2))
if __name__=='__main__':main()
