from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from beliefweave import (
    IdempotencyConflictError,
    PersonalMemoryEngine,
    TemporalValueError,
)
from demo.app import app


def test_default_runtime_does_not_implicitly_enable_optional_ml(tmp_path):
    engine = PersonalMemoryEngine(tmp_path / "default.db")
    caps = engine.runtime_capabilities()
    assert caps["ml_enabled"] is False
    assert caps["extractor"] == "RuleBasedObservationExtractor"
    assert caps["retriever"] == "MemoryRetriever"
    assert caps["conflict_resolver"] == "ConflictResolver"


def test_timestamp_is_canonicalized_before_idempotency_hashing(tmp_path):
    engine = PersonalMemoryEngine(tmp_path / "time.db")
    first = engine.ingest(
        "u",
        "I love tea.",
        timestamp="2026-01-01T01:00:00+01:00",
        idempotency_key="same-instant",
    )
    assert first["event"].timestamp == "2026-01-01T00:00:00+00:00"

    replay = engine.ingest(
        "u",
        "I love tea.",
        timestamp="2026-01-01T00:00:00Z",
        idempotency_key="same-instant",
    )
    assert replay["idempotent_replay"] is True


def test_invalid_temporal_values_fail_fast(tmp_path):
    engine = PersonalMemoryEngine(tmp_path / "invalid-time.db")
    with pytest.raises(TemporalValueError):
        engine.ingest("u", "I love tea.", timestamp="not-a-time")
    engine.ingest("u", "I love tea.")
    with pytest.raises(TemporalValueError):
        engine.recall("u", "tea", now="also-not-a-time")
    with pytest.raises(TemporalValueError):
        engine.current_state("u", now="bad")


def test_idempotency_conflict_has_typed_domain_error(tmp_path):
    engine = PersonalMemoryEngine(tmp_path / "idem.db")
    engine.ingest("u", "I love tea.", idempotency_key="k")
    with pytest.raises(IdempotencyConflictError):
        engine.ingest("u", "I love coffee.", idempotency_key="k")


def test_demo_api_maps_invalid_time_to_422():
    client = TestClient(app)
    response = client.post(
        "/api/ingest",
        json={"user_id": "time-api", "text": "I love tea.", "timestamp": "garbage"},
    )
    assert response.status_code == 422
    assert "ISO-8601" in response.json()["detail"]


def test_demo_api_requires_configured_token(monkeypatch):
    monkeypatch.setenv("BELIEFWEAVE_DEMO_TOKEN", "test-secret")
    client = TestClient(app)
    denied = client.get("/api/state/auth-user")
    assert denied.status_code == 401
    allowed = client.get(
        "/api/state/auth-user",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert allowed.status_code == 200


def test_openapi_documents_remote_demo_security_schemes():
    schema = app.openapi()
    schemes = schema['components']['securitySchemes']
    assert schemes['BearerAuth']['scheme'] == 'bearer'
    assert schemes['DemoApiKey']['name'] == 'X-API-Key'
    for path, operations in schema['paths'].items():
        if not path.startswith('/api/'):
            continue
        for operation in operations.values():
            if isinstance(operation, dict) and 'responses' in operation:
                assert {'BearerAuth': []} in operation['security']
                assert {'DemoApiKey': []} in operation['security']


def test_docker_compose_requires_explicit_demo_token():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[1] / 'docker-compose.yml').read_text()
    assert 'BELIEFWEAVE_DEMO_TOKEN' in text
    assert ':?Set BELIEFWEAVE_DEMO_TOKEN' in text
