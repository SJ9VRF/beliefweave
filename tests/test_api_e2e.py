from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient
from demo.app import app, engine

client = TestClient(app)


def test_api_ingest_recall_state_export_and_hard_forget():
    user_id = f"api-{uuid4().hex}"

    health = client.get('/health')
    assert health.status_code == 200
    assert health.json()['ok'] is True

    ing = client.post('/api/ingest', json={
        'user_id': user_id,
        'text': 'I love sushi.',
        'context': 'food',
    })
    assert ing.status_code == 200
    payload = ing.json()
    assert payload['event']['user_id'] == user_id
    memories = [a['memory'] for a in payload['actions'] if a['memory']]
    assert memories, payload
    memory_id = memories[0]['id']
    source_event_id = memories[0]['source_event_ids'][0]

    st = client.get(f'/api/state/{user_id}')
    assert st.status_code == 200
    assert any(b['value'] == 'sushi' for vals in st.json().values() for b in vals)

    rec = client.post('/api/recall', json={
        'user_id': user_id,
        'query': 'Where should I go for dinner?',
        'context': 'food',
        'limit': 5,
    })
    assert rec.status_code == 200
    assert any(r['memory']['value'] == 'sushi' for r in rec.json())

    exp = client.get(f'/api/export/{user_id}')
    assert exp.status_code == 200
    exported = exp.json()
    assert exported['user_id'] == user_id
    assert any(m['id'] == memory_id for m in exported['memories'])

    deleted = client.delete(f'/api/memory/{memory_id}?hard=true')
    assert deleted.status_code == 200
    assert deleted.json() == {'ok': True, 'hard': True}
    assert engine.memories.get(memory_id) is None
    assert engine.events.get(source_event_id) is None


def test_api_user_isolation():
    u1 = f"api-a-{uuid4().hex}"
    u2 = f"api-b-{uuid4().hex}"
    assert client.post('/api/ingest', json={'user_id': u1, 'text': 'I love tea.'}).status_code == 200
    assert client.post('/api/ingest', json={'user_id': u2, 'text': 'I love coffee.'}).status_code == 200

    e1 = client.get(f'/api/export/{u1}').json()
    e2 = client.get(f'/api/export/{u2}').json()
    vals1 = {m['value'] for m in e1['memories']}
    vals2 = {m['value'] for m in e2['memories']}
    assert 'tea' in vals1 and 'coffee' not in vals1
    assert 'coffee' in vals2 and 'tea' not in vals2


def test_api_idempotency_header_replay_conflict_and_privacy_tombstone():
    user_id=f"api-idem-{uuid4().hex}"
    key=f"req-{uuid4().hex}"
    body={'user_id':user_id,'text':'I love sushi.','context':'food'}
    first=client.post('/api/ingest',json=body,headers={'Idempotency-Key':key})
    assert first.status_code==200 and first.json()['idempotent_replay'] is False
    second=client.post('/api/ingest',json=body,headers={'Idempotency-Key':key})
    assert second.status_code==200 and second.json()['idempotent_replay'] is True
    assert second.json()['event']['id']==first.json()['event']['id']

    mismatch=client.post('/api/ingest',json={**body,'text':'I love ramen.'},headers={'Idempotency-Key':key})
    assert mismatch.status_code==409

    memory_id=next(a['memory']['id'] for a in first.json()['actions'] if a['memory'])
    assert client.delete(f'/api/memory/{memory_id}?hard=true').status_code==200
    gone=client.post('/api/ingest',json=body,headers={'Idempotency-Key':key})
    assert gone.status_code==410
    assert client.get(f'/api/export/{user_id}').json()['events']==[]


def test_api_rejects_disagreeing_header_and_body_idempotency_keys():
    r=client.post('/api/ingest',json={
        'user_id':f"api-idem-mismatch-{uuid4().hex}",
        'text':'I love tea.',
        'idempotency_key':'body-key',
    },headers={'Idempotency-Key':'header-key'})
    assert r.status_code==409


def test_api_correction_creates_versioned_provenance_and_is_idempotent():
    user = 'api-correction-user'
    created = client.post('/api/ingest', json={'user_id': user, 'text': 'I love sushi.'})
    assert created.status_code == 200
    old_id = created.json()['actions'][0]['memory']['id']

    first = client.patch(f'/api/memory/{old_id}', json={'value': 'ramen'})
    assert first.status_code == 200
    corrected = first.json()
    assert corrected['id'] != old_id
    assert corrected['supersedes'] == old_id
    assert corrected['user_verified'] is True
    assert corrected['source_event_ids']

    replay = client.patch(f'/api/memory/{old_id}', json={'value': 'ramen'})
    assert replay.status_code == 200
    assert replay.json()['id'] == corrected['id']

    stale = client.patch(f'/api/memory/{old_id}', json={'value': 'udon'})
    assert stale.status_code == 409
