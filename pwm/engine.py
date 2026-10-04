from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from pathlib import Path
from typing import Any, Callable

from pwm.belief_governance import PRODUCTION_GATE_VERSION, build_belief_gate
from pwm.events.store import EventStore
from pwm.memory.policy import HeuristicWritePolicy
from pwm.memory.schema import (
    ConflictType,
    Event,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    SourceType,
    WriteDecision,
    utcnow_iso,
)
from pwm.memory.retriever import MemoryRetriever
from pwm.memory.store import MemoryStore
from pwm.observations.extractor import RuleBasedObservationExtractor
from pwm.world_model import ConflictResolver, UserStateMaterializer
from pwm.temporal import normalize_iso


class MemoryStateConflictError(RuntimeError):
    """A memory mutation targets a stale or otherwise non-active version."""


class IdempotencyConflictError(ValueError):
    """An idempotency key was reused with a different request payload."""


class IdempotencyTombstonedError(RuntimeError):
    """A retry references an ingest that was explicitly hard-forgotten."""


class PersonalMemoryEngine:
    """Reference runtime for temporal memory and governed recall.

    The implementation favors explicit state transitions and inspectable failure
    modes over hidden end-to-end behavior. SQLite is the reference persistence
    layer for reproducibility; it is not presented as a production-scale store.
    """

    def __init__(
        self,
        db_path: str | Path = "pwm.db",
        *,
        gate_version: str = PRODUCTION_GATE_VERSION,
        enable_ml: bool = False,
        observer: Callable[[dict[str, Any]], None] | None = None,
        observer_hmac_key: bytes | str | None = None,
    ) -> None:
        self.events = EventStore(db_path)
        self.memories = MemoryStore(db_path)
        self._observer = observer
        if isinstance(observer_hmac_key, str):
            observer_hmac_key = observer_hmac_key.encode("utf-8")
        self._observer_hmac_key = observer_hmac_key or secrets.token_bytes(32)
        self.ml_enabled = False

        asset_root = Path(__file__).resolve().parent / "assets"
        router_model = asset_root / "observation_router.joblib"
        conflict_model = asset_root / "conflict_model.joblib"

        self.extractor = RuleBasedObservationExtractor()
        self.policy = HeuristicWritePolicy()
        self.retriever = MemoryRetriever(self.memories)
        self.conflicts = ConflictResolver()

        if enable_ml:
            try:
                from pwm.memory.semantic_retriever import SemanticMemoryRetriever
                from pwm.observations.hybrid import HybridObservationExtractor
                from pwm.world_model.hybrid_conflict import HybridConflictResolver
            except ModuleNotFoundError as exc:
                if exc.name not in {"joblib", "sklearn"} and not (
                    exc.name and exc.name.startswith("sklearn.")
                ):
                    raise
            else:
                if router_model.exists():
                    self.extractor = HybridObservationExtractor(router_model)
                self.retriever = SemanticMemoryRetriever(self.memories)
                if conflict_model.exists():
                    self.conflicts = HybridConflictResolver(conflict_model)
                self.ml_enabled = True

        self.state = UserStateMaterializer(self.memories)
        self.belief_gate_version = gate_version
        self.belief_gate = build_belief_gate(gate_version)


    def _emit(self, event: str, **fields: Any) -> None:
        """Emit privacy-safe operational metadata to an optional observer.

        The engine never includes raw interaction text or memory values in these
        events. Applications can attach tracing/metrics without coupling the
        reference runtime to a logging backend. Observer failures are isolated
        from memory semantics.
        """
        if self._observer is None:
            return
        user_id = fields.pop("user_id", None)
        if user_id is not None:
            fields["user_key"] = hmac.new(
                self._observer_hmac_key,
                str(user_id).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()[:16]
        payload = {
            "event": event,
            "gate_version": self.belief_gate_version,
            "ml_enabled": self.ml_enabled,
            **fields,
        }
        try:
            self._observer(payload)
        except Exception:
            # Observability must never change memory correctness.
            return

    def runtime_capabilities(self) -> dict[str, Any]:
        """Describe active runtime components without exposing user data."""
        return {
            "gate_version": self.belief_gate_version,
            "ml_enabled": self.ml_enabled,
            "retriever": type(self.retriever).__name__,
            "extractor": type(self.extractor).__name__,
            "conflict_resolver": type(self.conflicts).__name__,
        }

    @staticmethod
    def _request_hash(
        *,
        user_id: str,
        text: str,
        context: str | None,
        conversation_id: str | None,
        timestamp: str | None,
    ) -> str:
        payload = {
            "user_id": user_id,
            "text": text,
            "context": context,
            "conversation_id": conversation_id,
            "timestamp": timestamp,
        }
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _idempotency_key_digest(idempotency_key: str) -> str:
        """Return the persisted digest for an idempotency key.

        Raw idempotency keys are never stored in the database.
        """
        return hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()

    def _plan_memories(self, event: Event) -> list[tuple[Any, Any, MemoryRecord | None]]:
        planned: list[tuple[Any, Any, MemoryRecord | None]] = []
        for observation in self.extractor.extract(event):
            decision = self.policy.decide(observation)
            memory = None
            if decision.decision in {
                WriteDecision.WRITE,
                WriteDecision.STORE_TEMPORARILY,
            }:
                temporary = decision.decision == WriteDecision.STORE_TEMPORARILY
                memory_type = (
                    MemoryType.TEMPORARY_STATE
                    if temporary
                    else observation.memory_type
                )
                memory = MemoryRecord(
                    user_id=event.user_id,
                    subject=observation.subject,
                    predicate=observation.attribute,
                    value=observation.value,
                    memory_type=memory_type,
                    source_type=observation.source_type,
                    confidence=observation.confidence,
                    source_event_ids=[observation.source_event_id],
                    valid_from=observation.valid_from,
                    valid_until=observation.valid_until,
                    context_scope=observation.context_scope,
                    stability=0.35 if temporary else 0.75,
                    importance=min(1.0, decision.score),
                    user_verified=observation.correction,
                    correction_count=1 if observation.correction else 0,
                )
            planned.append((observation, decision, memory))
        return planned

    def ingest(
        self,
        user_id: str,
        text: str,
        *,
        context: str | None = None,
        conversation_id: str | None = None,
        timestamp: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Atomically ingest one event and every derived memory-state update.

        Repeating an idempotency key with the same payload returns the original
        event without new writes. Reusing a key with a different payload fails.
        A hard-forgotten idempotent request is tombstoned so an old retry cannot
        silently recreate deleted data.
        """
        if timestamp is not None:
            timestamp = normalize_iso(timestamp, field_name="timestamp")

        request_hash = self._request_hash(
            user_id=user_id,
            text=text,
            context=context,
            conversation_id=conversation_id,
            timestamp=timestamp,
        )

        event_kwargs: dict[str, Any] = {
            "user_id": user_id,
            "raw_text": text,
            "context": context,
            "conversation_id": conversation_id,
        }
        if timestamp is not None:
            event_kwargs["timestamp"] = timestamp
        event = Event(**event_kwargs)
        planned = self._plan_memories(event)

        actions: list[dict[str, Any]] = []
        replay_event: Event | None = None
        idempotency_digest = (
            self._idempotency_key_digest(idempotency_key)
            if idempotency_key is not None
            else None
        )

        with self.memories.transaction(immediate=True) as conn:
            if idempotency_digest is not None:
                receipt = conn.execute(
                    """
                    SELECT request_hash, event_id, tombstoned
                    FROM ingest_receipts
                    WHERE user_id=? AND idempotency_key=?
                    """,
                    (user_id, idempotency_digest),
                ).fetchone()
                if receipt is not None:
                    if receipt["tombstoned"]:
                        raise IdempotencyTombstonedError(
                            "idempotent request was hard-forgotten and cannot be replayed"
                        )
                    if receipt["request_hash"] != request_hash:
                        raise IdempotencyConflictError(
                            "idempotency key reused with a different request payload"
                        )
                    replay_event = self.events.get(receipt["event_id"])
                    if replay_event is None:
                        raise RuntimeError(
                            "idempotency receipt references a missing event"
                        )
                else:
                    self.events.add(event, conn=conn)
                    conn.execute(
                        """
                        INSERT INTO ingest_receipts
                        (user_id, idempotency_key, request_hash, event_id)
                        VALUES (?, ?, ?, ?)
                        """,
                        (user_id, idempotency_digest, request_hash, event.id),
                    )
            else:
                self.events.add(event, conn=conn)

            if replay_event is None:
                for observation, decision, memory in planned:
                    conflict_events: list[tuple[str, str]] = []
                    if memory is not None:
                        active = list(
                            self.memories.list_active(
                                user_id,
                                now=event.timestamp,
                                conn=conn,
                            )
                        )
                        self.memories.add(memory, conn=conn)

                        for old in active:
                            conflict_type = self.conflicts.classify(old, observation)
                            if conflict_type == ConflictType.NONE:
                                continue
                            conflict_events.append((old.id, conflict_type.value))

                            superseding = conflict_type in {
                                ConflictType.PREFERENCE_DRIFT,
                                ConflictType.GOAL_CHANGE,
                                ConflictType.TEMPORAL_UPDATE,
                            }
                            correction_override = (
                                observation.correction
                                and conflict_type != ConflictType.CONTEXT_DEPENDENT
                            )
                            if superseding or correction_override:
                                self.memories.supersede(
                                    old.id,
                                    memory.id,
                                    conn=conn,
                                )
                            elif conflict_type in {
                                ConflictType.APPARENT_CONFLICT,
                                ConflictType.SOURCE_DISAGREEMENT,
                            }:
                                self.memories.add_conflict(
                                    old.id,
                                    memory.id,
                                    conn=conn,
                                )

                    actions.append(
                        {
                            "observation": observation,
                            "policy": decision,
                            "memory": memory,
                            "conflicts": conflict_events,
                        }
                    )

        if replay_event is not None:
            self._emit(
                "ingest_replay",
                user_id=user_id,
                event_id=replay_event.id,
                action_count=0,
            )
            return {
                "event": replay_event,
                "actions": [],
                "state": self.current_state(
                    user_id,
                    now=replay_event.timestamp,
                ),
                "idempotent_replay": True,
            }
        self._emit(
            "ingest_committed",
            user_id=user_id,
            event_id=event.id,
            action_count=len(actions),
            memory_write_count=sum(1 for action in actions if action["memory"] is not None),
        )
        return {
            "event": event,
            "actions": actions,
            "state": self.current_state(user_id, now=event.timestamp),
            "idempotent_replay": False,
        }

    def recall(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        context: str | None = None,
        now: str | None = None,
    ):
        if now is not None:
            now = normalize_iso(now, field_name="now")
        results = self.retriever.retrieve(user_id, query, limit, context, now)
        self._emit(
            "recall_completed",
            user_id=user_id,
            result_count=len(results),
            limit=limit,
        )
        return results

    def current_state(self, user_id: str, now: str | None = None):
        if now is not None:
            now = normalize_iso(now, field_name="now")
        return self.state.current(user_id, now=now)

    def governed_recall(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        context: str | None = None,
        now: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve evidence, then decide whether each memory may affect behavior."""
        if now is not None:
            now = normalize_iso(now, field_name="now")
        governed: list[dict[str, Any]] = []
        for retrieval in self.recall(user_id, query, limit, context, now):
            unresolved_conflict = bool(retrieval.memory.conflicts_with)
            gate = self.belief_gate.decide(
                retrieval.memory,
                context=context,
                now=now,
                unresolved_conflict=unresolved_conflict,
            )
            governed.append(
                {
                    "retrieval": retrieval,
                    "gate": gate,
                    "gate_version": self.belief_gate_version,
                }
            )
        self._emit(
            "governed_recall_completed",
            user_id=user_id,
            result_count=len(governed),
            use_count=sum(1 for item in governed if item["gate"].action.value == "USE"),
            ask_count=sum(1 for item in governed if item["gate"].action.value == "ASK"),
            abstain_count=sum(1 for item in governed if item["gate"].action.value == "ABSTAIN"),
        )
        return governed

    def correct_memory(
        self,
        memory_id: str,
        new_value: str,
        *,
        timestamp: str | None = None,
    ) -> MemoryRecord | None:
        """Create a provenance-preserving user correction.

        Corrections are append-only at the semantic layer: a new user-verified
        memory and source event are created, while the previous memory is marked
        SUPERSEDED. Repeating the same correction against the original version
        returns the existing corrected memory instead of duplicating history.
        """
        value = new_value.strip()
        if not value:
            raise ValueError("corrected memory value must not be empty")
        if timestamp is not None:
            timestamp = normalize_iso(timestamp, field_name="timestamp")

        with self.memories.transaction(immediate=True) as conn:
            old = self.memories.get(memory_id, conn=conn)
            if old is None:
                return None

            existing_rows = conn.execute(
                """
                SELECT id FROM memories
                WHERE supersedes=? AND user_verified=1
                ORDER BY created_at DESC
                """,
                (memory_id,),
            ).fetchall()
            for row in existing_rows:
                existing = self.memories.get(row["id"], conn=conn)
                if existing is not None and existing.value == value:
                    return existing

            if old.status != MemoryStatus.ACTIVE:
                raise MemoryStateConflictError(
                    "correction target is not active; correct the latest memory version"
                )

            event_kwargs: dict[str, Any] = {
                "user_id": old.user_id,
                "raw_text": value,
                "context": old.context_scope,
                "metadata": {
                    "kind": "memory_correction",
                    "target_memory_id": old.id,
                },
            }
            if timestamp is not None:
                event_kwargs["timestamp"] = timestamp
            event = Event(**event_kwargs)
            self.events.add(event, conn=conn)

            corrected = MemoryRecord(
                user_id=old.user_id,
                subject=old.subject,
                predicate=old.predicate,
                value=value,
                memory_type=old.memory_type,
                source_type=SourceType.EXPLICIT,
                confidence=1.0,
                source_event_ids=[event.id],
                valid_from=event.timestamp,
                valid_until=old.valid_until,
                stability=max(old.stability, 0.9),
                importance=old.importance,
                context_scope=old.context_scope,
                user_verified=True,
                privacy_level=old.privacy_level,
                correction_count=old.correction_count + 1,
                supersedes=old.id,
            )
            self.memories.add(corrected, conn=conn)
            self.memories.supersede(old.id, corrected.id, conn=conn)

        self._emit(
            "memory_corrected",
            user_id=corrected.user_id,
            memory_id=corrected.id,
            superseded_memory_id=old.id,
        )
        return corrected

    def forget_memory(
        self,
        memory_id: str,
        *,
        delete_source_events: bool = False,
    ) -> bool:
        """Forget one memory, optionally purging its source events atomically."""
        memory = self.memories.get(memory_id)
        if memory is None:
            return False
        if not delete_source_events:
            self.memories.delete(memory_id)
            self._emit("memory_soft_deleted", memory_id=memory_id)
            return True

        conn = sqlite3.connect(self.memories.db_path, timeout=30.0)
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("BEGIN IMMEDIATE")
            rows = conn.execute(
                """
                SELECT id, source_event_ids_json, conflicts_with_json, supersedes
                FROM memories
                """
            ).fetchall()

            target_sources = set(memory.source_event_ids)
            purge_ids = {memory_id}
            remaining_sources: dict[str, list[str]] = {}

            for row in rows:
                current_id = row["id"]
                source_ids = list(json.loads(row["source_event_ids_json"]))
                if current_id == memory_id:
                    continue
                remaining = [
                    event_id
                    for event_id in source_ids
                    if event_id not in target_sources
                ]
                if len(remaining) != len(source_ids):
                    if remaining:
                        remaining_sources[current_id] = remaining
                    else:
                        purge_ids.add(current_id)

            for current_id, remaining in remaining_sources.items():
                if current_id not in purge_ids:
                    conn.execute(
                        """
                        UPDATE memories
                        SET source_event_ids_json=?, updated_at=?
                        WHERE id=?
                        """,
                        (json.dumps(remaining), utcnow_iso(), current_id),
                    )

            for row in rows:
                current_id = row["id"]
                if current_id in purge_ids:
                    continue
                conflicts = [
                    other_id
                    for other_id in json.loads(row["conflicts_with_json"])
                    if other_id not in purge_ids and other_id != current_id
                ]
                supersedes = row["supersedes"]
                if supersedes in purge_ids:
                    supersedes = None
                conn.execute(
                    """
                    UPDATE memories
                    SET conflicts_with_json=?, supersedes=?
                    WHERE id=?
                    """,
                    (json.dumps(conflicts), supersedes, current_id),
                )

            if purge_ids:
                placeholders = ",".join("?" for _ in purge_ids)
                conn.execute(
                    f"DELETE FROM memories WHERE id IN ({placeholders})",
                    tuple(sorted(purge_ids)),
                )

            for event_id in target_sources:
                conn.execute(
                    """
                    UPDATE ingest_receipts
                    SET tombstoned=1, request_hash='', event_id=''
                    WHERE event_id=?
                    """,
                    (event_id,),
                )
                conn.execute("DELETE FROM events WHERE id=?", (event_id,))

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        self._emit(
            "memory_hard_deleted",
            memory_id=memory_id,
            purged_memory_count=len(purge_ids),
            purged_event_count=len(target_sources),
        )
        return True

    def export_user_data(self, user_id: str) -> dict[str, Any]:
        """Return an inspectable inventory of all persisted data for one user.

        Idempotency receipts are control metadata rather than conversational
        content, but they are still persisted user-scoped data and therefore
        belong in a complete export. Raw idempotency keys are never stored, so
        only their digests can be exported.
        """
        with self.memories.transaction(immediate=False) as conn:
            receipt_rows = conn.execute(
                """
                SELECT idempotency_key, request_hash, event_id, tombstoned
                FROM ingest_receipts
                WHERE user_id=?
                ORDER BY idempotency_key
                """,
                (user_id,),
            ).fetchall()

        return {
            "user_id": user_id,
            "gate_version": self.belief_gate_version,
            "events": [
                event.to_dict()
                for event in self.events.list_for_user(user_id, limit=None)
            ],
            "memories": [
                memory.to_dict()
                for memory in self.memories.list_all(user_id)
            ],
            "control_metadata": {
                "ingest_receipts": [
                    {
                        "idempotency_key_digest": row["idempotency_key"],
                        "request_hash": row["request_hash"],
                        "event_id": row["event_id"],
                        "tombstoned": bool(row["tombstoned"]),
                    }
                    for row in receipt_rows
                ]
            },
            "state": self.current_state(user_id),
        }

    def purge_user_data(
        self,
        user_id: str,
        *,
        retain_replay_guard: bool = False,
    ) -> dict[str, Any]:
        """Atomically purge all persisted state for a user.

        ``retain_replay_guard=False`` removes events, memories, and idempotency
        receipts, leaving no BeliefWeave rows for the user. In that strongest
        erasure mode, an old client retry can no longer be recognized because no
        replay marker remains. ``retain_replay_guard=True`` keeps only scrubbed
        receipt tombstones (hashed keys; no event/request hashes), preventing
        replay resurrection while deliberately retaining minimal control metadata.
        """
        with self.memories.transaction(immediate=True) as conn:
            memory_count = conn.execute(
                "SELECT COUNT(*) FROM memories WHERE user_id=?", (user_id,)
            ).fetchone()[0]
            event_count = conn.execute(
                "SELECT COUNT(*) FROM events WHERE user_id=?", (user_id,)
            ).fetchone()[0]
            receipt_count = conn.execute(
                "SELECT COUNT(*) FROM ingest_receipts WHERE user_id=?", (user_id,)
            ).fetchone()[0]

            conn.execute("DELETE FROM memories WHERE user_id=?", (user_id,))
            conn.execute("DELETE FROM events WHERE user_id=?", (user_id,))
            if retain_replay_guard:
                conn.execute(
                    """
                    UPDATE ingest_receipts
                    SET tombstoned=1, request_hash='', event_id=''
                    WHERE user_id=?
                    """,
                    (user_id,),
                )
            else:
                conn.execute(
                    "DELETE FROM ingest_receipts WHERE user_id=?", (user_id,)
                )

        retained_receipts = receipt_count if retain_replay_guard else 0
        self._emit(
            "user_data_purged",
            user_id=user_id,
            purged_memory_count=memory_count,
            purged_event_count=event_count,
            purged_receipt_count=receipt_count - retained_receipts,
            retained_replay_guard_count=retained_receipts,
        )
        return {
            "user_id": user_id,
            "purged_memories": memory_count,
            "purged_events": event_count,
            "purged_receipts": receipt_count - retained_receipts,
            "retained_replay_guards": retained_receipts,
            "complete_erasure": not retain_replay_guard,
        }
