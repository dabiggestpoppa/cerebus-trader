"""FORGE observability substrate (Book II / Bloc II.6).

Structured events, correlation propagation, deterministic metrics, the
four-stream audit separation, the cost/usage ledger, the integrated error
contract and pre-emission redaction — in-process, deterministic, vendor-free.

Observability describes what happened. It never creates business, security,
evidence or commercial authority, and core execution never depends on it.

Import law: this package imports no FastAPI/Starlette/httpx/requests/psycopg;
domain modules (canonical, schemas, provenance, identity, policy, retrieval,
qa, persistence, backfill) import nothing from here.
"""

from __future__ import annotations

from app.forge.observability.audit import (
    DEFAULT_AUDIT_CAPACITY,
    BoundedAuditTrail,
    EntitlementAuditRecord,
    RetrievalAccessAuditRecord,
    security_audit_event,
)
from app.forge.observability.correlation import (
    UNATTRIBUTED,
    correlation_scope,
    current_request_id,
    effective_request_id,
)
from app.forge.observability.emitter import (
    EventSink,
    ForgeEventEmitter,
    InMemoryEventSink,
    StructuredLogSink,
)
from app.forge.observability.errors import (
    ERROR_CLASSES,
    ERROR_CODES,
    ForgeApplicationError,
    ForgeErrorClass,
    HTTP_STATUS,
    PROVIDER_FAILURE_TO_ERROR_CLASS,
    SAFE_MESSAGES,
    from_exception,
    from_provider_error,
    safe_error_response,
)
from app.forge.observability.events import (
    COMPONENTS,
    EVENT_SCHEMA_VERSION,
    ForgeEvent,
    OUTCOMES,
    SEVERITIES,
    STREAMS,
)
from app.forge.observability.integration import observe_provider_call
from app.forge.observability.metrics import (
    ALL_COUNTERS,
    ALL_GAUGES,
    ALL_HISTOGRAMS,
    MetricsRegistry,
)
from app.forge.observability.redaction import (
    MAX_ATTRIBUTE_VALUE_LENGTH,
    MAX_ATTRIBUTES,
    REDACTED,
    bounded_string,
    safe_attributes,
    safe_scalar,
    scrub_text,
)
from app.forge.observability.service import (
    ForgeObservabilityService,
    observability_from_config,
)
from app.forge.observability.usage import UsageLedger, UsageRecord

__all__ = [
    "ALL_COUNTERS",
    "ALL_GAUGES",
    "ALL_HISTOGRAMS",
    "COMPONENTS",
    "DEFAULT_AUDIT_CAPACITY",
    "ENTITLEMENT_EVENT_TYPES",
    "ERROR_CLASSES",
    "ERROR_CODES",
    "EVENT_SCHEMA_VERSION",
    "EventSink",
    "ForgeErrorClass",
    "ForgeEvent",
    "ForgeEventEmitter",
    "ForgeObservabilityService",
    "HTTP_STATUS",
    "InMemoryEventSink",
    "MAX_ATTRIBUTE_VALUE_LENGTH",
    "MAX_ATTRIBUTES",
    "MetricsRegistry",
    "OUTCOMES",
    "PROVIDER_FAILURE_TO_ERROR_CLASS",
    "REDACTED",
    "SAFE_MESSAGES",
    "SEVERITIES",
    "STREAMS",
    "StructuredLogSink",
    "UNATTRIBUTED",
    "UsageLedger",
    "UsageRecord",
    "BoundedAuditTrail",
    "EntitlementAuditRecord",
    "RetrievalAccessAuditRecord",
    "bounded_string",
    "correlation_scope",
    "current_request_id",
    "effective_request_id",
    "from_exception",
    "from_provider_error",
    "observe_provider_call",
    "observability_from_config",
    "safe_attributes",
    "safe_error_response",
    "safe_scalar",
    "scrub_text",
    "security_audit_event",
]