from pwm.belief_governance import DecisionAwareBeliefGateV2, PersonalizationAction
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType
NOW='2000-06-01T12:00:00+00:00'
def m(**kw):
    base=dict(user_id='u',subject='user',predicate='p',value='v',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.95,source_event_ids=['e'])
    base.update(kw); return MemoryRecord(**base)
def test_future_effective_abstains():
    assert DecisionAwareBeliefGateV2().decide(m(valid_from='2001-01-01T00:00:00+00:00'),now=NOW).action==PersonalizationAction.ABSTAIN
def test_scoped_unknown_context_asks():
    assert DecisionAwareBeliefGateV2().decide(m(context_scope='work'),context=None,now=NOW).action==PersonalizationAction.ASK
def test_synthetic_abstains():
    assert DecisionAwareBeliefGateV2().decide(m(source_type=SourceType.SYNTHETIC),context='x',now=NOW).action==PersonalizationAction.ABSTAIN
