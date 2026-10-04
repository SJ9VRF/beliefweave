from __future__ import annotations

from dataclasses import dataclass

from pwm.memory.schema import Observation, WriteDecision, MemoryType


@dataclass(slots=True)
class WritePolicyResult:
    decision: WriteDecision
    score: float
    reason: str


class HeuristicWritePolicy:
    """Transparent baseline policy for Sprint 1."""

    TYPE_WEIGHT = {
        MemoryType.GOAL: 0.90,
        MemoryType.CONSTRAINT: 0.90,
        MemoryType.COMMITMENT: 0.85,
        MemoryType.PREFERENCE: 0.80,
        MemoryType.ROUTINE: 0.75,
        MemoryType.FACT: 0.70,
        MemoryType.STYLE: 0.70,
        MemoryType.RELATIONSHIP: 0.70,
        MemoryType.TEMPORARY_STATE: 0.55,
        MemoryType.PAST_EVENT: 0.45,
        MemoryType.INFERRED_HYPOTHESIS: 0.35,
    }

    def decide(self, obs: Observation) -> WritePolicyResult:
        base = self.TYPE_WEIGHT[obs.memory_type]
        explicit_bonus = 0.08 if obs.source_type.value == "explicit" else 0.0
        confidence_bonus = max(0.0, min(0.08, (obs.confidence - 0.5) * 0.16))
        temporary_penalty = 0.10 if obs.temporality == "temporary" else 0.0
        score = max(0.0, min(1.0, base + explicit_bonus + confidence_bonus - temporary_penalty))

        if obs.temporality == "temporary" and score >= 0.55:
            return WritePolicyResult(WriteDecision.STORE_TEMPORARILY, score, "useful but explicitly temporary")
        if score >= 0.68:
            return WritePolicyResult(WriteDecision.WRITE, score, "high expected future personalization utility")
        if score >= 0.50:
            return WritePolicyResult(WriteDecision.ASK_USER, score, "potentially useful but ambiguous")
        return WritePolicyResult(WriteDecision.IGNORE, score, "low expected future utility")
