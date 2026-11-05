"""Setup-path invariants used by the acceptance suite (Ch III.5.12).

Pure assertions over payloads, records and evaluations.  Nothing here
mutates state, reads a clock, or touches the filesystem.
"""

from __future__ import annotations

from typing import Any, Iterator

from .contracts import (
    SEVERITY_ORDER,
    SetupEligibility,
    SetupRecord,
    SetupSurface,
)
from .eligibility import GATE_ORDER, SetupEvaluation
from .errors import SetupContractError
from .statistics import FORBIDDEN_FIELD_NAMES

__all__ = [
    "authority_separated",
    "contains_float",
    "forbidden_keys",
    "gate_order_complete",
    "precedence_is_total",
    "refusal_is_recorded",
    "walk_payload",
]


def walk_payload(value: Any) -> Iterator[tuple[str | None, Any]]:
    """Yield every (key, value) pair in a nested payload."""

    if isinstance(value, dict):
        for key, item in value.items():
            yield (str(key), item)
            yield from walk_payload(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_payload(item)
    else:
        yield (None, value)


def forbidden_keys(payload: Any) -> tuple[str, ...]:
    """Any payload key that would carry a performance or sizing figure."""

    found: list[str] = []
    for key, _value in walk_payload(payload):
        if key is not None and key.lower() in FORBIDDEN_FIELD_NAMES:
            found.append(key.lower())
    return tuple(sorted(set(found)))


def contains_float(payload: Any) -> bool:
    return any(
        isinstance(value, float) for _key, value in walk_payload(payload)
    )


def authority_separated(record: SetupRecord) -> bool:
    """Automation is never claimed without an approved card."""

    if record.automation_permitted and record.execution_class.value != "AUTOMATION_APPROVED":
        return False
    return record.manual_class.value == record.execution_class.value


def refusal_is_recorded(evaluation: SetupEvaluation) -> bool:
    """A non-positive verdict is a result with a bounded code, not an error."""

    if evaluation.eligibility is SetupEligibility.ELIGIBLE:
        return not evaluation.reasons
    return bool(evaluation.reasons)


def precedence_is_total() -> bool:
    """The four verdicts form a strict, total severity order."""

    ranks = [verdict.severity for verdict in SEVERITY_ORDER]
    return sorted(ranks, reverse=True) == ranks and len(set(ranks)) == len(ranks)


def gate_order_complete() -> bool:
    """The documented eleven-gate chain, in order."""

    return GATE_ORDER == (
        "REGISTRY",
        "STAND_DOWN",
        "MODEL_STATE",
        "ANCHOR",
        "TIER",
        "CLOCK",
        "HIGHER_LAYER",
        "DATA_QUALITY",
        "PARAMETERS",
        "TRIGGER",
        "INVALIDATION",
    )
