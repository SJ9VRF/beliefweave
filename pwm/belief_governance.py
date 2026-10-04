from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable

from pwm.memory.schema import MemoryRecord, MemoryStatus, SourceType


class PersonalizationAction(str, Enum):
    USE = "use"
    ASK = "ask"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class BeliefGateDecision:
    action: PersonalizationAction
    score: float
    reason: str


@dataclass(frozen=True)
class AuthorityCosts:
    false_personalization: float = 2.0
    missed_personalization: float = 1.0
    clarification: float = 0.25


class DecisionAwareBeliefGate:
    """Original authority gate kept frozen for reproducibility."""

    def __init__(self, use_threshold: float = 0.78, ask_threshold: float = 0.52):
        self.use_threshold = use_threshold
        self.ask_threshold = ask_threshold

    @staticmethod
    def _expired(memory: MemoryRecord, now: str | None) -> bool:
        if not memory.valid_until or not now:
            return False
        try:
            end = datetime.fromisoformat(memory.valid_until.replace("Z", "+00:00"))
            current = datetime.fromisoformat(now.replace("Z", "+00:00"))
        except ValueError:
            return False
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current > end

    def decide(
        self,
        memory: MemoryRecord,
        *,
        context: str | None = None,
        now: str | None = None,
        unresolved_conflict: bool = False,
    ) -> BeliefGateDecision:
        if memory.status != MemoryStatus.ACTIVE or self._expired(memory, now):
            return BeliefGateDecision(
                PersonalizationAction.ABSTAIN,
                0.0,
                "inactive_or_stale",
            )
        if memory.context_scope and context:
            if memory.context_scope.lower() != context.lower():
                return BeliefGateDecision(
                    PersonalizationAction.ABSTAIN,
                    0.1,
                    "context_mismatch",
                )
        if unresolved_conflict:
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                0.5,
                "unresolved_conflict",
            )

        score = float(memory.confidence)
        if memory.source_type == SourceType.INFERRED:
            score -= 0.18
        elif memory.source_type == SourceType.EXPLICIT:
            score += 0.08
        if memory.user_verified:
            score += 0.12
        score = max(0.0, min(1.0, score))

        if score >= self.use_threshold:
            return BeliefGateDecision(
                PersonalizationAction.USE,
                score,
                "sufficient_authority",
            )
        if score >= self.ask_threshold:
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                score,
                "uncertain_belief",
            )
        return BeliefGateDecision(
            PersonalizationAction.ABSTAIN,
            score,
            "insufficient_authority",
        )


class DecisionAwareBeliefGateV2(DecisionAwareBeliefGate):
    """Challenge-informed extension kept separate from the frozen v1 result."""

    @staticmethod
    def _not_yet_valid(memory: MemoryRecord, now: str | None) -> bool:
        if not memory.valid_from or not now:
            return False
        try:
            start = datetime.fromisoformat(memory.valid_from.replace("Z", "+00:00"))
            current = datetime.fromisoformat(now.replace("Z", "+00:00"))
        except ValueError:
            return False
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current < start

    def decide(
        self,
        memory: MemoryRecord,
        *,
        context: str | None = None,
        now: str | None = None,
        unresolved_conflict: bool = False,
    ) -> BeliefGateDecision:
        if self._not_yet_valid(memory, now):
            return BeliefGateDecision(
                PersonalizationAction.ABSTAIN,
                0.0,
                "not_yet_valid",
            )
        if memory.source_type == SourceType.SYNTHETIC:
            return BeliefGateDecision(
                PersonalizationAction.ABSTAIN,
                0.0,
                "synthetic_not_user_authority",
            )
        if memory.context_scope and not context:
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                0.5,
                "context_required",
            )
        return super().decide(
            memory,
            context=context,
            now=now,
            unresolved_conflict=unresolved_conflict,
        )


class DecisionAwareBeliefGateV3(DecisionAwareBeliefGateV2):
    """Specification-hardened production authority gate.

    V3 was written after post-hoc specification audits surfaced precedence,
    provenance, privacy, and malformed-temporal-metadata gaps. Scores on those
    same audits are regression evidence, not independent generalization evidence.
    """

    @staticmethod
    def _parse_time(value: str | None) -> tuple[datetime | None, bool]:
        if value is None:
            return None, True
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError, AttributeError):
            return None, False
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed, True

    def decide(
        self,
        memory: MemoryRecord,
        *,
        context: str | None = None,
        now: str | None = None,
        unresolved_conflict: bool = False,
    ) -> BeliefGateDecision:
        if memory.status != MemoryStatus.ACTIVE:
            return BeliefGateDecision(
                PersonalizationAction.ABSTAIN,
                0.0,
                "inactive_or_stale",
            )

        current, current_ok = self._parse_time(now)
        valid_from, valid_from_ok = self._parse_time(memory.valid_from)
        valid_until, valid_until_ok = self._parse_time(memory.valid_until)
        if not (current_ok and valid_from_ok and valid_until_ok):
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                0.5,
                "malformed_temporal_metadata",
            )
        if current is not None and valid_from is not None and current < valid_from:
            return BeliefGateDecision(
                PersonalizationAction.ABSTAIN,
                0.0,
                "not_yet_valid",
            )
        if current is not None and valid_until is not None and current > valid_until:
            return BeliefGateDecision(
                PersonalizationAction.ABSTAIN,
                0.0,
                "inactive_or_stale",
            )

        if memory.source_type == SourceType.SYNTHETIC:
            return BeliefGateDecision(
                PersonalizationAction.ABSTAIN,
                0.0,
                "synthetic_not_user_authority",
            )
        if not memory.source_event_ids:
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                0.5,
                "missing_provenance",
            )
        if memory.privacy_level.lower() not in {"normal", "public", "low"}:
            if not memory.user_verified:
                return BeliefGateDecision(
                    PersonalizationAction.ASK,
                    0.5,
                    "sensitive_unverified",
                )
        if memory.context_scope and not context:
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                0.5,
                "context_required",
            )
        if memory.context_scope and context:
            if memory.context_scope.lower() != context.lower():
                return BeliefGateDecision(
                    PersonalizationAction.ABSTAIN,
                    0.1,
                    "context_mismatch",
                )
        if unresolved_conflict:
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                0.5,
                "unresolved_conflict",
            )

        score = float(memory.confidence)
        if memory.source_type == SourceType.INFERRED:
            score -= 0.18
        elif memory.source_type == SourceType.EXPLICIT:
            score += 0.08
        if memory.user_verified:
            score += 0.12
        score = max(0.0, min(1.0, score))

        if score >= self.use_threshold:
            return BeliefGateDecision(
                PersonalizationAction.USE,
                score,
                "sufficient_authority",
            )
        if score >= self.ask_threshold:
            return BeliefGateDecision(
                PersonalizationAction.ASK,
                score,
                "uncertain_belief",
            )
        return BeliefGateDecision(
            PersonalizationAction.ABSTAIN,
            score,
            "insufficient_authority",
        )


