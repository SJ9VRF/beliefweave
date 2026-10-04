from __future__ import annotations
import json,random
from pathlib import Path

def generate(n_per_category=60,seed=23):
 r=random.Random(seed); foods=['sushi','ramen','pasta','tacos','curry','salad']; tones=['formal language','casual language','concise answers','detailed answers']; rows=[]; i=0
 for _ in range(n_per_category):
  x=r.choice(foods); rows.append({'id':f'reversal_{i}','category':'preference_reversal','turns':[f'I love {x}.',f'Actually, I dislike {x}.'],'expected':{'old_active':False,'new_predicate':'dislikes'}}); i+=1
 for _ in range(n_per_category):
  a,b=r.sample(tones,2); rows.append({'id':f'context_{i}','category':'context_dependence','turns':[{'text':f'I prefer {a}.','context':'work'},{'text':f'I prefer {b}.','context':'friends'}],'expected':{'active_count':2}}); i+=1
 for _ in range(n_per_category):
  x=r.choice(foods); rows.append({'id':f'temporary_{i}','category':'temporary_state','turns':[f"I'm avoiding {x} this month."],'expected':{'active_day_10':True,'active_day_40':False}}); i+=1
 for _ in range(n_per_category):
  x=r.choice(foods); rows.append({'id':f'correction_{i}','category':'explicit_correction','turns':[f'I love {x}.',f"No, that's wrong. I dislike {x}."],'expected':{'verified':True,'new_predicate':'dislikes'}}); i+=1
 for _ in range(n_per_category):
  x=r.choice(foods); rows.append({'id':f'poison_{i}','category':'third_party_attribution','turns':[f'My friend says I love {x}.'],'expected':{'write_count':0}}); i+=1
 for _ in range(n_per_category):
  x=r.choice(foods); lang=r.choice(['es','fr','fa']); text={'es':f'Me gusta {x}.','fr':f"J'aime {x}.",'fa':f'من {x} را دوست دارم'}[lang]; rows.append({'id':f'multilingual_{i}','category':'multilingual','language':lang,'turns':[text],'expected':{'predicate':'likes','value':x}}); i+=1
 p=Path('benchmark/data/hard_scenarios_360.jsonl'); p.parent.mkdir(parents=True,exist_ok=True); p.write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n'); print(f'generated {len(rows)} hard scenarios')
if __name__=='__main__': generate()
