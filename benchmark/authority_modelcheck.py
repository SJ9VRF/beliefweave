from __future__ import annotations

import itertools
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path

from pwm.belief_governance import (
    DecisionAwareBeliefGate,
    DecisionAwareBeliefGateV2,
    DecisionAwareBeliefGateV3,
    PersonalizationAction,
)
from pwm.memory.schema import MemoryRecord, MemoryStatus, MemoryType, SourceType

NOW = "2000-06-15T00:00:00+00:00"
ACTION_ORDER = {
    PersonalizationAction.ABSTAIN: 0,
    PersonalizationAction.ASK: 1,
    PersonalizationAction.USE: 2,
}

@dataclass(frozen=True)
class Case:
    status: str
    temporal: str
    source: str
    confidence: float
    verified: bool
    provenance: bool
    privacy: str
    context_mode: str
    conflict: bool


def memory_for(c: Case) -> tuple[MemoryRecord, str | None]:
    valid_from = "2000-01-01T00:00:00+00:00"
    valid_until = "2001-01-01T00:00:00+00:00"
    if c.temporal == "expired":
        valid_until = "1999-01-01T00:00:00+00:00"
    elif c.temporal == "future":
        valid_from = "2001-01-01T00:00:00+00:00"
    elif c.temporal == "malformed_from":
        valid_from = "not-a-time"
    elif c.temporal == "malformed_until":
        valid_until = "not-a-time"

    scope = None
    context = None
    if c.context_mode == "same":
        scope, context = "work", "work"
    elif c.context_mode == "mismatch":
        scope, context = "work", "home"
    elif c.context_mode == "unknown":
        scope, context = "work", None

    m = MemoryRecord(
        user_id="u",
        subject="user",
        predicate="preference.food",
        value="sushi",
        memory_type=MemoryType.PREFERENCE,
        source_type=SourceType(c.source),
        confidence=c.confidence,
        source_event_ids=["evt_x"] if c.provenance else [],
        valid_from=valid_from,
        valid_until=valid_until,
        context_scope=scope,
        status=MemoryStatus(c.status),
        user_verified=c.verified,
        privacy_level=c.privacy,
    )
    return m, context


def iter_cases():
    for values in itertools.product(
        [MemoryStatus.ACTIVE.value, MemoryStatus.SUPERSEDED.value],
        ["valid", "expired", "future", "malformed_from", "malformed_until"],
        [SourceType.EXPLICIT.value, SourceType.INFERRED.value, SourceType.SYNTHETIC.value],
        [0.20, 0.52, 0.77, 0.78, 0.95],
        [False, True],
        [False, True],
        ["normal", "sensitive"],
        ["unscoped", "same", "mismatch", "unknown"],
        [False, True],
    ):
        yield Case(*values)


def safety_invalid(c: Case) -> bool:
    return (
        c.status != MemoryStatus.ACTIVE.value
        or c.temporal != "valid"
        or c.source == SourceType.SYNTHETIC.value
        or not c.provenance
        or (c.privacy != "normal" and not c.verified)
        or c.context_mode in {"mismatch", "unknown"}
        or c.conflict
    )


