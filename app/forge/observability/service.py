"""Observability service facade (Book II / Bloc II.6, Phase 6).

The typed facade owned by `ForgeServiceContainer.observability`. It composes
the emitter (telemetry), the metrics registry, the security/retrieval/entitlement
audit trails and the usage ledger into one service-layer object.

Doctrine:

- This service DESCRIBES events. It holds no policy engine, no canonical
  writer, no entitlement state — nothing it exposes can grant, mutate or
  promote anything (ACCEPTANCE M5/M6).
- Every convenience recording method is a thin projection into the
  primitives (events/trails/metrics); all redaction happens beneath, at
  construction.
- It is entirely in-process: no vendor, no network, no external
  infrastructure. Core execution works with it unwired (ACCEPTANCE K3).
"""

from __future__ import annotations

from typing import Any, Callable

from app.forge.config import ForgeConfig
from app.forge.observability.audit import (
    BoundedAuditTrail,
    EntitlementAuditRecord,
    RetrievalAccessAuditRecord,
    security_audit_event,
)
from app.forge.observability.audit_ledger import (
    AUTHENTICATION_EVENT_TYPES,
    DurableAuditLedger,
)
from app.forge.observability.correlation import (
    correlation_scope,
    current_request_id,
    effective_request_id,
)
from app.forge.observability.emitter import (
    ForgeEventEmitter,
    InMemoryEventSink,
    StructuredLogSink,
    utc_now_iso,
)
from app.forge.observability.events import ForgeEvent, OUTCOMES
from app.forge.observability.metrics import MetricsRegistry
from app.forge.observability.usage import UsageLedger, UsageRecord


