from pathlib import Path
from datetime import datetime, timezone, timedelta
from pwm.memory.schema import MemoryRecord,MemoryType,SourceType,MemoryStatus
from pwm.memory.store import MemoryStore
from pwm.memory.semantic_retriever import SemanticMemoryRetriever

def test_retrieval_never_returns_inactive(tmp_path:Path):
    s=MemoryStore(tmp_path/'r.db'); now=datetime.now(timezone.utc).isoformat()
    active=MemoryRecord(user_id='u',subject='user',predicate='likes',value='quiet cafes',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_ids=['a'],valid_from=now)
    stale=MemoryRecord(user_id='u',subject='user',predicate='likes',value='restaurants',memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=1,source_event_ids=['b'],valid_from=now,status=MemoryStatus.SUPERSEDED)
    s.add(active); s.add(stale)
    out=SemanticMemoryRetriever(s).retrieve('u','restaurant',limit=10)
    assert [x.memory.id for x in out]==[active.id]

def test_context_bonus_changes_ranking(tmp_path:Path):
    s=MemoryStore(tmp_path/'c.db'); now=datetime.now(timezone.utc).isoformat()
    for value,ctx in [('formal tone','work'),('casual tone','friends')]:
        s.add(MemoryRecord(user_id='u',subject='user',predicate='prefers',value=value,memory_type=MemoryType.PREFERENCE,source_type=SourceType.EXPLICIT,confidence=.9,source_event_ids=[value],valid_from=now,context_scope=ctx))
    r=SemanticMemoryRetriever(s)
    assert r.retrieve('u','How should I write?',1,context='work')[0].memory.value=='formal tone'
    assert r.retrieve('u','How should I write?',1,context='friends')[0].memory.value=='casual tone'
