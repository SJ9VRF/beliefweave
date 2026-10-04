from pathlib import Path
import random

from pwm.engine import PersonalMemoryEngine
from pwm.simulation import LongitudinalUserGenerator


def test_generator_same_seed_is_identical():
    a = LongitudinalUserGenerator(seed=17).generate(n_users=4, n_turns=30)
    b = LongitudinalUserGenerator(seed=17).generate(n_users=4, n_turns=30)
    assert a == b


def test_generator_different_seed_changes_trajectory():
    a = LongitudinalUserGenerator(seed=17).generate(n_users=3, n_turns=20)
    b = LongitudinalUserGenerator(seed=18).generate(n_users=3, n_turns=20)
    assert a != b


def test_randomized_multiuser_operations_preserve_isolation(tmp_path: Path):
    engine = PersonalMemoryEngine(tmp_path / "invariants.db")
    rng = random.Random(20260923)
    users = ["alice", "bob", "carol"]
    foods = ["sushi", "ramen", "pasta", "tacos"]

    # Deterministic failure-injection workload: interleave writes, reversals,
    # recalls, soft deletes, and hard forgets across independent users.
    for step in range(60):
        user = rng.choice(users)
        food = rng.choice(foods)
        if step % 11 == 0:
            engine.ingest(user, f"Actually, I dislike {food}.", context="food")
        else:
            engine.ingest(user, f"I love {food}.", context="food")

        if step % 7 == 0:
            engine.recall(user, "What food do I like?", context="food")

        active = engine.memories.list_active(user)
        if active and step % 13 == 0:
            engine.forget_memory(active[0].id, delete_source_events=(step % 26 == 0))

    # Cross-user lookup by list API must never surface another user's records.
    ids_by_user = {u: {m.id for m in engine.memories.list_all(u)} for u in users}
    for user in users:
        # Every row returned for one user must belong to that user, even after
        # destructive operations and interleaving.
        assert all(m.user_id == user for m in engine.memories.list_all(user))
        state = engine.current_state(user)
        state_memory_ids = {belief.memory_id for beliefs in state.values() for belief in beliefs}
        assert state_memory_ids.issubset(ids_by_user[user])

    assert ids_by_user["alice"].isdisjoint(ids_by_user["bob"])
    assert ids_by_user["alice"].isdisjoint(ids_by_user["carol"])
    assert ids_by_user["bob"].isdisjoint(ids_by_user["carol"])
