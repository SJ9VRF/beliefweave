from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_experiment_lineage_hashes_match_release_files():
    path = ROOT / "results" / "experiment_lineage.json"
    assert path.exists()
    payload = json.loads(path.read_text())
    assert payload["schema"] == "beliefweave.experiment-lineage.v1"
    assert len(payload["experiments"]) >= 8
    for exp in payload["experiments"]:
        result = ROOT / exp["result"]
        assert result.exists()
        assert exp["result_sha256"] == _sha(result)
        for item in exp["code"] + exp["inputs"]:
            p = ROOT / item["path"]
            assert p.exists()
            assert item["sha256"] == _sha(p)
