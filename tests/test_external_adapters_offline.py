import json
from pathlib import Path

from benchmark.external.locomo_adapter import run as run_locomo
from scripts.fetch_external_benchmarks import DATASETS


def test_locomo_adapter_mini_fixture(tmp_path: Path):
    fixture = [{
        "sample_id": "mini-1",
        "conversation": {
            "session_1": [
                {"dia_id": "d1", "speaker": "A", "text": "I like sushi."},
                {"dia_id": "d2", "speaker": "B", "text": "Great."},
            ],
            "session_2": [
                {"dia_id": "d3", "speaker": "A", "text": "I now prefer ramen."},
            ],
        },
        "qa": [
            {"question": "What food do I like?", "answer": "ramen", "category": 1, "evidence": ["d3"]},
            {"question": "What impossible fact is true?", "answer": "none", "category": 5, "evidence": []},
        ],
    }]
    p = tmp_path / "locomo.json"
    p.write_text(json.dumps(fixture))
    out = run_locomo(p, top_k=5)
    assert out["samples"] == 1
    assert out["answerable_questions"] == 1
    assert len(out["rows"]) == 2
    assert out["rows"][1]["answerable"] is False
    assert 0.0 <= out["mean_evidence_recall_at_k"] <= 1.0


def test_external_fetch_registry_has_pinned_sources():
    assert {"longmemeval_oracle", "locomo10", "personamem_questions_32k", "personamem_contexts_32k"}.issubset(DATASETS)
    assert len(DATASETS["longmemeval_oracle"]["sha256"]) == 64
    assert len(DATASETS["locomo10"]["sha256"]) == 64
    for spec in DATASETS.values():
        assert spec["url"].startswith("https://")
        assert spec["filename"]
        assert spec["license"]