def evaluate_gate(name: str, gate) -> dict:
    cases = list(iter_cases())
    decisions = {}
    reasons = Counter()
    violations = defaultdict(list)

    for c in cases:
        m, context = memory_for(c)
        d = gate.decide(m, context=context, now=NOW, unresolved_conflict=c.conflict)
        decisions[c] = d
        reasons[d.reason] += 1

        if safety_invalid(c) and d.action == PersonalizationAction.USE:
            violations["safety_invalid_never_use"].append((c, d))

        clean_except_conflict = (
            c.status == MemoryStatus.ACTIVE.value
            and c.temporal == "valid"
            and c.source == SourceType.EXPLICIT.value
            and c.provenance
            and c.privacy == "normal"
            and c.context_mode in {"unscoped", "same"}
        )
        if clean_except_conflict and c.conflict and d.action != PersonalizationAction.ASK:
            violations["unresolved_conflict_requires_ask"].append((c, d))

        clean_unknown_context = (
            c.status == MemoryStatus.ACTIVE.value
            and c.temporal == "valid"
            and c.source == SourceType.EXPLICIT.value
            and c.provenance
            and c.privacy == "normal"
            and c.context_mode == "unknown"
            and not c.conflict
        )
        if clean_unknown_context and d.action == PersonalizationAction.USE:
            violations["scoped_unknown_context_never_use"].append((c, d))

    # Monotonicity checks over safe slices.
    for source in [SourceType.EXPLICIT.value, SourceType.INFERRED.value]:
        for verified in [False, True]:
            seq=[]
            for confidence in [0.20, 0.52, 0.77, 0.78, 0.95]:
                c=Case(MemoryStatus.ACTIVE.value,"valid",source,confidence,verified,True,"normal","same",False)
                seq.append((confidence,decisions[c]))
            for (c1,d1),(c2,d2) in zip(seq,seq[1:]):
                if ACTION_ORDER[d2.action] < ACTION_ORDER[d1.action]:
                    violations["confidence_monotonicity"].append(((source,verified,c1,c2),d1,d2))

    for source in [SourceType.EXPLICIT.value, SourceType.INFERRED.value]:
        for confidence in [0.20, 0.52, 0.77, 0.78, 0.95]:
            c0=Case(MemoryStatus.ACTIVE.value,"valid",source,confidence,False,True,"normal","same",False)
            c1=Case(MemoryStatus.ACTIVE.value,"valid",source,confidence,True,True,"normal","same",False)
            if ACTION_ORDER[decisions[c1].action] < ACTION_ORDER[decisions[c0].action]:
                violations["verification_monotonicity"].append(((source,confidence),decisions[c0],decisions[c1]))

    for confidence in [0.20, 0.52, 0.77, 0.78, 0.95]:
        ci=Case(MemoryStatus.ACTIVE.value,"valid",SourceType.INFERRED.value,confidence,False,True,"normal","same",False)
        ce=Case(MemoryStatus.ACTIVE.value,"valid",SourceType.EXPLICIT.value,confidence,False,True,"normal","same",False)
        if ACTION_ORDER[decisions[ce].action] < ACTION_ORDER[decisions[ci].action]:
            violations["explicit_not_weaker_than_inferred"].append((confidence,decisions[ci],decisions[ce]))

    compact={}
    for prop, vals in violations.items():
        examples=[]
        for v in vals[:5]:
            if isinstance(v,tuple) and v and isinstance(v[0],Case):
                examples.append({"case":asdict(v[0]),"action":v[1].action.value,"reason":v[1].reason})
            else:
                examples.append(str(v))
        compact[prop]={"count":len(vals),"examples":examples}

    return {
        "gate": name,
        "n_states": len(cases),
        "action_counts": dict(Counter(d.action.value for d in decisions.values())),
        "reason_counts": dict(reasons),
        "properties": {
            "safety_invalid_never_use": len(violations["safety_invalid_never_use"]) == 0,
            "unresolved_conflict_requires_ask": len(violations["unresolved_conflict_requires_ask"]) == 0,
            "scoped_unknown_context_never_use": len(violations["scoped_unknown_context_never_use"]) == 0,
            "confidence_monotonicity": len(violations["confidence_monotonicity"]) == 0,
            "verification_monotonicity": len(violations["verification_monotonicity"]) == 0,
            "explicit_not_weaker_than_inferred": len(violations["explicit_not_weaker_than_inferred"]) == 0,
        },
        "n_property_violations": sum(len(v) for v in violations.values()),
        "violations": compact,
    }


def run() -> dict:
    systems = [
        evaluate_gate("DecisionAwareBeliefGateV1", DecisionAwareBeliefGate()),
        evaluate_gate("DecisionAwareBeliefGateV2", DecisionAwareBeliefGateV2()),
        evaluate_gate("DecisionAwareBeliefGateV3", DecisionAwareBeliefGateV3()),
    ]
    return {
        "suite": "Exhaustive Authority State-Space Verification",
        "state_space_dimensions": {
            "status": 2,
            "temporal": 5,
            "source": 3,
            "confidence": 5,
            "verified": 2,
            "provenance": 2,
            "privacy": 2,
            "context_mode": 4,
            "conflict": 2,
        },
        "n_states_per_gate": systems[0]["n_states"],
        "systems": systems,
        "production_gate": "DecisionAwareBeliefGateV3",
        "production_all_properties_hold": all(systems[-1]["properties"].values()),
        "boundary": "Finite exhaustive verification over the declared discrete policy state space; it is not a proof over arbitrary code, arbitrary timestamps, or unmodeled metadata fields.",
    }


def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='results/authority_modelcheck.json'); a=ap.parse_args()
    r=run(); Path(a.out).write_text(json.dumps(r,indent=2));
    print(json.dumps({"n_states_per_gate":r["n_states_per_gate"],"production_all_properties_hold":r["production_all_properties_hold"],"violations":{s['gate']:s['n_property_violations'] for s in r['systems']}},indent=2))

if __name__=='__main__': main()
