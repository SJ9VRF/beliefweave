from fastapi.testclient import TestClient

from demo.app import app, engine


def test_export_api_includes_control_metadata_and_full_purge(tmp_path, monkeypatch):
    # The demo module owns a process-local engine. Use a unique user so the test
    # remains isolated without mutating global application configuration.
    user = f"api-purge-{tmp_path.name}"
    client = TestClient(app)

    ingest = client.post(
        "/api/ingest",
        json={"user_id": user, "text": "I like tea."},
        headers={"Idempotency-Key": "api-key-1"},
    )
    assert ingest.status_code == 200

    exported = client.get(f"/api/export/{user}")
    assert exported.status_code == 200
    body = exported.json()
    assert body["events"]
    assert body["control_metadata"]["ingest_receipts"]

    deleted = client.delete(f"/api/user/{user}")
    assert deleted.status_code == 200
    assert deleted.json()["complete_erasure"] is True

    after = client.get(f"/api/export/{user}").json()
    assert after["events"] == []
    assert after["memories"] == []
    assert after["control_metadata"]["ingest_receipts"] == []


def test_guarded_user_purge_keeps_only_scrubbed_receipt(tmp_path):
    user = f"api-guard-{tmp_path.name}"
    client = TestClient(app)
    assert client.post(
        "/api/ingest",
        json={"user_id": user, "text": "I prefer concise answers."},
        headers={"Idempotency-Key": "api-guard-key"},
    ).status_code == 200

    deleted = client.delete(
        f"/api/user/{user}", params={"retain_replay_guard": "true"}
    )
    assert deleted.status_code == 200
    assert deleted.json()["complete_erasure"] is False

    receipt = client.get(f"/api/export/{user}").json()["control_metadata"]["ingest_receipts"][0]
    assert receipt["tombstoned"] is True
    assert receipt["request_hash"] == ""
    assert receipt["event_id"] == ""


def test_demo_misc_routes_cover_public_contract(tmp_path):
    user = f"api-misc-{tmp_path.name}"
    client = TestClient(app)
    assert client.get('/').status_code == 200
    assert client.post(
        '/api/ingest', json={'user_id': user, 'text': 'I like green tea.'}
    ).status_code == 200
    governed = client.post(
        '/api/governed-recall', json={'user_id': user, 'query': 'tea'}
    )
    assert governed.status_code == 200
    assert isinstance(governed.json(), list)
    memories = client.get(f'/api/memories/{user}')
    assert memories.status_code == 200
    assert memories.json()
    assert client.delete('/api/memory/not-a-real-memory').status_code == 404
    assert client.patch(
        '/api/memory/not-a-real-memory', json={'value': 'replacement'}
    ).status_code == 404
