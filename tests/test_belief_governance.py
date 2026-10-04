from pwm.belief_governance import *
from pwm.memory.schema import *
def m(**kw):
    base=dict(user_id='u',subject='user',predicate='p',value='v',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.95,source_event_ids=['e']);base.update(kw);return MemoryRecord(**base)
def test_gate_uses_strong_explicit_memory(): assert DecisionAwareBeliefGate().decide(m()).action==PersonalizationAction.USE
def test_gate_rejects_stale_memory(): assert DecisionAwareBeliefGate().decide(m(valid_until='2025-01-01T00:00:00+00:00'),now='2026-01-01T00:00:00+00:00').action==PersonalizationAction.ABSTAIN
def test_gate_asks_on_unresolved_conflict(): assert DecisionAwareBeliefGate().decide(m(),unresolved_conflict=True).action==PersonalizationAction.ASK
def test_false_personalization_costs_more(): assert counterfactual_personalization_regret([False],[PersonalizationAction.USE])>counterfactual_personalization_regret([True],[PersonalizationAction.ABSTAIN])
def test_intervention_fidelity(): assert memory_intervention_fidelity([True,False],[True,False])==1.0

def test_engine_governed_recall(tmp_path):
    from pwm.engine import PersonalMemoryEngine
    e=PersonalMemoryEngine(tmp_path/'g.db')
    e.ingest('u','I love sushi.')
    out=e.governed_recall('u','food sushi',limit=3)
    assert out
    assert out[0]['gate'].action in {PersonalizationAction.USE,PersonalizationAction.ASK}
