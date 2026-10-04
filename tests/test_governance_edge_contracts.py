from __future__ import annotations

import pytest

from pwm.belief_governance import (
    CostSensitiveAuthorityPolicy,
    DecisionAwareBeliefGate,
    DecisionAwareBeliefGateV2,
    DecisionAwareBeliefGateV3,
    PersonalizationAction,
    authority_probability,
    build_belief_gate,
    memory_intervention_fidelity,
)
from pwm.memory.schema import MemoryRecord, MemoryStatus, MemoryType, SourceType


def memory(**overrides) -> MemoryRecord:
    data = dict(
        user_id="u",
        subject="user",
        predicate="likes",
        value="jazz",
        memory_type=MemoryType.PREFERENCE,
        source_type=SourceType.EXPLICIT,
        confidence=0.8,
        source_event_ids=["evt_1"],
    )
    data.update(overrides)
    return MemoryRecord(**data)


def test_naive_iso_timestamps_are_treated_as_utc():
    m = memory(valid_until="2000-01-01T00:00:00")
    gate = DecisionAwareBeliefGate()
    assert gate._expired(m, "2000-01-02T00:00:00") is True

    future = memory(valid_from="2000-01-02T00:00:00")
    assert DecisionAwareBeliefGateV2._not_yet_valid(
        future, "2000-01-01T00:00:00"
    ) is True

    parsed, ok = DecisionAwareBeliefGateV3._parse_time("2000-01-01T00:00:00")
    assert ok is True
    assert parsed is not None and parsed.tzinfo is not None


def test_authority_probability_covers_lifecycle_context_and_conflict():
    inactive = memory(status=MemoryStatus.SUPERSEDED)
    assert authority_probability(inactive) == pytest.approx(1e-6)

    scoped = memory(context_scope="work")
    assert authority_probability(scoped, context="travel") == pytest.approx(0.05)
    assert authority_probability(scoped, context="work", unresolved_conflict=True) == 0.5


def test_cost_sensitive_policy_runs_through_memory_probability():
    policy = CostSensitiveAuthorityPolicy()
    decision = policy.decide(memory(confidence=0.99, user_verified=True))
    assert decision.action == PersonalizationAction.USE
    assert decision.reason.startswith("expected_cost:")


def test_empty_intervention_set_and_unknown_gate_are_explicit():
    assert memory_intervention_fidelity([], []) == 0.0
    with pytest.raises(ValueError, match="unknown belief gate version"):
        build_belief_gate("v99")
