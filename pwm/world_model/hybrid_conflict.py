from __future__ import annotations
from pathlib import Path
from pwm.memory.schema import MemoryRecord, Observation, ConflictType, MemoryType
from .conflict import ConflictResolver
from .learned_conflict import LearnedConflictResolver

class HybridConflictResolver:
    """Safety-gated learned conflict resolver.

    Deterministic structural rules handle obvious temporal/context relations. The
    learned model only refines explicit corrections inside the same compatible
    memory family. Additive facts are never overwritten merely because a classifier
    predicts a conflict.
    """
    def __init__(self, model_path: str|Path):
        self.rules=ConflictResolver(); self.learned=LearnedConflictResolver(model_path)
    def classify(self,old:MemoryRecord,obs:Observation)->ConflictType:
        rule=self.rules.classify(old,obs)
        if rule!=ConflictType.NONE:return rule
        # Learned refinement is permitted only for an explicit correction of the
        # same predicate/type. Everything else is additive by default.
        if not (obs.correction and old.memory_type==obs.memory_type and old.predicate==obs.attribute):
            return ConflictType.NONE
        pred=self.learned.classify(old,obs)
        if old.memory_type==MemoryType.GOAL and pred==ConflictType.GOAL_CHANGE:return pred
        if old.memory_type==MemoryType.PREFERENCE and pred==ConflictType.PREFERENCE_DRIFT:return pred
        if old.memory_type in {MemoryType.FACT,MemoryType.CONSTRAINT} and pred==ConflictType.TEMPORAL_UPDATE:return pred
        return ConflictType.NONE
