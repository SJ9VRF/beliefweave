from pwm.engine import PersonalMemoryEngine
from pwm.memory.schema import MemoryType, WriteDecision


def test_preference_is_written(tmp_path):
    engine = PersonalMemoryEngine(tmp_path / "test.db")
    result = engine.ingest("u1", "I love sushi.", context="food")
    assert len(result["actions"]) == 1
    assert result["actions"][0]["policy"].decision == WriteDecision.WRITE
    memories = engine.memories.list_active("u1")
    assert len(memories) == 1
    assert memories[0].memory_type == MemoryType.PREFERENCE
    assert memories[0].value.lower() == "sushi"


def test_temporary_constraint_is_temporary(tmp_path):
    engine = PersonalMemoryEngine(tmp_path / "test.db")
    result = engine.ingest("u1", "I'm avoiding raw fish this month.", context="food")
    assert result["actions"][0]["policy"].decision == WriteDecision.STORE_TEMPORARILY
    memories = engine.memories.list_active("u1")
    assert memories[0].memory_type == MemoryType.TEMPORARY_STATE


def test_retrieval_prioritizes_relevant_memory(tmp_path):
    engine = PersonalMemoryEngine(tmp_path / "test.db")
    engine.ingest("u1", "I love sushi.", context="food")
    engine.ingest("u1", "I prefer concise technical explanations.", context="communication")
    results = engine.recall("u1", "sushi food dinner", limit=1)
    assert len(results) == 1
    assert "sushi" in results[0].memory.value.lower()
