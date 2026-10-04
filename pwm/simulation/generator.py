from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone,timedelta
import json,random
from pathlib import Path

PREFS={
 'food':['sushi','pasta','tacos','salad','ramen','curry'],
 'tone':['concise explanations','detailed explanations','formal language','casual language'],
 'activity':['running','cycling','swimming','hiking']
}
GOALS=['publish a paper','learn Spanish','run a marathon','build an AI demo','save for a trip']
@dataclass
class Turn:
 user_id:str; turn:int; timestamp:str; text:str; context:str; kind:str; ground_truth:dict

class LongitudinalUserGenerator:
 def __init__(self,seed:int=7): self.r=random.Random(seed)
 def trajectory(self,user_id:str,n_turns:int=100)->list[Turn]:
  base=datetime(2026,1,1,tzinfo=timezone.utc)
  food=self.r.choice(PREFS['food']); tone=self.r.choice(PREFS['tone']); activity=self.r.choice(PREFS['activity']); goal=self.r.choice(GOALS)
  state={'food_like':food,'tone_pref':tone,'activity_like':activity,'goal':goal,'temporary_avoid':None}
  out=[]
  for i in range(n_turns):
   ts=(base+timedelta(days=i)).isoformat(); kind='noise'; context='general'; text=f"Can you help me with task {i}?"
   if i==0: kind='preference'; context='food'; text=f"I love {food}."
   elif i==1: kind='preference'; context='communication'; text=f"I prefer {tone}."
   elif i==2: kind='goal'; text=f"My goal is to {goal}."
   elif i==3: kind='preference'; context='fitness'; text=f"I love {activity}."
   elif i==n_turns//3:
    old=food; food=self.r.choice([x for x in PREFS['food'] if x!=old]); state['food_like']=food; kind='drift'; context='food'; text=f"Actually, I dislike {old}."
   elif i==n_turns//3+1:
    kind='drift'; context='food'; text=f"I love {food}."
   elif i==n_turns//2:
    state['temporary_avoid']='raw fish'; kind='temporary'; context='food'; text="I'm avoiding raw fish this month."
   elif i==n_turns//2+31:
    state['temporary_avoid']=None; kind='expiry_probe'; context='food'; text="Can you recommend dinner?"
   elif i==2*n_turns//3:
    old=goal; goal=self.r.choice([g for g in GOALS if g!=old]); state['goal']=goal; kind='goal_change'; text=f"Actually, my goal is to {goal}."
   elif i%17==0:
    kind='routine'; context='fitness'; text=f"I usually do {activity} on weekends."
   out.append(Turn(user_id,i,ts,text,context,kind,dict(state)))
  return out
 def generate(self,n_users:int=1000,n_turns:int=100,path:str|Path|None=None):
  data=[asdict(t) for u in range(n_users) for t in self.trajectory(f'u{u:04d}',n_turns)]
  if path:
   p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('w') as f:
    for row in data: f.write(json.dumps(row)+'\n')
  return data
