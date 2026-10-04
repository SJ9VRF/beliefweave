from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryType(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    GOAL = "goal"
    CONSTRAINT = "constraint"
    ROUTINE = "routine"
    RELATIONSHIP = "relationship"
    COMMITMENT = "commitment"
    PAST_EVENT = "past_event"
    STYLE = "style"
    TEMPORARY_STATE = "temporary_state"
    INFERRED_HYPOTHESIS = "inferred_hypothesis"


class SourceType(str, Enum):
    EXPLICIT = "explicit"
    IMPLICIT = "implicit"
    INFERRED = "inferred"
    OBSERVED = "observed"
    SYNTHETIC = "synthetic"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    DELETED = "deleted"
    ARCHIVED = "archived"


class WriteDecision(str, Enum):
    WRITE = "write"
    STORE_TEMPORARILY = "store_temporarily"
    ASK_USER = "ask_user"
    IGNORE = "ignore"


class ConflictType(str, Enum):
    NONE = "none"
    DIRECT_CONTRADICTION = "direct_contradiction"
    TEMPORAL_UPDATE = "temporal_update"
    CONTEXT_DEPENDENT = "context_dependent"
    GOAL_CHANGE = "goal_change"
    PREFERENCE_DRIFT = "preference_drift"
    SOURCE_DISAGREEMENT = "source_disagreement"
    APPARENT_CONFLICT = "apparent_conflict"


@dataclass(slots=True)
class Event:
    user_id: str
    raw_text: str
    timestamp: str = field(default_factory=utcnow_iso)
    conversation_id: str | None = None
    modality: str = "text"
    context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Observation:
    subject: str
    attribute: str
    value: str
    memory_type: MemoryType
    source_type: SourceType
    confidence: float
    source_event_id: str
    context_scope: str | None = None
    temporality: str = "unspecified"
    valid_from: str | None = None
    valid_until: str | None = None
    raw_evidence: str | None = None
    correction: bool = False
    id: str = field(default_factory=lambda: f"obs_{uuid.uuid4().hex[:12]}")


@dataclass(slots=True)
class MemoryRecord:
    user_id: str
    subject: str
    predicate: str
    value: str
    memory_type: MemoryType
    source_type: SourceType
    confidence: float
    source_event_ids: list[str]
    created_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)
    valid_from: str | None = None
    valid_until: str | None = None
    stability: float = 0.5
    importance: float = 0.5
    context_scope: str | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    supersedes: str | None = None
    conflicts_with: list[str] = field(default_factory=list)
    retrieval_count: int = 0
    last_used_at: str | None = None
    user_verified: bool = False
    privacy_level: str = "normal"
    correction_count: int = 0
    id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["memory_type"] = self.memory_type.value
        data["source_type"] = self.source_type.value
        data["status"] = self.status.value
        return data


@dataclass(slots=True)
class StateBelief:
    key: str
    value: str
    confidence: float
    memory_id: str
    valid_from: str | None
    valid_until: str | None
    context_scope: str | None
    provenance: list[str]
