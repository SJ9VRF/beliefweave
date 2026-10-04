from __future__ import annotations
import math,re
from dataclasses import dataclass
from datetime import datetime, timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pwm.memory.schema import MemoryRecord,MemoryType
from pwm.memory.store import MemoryStore
from pwm.temporal import parse_iso

SYNONYMS={
 'calm':['quiet'], 'quiet':['calm'], 'coffee':['cafe','cafes'], 'cafe':['coffee','restaurant'], 'cafes':['coffee','restaurant'],
 'restaurant':['food','dinner','eat','cafe','cafes'], 'dinner':['restaurant','food','eat'], 'food':['restaurant','dinner','eat'],
 'job':['work','career'], 'work':['job','career'], 'career':['job','work','goal'],
 'exercise':['workout','running','run'], 'workout':['exercise','running','run'], 'running':['exercise','workout'], 'run':['exercise','workout'],
 'formal':['professional'], 'professional':['formal'], 'restriction':['avoid','constraint'], 'avoid':['restriction','constraint']
}

def expand(text:str)->str:
    toks=re.findall(r"[\w'-]+",text.lower(),re.UNICODE); extra=[]
    for t in toks: extra.extend(SYNONYMS.get(t,[]))
    return text+' '+' '.join(extra)

def intent_bonus(query:str,m:MemoryRecord)->float:
    q=query.lower(); typ=m.memory_type
    food=bool(re.search(r'\b(food|eat|dinner|lunch|restaurant|meal|cafe|coffee)\b',q))
    career=bool(re.search(r'\b(career|job|work|professional|goal|priority)\b',q))
    fitness=bool(re.search(r'\b(workout|exercise|fitness|run|training)\b',q))
    style=bool(re.search(r'\b(write|message|tone|reply|email|communicat)',q))
    restriction=bool(re.search(r'\b(avoid|restriction|cannot|can.t|shouldn.t)\b',q))
    if food and typ in {MemoryType.PREFERENCE,MemoryType.CONSTRAINT}: return .12
    if career and typ in {MemoryType.GOAL,MemoryType.FACT,MemoryType.COMMITMENT}: return .10
    if fitness and typ in {MemoryType.ROUTINE,MemoryType.GOAL,MemoryType.CONSTRAINT}: return .10
    if style and typ in {MemoryType.PREFERENCE,MemoryType.STYLE}: return .10
    if restriction and typ==MemoryType.CONSTRAINT: return .14
    return 0.0

@dataclass(slots=True)
class RetrievedMemory:
    memory: MemoryRecord
    score: float
    reasons: dict[str,float]

class SemanticMemoryRetriever:
    """Transparent local retrieval baseline.

    Combines word/character TF-IDF, bounded query-intent/type priors, confidence,
    importance, recency, stability and exact context match. No external model or
    embedding service is required, and every score component is inspectable.
    """
    def __init__(self,store:MemoryStore): self.store=store
    def retrieve(self,user_id:str,query:str,limit:int=5,context:str|None=None,now:str|None=None):
        memories=self.store.list_active(user_id,now=now)
        if not memories:return []
        docs=[expand(f"{m.memory_type.value} {m.predicate.replace('_',' ')} {m.value} {m.context_scope or ''}") for m in memories]
        corpus=docs+[expand(query)]
        word=TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True).fit_transform(corpus)
        char=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True).fit_transform(corpus)
        sem=.65*cosine_similarity(word[-1],word[:-1]).ravel()+.35*cosine_similarity(char[-1],char[:-1]).ravel()
        ref=parse_iso(now) if now else datetime.now(timezone.utc); out=[]
        for i,m in enumerate(memories):
            vf=parse_iso(m.valid_from); age=max(0,(ref-vf).total_seconds()/86400) if vf else 0; recency=math.exp(-age/180)
            ctx=.18 if context and m.context_scope==context else 0
            intent=intent_bonus(query,m)
            score=.54*float(sem[i])+.10*m.confidence+.07*m.importance+.05*recency+.06*m.stability+ctx+intent
            out.append(RetrievedMemory(m,score,{'semantic_similarity':float(sem[i]),'intent_bonus':intent,'confidence':m.confidence,'importance':m.importance,'recency':recency,'stability':m.stability,'context_bonus':ctx}))
        out.sort(key=lambda r:r.score,reverse=True)
        for r in out[:limit]: self.store.touch_retrieved(r.memory.id)
        return out[:limit]
