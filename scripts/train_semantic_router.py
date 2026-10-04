from __future__ import annotations
import argparse, json, random
from pathlib import Path
import joblib
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

random.seed(17)
VALUES={
 'PREFERENCE':['sushi','jazz','quiet cafes','short answers','window seats','science fiction','morning workouts'],
 'GOAL':['publish a paper','run a marathon','learn French','save for a house','finish my thesis','get stronger'],
 'CONSTRAINT':['raw fish','dairy','late meetings','red-eye flights','spicy food','weekend work'],
 'COMMITMENT':['call my advisor','submit the form','renew my passport','email Sabrina','book the hotel'],
 'FACT':['New York','Google','Brooklyn','a robotics lab','Seattle','UC Davis'],
 'ROUTINE':['work out before breakfast','read at night','walk after lunch','plan Sundays','cook on weekends'],
}
TEMPLATES={
 'PREFERENCE':['I like {v}.','I really enjoy {v}.','I am a big fan of {v}.','If possible, I would choose {v}.','My preference is {v}.','I tend to prefer {v}.','I favor {v}.','I tend to choose {v}.','{v} is usually my first choice.','I am partial to {v}.','{v} works best for me.'],
 'GOAL':['My goal is to {v}.','I am trying to {v}.','I want to {v}.','I am working toward this: {v}.','One of my goals is to {v}.','I am pursuing a goal to {v}.','My objective is to {v}.','A target of mine is to {v}.','I plan to {v}.','I am aiming to {v}.'],
 'CONSTRAINT':['I am avoiding {v}.','Please avoid {v} for me.','I cannot do {v}.','I need to stay away from {v}.','For now I am avoiding {v}.','{v} is off limits for me.','Treat {v} as a restriction.','I need to avoid {v}.','Please keep {v} out of my options.'],
 'COMMITMENT':['I need to {v}.','I have to {v}.','Please remember that I must {v}.','I committed to {v}.','I promised I would {v}.','I am responsible for {v}.','I still need to make sure I {v}.','I owe it to myself to {v}.'],
 'FACT':['I live in {v}.','I work at {v}.','My current place is {v}.','A fact about me: {v}.','I am based in {v}.','My workplace is {v}.'],
 'ROUTINE':['I usually {v}.','Most days I {v}.','My routine is to {v}.','I tend to {v}.','I regularly {v}.','It is typical for me to {v}.','A habit of mine is to {v}.'],
}
NEG=[
 'What is the capital of France?','Explain transformers.','Write a Python function.','Summarize this article.','My friend says I love sushi.','Pretend that I like jazz for this roleplay.','If I liked tea, what would you recommend?','She lives in Seattle.','Someone said I work at Google.','Do not remember this sentence.','Is sushi healthy?','Translate this sentence to French.','Suppose I loved sushi; what then?','Pretend I prefer tea.','My colleague thinks I should run.','He said I need to book a hotel.','The character in the story lives in Paris.'
]

def build(n_per=600):
    X=[]; y=[]
    for label, tmpls in TEMPLATES.items():
        vals=VALUES[label]
        for _ in range(n_per):
            t=random.choice(tmpls); v=random.choice(vals)
            text=t.format(v=v)
            if random.random()<.25: text='Actually, '+text[0].lower()+text[1:]
            if random.random()<.15: text=text.replace('.', ' this month.') if label in {'CONSTRAINT','ROUTINE'} else text
            X.append(text); y.append(label)
    for _ in range(n_per*2):
        X.append(random.choice(NEG)); y.append('NONE')
    return X,y

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='results/observation_router.joblib'); ap.add_argument('--metrics',default='results/observation_router.json'); args=ap.parse_args()
    X,y=build(); Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
    features=FeatureUnion([
      ('word',TfidfVectorizer(ngram_range=(1,2),min_df=1,sublinear_tf=True)),
      ('char',TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=1,sublinear_tf=True)),
    ])
    pipe=Pipeline([('features',features),('clf',LogisticRegression(max_iter=1200,class_weight='balanced',random_state=42))])
    pipe.fit(Xtr,ytr); pred=pipe.predict(Xte)
    metrics={'accuracy':accuracy_score(yte,pred),'n_train':len(Xtr),'n_test':len(Xte),'classification_report':classification_report(yte,pred,output_dict=True,zero_division=0)}
    Path(args.out).parent.mkdir(parents=True,exist_ok=True); joblib.dump(pipe,args.out); Path(args.metrics).write_text(json.dumps(metrics,indent=2))
    print(json.dumps({'accuracy':metrics['accuracy'],'n_train':metrics['n_train'],'n_test':metrics['n_test']},indent=2))
if __name__=='__main__': main()
