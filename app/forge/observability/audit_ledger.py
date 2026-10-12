"""Durable audit/event ledger (Book II GAP-05; frozen Ch II.2.6).

Second-tier durability for the II.6 audit streams: each audit/event fact is
written through the `AuditEventPort` (PostgreSQL/SQLite SQL gateway or the
in-memory reference double) so it survives process restart, while a bounded
replay cache keeps recent events in-process for fast read-back.

Laws honored here:

- APPEND-ONLY: the ledger never rewrites, reorders or deletes history; the
  cache is a bounded FIFO view (oldest evicted), the store is append-only.
- CONTENT-MINIMIZED: details pass the frozen redaction path
  (`observability.redaction`) before they reach any record — scalars only,
  secrets scrubbed, oversized values refused/marked, never corpus content.
- FAILURE CONTAINMENT: persistence NEVER imports observability; the failover
  decision lives HERE, on the observability side of the boundary. Under
  `best_effort` a backend fault never raises (fallback marker + NOT_OK
  status + redacted cause); under `require_durable` the typed
  `DurableAuditWriteError` propagates — the operator's explicit choice.
- NO SECOND AUTHORITY: this ledger records facts other modules decided
  (II.3 authentication, II.4 policy, II.6 audit vocabulary). It decides
  nothing, and it is not Book I evidence provenance nor Book VI entitlement
  truth (closure_repair/GOVERNANCE §2).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from app.forge.observability.audit import BoundedAuditTrail
from app.forge.observability.emitter import utc_now_iso
from app.forge.observability.redaction import bounded_string, safe_attributes

# Failover write policies (validated at config time and at construction).
AUDIT_WRITE_POLICY_BEST_EFFORT = "best_effort"
AUDIT_WRITE_POLICY_REQUIRE_DURABLE = "require_durable"
AUDIT_WRITE_POLICIES: frozenset[str] = frozenset(
    {AUDIT_WRITE_POLICY_BEST_EFFORT, AUDIT_WRITE_POLICY_REQUIRE_DURABLE}
)

DEFAULT_DURABLE_CAPACITY = 10_000

# Frozen authentication/security event vocabulary for Ch II.2.6's
# "authentication/security events" class. Fail-closed: unknown types are
# rejected at the seam (same doctrine as ENTITLEMENT_EVENT_TYPES).
AUTHENTICATION_EVENT_TYPES: tuple[str, ...] = (
    "session_opened",
    "session_revoked",
    "sessions_revoked_all",
    "authentication_failed",
    "identity_linked",
)


class DurableAuditWriteError(Exception):
    """Typed, redacted durable-write failure (`require_durable` only).

    `kind` is an exception class name or a persistence `kind` token — never
    a URL, credential, payload or stack trace (redaction law).
    """

    def __init__(self, kind: str) -> None:
        super().__init__(f"durable audit write failed: {kind}")
        self.kind = kind


@dataclass(frozen=True)
class LedgerEvent:
    """Observability-side envelope handed to the durable port.

    Deliberately defined HERE: the frozen K5/K7 import law forbids the
    observability package from importing persistence types (neither store is
    written through the other's module). The port duck-types on shape; the
    persistence side coerces this envelope into its own `AuditEventRecord`
    at the boundary (`persistence.records.coerce_audit_event`). Field names
    match the storage columns 1:1; `seq`/`created_at` are persistence-owned
    and absent by design.
    """

    event_id: str
    stream: str
    event_type: str
    severity: str
    occurred_at: str
    details_json: str = "{}"
    request_id: str | None = None
    actor_type: str = "system"
    actor_id: str | None = None
    resource: str = ""
    outcome: str = ""
    reason: str = ""
    environment: str = "local"


@dataclass(frozen=True)
class FallbackAuditMarker:
    """What a faulted durable append leaves behind under `best_effort`.

    The audit FACT is never silently dropped: the marker names the original
    stream/event_type/time plus the redacted failure cause, so an operator
    can correlate a NOT_OK ledger status with the affected event class.
    """

    stream: str
    event_type: str
    occurred_at: str
    cause_kind: str


class DurableAuditLedger:
    """Bounded replay cache + append-only durable store + failover policy."""

    def __init__(
        self,
        port: Any,
        *,
        capacity: int = DEFAULT_DURABLE_CAPACITY,
        write_policy: str = AUDIT_WRITE_POLICY_BEST_EFFORT,
        environment: str = "local",
        clock: Callable[[], str] = utc_now_iso,
    ) -> None:
        if int(capacity) < 1:
            raise ValueError("durable audit capacity must be >= 1")
        if write_policy not in AUDIT_WRITE_POLICIES:
            raise ValueError(
                f"write_policy must be one of {sorted(AUDIT_WRITE_POLICIES)}"
            )
        if port is None:
            raise ValueError("durable audit ledger requires a persistence port")
        self._port = port
        self._capacity = int(capacity)
        self._write_policy = write_policy
        self._environment = environment
        self._clock = clock
        self._cache: BoundedAuditTrail = BoundedAuditTrail(self._capacity)
        self._fallbacks: BoundedAuditTrail = BoundedAuditTrail(self._capacity)
        self._durable_appends = 0
        self._fallback_appends = 0
        self._last_error_kind = ""
        self._status = "OK"

    # -- introspection --------------------------------------------------------

    @property
    def write_policy(self) -> str:
        return self._write_policy

    @property
    def status(self) -> str:
        """OK while the most recent append succeeded; NOT_OK after a fault."""

        return self._status

    def records(self) -> tuple[LedgerEvent, ...]:
        return tuple(self._cache.records())

    def fallbacks(self) -> tuple[FallbackAuditMarker, ...]:
        return tuple(self._fallbacks.records())

    def snapshot(self) -> dict[str, Any]:
        """Bounded counters for readiness/meta diagnostics (never payloads)."""

        return {
            "status": self._status,
            "write_policy": self._write_policy,
            "durable_appends": self._durable_appends,
            "fallback_appends": self._fallback_appends,
            "cached": len(self._cache),
            "last_error_kind": self._last_error_kind,
        }

    # -- write path -----------------------------------------------------------

    def append_event(
        self,
        *,
        stream: str,
        event_type: str,
        severity: str = "INFO",
        occurred_at: str | None = None,
        request_id: str | None = None,
        actor_type: str = "system",
        actor_id: str | None = None,
        resource: str = "",
        outcome: str = "success",
        reason: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> bool:
        """Append one audit/event fact durably.

        Returns True when the fact is durably stored (fresh or already
        present — idempotent by generated event_id), False when a
        `best_effort` fault was contained into a fallback marker. Raises
        `DurableAuditWriteError` on a fault only under `require_durable`.
        """

        safe_details = self._safe_details(details)
        record = LedgerEvent(
            event_id=str(uuid.uuid4()),
            stream=str(stream),
            event_type=str(event_type),
            severity=str(severity),
            occurred_at=str(occurred_at or self._clock()),
            details_json=json.dumps(safe_details, sort_keys=True),
            request_id=str(request_id) if request_id else None,
            actor_type=str(actor_type or "system"),
            actor_id=str(actor_id) if actor_id else None,
            resource=bounded_string(str(resource or ""), limit=256),
            outcome=str(outcome or ""),
            reason=bounded_string(str(reason or ""), limit=120),
            environment=self._environment,
        )
        try:
            self._port.append_audit_event(record)
        except Exception as exc:  # normalized cause only, never re-raised
            kind = str(getattr(exc, "kind", "") or type(exc).__name__)
            self._fallback_appends += 1
            self._last_error_kind = kind
            self._status = "NOT_OK"
            self._fallbacks.append(
                FallbackAuditMarker(
                    stream=record.stream,
                    event_type=record.event_type,
                    occurred_at=record.occurred_at,
                    cause_kind=kind,
                )
            )
            if self._write_policy == AUDIT_WRITE_POLICY_REQUIRE_DURABLE:
                raise DurableAuditWriteError(kind) from None
            return False
        # Stored (or already present): record the fact in the bounded cache
        # and flip health back to OK — recovery is observable, like faults.
        self._durable_appends += 1
        self._last_error_kind = ""
        self._status = "OK"
        self._cache.append(record)
        return True

    def list_events(
        self, *, limit: int = 100, stream: str | None = None
    ) -> tuple[Any, ...]:
        """Bounded, append-ordered durable read-back (record-before-read).

        Returns persistence-side records (duck-typed shape, identical field
        names) — the observability package never imports their type.
        """

        return self._port.list_audit_events(limit=limit, stream=stream)

    # -- content minimization -------------------------------------------------

    @staticmethod
    def _safe_details(details: Mapping[str, Any] | None) -> dict[str, Any]:
        """Frozen redaction path applied before any detail reaches storage.

        Non-scalar values, oversized values and secret-shaped strings never
        cross the boundary: `safe_attributes` scrubs/bounds scalars and
        refuses containers (a refused mapping collapses to a single bounded
        marker instead of failing the audit append).
        """

        if not details:
            return {}
        if not isinstance(details, Mapping):
            return {"_details": bounded_string(str(details))}
        try:
            return safe_attributes(details)
        except ValueError:
            return {"_details": "details_rejected_not_scalar_or_too_many"}


__all__ = [
    "AUDIT_WRITE_POLICIES",
    "AUDIT_WRITE_POLICY_BEST_EFFORT",
    "AUDIT_WRITE_POLICY_REQUIRE_DURABLE",
    "AUTHENTICATION_EVENT_TYPES",
    "DEFAULT_DURABLE_CAPACITY",
    "DurableAuditLedger",
    "DurableAuditWriteError",
    "FallbackAuditMarker",
    "LedgerEvent",
]
