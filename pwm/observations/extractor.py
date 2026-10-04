from __future__ import annotations
import re
from pwm.memory.schema import Event, Observation, MemoryType, SourceType
from pwm.temporal import infer_valid_until

class RuleBasedObservationExtractor:
    """Deterministic, reproducible baseline extractor. Intentionally dependency-free."""
    PATTERNS = [
        (re.compile(r"\bi (?:really )?(?:love|like|enjoy) (?P<value>.+?)[.!]?$", re.I), MemoryType.PREFERENCE, "likes"),
        (re.compile(r"\bi (?:hate|dislike|don't like|do not like) (?P<value>.+?)[.!]?$", re.I), MemoryType.PREFERENCE, "dislikes"),
        (re.compile(r"\bi prefer (?P<value>.+?)[.!]?$", re.I), MemoryType.PREFERENCE, "prefers"),
        (re.compile(r"\bmy goal is to (?P<value>.+?)[.!]?$", re.I), MemoryType.GOAL, "goal"),
        (re.compile(r"\bi need to (?P<value>.+?)[.!]?$", re.I), MemoryType.COMMITMENT, "needs_to"),
        (re.compile(r"\bi(?:'m| am) avoiding (?P<value>.+?)[.!]?$", re.I), MemoryType.CONSTRAINT, "avoids"),
        (re.compile(r"\bi (?:don't|do not) eat (?P<value>.+?)[.!]?$", re.I), MemoryType.CONSTRAINT, "does_not_eat"),
        (re.compile(r"\bi (?:stopped|have stopped|don't|do not) (?:eating|drinking) (?P<value>.+?)[.!]?$", re.I), MemoryType.CONSTRAINT, "does_not_consume"),
        (re.compile(r"\bi live in (?P<value>.+?)[.!]?$", re.I), MemoryType.FACT, "lives_in"),
        (re.compile(r"\bi work (?:at|for) (?P<value>.+?)[.!]?$", re.I), MemoryType.FACT, "works_at"),
        (re.compile(r"\bi usually (?P<value>.+?)[.!]?$", re.I), MemoryType.ROUTINE, "usually"),
    ]
    TEMPORARY_MARKERS=("this week","this month","today","for now","temporarily","for 2 days","for 3 days","for 7 days")
    CORRECTION_MARKERS=("no, that's wrong","no that's wrong","actually","correction:","i changed my mind","not anymore")

    def extract(self, event: Event) -> list[Observation]:
        text=event.raw_text.strip(); lower=text.lower(); out=[]
        if any(x in lower for x in ("don't remember","do not remember","don't save","do not save","forget this","don't store","do not store")):
            return out
        third_party_prefixes=("my friend says", "my friend said", "someone says", "someone said", "they say", "he says", "she says")
        if lower.startswith(third_party_prefixes):
            return out
        if re.search(r"\b(?:pretend|role\s*play|hypothetically|suppose i|if i (?:liked|loved|wanted|lived))\b", lower):
            return out
        temporality="temporary" if any(m in lower for m in self.TEMPORARY_MARKERS) else "unspecified"
        correction=any(m in lower for m in self.CORRECTION_MARKERS)
        cleaned=re.sub(r"^(no,?\s*(?:that's|that is)\s+wrong[.!]?\s*|actually[, ]+|correction:\s*)", "", text, flags=re.I)
        multilingual = [
            (re.compile(r"^me gusta (?P<value>.+?)[.!]?$", re.I), MemoryType.PREFERENCE, "likes"),
            (re.compile(r"^j['’]aime (?P<value>.+?)[.!]?$", re.I), MemoryType.PREFERENCE, "likes"),
            (re.compile(r"^من (?P<value>.+?) را دوست دارم[.!؟]?$"), MemoryType.PREFERENCE, "likes"),
            (re.compile(r"^no me gusta (?P<value>.+?)[.!]?$", re.I), MemoryType.PREFERENCE, "dislikes"),
            (re.compile(r"^je n['’]aime pas (?P<value>.+?)[.!]?$", re.I), MemoryType.PREFERENCE, "dislikes"),
            (re.compile(r"^من (?P<value>.+?) را دوست ندارم[.!؟]?$"), MemoryType.PREFERENCE, "dislikes"),
        ]
        for pattern, mem_type, predicate in self.PATTERNS + multilingual:
            m=pattern.search(cleaned)
            if not m: continue
            value=m.group("value").strip().rstrip(".!")
            out.append(Observation(subject="user", attribute=predicate, value=value, memory_type=mem_type, source_type=SourceType.EXPLICIT, confidence=.99 if correction else .95, source_event_id=event.id, context_scope=event.context, temporality=temporality, valid_from=event.timestamp, valid_until=infer_valid_until(text,event.timestamp) if temporality=="temporary" else None, raw_evidence=text, correction=correction))
        return out
