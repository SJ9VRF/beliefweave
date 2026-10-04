from pwm.belief_governance import DecisionAwareBeliefGateV3,PersonalizationAction
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType,MemoryStatus
NOW='2000-06-01T12:00:00+00:00'
def m(**kw):
    d=dict(user_id='u',subject='user',predicate='p',value='v',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_ids=['evt'],status=MemoryStatus.ACTIVE)
    d.update(kw);return MemoryRecord(**d)
def test_v3_lifecycle_dominates_unknown_context():
    g=DecisionAwareBeliefGateV3()
    assert g.decide(m(status=MemoryStatus.DELETED,context_scope='work'),context=None,now=NOW).action==PersonalizationAction.ABSTAIN
def test_v3_malformed_time_asks():
    g=DecisionAwareBeliefGateV3()
    assert g.decide(m(valid_until='bad'),context='x',now=NOW).action==PersonalizationAction.ASK
def test_v3_missing_provenance_asks():
    assert DecisionAwareBeliefGateV3().decide(m(source_event_ids=[]),context='x',now=NOW).action==PersonalizationAction.ASK
def test_v3_sensitive_unverified_asks_and_verified_can_use():
    g=DecisionAwareBeliefGateV3()
    assert g.decide(m(privacy_level='sensitive'),context='x',now=NOW).action==PersonalizationAction.ASK
    assert g.decide(m(privacy_level='sensitive',user_verified=True),context='x',now=NOW).action==PersonalizationAction.USE
def test_v3_exact_temporal_boundary_is_valid():
    assert DecisionAwareBeliefGateV3().decide(m(valid_from=NOW,valid_until=NOW),context='x',now=NOW).action==PersonalizationAction.USE
