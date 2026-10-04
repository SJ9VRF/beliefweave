from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from pwm.memory.schema import MemoryRecord
from pwm.memory.store import MemoryStore
from pwm.temporal import parse_iso

TOKEN_RE = re.compile(r"[\w'-]+", re.UNICODE)


def tokens(text: str) -> set[str]:
    """Return normalized lexical tokens for transparent local retrieval."""
    return {token.lower() for token in TOKEN_RE.findall(text)}


@dataclass(slots=True)
class RetrievedMemory:
    memory: MemoryRecord
    score: float
    reasons: dict[str, float]


class MemoryRetriever:
    """Dependency-free retrieval baseline used by the core runtime.

    The scorer deliberately stays inspectable: lexical overlap, confidence,
    importance, recency, validity, and context match are all returned as score
    components. The optional ML extra can replace this with the TF-IDF hybrid
    retriever without changing the engine API.
    """

    def __init__(self, store: MemoryStore):
        self.store = store

    def retrieve(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        context: str | None = None,
        now: str | None = None,
    ) -> list[RetrievedMemory]:
        query_tokens = tokens(query)
        reference_time = parse_iso(now) if now else datetime.now(timezone.utc)
        scored: list[RetrievedMemory] = []

        for memory in self.store.list_active(user_id, now=now):
            memory_tokens = tokens(
                f"{memory.predicate} {memory.value} {memory.context_scope or ''}"
            )
            overlap = len(query_tokens & memory_tokens) / max(
                1, len(query_tokens | memory_tokens)
            )
            context_bonus = 0.0
            if context and memory.context_scope == context:
                context_bonus = 0.18
            elif memory.context_scope and tokens(memory.context_scope) & query_tokens:
                context_bonus = 0.12

            valid_from = parse_iso(memory.valid_from)
            age_days = 0.0
            if valid_from and reference_time:
                age_days = max(
                    0.0,
                    (reference_time - valid_from).total_seconds() / 86400.0,
                )
            recency = math.exp(-age_days / 180.0)
            current_validity = 1.0
            score = (
                0.38 * overlap
                + 0.18 * memory.confidence
                + 0.14 * memory.importance
                + 0.10 * recency
                + 0.10 * current_validity
                + context_bonus
            )
            scored.append(
                RetrievedMemory(
                    memory=memory,
                    score=score,
                    reasons={
                        "lexical_overlap": overlap,
                        "confidence": memory.confidence,
                        "importance": memory.importance,
                        "recency": recency,
                        "context_bonus": context_bonus,
                        "current_validity": current_validity,
                    },
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        top = scored[:limit]
        for retrieval in top:
            self.store.touch_retrieved(retrieval.memory.id)
        return top
