#!/usr/bin/env python3
"""Verify the wheel works with no optional ML dependencies installed."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results" / "core_install.json"


def main() -> int:
    wheels = sorted((ROOT / "dist").glob("beliefweave-*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected exactly one wheel, found {len(wheels)}")
    wheel = wheels[0]

    with tempfile.TemporaryDirectory(prefix="beliefweave-core-") as tmp:
        env_dir = Path(tmp) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
        python = env_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        pip = [str(python), "-m", "pip"]
        subprocess.run(pip + ["install", "--no-deps", str(wheel)], check=True, capture_output=True, text=True)
        code = r'''
from pathlib import Path
from tempfile import TemporaryDirectory
from beliefweave import PersonalMemoryEngine
with TemporaryDirectory() as d:
    engine = PersonalMemoryEngine(Path(d) / "core.db")
    caps = engine.runtime_capabilities()
    assert caps["ml_enabled"] is False, caps
    out = engine.ingest("u", "I love sushi.", idempotency_key="one")
    assert out["event"].user_id == "u"
    assert engine.current_state("u")
    print(caps)
'''
        proc = subprocess.run([str(python), "-c", code], check=True, capture_output=True, text=True)

    payload = {
        "status": "PASS",
        "wheel": wheel.name,
        "installed_with_no_dependencies": True,
        "core_runtime_without_ml": True,
        "stdout": proc.stdout.strip(),
    }
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print("CORE INSTALL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
