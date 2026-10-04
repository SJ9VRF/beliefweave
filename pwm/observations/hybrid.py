from __future__ import annotations
import re
from pathlib import Path
from pwm.memory.schema import Event, Observation, MemoryType, SourceType
from pwm.temporal import infer_valid_until
from .extractor import RuleBasedObservationExtractor
from .learned_router import LearnedObservationRouter

TYPE_MAP={x.name:x for x in MemoryType if x.name in {'PREFERENCE','GOAL','CONSTRAINT','COMMITMENT','FACT','ROUTINE'}}
THIRD_PARTY=re.compile(r"^(?:my friend|my colleague|someone|they|he|she)\s+(?:says?|said|thinks?|told me)\b",re.I)
ROLEPLAY=re.compile(r"\b(?:pretend|role\s*play|hypothetically|if i (?:liked|loved|wanted|lived))\b",re.I)

class HybridObservationExtractor:
    """Rules first; learned routing only expands coverage for grounded first-person statements."""
    def __init__(self, model_path: str|Path):
        self.rules=RuleBasedObservationExtractor(); self.router=LearnedObservationRouter(model_path)

    def extract(self,event:Event)->list[Observation]:
        ruled=self.rules.extract(event)
        if ruled: return ruled
        text=event.raw_text.strip()
        if THIRD_PARTY.search(text) or ROLEPLAY.search(text): return []
        routed=self.router.route(text)
        if routed.label=='NONE' or routed.confidence<0.72: return []
        slot=self._slot(text,routed.label)
        if not slot: return []
        predicate,value=slot
        temporary=bool(re.search(r"\b(?:this (?:week|month)|today|for now|temporarily|until )",text,re.I))
        return [Observation(subject='user',attribute=predicate,value=value,memory_type=TYPE_MAP[routed.label],source_type=SourceType.EXPLICIT,confidence=min(.94,routed.confidence),source_event_id=event.id,context_scope=event.context,temporality='temporary' if temporary else 'unspecified',valid_from=event.timestamp,valid_until=infer_valid_until(text,event.timestamp) if temporary else None,raw_evidence=text,correction=bool(re.match(r"^(?:actually|correction|no[, ]+that's wrong)",text,re.I)))]

    def _slot(self,text:str,label:str):
        patterns={
          'PREFERENCE':[(r"^i (?:am )?(?:a big fan of|enjoy|like|love) (.+?)[.!]?$",'likes'),(r"^(?:my preference is|if possible, i would choose) (.+?)[.!]?$",'prefers')],
          'GOAL':[(r"^i (?:want|am trying|am aiming|hope) to (.+?)[.!]?$",'goal'),(r"^(?:one of my goals is to|i am working toward this:) (.+?)[.!]?$",'goal')],
          'CONSTRAINT':[(r"^(?:please avoid|i need to stay away from) (.+?)(?: for me)?[.!]?$",'avoids'),(r"^i cannot (?:eat|do|have) (.+?)[.!]?$",'avoids')],
          'COMMITMENT':[(r"^i (?:have|must|committed) to (.+?)[.!]?$",'needs_to'),(r"^please remember that i must (.+?)[.!]?$",'needs_to')],
          'FACT':[(r"^(?:my current place is|a fact about me:) (.+?)[.!]?$",'fact'),(r"^i am based in (.+?)[.!]?$",'lives_in')],
          'ROUTINE':[(r"^(?:most days i|my routine is to|i tend to) (.+?)[.!]?$",'usually')],
        }
        cleaned=re.sub(r"^(?:actually[, ]+|correction:\s*)",'',text,flags=re.I)
        for p,pred in patterns.get(label,[]):
            m=re.match(p,cleaned,re.I)
            if m:return pred,m.group(1).strip().rstrip('.!')
        return None
