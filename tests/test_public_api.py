from __future__ import annotations

import beliefweave


def test_public_api_matches_package_identity(tmp_path):
    import tomllib
    from pathlib import Path

    expected = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())["project"]["version"]
    assert beliefweave.__version__ == expected
    assert beliefweave.PRODUCTION_GATE_VERSION == "v3"

    engine = beliefweave.PersonalMemoryEngine(tmp_path / "api.db")
    result = engine.ingest("u", "I like jazz", idempotency_key="req-1")
    assert result["idempotent_replay"] is False

    replay = engine.ingest("u", "I like jazz", idempotency_key="req-1")
    assert replay["idempotent_replay"] is True


def test_legacy_namespace_remains_available():
    from pwm.engine import PersonalMemoryEngine as LegacyEngine

    assert LegacyEngine is beliefweave.PersonalMemoryEngine
