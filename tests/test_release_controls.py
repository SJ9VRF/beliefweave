from pathlib import Path
from fastapi.testclient import TestClient
from demo.app import app, engine

client = TestClient(app)

def test_health_and_project_routes():
    assert client.get('/health').status_code == 200
    assert client.get('/project').status_code == 200
    assert client.get('/dashboard').status_code == 200


def test_export_and_hard_forget_roundtrip(tmp_path, monkeypatch):
    # Use the real engine API directly for deterministic source-event deletion semantics.
    from pwm.engine import PersonalMemoryEngine
    e = PersonalMemoryEngine(tmp_path / 'x.db')
    out = e.ingest('u-release', 'I love sushi.')
    memory = next(a['memory'] for a in out['actions'] if a['memory'])
    assert memory is not None
    event_id = out['event'].id
    assert e.events.get(event_id) is not None
    assert e.forget_memory(memory.id, delete_source_events=True)
    assert e.memories.get(memory.id) is None
    assert e.events.get(event_id) is None


def test_user_state_isolation(tmp_path):
    from pwm.engine import PersonalMemoryEngine
    e = PersonalMemoryEngine(tmp_path / 'isolation.db')
    e.ingest('alice', 'I love sushi.')
    e.ingest('bob', 'I dislike sushi.')
    alice = e.current_state('alice')
    bob = e.current_state('bob')
    assert str(alice) != str(bob)
    assert all(m.user_id == 'alice' for m in e.memories.list_all('alice'))
    assert all(m.user_id == 'bob' for m in e.memories.list_all('bob'))
