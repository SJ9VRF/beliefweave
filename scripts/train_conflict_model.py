from __future__ import annotations
import argparse,json,random
from pathlib import Path
import joblib
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,classification_report
random.seed(23)
ITEMS=['sushi','coffee','jazz','running','spicy food','tea','window seats','formal tone']
GOALS=['publish a paper','run a marathon','learn French','change jobs','finish the thesis']

def ex(oldtype,oldpred,old,newtype,newpred,new,ctx1='-',ctx2='-',corr=0):
 return f'OLDTYPE={oldtype} OLDPRED={oldpred} OLD={old} CONTEXT={ctx1} || NEWTYPE={newtype} NEWPRED={newpred} NEW={new} CONTEXT={ctx2} CORRECTION={corr}'
def build(n=1200):
 X=[];y=[]
 for _ in range(n):
  item=random.choice(ITEMS)
  X.append(ex('preference','likes',item,'preference','dislikes',item)); y.append('preference_drift')
  X.append(ex('preference','dislikes',item,'preference','likes',item)); y.append('preference_drift')
  a,b=random.sample(GOALS,2); X.append(ex('goal','goal',a,'goal','goal',b)); y.append('goal_change')
  X.append(ex('fact','lives_in','Seattle','fact','lives_in','New York')); y.append('temporal_update')
  X.append(ex('preference','prefers','formal tone','preference','prefers','casual tone','work','friends')); y.append('context_dependent')
  X.append(ex('preference','likes','sushi','constraint','does_not_eat','fish')); y.append('apparent_conflict')
  X.append(ex('preference','likes',item,'preference','likes',item)); y.append('none')
  X.append(ex('fact','works_at','Google','preference','likes','coffee')); y.append('none')
 return X,y

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',default='results/conflict_model.joblib'); ap.add_argument('--metrics',default='results/conflict_model.json'); args=ap.parse_args()
 X,y=build(); Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
 feat=FeatureUnion([('word',TfidfVectorizer(ngram_range=(1,2))),('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5)))])
 pipe=Pipeline([('features',feat),('clf',LogisticRegression(max_iter=1200,class_weight='balanced',random_state=42))])
 pipe.fit(Xtr,ytr); pred=pipe.predict(Xte); m={'accuracy':accuracy_score(yte,pred),'n_train':len(Xtr),'n_test':len(Xte),'classification_report':classification_report(yte,pred,output_dict=True,zero_division=0)}
 Path(args.out).parent.mkdir(parents=True,exist_ok=True); joblib.dump(pipe,args.out); Path(args.metrics).write_text(json.dumps(m,indent=2)); print(json.dumps({'accuracy':m['accuracy'],'n_train':m['n_train'],'n_test':m['n_test']},indent=2))
if __name__=='__main__': main()
