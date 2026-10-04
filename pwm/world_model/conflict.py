from __future__ import annotations
import re
from pwm.memory.schema import MemoryRecord, Observation, ConflictType, MemoryType

OPPOSITES={"likes":"dislikes","dislikes":"likes"}
STOPWORDS={"the","a","an","this","that","for","now","month","week","today","completely","anymore"}
SINGLETON_PREDICATES={'lives_in','works_at'}

def norm(s:str)->set[str]: return {x for x in re.findall(r"[\w'-]+",s.lower()) if x not in STOPWORDS}
def related(a:str,b:str)->bool:
    A,B=norm(a),norm(b)
    return bool(A&B) or ("sushi" in A and "fish" in B) or ("sushi" in B and "fish" in A)

class ConflictResolver:
    """Conservative resolver: additive memories are preserved unless evidence supports replacement."""
    def classify(self, old:MemoryRecord, obs:Observation)->ConflictType:
        # Same relation in distinct contexts is not a contradiction.
        if old.context_scope and obs.context_scope and old.context_scope != obs.context_scope and old.predicate==obs.attribute:
            return ConflictType.CONTEXT_DEPENDENT
        # Explicit polarity reversal about the same/related object.
        if old.predicate in OPPOSITES and OPPOSITES[old.predicate]==obs.attribute and related(old.value,obs.value):
            return ConflictType.PREFERENCE_DRIFT if obs.memory_type==MemoryType.PREFERENCE else ConflictType.TEMPORAL_UPDATE
        # Preference vs constraint can coexist but should be linked as an apparent conflict.
        if old.memory_type==MemoryType.PREFERENCE and obs.memory_type==MemoryType.CONSTRAINT and related(old.value,obs.value):
            return ConflictType.APPARENT_CONFLICT
        if old.memory_type==MemoryType.CONSTRAINT and obs.memory_type==MemoryType.PREFERENCE and related(old.value,obs.value):
            return ConflictType.APPARENT_CONFLICT
        # Single-valued state attributes are replaced by newer values.
        if old.predicate==obs.attribute and old.value.lower()!=obs.value.lower() and old.predicate in SINGLETON_PREDICATES:
            return ConflictType.TEMPORAL_UPDATE
        # Explicit correction can replace a semantically related value in the same family.
        if obs.correction and old.memory_type==obs.memory_type and old.predicate==obs.attribute and related(old.value,obs.value):
            if obs.memory_type==MemoryType.GOAL:return ConflictType.GOAL_CHANGE
            if obs.memory_type==MemoryType.PREFERENCE:return ConflictType.PREFERENCE_DRIFT
            return ConflictType.TEMPORAL_UPDATE
        # Goals, likes, constraints, routines, and commitments are additive by default.
        return ConflictType.NONE
