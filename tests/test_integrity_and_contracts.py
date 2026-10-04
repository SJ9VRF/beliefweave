from __future__ import annotations
import json, random, sqlite3
from contextlib import closing
from pathlib import Path

from pwm.engine import PersonalMemoryEngine
from pwm.integrity import audit_database


def test_database_integrity_clean(tmp_path):
    db=tmp_path/'clean.db'; e=PersonalMemoryEngine(db)
    e.ingest('alice','I love sushi.')
    e.ingest('alice','Actually, I dislike sushi.')
    report=audit_database(db)
    assert report['ok'] is True
    assert report['error_count']==0
    assert report['events']==2
    assert report['memories']>=2


def test_database_integrity_detects_orphan_source(tmp_path):
    db=tmp_path/'orphan.db'; e=PersonalMemoryEngine(db)
    out=e.ingest('alice','I love sushi.')
    mem=next(a['memory'] for a in out['actions'] if a['memory'])
    with closing(sqlite3.connect(db)) as conn:
        conn.execute('DELETE FROM events WHERE id=?',(mem.source_event_ids[0],))
        conn.commit()
    report=audit_database(db)
    assert report['ok'] is False
    assert any(x['code']=='orphan_source_event' for x in report['issues'])


def test_openapi_contract(tmp_path):
    from demo.app import app
    spec=app.openapi()
    required={
        '/health': {'get'},
        '/api/ingest': {'post'},
        '/api/recall': {'post'},
        '/api/state/{user_id}': {'get'},
        '/api/memories/{user_id}': {'get'},
        '/api/export/{user_id}': {'get'},
        '/api/user/{user_id}': {'delete'},
        '/api/memory/{memory_id}': {'delete','patch'},
    }
    for path, methods in required.items():
        assert path in spec['paths']
        assert methods.issubset(set(spec['paths'][path]))


def test_randomized_state_machine_invariants(tmp_path):
    rng=random.Random(20260923)
    db=tmp_path/'state-machine.db'; e=PersonalMemoryEngine(db)
    users=['u0','u1','u2']
    phrases=['I love sushi.','I like jazz.','My goal is to publish a paper.','I prefer concise answers.','Actually, I dislike sushi.']
    for _ in range(250):
        user=rng.choice(users); op=rng.random()
        if op < .62:
            e.ingest(user,rng.choice(phrases))
        elif op < .78:
            e.recall(user,rng.choice(['food','music','goal','style']),limit=3)
        elif op < .9:
            active=e.memories.list_active(user)
            if active: e.memories.correct(rng.choice(active).id,'corrected value')
        else:
            active=e.memories.list_active(user)
            if active: e.forget_memory(rng.choice(active).id,delete_source_events=rng.random()<.35)
        # Cross-user isolation and state referential integrity after every operation.
        for u in users:
            allm=e.memories.list_all(u)
            assert all(m.user_id==u for m in allm)
            active_ids={m.id for m in e.memories.list_active(u)}
            for vals in e.current_state(u).values():
                assert all(b.memory_id in active_ids for b in vals)
    assert audit_database(db)['ok'] is True

def test_database_integrity_reports_corruption_classes(tmp_path):
    db=tmp_path/'corrupt.db'; e=PersonalMemoryEngine(db)
    a=e.ingest('alice','I love sushi.')
    b=e.ingest('bob','I like jazz.')
    am=next(x['memory'] for x in a['actions'] if x['memory'])
    bm=next(x['memory'] for x in b['actions'] if x['memory'])
    be=b['event']
    with closing(sqlite3.connect(db)) as conn:
        # Cross-user provenance and relation errors on Alice memory.
        conn.execute('UPDATE memories SET source_event_ids_json=?, supersedes=?, conflicts_with_json=? WHERE id=?',
                     (json.dumps([be.id]), bm.id, json.dumps([bm.id,'mem_missing']), am.id))
        # Separate invalid JSON record.
        conn.execute("INSERT INTO memories (id,user_id,subject,predicate,value,memory_type,source_type,confidence,source_event_ids_json,created_at,updated_at,valid_from,valid_until,stability,importance,context_scope,status,supersedes,conflicts_with_json,retrieval_count,last_used_at,user_verified,privacy_level,correction_count) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     ('mem_bad','alice','user','likes','tea','preference','explicit',.9,'{bad','2026-01-01T00:00:00+00:00','2026-01-01T00:00:00+00:00',None,None,.5,.5,None,'active',None,'{bad',0,None,0,'normal',0))
        conn.commit()
    report=audit_database(db)
    codes={x['code'] for x in report['issues']}
    assert {'cross_user_provenance','cross_user_supersedes','cross_user_conflict','orphan_conflict','invalid_source_json','invalid_conflict_json'} <= codes
    assert report['ok'] is False


def test_database_integrity_missing_tables(tmp_path):
    db=tmp_path/'empty.db'
    with closing(sqlite3.connect(db)):
        pass
    report=audit_database(db)
    assert report['ok'] is False
    assert any(x['code']=='missing_tables' for x in report['issues'])


def test_database_integrity_flags_lazy_expiry(tmp_path):
    db=tmp_path/'expired.db'; e=PersonalMemoryEngine(db)
    out=e.ingest('alice','I love sushi.')
    mem=next(x['memory'] for x in out['actions'] if x['memory'])
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("UPDATE memories SET valid_until='2020-01-01T00:00:00+00:00' WHERE id=?",(mem.id,)); conn.commit()
    report=audit_database(db, now='2026-01-01T00:00:00+00:00')
    assert report['ok'] is True
    assert report['warning_count']==1
    assert report['issues'][0]['code']=='active_but_expired'
