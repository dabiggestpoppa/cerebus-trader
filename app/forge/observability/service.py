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
from app.forge.observability.events import ForgeEvent
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
        return self._emitter.safe_emit(
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
        return record

    def usage_records(self) -> tuple[UsageRecord, ...]:
        return tuple(self._usage_ledger.records())

    # -- diagnostics ---------------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Bounded, safe snapshot for health/meta diagnostics (no payloads)."""

        return {
            "environment": self._environment,
            "events_recorded": self._emitter.seq,
            "dropped_events": self._emitter.dropped_events,
            "rejected_events": self._emitter.rejected_events,
            "retrieval_audit_records": len(self._retrieval_audit),
            "entitlement_audit_records": len(self._entitlement_audit),
            "usage_records": len(self._usage_ledger),
            "metrics": self._metrics.snapshot(),
        }


def observability_from_config(config: ForgeConfig) -> ForgeObservabilityService:
    """Composition-root factory (Ch II.6 wiring).

    In-process sinks only: bounded in-memory ring + stdlib structured log
    line. No external telemetry vendor, no network, no credentials.
    """

    sinks: list[Any] = [InMemoryEventSink(config.observability_event_capacity)]
    if config.observability_log_sinks:
        sinks.append(StructuredLogSink())
    emitter = ForgeEventEmitter(
        environment=config.environment,
        sinks=tuple(sinks),
    )
    return ForgeObservabilityService(
        emitter,
        environment=config.environment,
        audit_capacity=config.observability_event_capacity,
        with_log_sink=config.observability_log_sinks,
    )


__all__ = [
    "ForgeObservabilityService",
    "observability_from_config",
]
