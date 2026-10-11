"""Structured event records (Book II / Bloc II.6, Ch II.6.2 / II.6.3).

Frozen field set (PLAN §3): schema_version, seq, timestamp, environment,
stream, severity, request_id, job_id, actor_class, actor_id, component,
operation, object_type, object_id, capability, outcome, reason_code,
duration_ms, provider_type, provider_name, model_id, error_class,
provider_failure_class, attributes.

Laws:

- Structured, not free-form: attributes are bounded scalars only (refused
  otherwise) and every string field is bounded at construction.
- Redaction is applied at construction (see redaction.py), before any sink.
- Deterministic: `to_dict()` is sorted-key; identical inputs produce
  identical serialized output.
- Observability only DESCRIBES: this record carries no authority — it can
  never grant, mutate or promote anything.

Import law: no FastAPI, no providers, no persistence here. Pure records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from app.forge.observability.redaction import safe_attributes, scrub_text

EVENT_SCHEMA_VERSION = "FORGE_EVENT_V1"

# Frozen vocabularies (test-enforced; unknown values are refused).
SEVERITIES: tuple[str, ...] = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
OUTCOMES: tuple[str, ...] = ("success", "failure", "denied", "degraded")
STREAMS: tuple[str, ...] = (
    "telemetry",        # operational: what a component did
    "security_audit",   # which authorization decision occurred
    "usage_ledger",     # cost/usage accounting (Ch II.6.9)
    "entitlement_audit",  # commercial audit vocabulary (Ch II.6.6)
)
# Ch II.6.3 high-value boundaries (+ observability itself).
COMPONENTS: tuple[str, ...] = (
    "api",
    "identity",
    "policy",
    "persistence",
    "retrieval",
    "provider",
    "jobs",
    "observability",
)

MAX_FIELD_LENGTH = 128


def _bounded(name: str, value: str | None, *, required: bool = False) -> str:
    if value is None or value == "":
        if required:
            raise ValueError(f"event field {name!r} is required")
        return ""
    if not isinstance(value, str):
        raise ValueError(f"event field {name!r} must be a string")
    if len(value) > MAX_FIELD_LENGTH:
        raise ValueError(
            f"event field {name!r} exceeds {MAX_FIELD_LENGTH} characters"
        )
    return value


def _vocabulary(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if value not in allowed:
        raise ValueError(
            f"event field {name!r} must be one of {allowed}, got {value!r}"
        )
    return value


@dataclass(frozen=True)
class ForgeEvent:
    """One bounded, structured, redacted FORGE observability event."""

    # Identity / ordering
    seq: int = 0
    timestamp: str = ""  # caller/lifecycle-supplied ISO-8601 (clock-free core)
    environment: str = ""
    stream: str = "telemetry"
    severity: str = "INFO"
    # Correlation (Ch II.6.1)
    request_id: str = ""
    job_id: str = ""
    # Actor (Ch II.6.2)
    actor_class: str = ""  # e.g. user / service / system
    actor_id: str = ""  # FORGE internal id only, never a provider id
    # What happened (Ch II.6.2 / II.6.3)
    component: str = ""
    operation: str = ""
    object_type: str = ""
    object_id: str = ""
    capability: str = ""
    outcome: str = "success"
    reason_code: str = ""
    duration_ms: float | None = None
    # Provider attribution (Ch II.6.2) — ids only, never payloads
    provider_type: str = ""
    provider_name: str = ""
    model_id: str = ""
    error_class: str = ""
    provider_failure_class: str = ""
    # Bounded scalar attributes (redacted at construction)
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.seq, int) or self.seq < 0:
            raise ValueError("event seq must be a non-negative int")
        if self.duration_ms is not None:
            if not isinstance(self.duration_ms, (int, float)):
                raise ValueError("duration_ms must be numeric")
            if self.duration_ms < 0:
                raise ValueError("duration_ms must be >= 0")
            object.__setattr__(self, "duration_ms", float(self.duration_ms))
        _vocabulary("stream", self.stream, STREAMS)
        _vocabulary("severity", self.severity, SEVERITIES)
        _vocabulary("outcome", self.outcome, OUTCOMES)
        if self.component:
            _vocabulary("component", self.component, COMPONENTS)
        for name in (
            "timestamp",
            "environment",
            "request_id",
            "job_id",
            "actor_class",
            "actor_id",
            "operation",
            "object_type",
            "object_id",
            "capability",
            "reason_code",
            "provider_type",
            "provider_name",
            "model_id",
            "error_class",
            "provider_failure_class",
        ):
            value = getattr(self, name)
            if isinstance(value, str) and value:
                # Pre-emission scrub for TYPED fields too: a caller passing a
                # secret-shaped value (provider key, bearer token, opaque
                # run) into an id/label field must never reach a sink. The
                # bound still fails closed first (oversized => refuse).
                object.__setattr__(self, name, scrub_text(_bounded(name, value)))
        object.__setattr__(
            self,
            "attributes",
            safe_attributes(self.attributes),
        )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic sorted-key representation."""

        return {
            "schema_version": EVENT_SCHEMA_VERSION,
            "seq": self.seq,
            "timestamp": self.timestamp,
            "environment": self.environment,
            "stream": self.stream,
            "severity": self.severity,
            "request_id": self.request_id,
            "job_id": self.job_id,
            "actor_class": self.actor_class,
            "actor_id": self.actor_id,
            "component": self.component,
            "operation": self.operation,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "capability": self.capability,
            "outcome": self.outcome,
            "reason_code": self.reason_code,
            "duration_ms": self.duration_ms,
            "provider_type": self.provider_type,
            "provider_name": self.provider_name,
            "model_id": self.model_id,
            "error_class": self.error_class,
            "provider_failure_class": self.provider_failure_class,
            "attributes": dict(self.attributes),
        }


__all__ = [
    "COMPONENTS",
    "EVENT_SCHEMA_VERSION",
    "ForgeEvent",
    "MAX_FIELD_LENGTH",
    "OUTCOMES",
    "SEVERITIES",
    "STREAMS",
]
