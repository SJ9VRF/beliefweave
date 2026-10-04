from datetime import datetime,timezone,timedelta
from pwm.engine import PersonalMemoryEngine
from pwm.memory.schema import MemoryStatus

def iso(days=0): return (datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(days=days)).isoformat()

def test_preference_reversal_supersedes(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'x.db')
    e.ingest('u','I love sushi.',context='food',timestamp=iso(0))
    e.ingest('u','I dislike sushi.',context='food',timestamp=iso(10))
    allm=e.memories.list_all('u')
    assert len(allm)==2
    assert allm[0].status==MemoryStatus.SUPERSEDED
    assert allm[1].status==MemoryStatus.ACTIVE
    assert allm[1].supersedes==allm[0].id

def test_temporary_memory_expires(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'x.db')
    e.ingest('u',"I'm avoiding raw fish this month.",context='food',timestamp=iso(0))
    assert len(e.memories.list_active('u',now=iso(10)))==1
    assert len(e.memories.list_active('u',now=iso(40)))==0
    assert e.memories.list_all('u')[0].status==MemoryStatus.EXPIRED

def test_context_dependent_preferences_coexist(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'x.db')
    e.ingest('u','I prefer formal language.',context='work',timestamp=iso(0))
    e.ingest('u','I prefer casual language.',context='friends',timestamp=iso(1))
    assert len(e.memories.list_active('u'))==2

def test_current_state_has_provenance(tmp_path):
    e=PersonalMemoryEngine(tmp_path/'x.db')
    e.ingest('u','My goal is to publish a paper.',timestamp=iso(0))
    state=e.current_state('u')
    assert 'goal.goal' in state
    assert state['goal.goal'][0].provenance
