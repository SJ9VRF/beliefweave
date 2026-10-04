from __future__ import annotations
from pathlib import Path
import joblib
from pwm.memory.schema import MemoryRecord, Observation, ConflictType

_MODEL_CACHE={}

class LearnedConflictResolver:
    def __init__(self, model_path: str | Path):
        path=str(Path(model_path).resolve())
        if path not in _MODEL_CACHE:
            _MODEL_CACHE[path]=joblib.load(path)
        self.pipeline=_MODEL_CACHE[path]
    @staticmethod
    def featurize(old:MemoryRecord, obs:Observation)->str:
        return f"OLDTYPE={old.memory_type.value} OLDPRED={old.predicate} OLD={old.value} CONTEXT={old.context_scope or '-'} || NEWTYPE={obs.memory_type.value} NEWPRED={obs.attribute} NEW={obs.value} CONTEXT={obs.context_scope or '-'} CORRECTION={int(obs.correction)}"
    def classify(self, old:MemoryRecord, obs:Observation)->ConflictType:
        label=str(self.pipeline.predict([self.featurize(old,obs)])[0])
        return ConflictType(label)
