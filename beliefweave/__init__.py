"""Public BeliefWeave API.

The historical ``pwm`` package remains importable so frozen experiments and older
artifacts keep reproducing. New integrations should import from ``beliefweave``.
"""

from importlib.metadata import PackageNotFoundError, version as distribution_version
from pathlib import Path
import tomllib

from pwm.belief_governance import (
    AuthorityCosts,
    BeliefGateDecision,
    DecisionAwareBeliefGateV3,
    PersonalizationAction,
    PRODUCTION_GATE_VERSION,
    build_belief_gate,
)
from pwm.engine import (
    IdempotencyConflictError,
    IdempotencyTombstonedError,
    MemoryStateConflictError,
    PersonalMemoryEngine,
)
from pwm.temporal import TemporalValueError
from pwm.memory.schema import (
    ConflictType,
    Event,
    MemoryRecord,
    MemoryStatus,
    MemoryType,
    SourceType,
    WriteDecision,
)

__all__ = [
    "AuthorityCosts",
    "BeliefGateDecision",
    "ConflictType",
    "DecisionAwareBeliefGateV3",
    "Event",
    "IdempotencyConflictError",
    "IdempotencyTombstonedError",
    "MemoryRecord",
    "MemoryStateConflictError",
    "MemoryStatus",
    "MemoryType",
    "PersonalMemoryEngine",
    "PersonalizationAction",
    "PRODUCTION_GATE_VERSION",
    "SourceType",
    "TemporalValueError",
    "WriteDecision",
    "build_belief_gate",
]

def _runtime_version() -> str:
    """Resolve the source-tree or installed distribution version without duplication."""
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject.exists():
        return tomllib.loads(pyproject.read_text())["project"]["version"]
    try:
        return distribution_version("beliefweave")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = _runtime_version()
