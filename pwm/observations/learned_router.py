from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import joblib

_MODEL_CACHE={}

@dataclass(slots=True)
class RoutedObservation:
    label: str
    confidence: float

class LearnedObservationRouter:
    """Lightweight learned router for memory-worthy intent/type classification.

    Models are cached per process because benchmark suites may instantiate many
    isolated engines while sharing the same immutable serialized classifier.
    """
    def __init__(self, model_path: str | Path):
        self.model_path = str(Path(model_path).resolve())
        if self.model_path not in _MODEL_CACHE:
            _MODEL_CACHE[self.model_path]=joblib.load(self.model_path)
        self.pipeline = _MODEL_CACHE[self.model_path]

    def route(self, text: str) -> RoutedObservation:
        probs = self.pipeline.predict_proba([text])[0]
        idx = int(probs.argmax())
        return RoutedObservation(str(self.pipeline.classes_[idx]), float(probs[idx]))