class ForgeObservabilityService:
    """Typed observability boundary for the FORGE composition root."""

    def __init__(
        self,
        emitter: ForgeEventEmitter,
        metrics: MetricsRegistry | None = None,
        *,
        environment: str = "local",
        audit_capacity: int = 256,
        with_log_sink: bool = True,
        clock: Callable[[], str] = utc_now_iso,
        audit_ledger: DurableAuditLedger | None = None,
    ) -> None:
        self._emitter = emitter
        self._metrics = metrics or MetricsRegistry()
        self._environment = environment
        self._clock = clock
        self._with_log_sink = with_log_sink
        self._retrieval_audit: BoundedAuditTrail = BoundedAuditTrail(
            audit_capacity
        )
        self._entitlement_audit: BoundedAuditTrail = BoundedAuditTrail(
            audit_capacity
        )
        self._usage_ledger: UsageLedger = UsageLedger(audit_capacity)
        # GAP-05 / Ch II.2.6: optional durable audit/event ledger. Default
        # None keeps every existing behavior byte-identical; the composition
        # root wires it only when config.audit_durable.enabled (fail-closed
        # config validation guarantees a persistence port is present).
        self._audit_ledger = audit_ledger

    # -- primitives ----------------------------------------------------------

    @property
    def emitter(self) -> ForgeEventEmitter:
        return self._emitter

    @property
    def metrics(self) -> MetricsRegistry:
        return self._metrics

    def emit(self, **kwargs: Any) -> ForgeEvent | None:
        """Emit a telemetry event (malformed events are counted, not raised)."""

        return self._emitter.safe_emit(**kwargs)

    def emit_strict(self, **kwargs: Any) -> ForgeEvent:
        """Emit raising on malformed input (tests/strict internal paths)."""

        return self._emitter.emit(**kwargs)

    # -- durable audit/event ledger (frozen Ch II.2.6; GAP-05) ---------------

    def _durable(self, **kwargs: Any) -> bool | None:
        """Mirror one audit fact into the durable ledger when wired.

        Recording only: the durable mirror never re-decides anything and is
        byte-invisible when unwired. Fault semantics live in the ledger
        (`best_effort` contains, `require_durable` raises the typed error).
        """

        if self._audit_ledger is None:
            return None
        return self._audit_ledger.append_event(**kwargs)

    @property
    def audit_ledger(self) -> DurableAuditLedger | None:
        return self._audit_ledger

    def durable_audit_events(
        self, *, limit: int = 100, stream: str | None = None
    ) -> tuple[Any, ...]:
        """Bounded, append-ordered durable read-back (empty when unwired).

        Returns persistence-side audit records, duck-typed (frozen K5/K7
        law: observability never imports persistence types).
        """

        if self._audit_ledger is None:
            return ()
        return self._audit_ledger.list_events(limit=limit, stream=stream)

    def record_authentication_event(
        self,
        *,
        event_type: str,
        outcome: str = "success",
        actor_type: str = "system",
        actor_id: str | None = None,
        resource: str = "",
        reason: str = "",
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        at: str | None = None,
    ) -> bool | None:
        """Append one authentication/security event (Ch II.2.6).

        Vocabulary-validated (fail closed) and content-free: session ids,
        user ids and failure kinds only — never credential material. The II.3
        boundary stays the single credential authority; this method only
        RECORDS the fact another module established. Returns the durable
        result (None when the ledger is unwired).
        """

        if event_type not in AUTHENTICATION_EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of {AUTHENTICATION_EVENT_TYPES}"
            )
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {OUTCOMES}")
        self._emitter.safe_emit(
            severity="INFO" if outcome == "success" else "WARNING",
            stream="security_audit",
            component="authentication",
            operation=event_type,
            outcome=outcome,
            request_id=request_id or "",
            actor_class=actor_type,
            actor_id=actor_id or "",
            reason_code=reason,
            attributes={},
        )
        return self._durable(
            stream="security_audit",
            event_type=event_type,
            severity="INFO" if outcome == "success" else "WARNING",
            occurred_at=at,
            request_id=request_id,
            actor_type=actor_type,
            actor_id=actor_id,
            resource=resource,
            outcome=outcome,
            reason=reason,
            details=details,
        )

    def correlation_scope(self, request_id: str | None) -> Any:
        """Bind correlation for a scope (Ch II.6.1 propagation)."""

        return correlation_scope(request_id)

    def current_request_id(self) -> str | None:
        return current_request_id()

    def effective_request_id(self) -> str:
        return effective_request_id()

    # -- security audit (reuses II.4 records; never re-decides) --------------

    def record_policy_decision(self, policy_record: Any) -> ForgeEvent | None:
        """Project an II.4 PolicyAuditRecord into the security-audit stream."""

        event = security_audit_event(
            policy_record,
            environment=self._environment,
            timestamp=self._clock(),
        )
        allowed = bool(getattr(policy_record, "allowed", False))
        self._metrics.increment(
            "policy_allow_total" if allowed else "policy_deny_total"
        )
        emitted = self._emitter.safe_emit(
            severity=event.severity,
            stream="security_audit",
            component="policy",
            operation=event.operation,
            outcome=event.outcome,
            request_id=event.request_id,
            actor_class=event.actor_class,
            actor_id=event.actor_id,
            object_type=event.object_type,
            object_id=event.object_id,
            capability=event.capability,
            reason_code=event.reason_code,
            attributes=dict(event.attributes),
        )
        # Durable mirror (Ch II.2.6 "policy decisions"): records the II.4
        # decision projection above — never re-decides it.
        self._durable(
            stream="security_audit",
            event_type="policy.allow" if allowed else "policy.deny",
            severity=event.severity,
            occurred_at=(
                getattr(policy_record, "at", "") or event.timestamp or None
            ),
            request_id=event.request_id or None,
            actor_type=event.actor_class,
            actor_id=event.actor_id or None,
            resource=f"{event.object_type}:{event.object_id}",
            outcome=event.outcome,
            reason=event.reason_code,
            details=dict(event.attributes),
        )
        return emitted

    # -- retrieval access audit (Ch II.6.5) ----------------------------------

    def record_retrieval_access(
        self,
        *,
        principal_id: str,
        service: str,
        capability: str,
        canonical_object_ids: tuple[str, ...] = (),
        retrieval_object_ids: tuple[str, ...] = (),
        exposure: str = "UNSPECIFIED",
        decision: str = "DENY",
        correlation_id: str | None = None,
        at: str | None = None,
    ) -> RetrievalAccessAuditRecord:
        """Append a bounded, content-free retrieval access fact."""

        record = RetrievalAccessAuditRecord(
            correlation_id=correlation_id or effective_request_id(),
            principal_id=principal_id,
            service=service,
            capability=capability,
            canonical_object_ids=canonical_object_ids,
            retrieval_object_ids=retrieval_object_ids,
            exposure=exposure,
            decision=decision,
            at=at if at is not None else self._clock(),
        )
        self._retrieval_audit.append(record)
        if decision == "ALLOW" and canonical_object_ids:
            self._metrics.increment(
                "retrieval_objects_total", float(len(canonical_object_ids))
            )
        # Durable mirror (Ch II.2.6 "protected retrieval access"): IDs and
        # decisions only — full source content never enters the ledger.
        # Stream: security_audit (frozen STREAMS vocabulary — an access
        # decision is an authorization fact; event_type names the class).
        self._durable(
            stream="security_audit",
            event_type="retrieval.access",
            severity="INFO" if decision == "ALLOW" else "WARNING",
            occurred_at=record.at or None,
            request_id=record.correlation_id or None,
            actor_type="user",
            actor_id=record.principal_id,
            resource=record.exposure,
            outcome="success" if decision == "ALLOW" else "denied",
            details={
                "service": record.service,
                "capability": record.capability,
                "canonical_object_ids": ", ".join(record.canonical_object_ids),
                "retrieval_object_ids": ", ".join(record.retrieval_object_ids),
            },
        )
        return record

    def retrieval_audit_records(self) -> tuple[RetrievalAccessAuditRecord, ...]:
        return tuple(self._retrieval_audit.records())

    # -- entitlement audit (Ch II.6.6; records only, Book VI mutates) --------

    def record_entitlement_event(
        self,
        *,
        event_type: str,
        principal_id: str,
        entitlement_id: str,
        source_event_id: str = "",
        provider_type: str = "",
        provider_name: str = "",
        correlation_id: str | None = None,
        at: str | None = None,
    ) -> EntitlementAuditRecord:
        """Append one commercial audit fact (vocabulary-validated)."""

        record = EntitlementAuditRecord(
            event_type=event_type,
            principal_id=principal_id,
            entitlement_id=entitlement_id,
            source_event_id=source_event_id,
            provider_type=provider_type,
            provider_name=provider_name,
            correlation_id=correlation_id or effective_request_id(),
            at=at if at is not None else self._clock(),
        )
        self._entitlement_audit.append(record)
        self._metrics.increment("commerce_events_total")
        self._emitter.safe_emit(
            severity="INFO",
            stream="entitlement_audit",
            component="policy",
            operation=f"entitlement.{event_type}",
            outcome="success",
            request_id=record.correlation_id,
            actor_class="system",
            object_type="entitlement",
            object_id=entitlement_id,
            reason_code=event_type,
            provider_type=provider_type,
            provider_name=provider_name,
            attributes={"source_event_id": source_event_id},
        )
        # Durable mirror (Ch II.2.6 "entitlement changes"): a RECORD of the
        # vocabulary entry only — II.6 records, Book VI owns the meaning
        # (GOVERNANCE §2: no entitlement authority is derived here).
        self._durable(
            stream="entitlement_audit",
            event_type=f"entitlement.{event_type}",
            severity="INFO",
            occurred_at=record.at or None,
            request_id=record.correlation_id or None,
            actor_type="system",
            actor_id=record.principal_id or None,
            resource=record.entitlement_id,
            outcome="recorded",
            reason=event_type,
            details={
                "source_event_id": source_event_id,
                "provider_type": provider_type,
                "provider_name": provider_name,
            },
        )
        return record

    def entitlement_audit_records(self) -> tuple[EntitlementAuditRecord, ...]:
        return tuple(self._entitlement_audit.records())

    # -- usage ledger (Ch II.6.9) --------------------------------------------

    def record_usage(
        self,
        *,
        provider_type: str,
        provider_name: str,
        request_id: str | None = None,
        model_id: str = "",
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        normalized_cost: float | None = None,
        latency_ms: float | None = None,
        success: bool = True,
        at: str | None = None,
    ) -> UsageRecord:
        """Append one usage observation; unsupplied fields stay None."""

        record = UsageRecord(
            request_id=request_id or effective_request_id(),
            provider_type=provider_type,
            provider_name=provider_name,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            normalized_cost=normalized_cost,
            latency_ms=latency_ms,
            success=success,
            at=at if at is not None else self._clock(),
        )
        self._usage_ledger.append(record)
        self._metrics.add_llm_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            normalized_cost=normalized_cost,
        )
        self._emitter.safe_emit(
            severity="INFO",
            stream="usage_ledger",
            component="provider",
            operation=f"{provider_type}.usage",
            outcome="success" if success else "failure",
            request_id=record.request_id,
            provider_type=provider_type,
            provider_name=provider_name,
            model_id=model_id,
            duration_ms=latency_ms,
            attributes={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "normalized_cost": normalized_cost,
            },
        )
        # Durable mirror (Ch II.2.6 "provider event"): usage observation as
        # a usage_ledger-stream record (frozen STREAMS vocabulary) — counts
        # and ids only, never prompts or raw provider payloads.
        self._durable(
            stream="usage_ledger",
            event_type="provider.usage",
            severity="INFO" if success else "WARNING",
            occurred_at=record.at or None,
            request_id=record.request_id or None,
            actor_type="system",
            resource=f"{provider_type}:{provider_name}",
            outcome="success" if success else "failure",
            details={
                "model_id": model_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "normalized_cost": normalized_cost,
                "latency_ms": latency_ms,
            },
        )
        return record

    def usage_records(self) -> tuple[UsageRecord, ...]:
        return tuple(self._usage_ledger.records())

    # -- diagnostics ---------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Bounded, safe snapshot for health/meta diagnostics (no payloads)."""

        snapshot: dict[str, Any] = {
            "environment": self._environment,
            "events_recorded": self._emitter.seq,
            "dropped_events": self._emitter.dropped_events,
            "rejected_events": self._emitter.rejected_events,
            "retrieval_audit_records": len(self._retrieval_audit),
            "entitlement_audit_records": len(self._entitlement_audit),
            "usage_records": len(self._usage_ledger),
            "metrics": self._metrics.snapshot(),
        }
        # GAP-05: disclose durable ledger health ONLY when configured — the
        # unwired snapshot stays byte-identical to the pre-GAP-05 shape.
        if self._audit_ledger is not None:
            snapshot["durable_audit"] = self._audit_ledger.snapshot()
        return snapshot


