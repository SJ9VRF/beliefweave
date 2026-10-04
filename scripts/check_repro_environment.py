from __future__ import annotations

import importlib.metadata as md
import json
import platform
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSTRAINTS = ROOT / "constraints" / "reproducible.txt"


def parse_constraints() -> dict[str, str]:
    out = {}
    for raw in CONSTRAINTS.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        out[name] = version
    return out


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="exit nonzero when the current environment differs from the reference constraints")
    args=ap.parse_args()
    expected = parse_constraints()
    packages = {}
    mismatches = []
    for name, wanted in expected.items():
        try:
            actual = md.version(name)
        except md.PackageNotFoundError:
            actual = None
        packages[name] = {"expected": wanted, "actual": actual, "match": actual == wanted}
        if actual != wanted:
            mismatches.append(name)
    payload = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "constraints_file": "constraints/reproducible.txt",
        "packages": packages,
        "match": not mismatches,
        "mismatches": mismatches,
        "scope": "reference validation environment; package supports a broader version range declared in pyproject.toml",
    }
    out = ROOT / "results" / "repro_environment.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.strict and not payload["match"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
