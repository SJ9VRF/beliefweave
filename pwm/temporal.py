from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone


class TemporalValueError(ValueError):
    """Raised when an externally supplied temporal value is not valid ISO-8601."""


def parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp into an aware UTC datetime.

    `None`/empty values return `None`. Invalid strings also return `None` for
    legacy internal call sites that intentionally probe optional metadata.
    Naive datetimes are interpreted as UTC so arithmetic never mixes naive and
    aware values.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_iso(value: str, *, field_name: str = "timestamp") -> str:
    """Validate and canonicalize an external timestamp to UTC ISO-8601.

    Naive timestamps are treated as UTC for backwards compatibility. Invalid
    values fail fast instead of being stored and corrupting temporal ordering.
    """
    parsed = parse_iso(value)
    if parsed is None:
        raise TemporalValueError(
            f"{field_name} must be a valid ISO-8601 timestamp; got {value!r}"
        )
    return parsed.isoformat()


def infer_valid_until(text: str, start_iso: str) -> str | None:
    start = parse_iso(start_iso) or datetime.now(timezone.utc)
    lowered = text.lower()
    if "today" in lowered:
        return (start + timedelta(days=1)).isoformat()
    if "this week" in lowered:
        return (start + timedelta(days=7)).isoformat()
    if "this month" in lowered:
        return (start + timedelta(days=30)).isoformat()

    match = re.search(r"for\s+(\d+)\s+days?", lowered)
    if match:
        return (start + timedelta(days=int(match.group(1)))).isoformat()
    match = re.search(r"for\s+(\d+)\s+weeks?", lowered)
    if match:
        return (start + timedelta(weeks=int(match.group(1)))).isoformat()
    return None


def is_expired(valid_until: str | None, now: str | None = None) -> bool:
    end = parse_iso(valid_until)
    if end is None:
        return False
    reference = parse_iso(now) if now else datetime.now(timezone.utc)
    return bool(reference and end <= reference)