def counterfactual_personalization_regret(
    gold_should_use: Iterable[bool],
    predicted_actions: Iterable[PersonalizationAction],
    *,
    false_personalization_cost: float = 2.0,
    missed_personalization_cost: float = 1.0,
    ask_cost: float = 0.25,
) -> float:
    total = 0.0
    count = 0
    for gold, action in zip(gold_should_use, predicted_actions):
        count += 1
        if gold:
            if action == PersonalizationAction.USE:
                cost = 0.0
            elif action == PersonalizationAction.ASK:
                cost = ask_cost
            else:
                cost = missed_personalization_cost
        elif action == PersonalizationAction.USE:
            cost = false_personalization_cost
        elif action == PersonalizationAction.ASK:
            cost = ask_cost
        else:
            cost = 0.0
        total += cost
    return total / max(count, 1)


def memory_intervention_fidelity(
    gold_causal: Iterable[bool],
    changed_after_removal: Iterable[bool],
) -> float:
    pairs = list(zip(gold_causal, changed_after_removal))
    if not pairs:
        return 0.0
    return sum(int(gold == predicted) for gold, predicted in pairs) / len(pairs)


def authority_probability(
    memory: MemoryRecord,
    *,
    context: str | None = None,
    now: str | None = None,
    unresolved_conflict: bool = False,
) -> float:
    """Estimate whether a memory should influence the current decision."""
    gate = DecisionAwareBeliefGate()
    if memory.status != MemoryStatus.ACTIVE or gate._expired(memory, now):
        return 1e-6
    if memory.context_scope and context:
        if memory.context_scope.lower() != context.lower():
            return 0.05
    if unresolved_conflict:
        return 0.5

    probability = float(memory.confidence)
    if memory.source_type == SourceType.INFERRED:
        probability -= 0.18
    elif memory.source_type == SourceType.EXPLICIT:
        probability += 0.08
    if memory.user_verified:
        probability += 0.12
    return max(1e-6, min(1 - 1e-6, probability))


class CostSensitiveAuthorityPolicy:
    """Bayes decision rule over USE / ASK / ABSTAIN under explicit costs."""

    def __init__(self, costs: AuthorityCosts | None = None):
        self.costs = costs or AuthorityCosts()

    def decide_from_probability(self, probability: float) -> BeliefGateDecision:
        probability = max(0.0, min(1.0, float(probability)))
        costs = self.costs
        losses = {
            PersonalizationAction.USE: (
                (1 - probability) * costs.false_personalization
            ),
            PersonalizationAction.ABSTAIN: (
                probability * costs.missed_personalization
            ),
            PersonalizationAction.ASK: costs.clarification,
        }
        action = min(losses, key=losses.get)
        return BeliefGateDecision(
            action,
            probability,
            f"expected_cost:{losses[action]:.6f}",
        )

    def decide(
        self,
        memory: MemoryRecord,
        *,
        context: str | None = None,
        now: str | None = None,
        unresolved_conflict: bool = False,
    ) -> BeliefGateDecision:
        probability = authority_probability(
            memory,
            context=context,
            now=now,
            unresolved_conflict=unresolved_conflict,
        )
        return self.decide_from_probability(probability)


PRODUCTION_GATE_VERSION = "v3"

GATE_REGISTRY = {
    "v1": DecisionAwareBeliefGate,
    "v2": DecisionAwareBeliefGateV2,
    "v3": DecisionAwareBeliefGateV3,
}


def build_belief_gate(
    version: str = PRODUCTION_GATE_VERSION,
    **kwargs,
) -> DecisionAwareBeliefGate:
    """Build a named gate while keeping frozen historical policies reproducible."""
    key = str(version).lower().strip()
    if key not in GATE_REGISTRY:
        choices = ", ".join(sorted(GATE_REGISTRY))
        raise ValueError(f"unknown belief gate version {version!r}; choose {choices}")
    return GATE_REGISTRY[key](**kwargs)
