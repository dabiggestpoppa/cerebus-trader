"""Auditability layer (Book II / Bloc II.6, Ch II.6.5 / II.6.6).

The four-stream separation (PLAN §4), enforced structurally — there is no
generic log:

1. Operational telemetry  -> ForgeEvent with stream="telemetry" (emitter.py)
2. Security audit         -> stream="security_audit"; the DECISION authority
                             stays with II.4. This module only adapts II.4's
                             bounded, content-free `PolicyAuditRecord` into
                             audit events. No second policy engine exists.
3. Evidence provenance    -> Book I `app.forge.provenance` remains the only
                             "why a claim is supported" authority. Nothing in
                             this module touches it; no evidence content may
                             enter telemetry or audit records.
4. Commercial ledger      -> entitlement audit VOCABULARY only (Ch II.6.6).
                             Book VI performs mutations; II.6 records. No
                             entitlement state machine exists here.

Retrieval access audit (Ch II.6.5): who/which service, capability,
canonical/retrieval object IDs, exposure, decision, timestamp. Full source
documents are NEVER copied into audit records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.forge.observability.events import ForgeEvent

# Bounded audit memory (append-only, oldest evicted).
DEFAULT_AUDIT_CAPACITY = 256
MAX_AUDIT_OBJECT_IDS = 32

# Frozen entitlement audit vocabulary (Ch II.6.6), exact set.
ENTITLEMENT_EVENT_TYPES: tuple[str, ...] = (
    "grant",
    "renew",
    "grace",
    "expire",
    "revoke",
    "admin_correction",
)

_AUDIT_DECISIONS: frozenset[str] = frozenset({"ALLOW", "DENY"})


@dataclass(frozen=True)
class RetrievalAccessAuditRecord:
    """Ch II.6.5 protected retrieval fact. IDs and decisions only."""

    correlation_id: str
    principal_id: str  # FORGE user id, or "anonymous"
    service: str  # which service performed the access
    capability: str
    canonical_object_ids: tuple[str, ...] = ()
    retrieval_object_ids: tuple[str, ...] = ()
    exposure: str = "UNSPECIFIED"
    decision: str = "DENY"
    at: str = ""  # caller-supplied timestamp (clock-free core)

    def __post_init__(self) -> None:
        if self.decision not in _AUDIT_DECISIONS:
            raise ValueError("decision must be ALLOW or DENY")
        for name in ("canonical_object_ids", "retrieval_object_ids"):
            ids = getattr(self, name)
            if len(ids) > MAX_AUDIT_OBJECT_IDS:
                raise ValueError(f"{name} exceeds bound {MAX_AUDIT_OBJECT_IDS}")
            if not all(isinstance(i, str) and len(i) <= 128 for i in ids):
                raise ValueError(f"{name} must be bounded strings")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "retrieval_access",
            "correlation_id": self.correlation_id,
            "principal_id": self.principal_id,
            "service": self.service,
            "capability": self.capability,
            "canonical_object_ids": list(self.canonical_object_ids),
            "retrieval_object_ids": list(self.retrieval_object_ids),
            "exposure": self.exposure,
            "decision": self.decision,
            "at": self.at,
        }


@dataclass(frozen=True)
class EntitlementAuditRecord:
    """Ch II.6.6 commercial audit fact. Records an event vocabulary entry.

    II.6 RECORDS entitlement events; Book VI owns mutation semantics. The
    source event / provider mapping makes provider->entitlement tracing
    reconstructable without granting providers any authority here.
    """

    event_type: str
    principal_id: str
    entitlement_id: str
    source_event_id: str = ""
    provider_type: str = ""
    provider_name: str = ""
    correlation_id: str = ""
    at: str = ""

    def __post_init__(self) -> None:
        if self.event_type not in ENTITLEMENT_EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of {ENTITLEMENT_EVENT_TYPES}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "entitlement",
            "event_type": self.event_type,
            "principal_id": self.principal_id,
            "entitlement_id": self.entitlement_id,
            "source_event_id": self.source_event_id,
            "provider_type": self.provider_type,
            "provider_name": self.provider_name,
            "correlation_id": self.correlation_id,
            "at": self.at,
        }


class BoundedAuditTrail:
    """Append-only bounded trail (oldest evicted, order preserved)."""

    def __init__(self, capacity: int = DEFAULT_AUDIT_CAPACITY) -> None:
        if capacity < 1:
            raise ValueError("audit capacity must be >= 1")
        self._capacity = capacity
        self._records: list[Any] = []

    def append(self, record: Any) -> None:
        self._records.append(record)
        if len(self._records) > self._capacity:
            del self._records[: len(self._records) - self._capacity]

    def records(self) -> tuple[Any, ...]:
        return tuple(self._records)

    def __len__(self) -> int:
        return len(self._records)


def security_audit_event(
    policy_record: Any, *, environment: str, seq: int = 0, timestamp: str = ""
) -> ForgeEvent:
    """Adapt an II.4 `PolicyAuditRecord` into a security-audit event.

    Pure projection: every field comes from the II.4 record (the single
    authorization-decision authority); this adds no decision logic and
    carries no content. Field access is structural (duck-typed) to keep the
    observability package free of service-layer import cycles.
    """

    allowed = bool(getattr(policy_record, "allowed", False))
    return ForgeEvent(
        seq=seq,
        timestamp=timestamp or getattr(policy_record, "at", ""),
        environment=environment,
        stream="security_audit",
        severity="INFO" if allowed else "WARNING",
        request_id=getattr(policy_record, "correlation_id", ""),
        actor_class="user",
        actor_id=getattr(policy_record, "principal_id", ""),
        component="policy",
        operation=getattr(policy_record, "action", ""),
        object_type=getattr(policy_record, "resource_type", ""),
        object_id=getattr(policy_record, "resource_id", ""),
        capability=getattr(policy_record, "exposure", ""),
        outcome="success" if allowed else "denied",
        reason_code=getattr(policy_record, "reason_code", ""),
        attributes={
            "authenticated": bool(
                getattr(policy_record, "authenticated", False)
            ),
        },
    )


__all__ = [
    "BoundedAuditTrail",
    "DEFAULT_AUDIT_CAPACITY",
    "ENTITLEMENT_EVENT_TYPES",
    "EntitlementAuditRecord",
    "MAX_AUDIT_OBJECT_IDS",
    "RetrievalAccessAuditRecord",
    "security_audit_event",
]
