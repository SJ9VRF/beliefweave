from __future__ import annotations

import hashlib
import importlib.metadata as md
import json
import platform
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"


def sha256(rel: str) -> str:
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest()


def existing(items: list[str]) -> list[str]:
    return [x for x in items if (ROOT / x).exists()]


EXPERIMENTS = {
    "paper_grade_eval": {
        "result": "results/paper_grade_eval.json",
        "command": "python benchmark/paper_grade_eval.py",
        "code": ["benchmark/paper_grade_eval.py", "pwm/belief_governance.py"],
        "inputs": ["benchmark/beliefshift_v2_test_manifest.json"],
    },
    "behavior_intervention": {
        "result": "results/behavior_intervention.json",
        "command": "python benchmark/behavior_intervention_eval.py",
        "code": ["benchmark/behavior_intervention_eval.py", "pwm/belief_governance.py"],
        "inputs": ["benchmark/beliefshift_v2_test_manifest.json"],
    },
    "sealed_spec_challenge": {
        "result": "results/sealed_spec_challenge.json",
        "command": "python benchmark/sealed_spec_challenge.py",
        "code": ["benchmark/sealed_spec_challenge.py", "pwm/belief_governance.py"],
        "inputs": ["benchmark/sealed_spec_manifest.json", "benchmark/sealed_spec_manifest.sha256"],
    },
    "authority_modelcheck": {
        "result": "results/authority_modelcheck.json",
        "command": "python benchmark/authority_modelcheck.py",
        "code": ["benchmark/authority_modelcheck.py", "pwm/belief_governance.py"],
        "inputs": [],
    },
    "privacy_erasure": {
        "result": "results/privacy_erasure.json",
        "command": "python benchmark/privacy_erasure_eval.py",
        "code": ["benchmark/privacy_erasure_eval.py", "pwm/engine.py", "pwm/integrity.py"],
        "inputs": [],
    },
    "concurrency_integrity": {
        "result": "results/concurrency_integrity.json",
        "command": "python benchmark/concurrency_integrity_eval.py",
        "code": ["benchmark/concurrency_integrity_eval.py", "pwm/engine.py", "pwm/memory/store.py", "pwm/events/store.py"],
        "inputs": [],
    },
    "atomicity_fault_injection": {
        "result": "results/atomicity_fault_injection.json",
        "command": "python benchmark/atomicity_fault_injection_eval.py",
        "code": ["benchmark/atomicity_fault_injection_eval.py", "pwm/engine.py", "pwm/memory/store.py", "pwm/events/store.py"],
        "inputs": [],
    },
    "horizon_scaling": {
        "result": "results/horizon_scaling.json",
        "command": "python benchmark/horizon_scaling.py",
        "code": ["benchmark/horizon_scaling.py", "pwm/engine.py"],
        "inputs": [],
    },
    "retrieval_eval": {
        "result": "results/retrieval_eval.json",
        "command": "python benchmark/evaluate_retrieval.py",
        "code": ["benchmark/evaluate_retrieval.py", "pwm/memory/retriever.py", "pwm/memory/semantic_retriever.py"],
        "inputs": [],
    },
    "database_resilience": {
        "result": "results/database_resilience.json",
        "command": "python benchmark/database_resilience.py",
        "code": ["benchmark/database_resilience.py", "pwm/engine.py", "pwm/memory/store.py", "pwm/events/store.py"],
        "inputs": [],
    },
    "privacy_inventory": {
        "result": "results/privacy_inventory.json",
        "command": "python benchmark/privacy_inventory_eval.py",
        "code": ["benchmark/privacy_inventory_eval.py", "pwm/engine.py", "pwm/integrity.py"],
        "inputs": [],
    },
}


def package_version(name: str) -> str | None:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def main() -> None:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    records = []
    for name, spec in EXPERIMENTS.items():
        if not (ROOT / spec["result"]).exists():
            continue
        code = existing(spec["code"])
        inputs = existing(spec["inputs"])
        records.append({
            "name": name,
            "command": spec["command"],
            "result": spec["result"],
            "result_sha256": sha256(spec["result"]),
            "code": [{"path": x, "sha256": sha256(x)} for x in code],
            "inputs": [{"path": x, "sha256": sha256(x)} for x in inputs],
        })
    payload = {
        "schema": "beliefweave.experiment-lineage.v1",
        "package_version": version,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": sys.platform,
            "numpy": package_version("numpy"),
            "scipy": package_version("scipy"),
            "scikit_learn": package_version("scikit-learn"),
            "joblib": package_version("joblib"),
        },
        "experiments": records,
    }
    (R / "experiment_lineage.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"experiments": len(records), "output": "results/experiment_lineage.json"}, indent=2))


if __name__ == "__main__":
    main()
