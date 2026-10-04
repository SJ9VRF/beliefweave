from __future__ import annotations
import json,random
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report,accuracy_score
from sklearn.model_selection import train_test_split
import joblib

def build(seed=9):
 r=random.Random(seed); rows=[]
 pos=["I love {x}.","I prefer {x}.","My goal is to {x}.","I need to {x}.","I live in {x}.","I usually {x}."]
 neg=["What is {x}?","Tell me about {x}.","Write a poem about {x}.","Explain {x}.","Translate {x}.","Give me facts about {x}."]
 vals=['sushi','concise answers','finish my paper','call the dentist','New York','run on Sundays','transformers','Paris','linear algebra','music']
 for _ in range(1200):
  y=r.randint(0,1); tmpl=r.choice(pos if y else neg); rows.append((tmpl.format(x=r.choice(vals)),y))
 return rows

def train():
 rows=build(); X=[x for x,y in rows]; y=[y for x,y in rows]; Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
 model=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2))),('clf',LogisticRegression(max_iter=500))]); model.fit(Xtr,ytr); pred=model.predict(Xte)
 report={'accuracy':accuracy_score(yte,pred),'n_train':len(Xtr),'n_test':len(Xte),'classification_report':classification_report(yte,pred,output_dict=True),'note':'Template-controlled learned write-policy proof of execution; not human-data performance.'}
 Path('results').mkdir(exist_ok=True); Path('results/write_policy.json').write_text(json.dumps(report,indent=2)); joblib.dump(model,'results/write_policy.joblib'); print(json.dumps(report,indent=2)); return report
if __name__=='__main__': train()