def observability_from_config(
    config: ForgeConfig, persistence: Any = None
) -> ForgeObservabilityService:
    """Composition-root factory (Ch II.6 wiring).

    In-process sinks only: bounded in-memory ring + stdlib structured log
    line. No external telemetry vendor, no network, no credentials.

    GAP-05 (frozen Ch II.2.6): when `config.audit_durable.enabled`, the
    durable audit/event ledger is wired through the injected persistence
    port. Fail-closed: enabled WITHOUT a persistence port raises — durable
    audit is never silently downgraded to in-memory. Unchanged when disabled
    (the default), byte-identical to the pre-GAP-05 factory.
    """

    sinks: list[Any] = [InMemoryEventSink(config.observability_event_capacity)]
    if config.observability_log_sinks:
        sinks.append(StructuredLogSink())
    emitter = ForgeEventEmitter(
        environment=config.environment,
        sinks=tuple(sinks),
    )
    audit_ledger: DurableAuditLedger | None = None
    if config.audit_durable.enabled:
        if persistence is None:
            raise ValueError(
                "audit_durable enabled but no persistence gateway supplied "
                "(fail closed: durable audit is never in-memory-only)"
            )
        audit_ledger = DurableAuditLedger(
            persistence,
            capacity=config.audit_durable.capacity,
            write_policy=config.audit_durable.write_policy,
            environment=config.environment,
        )
    return ForgeObservabilityService(
        emitter,
        environment=config.environment,
        audit_capacity=config.observability_event_capacity,
        with_log_sink=config.observability_log_sinks,
        audit_ledger=audit_ledger,
    )


__all__ = [
    "ForgeObservabilityService",
    "observability_from_config",
]
