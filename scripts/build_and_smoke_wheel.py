from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DIST.mkdir(exist_ok=True)
for old in DIST.glob("*.whl"):
    old.unlink()

version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
subprocess.run(
    [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        ".",
        "--no-deps",
        "--no-build-isolation",
        "-w",
        str(DIST),
    ],
    cwd=ROOT,
    check=True,
)
wheels = sorted(DIST.glob("beliefweave-*.whl"))
if len(wheels) != 1:
    raise SystemExit(f"expected one wheel, found {wheels}")
wheel = wheels[0]

with zipfile.ZipFile(wheel) as zf:
    names = set(zf.namelist())
asset_router = any(name.endswith("pwm/assets/observation_router.joblib") for name in names)
asset_conflict = any(name.endswith("pwm/assets/conflict_model.joblib") for name in names)
public_api = any(name.endswith("beliefweave/__init__.py") for name in names)
py_typed = any(name.endswith("beliefweave/py.typed") for name in names)

with tempfile.TemporaryDirectory(prefix="beliefweave-wheel-smoke-") as td:
    target = Path(td) / "site"
    target.mkdir()
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            str(target),
            str(wheel),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    smoke = f'''
from pathlib import Path
from tempfile import TemporaryDirectory
import beliefweave
from beliefweave import PersonalMemoryEngine
assert beliefweave.__version__ == {version!r}, beliefweave.__version__
with TemporaryDirectory() as d:
    engine = PersonalMemoryEngine(Path(d) / "x.db", enable_ml=False)
    assert engine.runtime_capabilities()["ml_enabled"] is False
    out = engine.ingest("u", "I love sushi.", context="food")
    assert out["event"].user_id == "u"
print("ok")
'''
    env = os.environ.copy()
    env["PYTHONPATH"] = str(target)
    proc = subprocess.run(
        [sys.executable, "-c", smoke],
        cwd="/tmp",
        env=env,
        capture_output=True,
        text=True,
    )
    installed_ok = proc.returncode == 0

result = {
    "passed": bool(
        asset_router
        and asset_conflict
        and public_api
        and py_typed
        and installed_ok
    ),
    "wheel": wheel.name,
    "wheel_size_bytes": wheel.stat().st_size,
    "contains_observation_router": asset_router,
    "contains_conflict_model": asset_conflict,
    "contains_public_api": public_api,
    "contains_py_typed": py_typed,
    "core_target_install_smoke": installed_ok,
    "stdout": proc.stdout.strip(),
    "stderr": proc.stderr.strip(),
}
(ROOT / "results" / "package_smoke.json").write_text(
    json.dumps(result, indent=2, sort_keys=True) + "\n"
)
print(json.dumps(result, indent=2, sort_keys=True))
if not result["passed"]:
    raise SystemExit(1)
