from pwm.belief_governance import AuthorityCosts,CostSensitiveAuthorityPolicy,PersonalizationAction,authority_probability
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType

def mem(conf=.9,source=SourceType.EXPLICIT,verified=False):
    return MemoryRecord(user_id='u',subject='user',predicate='likes',value='sushi',memory_type=MemoryType.PREFERENCE,source_type=source,confidence=conf,source_event_ids=['e'],user_verified=verified)

def test_cost_policy_extremes():
    p=CostSensitiveAuthorityPolicy(AuthorityCosts(2,1,.25))
    assert p.decide_from_probability(.99).action==PersonalizationAction.USE
    assert p.decide_from_probability(.5).action==PersonalizationAction.ASK
    assert p.decide_from_probability(.01).action==PersonalizationAction.ABSTAIN

def test_authority_probability_respects_provenance_and_verification():
    assert authority_probability(mem(.7,SourceType.INFERRED)) < authority_probability(mem(.7,SourceType.EXPLICIT))
    assert authority_probability(mem(.7,SourceType.EXPLICIT,True)) > authority_probability(mem(.7,SourceType.EXPLICIT,False))
