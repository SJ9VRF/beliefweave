import json
from pathlib import Path

from pwm.cli import main, _benchmark_payload, _demo_payload, _doctor_payload


def test_demo_payload_end_to_end():
    p = _demo_payload()
    assert p["scenario"].startswith("preference reversal")
    assert p["hard_forget_ok"] is True
    assert p["memory_count_after_forget"] < p["memory_count_before_forget"]


def test_installed_package_sanity_benchmark_logic():
    p = _benchmark_payload()
    assert p["cases"] == 4
    assert p["pass_rate"] == 1.0


def test_doctor_reports_assets_and_schema(tmp_path: Path):
    p = _doctor_payload(str(tmp_path / "doctor.db"))
    assert p["ok"] is True
    assert p["checks"]["database"]["memory_columns"] >= 20
    assert p["checks"]["core_runtime"]["ok"] is True
    assert p["checks"]["learned_assets"]["required"] is False


def test_cli_ingest_and_state(tmp_path: Path, capsys):
    db = str(tmp_path / "cli.db")
    assert main(["--db", db, "--user", "u", "ingest", "I love sushi."]) == 0
    ingest = json.loads(capsys.readouterr().out)
    assert ingest["actions"]
    assert main(["--db", db, "--user", "u", "state"]) == 0
    state = json.loads(capsys.readouterr().out)
    assert state


def test_cli_recall_memories_correct_forget(tmp_path: Path, capsys):
    db = str(tmp_path / "crud.db")
    assert main(["--db", db, "--user", "u", "ingest", "I love sushi."]) == 0
    ingest = json.loads(capsys.readouterr().out)
    mid = ingest["actions"][0]["memory"]["id"]

    assert main(["--db", db, "--user", "u", "recall", "dinner food"]) == 0
    recall = json.loads(capsys.readouterr().out)
    assert recall

    assert main(["--db", db, "--user", "u", "memories"]) == 0
    memories = json.loads(capsys.readouterr().out)
    assert memories[0]["id"] == mid

    assert main(["--db", db, "correct", mid, "ramen"]) == 0
    corrected = json.loads(capsys.readouterr().out)
    assert corrected["ok"] is True
    corrected_id = corrected["memory"]["id"]
    assert corrected["memory"]["supersedes"] == mid

    assert main(["--db", db, "forget", corrected_id]) == 0
    forgotten = json.loads(capsys.readouterr().out)
    assert forgotten == {"hard": False, "memory_id": corrected_id, "ok": True}


def test_cli_missing_memory_returns_failure(tmp_path: Path, capsys):
    db = str(tmp_path / "missing.db")
    assert main(["--db", db, "correct", "mem_missing", "x"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert main(["--db", db, "forget", "mem_missing", "--hard"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False


def test_cli_doctor_benchmark_demo_commands(tmp_path: Path, capsys):
    db = str(tmp_path / "doctor.db")
    assert main(["--db", db, "doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert main(["benchmark"]) == 0
    assert json.loads(capsys.readouterr().out)["pass_rate"] == 1.0
    assert main(["demo"]) == 0
    assert json.loads(capsys.readouterr().out)["hard_forget_ok"] is True
