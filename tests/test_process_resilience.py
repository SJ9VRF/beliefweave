from pathlib import Path

from benchmark.database_resilience import crash_recovery_check, multiprocess_check


def test_process_crash_rolls_back_uncommitted_event_and_memory(tmp_path: Path):
    result = crash_recovery_check(tmp_path / "crash.db")
    assert result["pass"] is True
    assert result["events_after_recovery"] == 0
    assert result["memories_after_recovery"] == 0


def test_independent_process_writers_preserve_isolation(tmp_path: Path):
    result = multiprocess_check(tmp_path / "multi.db", workers=2, operations=5)
    assert result["pass"] is True
    assert result["observed_events"] == 10


def test_database_resilience_combined_run_writes_machine_readable_result(tmp_path: Path):
    from benchmark.database_resilience import run

    output = tmp_path / "resilience.json"
    result = run(output)
    assert result["pass"] is True
    assert output.exists()
    assert '"pass": true' in output.read_text()
