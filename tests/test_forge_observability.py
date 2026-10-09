"""Book II / Bloc II.6 — focused observability test matrix.

Deterministic: injected clocks and simulated time only; no network, no
sleeping, no external telemetry infrastructure. Covers the directive matrix
items 1-25 plus the frozen Ch II.6.x chapter gates and the four verbatim
Acceptance II.6 clauses; items 26-32 are the regression/full-suite/CI gates
recorded in EVIDENCE.md.
"""

from __future__ import annotations

import ast
import json
import logging
from pathlib import Path

import pytest

from app.forge.canonical import (
    EvidenceStatus,
    Layer,
    ObjectType,
    ProductExposure,
)
from app.forge.config import ForgeConfig
from app.forge.identity import ForgePrincipal
from app.forge.observability import (
    COMPONENTS,
    ENTITLEMENT_EVENT_TYPES,
    ERROR_CLASSES,
    ERROR_CODES,
    EVENT_SCHEMA_VERSION,
    ForgeErrorClass,
    ForgeEvent,
    ForgeEventEmitter,
    ForgeObservabilityService,
    InMemoryEventSink,
    MAX_ATTRIBUTE_VALUE_LENGTH,
    MetricsRegistry,
    OUTCOMES,
    PROVIDER_FAILURE_TO_ERROR_CLASS,
    SAFE_MESSAGES,
    SEVERITIES,
    STREAMS,
    UNATTRIBUTED,
    UsageLedger,
    UsageRecord,
    correlation_scope,
    effective_request_id,
    from_provider_error,
    observe_provider_call,
    observability_from_config,
    safe_error_response,
    scrub_text,
)
from app.forge.observability.audit import (
    BoundedAuditTrail,
    EntitlementAuditRecord,
    RetrievalAccessAuditRecord,
)
from app.forge.observability.errors import from_exception
from app.forge.observability.metrics import MAX_HISTOGRAM_SAMPLES
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.port import PersistenceUnavailable
from app.forge.persistence.records import CanonicalObjectRecord
from app.forge.policy import (
    AuthorizationContext,
    DefaultDenyPolicyEngine,
    PolicyAction,
    PolicyResourceType,
    ResourcePolicyMetadata,
)
from app.forge.providers.doctrine import PORTS
from app.forge.providers.errors import (
    FAILURE_CLASSES,
    ProviderAuthenticationFailedError,
    ProviderError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
    ProviderUnknownError,
    ProviderUnavailableError,
)
from app.forge.providers.fakes import (
    FakeBehavior,
    FakeCommerceProvider,
    FakeLLMProvider,
    SimulatedClock,
)
from app.forge.providers.llm import LLMRequest
from app.forge.providers.registry import ProviderRegistry, providers_from_config
from app.forge.providers.resilience import CircuitBreaker
from app.forge.service.container import ForgeServiceContainer
from app.forge.service.lifecycle import ForgeLifecycle
from app.forge.service.policy_enforcement import (
    ForgePolicyEnforcementService,
    PolicyAuditRecord,
)

# ---------------------------------------------------------------------------
# helpers / sentinels
# ---------------------------------------------------------------------------

SENTINEL_SECRET = "sk-live-AbCdEf1234567890XYZ"
SENTINEL_TOKEN = "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVphYmNkZWY"  # 43-char urlsafe
SENTINEL_CREDENTIAL = "api_key=SuperSecretValue12345"
SENTINEL_PROTECTED_BODY = (
    "PROTECTED_CORPUS_BODY: exact alpha study says the 34.2% rekey level "
    "remains valid into the weekly close and the operator card asserts "
    "nothing beyond the frozen evidence chain for this claim under review "
    + "lorem ipsum research detail " * 20
)


def _fixed_clock(tick: str = "2026-10-09T00:00:00+00:00"):
    return lambda: tick


def _service() -> tuple[ForgeObservabilityService, InMemoryEventSink]:
    sink = InMemoryEventSink()
    obs = ForgeObservabilityService(
        ForgeEventEmitter(
            environment="test", sinks=(sink,), clock=_fixed_clock()
        ),
        environment="test",
        clock=_fixed_clock(),
    )
    return obs, sink


def _principal(authenticated: bool = True) -> ForgePrincipal:
    return ForgePrincipal(
        authenticated=authenticated,
        forge_user_id="u1" if authenticated else None,
        session_id="s1" if authenticated else None,
        roles=frozenset(),
    )


def _resource(exposure: ProductExposure) -> ResourcePolicyMetadata:
    return ResourcePolicyMetadata(
        resource_type=PolicyResourceType.CANONICAL_OBJECT,
        resource_id="EV.TEST.V1",
        exposure=exposure,
    )


def _evidence_record(canonical_id: str) -> CanonicalObjectRecord:
    return CanonicalObjectRecord(
        canonical_id=canonical_id,
        object_type=ObjectType.EVIDENCE,
        title="t",
        version="1.0",
        status=EvidenceStatus.VALIDATED,
        exposure=ProductExposure.PUBLIC_TEACHING,
        layer=Layer.L1,
        references=(),
        metadata={},
    )


class _PingDownGateway(InMemoryPersistenceGateway):
    """Full port implementation whose backend cannot serve (ping fails)."""

    def ping(self) -> None:
        raise PersistenceUnavailable("postgres")


def _observe(
    obs: ForgeObservabilityService,
    call,
    *,
    port: str,
    provider_type: str,
    provider_name: str,
    request_id: str | None = None,
    clock=None,
):
    kwargs: dict = {}
    if clock is not None:
        kwargs["clock"] = clock
    return observe_provider_call(
        obs.emit,
        obs.metrics.increment,
        obs.metrics.observe,
        port=port,
        provider_type=provider_type,
        provider_name=provider_name,
        request_id=request_id,
        call=call,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 1-2: correlation propagation & request identity (Ch II.6.1)
# ---------------------------------------------------------------------------


class TestCorrelationPropagation:
    def test_scope_binds_and_restores(self) -> None:
        with correlation_scope("fg-abc123") as bound:
            assert bound == "fg-abc123"
            assert effective_request_id() == "fg-abc123"
            with correlation_scope("fg-nested1") as inner:
                assert inner == "fg-nested1"
            assert effective_request_id() == "fg-abc123"
        assert effective_request_id() == UNATTRIBUTED

    def test_inbound_unsafe_id_is_regenerated(self) -> None:
        with correlation_scope("not safe !! <script>") as bound:
            assert bound.startswith("fg-")
            assert effective_request_id() == bound

    def test_events_inherit_scope_request_id(self) -> None:
        obs, sink = _service()
        with correlation_scope("fg-scope1"):
            obs.emit(operation="op", component="api")
        assert sink.events()[0].request_id == "fg-scope1"

    def test_explicit_request_id_beats_scope(self) -> None:
        obs, sink = _service()
        with correlation_scope("fg-scope2"):
            obs.emit(operation="op", component="api", request_id="fg-explicit")
        assert sink.events()[0].request_id == "fg-explicit"

    def test_route_round_trip_request_identity(self) -> None:
        from fastapi.testclient import TestClient

        from app.forge.service.routes import create_forge_router

        config = ForgeConfig(environment="test")
        obs, _ = _service()
        container = ForgeServiceContainer(config=config, observability=obs)
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(create_forge_router(config=config, container=container))
        client = TestClient(app)
        response = client.get(
            "/forge/v1/health", headers={"X-Request-Id": "fg-routeid1"}
        )
        assert response.status_code == 200
        assert response.json()["request_id"] == "fg-routeid1"

        missing = client.get("/forge/v1/health")
        assert missing.json()["request_id"].startswith("fg-")

    def test_route_emits_request_event_with_response_request_id(self) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.forge.service.routes import create_forge_router

        config = ForgeConfig(environment="test")
        obs, sink = _service()
        container = ForgeServiceContainer(config=config, observability=obs)
        app = FastAPI()
        app.include_router(create_forge_router(config=config, container=container))
        client = TestClient(app)
        response = client.get(
            "/forge/v1/meta", headers={"X-Request-Id": "fg-metaroute"}
        )
        assert response.status_code == 200
        assert response.json()["request_id"] == "fg-metaroute"
        request_events = [
            e for e in sink.events() if e.operation == "GET /forge/v1/meta"
        ]
        assert request_events and request_events[0].request_id == "fg-metaroute"
        assert request_events[0].component == "api"


# ---------------------------------------------------------------------------
# 3: structured event schema (Ch II.6.2 / II.6.3)
# ---------------------------------------------------------------------------


class TestEventSchema:
    def test_frozen_field_set(self) -> None:
        event = ForgeEvent(environment="test", timestamp="t")
        data = event.to_dict()
        assert data["schema_version"] == EVENT_SCHEMA_VERSION
        assert set(data) == {
            "schema_version", "seq", "timestamp", "environment", "stream",
            "severity", "request_id", "job_id", "actor_class", "actor_id",
            "component", "operation", "object_type", "object_id", "capability",
            "outcome", "reason_code", "duration_ms", "provider_type",
            "provider_name", "model_id", "error_class",
            "provider_failure_class", "attributes",
        }

    def test_vocabularies_exact(self) -> None:
        assert SEVERITIES == ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        assert OUTCOMES == ("success", "failure", "denied", "degraded")
        assert set(COMPONENTS) == {
            "api", "identity", "policy", "persistence", "retrieval",
            "provider", "jobs", "observability",
        }
        assert set(STREAMS) == {
            "telemetry", "security_audit", "usage_ledger", "entitlement_audit",
        }

    def test_unknown_vocabulary_refused(self) -> None:
        with pytest.raises(ValueError):
            ForgeEvent(severity="LOUD")
        with pytest.raises(ValueError):
            ForgeEvent(outcome="kinda")
        with pytest.raises(ValueError):
            ForgeEvent(component="billing")

    def test_oversized_field_refused(self) -> None:
        with pytest.raises(ValueError):
            ForgeEvent(operation="x" * 129)
        with pytest.raises(ValueError):
            ForgeEvent(reason_code="y" * 129)

    def test_nested_attributes_refused(self) -> None:
        with pytest.raises(ValueError):
            ForgeEvent(attributes={"nested": {"a": 1}})
        with pytest.raises(ValueError):
            ForgeEvent(attributes={"list": [1, 2, 3]})

    def test_too_many_attributes_refused(self) -> None:
        with pytest.raises(ValueError):
            ForgeEvent(attributes={f"k{i}": i for i in range(17)})

    def test_negative_duration_refused(self) -> None:
        with pytest.raises(ValueError):
            ForgeEvent(duration_ms=-1.0)

    def test_scalar_attributes_survive(self) -> None:
        event = ForgeEvent(
            attributes={"count": 3, "ratio": 0.5, "ok": True, "none": None}
        )
        assert dict(event.attributes) == {
            "count": 3, "ratio": 0.5, "ok": True, "none": None,
        }


# ---------------------------------------------------------------------------
# 4: deterministic event output (injected clocks)
# ---------------------------------------------------------------------------


class TestDeterministicOrdering:
    def _script(self):
        outputs = []
        for _ in range(2):
            obs, sink = _service()
            with correlation_scope("fg-det1"):
                obs.emit(operation="a", component="api")
                obs.emit(
                    operation="b", component="persistence", outcome="failure"
                )
                obs.emit(operation="c", component="provider", severity="WARNING")
            outputs.append(tuple(e.to_dict() for e in sink.events()))
        return outputs

    def test_identical_scripts_identical_events(self) -> None:
        first, second = self._script()
        assert first == second

    def test_seq_monotonic_and_gapless(self) -> None:
        obs, sink = _service()
        for i in range(5):
            obs.emit(operation=f"op{i}", component="api")
        assert [e.seq for e in sink.events()] == [1, 2, 3, 4, 5]

    def test_timestamps_from_injected_clock(self) -> None:
        obs, sink = _service()
        obs.emit(operation="op", component="api")
        assert sink.events()[0].timestamp == "2026-10-09T00:00:00+00:00"

    def test_to_dict_sorted_key_deterministic(self) -> None:
        event = ForgeEvent(environment="test", timestamp="t")
        assert json.dumps(event.to_dict(), sort_keys=True) == json.dumps(
            event.to_dict(), sort_keys=True
        )


# ---------------------------------------------------------------------------
# 6-8 + J1-J4 + N2: redaction & minimization
# ---------------------------------------------------------------------------


class TestRedaction:
    def test_secret_patterns_scrubbed(self) -> None:
        for secret in (SENTINEL_SECRET, SENTINEL_TOKEN, SENTINEL_CREDENTIAL):
            assert secret not in scrub_text(f"leaked {secret} here")

    def test_bearer_header_scrubbed(self) -> None:
        assert "tok3n1234567890abcd" not in scrub_text(
            "Authorization: Bearer tok3n1234567890abcd"
        )

    def test_secret_attribute_never_reaches_sink(self) -> None:
        obs, sink = _service()
        obs.emit(
            operation="op",
            component="api",
            attributes={"note": f"header {SENTINEL_CREDENTIAL}"},
        )
        assert SENTINEL_CREDENTIAL not in json.dumps(sink.events()[0].to_dict())

    def test_session_token_attribute_never_reaches_sink(self) -> None:
        obs, sink = _service()
        obs.emit(
            operation="op",
            component="identity",
            attributes={"session": SENTINEL_TOKEN},
        )
        assert SENTINEL_TOKEN not in json.dumps(sink.events()[0].to_dict())

    def test_protected_body_omitted_not_carried(self) -> None:
        obs, sink = _service()
        obs.emit(
            operation="op",
            component="retrieval",
            attributes={"body": SENTINEL_PROTECTED_BODY},
        )
        value = sink.events()[0].attributes["body"]
        serialized = json.dumps(sink.events()[0].to_dict())
        # Oversized values are OMITTED entirely — no prefix of a protected
        # body ever reaches a sink.
        assert "PROTECTED_CORPUS_BODY" not in serialized
        assert value.startswith("[truncated]")
        assert len(value) < MAX_ATTRIBUTE_VALUE_LENGTH

    def test_log_sink_lines_redacted(self) -> None:
        from app.forge.observability.emitter import StructuredLogSink

        records: list[str] = []

        class _Recorder(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record.getMessage())

        log = logging.getLogger("forge.test.redaction")
        handler = _Recorder()
        log.addHandler(handler)
        log.setLevel(logging.DEBUG)
        try:
            obs = ForgeObservabilityService(
                ForgeEventEmitter(
                    environment="test",
                    sinks=(StructuredLogSink(log),),
                    clock=_fixed_clock(),
                ),
                environment="test",
            )
            obs.emit(
                operation="op",
                component="api",
                attributes={
                    "a": SENTINEL_SECRET,
                    "b": SENTINEL_PROTECTED_BODY,
                    "c": SENTINEL_TOKEN,
                    "d": SENTINEL_CREDENTIAL,
                },
            )
        finally:
            log.removeHandler(handler)
        joined = "\n".join(records)
        assert records, "log sink must have produced a line"
        for sentinel in (
            SENTINEL_SECRET,
            SENTINEL_PROTECTED_BODY,
            SENTINEL_TOKEN,
            SENTINEL_CREDENTIAL,
        ):
            assert sentinel not in joined

    def test_pre_emission_law_sink_only_sees_redacted(self) -> None:
        class _RawRecorder(InMemoryEventSink):
            raw_bodies: list[str] = []

            def deliver(self, event: ForgeEvent) -> None:
                # Serialize exactly what THIS sink receives, before any
                # downstream consumer could hide fields.
                _RawRecorder.raw_bodies.append(
                    json.dumps(event.to_dict(), default=str)
                )
                super().deliver(event)

        _RawRecorder.raw_bodies = []
        sink = _RawRecorder()
        obs = ForgeObservabilityService(
            ForgeEventEmitter(
                environment="test", sinks=(sink,), clock=_fixed_clock()
            ),
            environment="test",
        )
        obs.emit(
            operation="op",
            component="api",
            attributes={
                "leak": SENTINEL_SECRET,
                "body": SENTINEL_PROTECTED_BODY,
                "session": SENTINEL_TOKEN,
            },
        )
        raw = _RawRecorder.raw_bodies[0]
        for sentinel in (SENTINEL_SECRET, SENTINEL_PROTECTED_BODY, SENTINEL_TOKEN):
            assert sentinel not in raw

    def test_diagnostics_never_carry_event_payloads(self) -> None:
        obs, _ = _service()
        obs.emit(
            operation="op",
            component="api",
            attributes={"secret": SENTINEL_SECRET},
        )
        assert SENTINEL_SECRET not in json.dumps(obs.snapshot(), default=str)

    def test_audit_records_carry_no_content(self) -> None:
        obs, _ = _service()
        obs.record_retrieval_access(
            principal_id="u1",
            service="forge-retrieval",
            capability="read_evidence",
            canonical_object_ids=("EV.1",),
            exposure="RESEARCH_LAB",
            decision="DENY",
        )
        serialized = json.dumps(
            [r.to_dict() for r in obs.retrieval_audit_records()], default=str
        )
        assert "content" not in serialized
        assert "body" not in serialized
        assert "text" not in serialized


# ---------------------------------------------------------------------------
# 5: bounded diagnostics
# ---------------------------------------------------------------------------


class TestBoundedDiagnostics:
    def test_sink_capacity_bounds_events(self) -> None:
        sink = InMemoryEventSink(capacity=3)
        obs = ForgeObservabilityService(
            ForgeEventEmitter(environment="test", sinks=(sink,)),
            environment="test",
        )
        for i in range(10):
            obs.emit(operation=f"op{i}", component="api")
        assert len(sink.events()) == 3

    def test_snapshot_counters_deterministic(self) -> None:
        obs, _ = _service()
        obs.emit(operation="op", component="api")
        snap = obs.snapshot()
        assert snap["events_recorded"] == 1
        assert snap["dropped_events"] == 0
        assert snap["rejected_events"] == 0
        assert "counters" in snap["metrics"]

    def test_audit_trail_capacity_evicts_oldest(self) -> None:
        trail: BoundedAuditTrail = BoundedAuditTrail(capacity=3)
        for i in range(5):
            trail.append(i)
        assert trail.records() == (2, 3, 4)


# ---------------------------------------------------------------------------
# 9-10 + L1-L2 + N1: security audit (II.4 reuse, allow and deny)
# ---------------------------------------------------------------------------


class TestSecurityAudit:
    def test_deny_decision_produces_content_free_audit_record(self) -> None:
        service = ForgePolicyEnforcementService(DefaultDenyPolicyEngine())
        denied = service.authorize(
            _principal(),
            AuthorizationContext(),
            PolicyAction.VIEW,
            _resource(ProductExposure.RESEARCH_LAB),
            correlation_id="fg-audit1",
        )
        assert not denied.allowed
        records = service.audit_records()
        assert len(records) == 1
        record = records[0]
        assert record.correlation_id == "fg-audit1"
        assert record.allowed is False
        serialized = json.dumps(record.__dict__, default=str)
        for sentinel in (SENTINEL_SECRET, SENTINEL_PROTECTED_BODY):
            assert sentinel not in serialized

    def test_allow_decision_audited(self) -> None:
        obs, sink = _service()
        obs.record_policy_decision(
            PolicyAuditRecord(
                correlation_id="fg-audit2",
                principal_id="u1",
                authenticated=True,
                action="VIEW",
                resource_type="CANONICAL_OBJECT",
                resource_id="EV.TEST.V1",
                exposure="PUBLIC_TEACHING",
                allowed=True,
                reason_code="GRANTED",
                at="t",
            )
        )
        events = tuple(e for e in sink.events() if e.stream == "security_audit")
        assert len(events) == 1
        assert events[0].outcome == "success"
        assert events[0].component == "policy"
        assert events[0].request_id == "fg-audit2"
        assert obs.metrics.counter("policy_allow_total") == 1.0

    def test_deny_increments_deny_counter(self) -> None:
        obs, _ = _service()
        obs.record_policy_decision(
            PolicyAuditRecord(
                correlation_id="fg-audit3",
                principal_id="u1",
                authenticated=True,
                action="VIEW",
                resource_type="CANONICAL_OBJECT",
                resource_id="EV.X",
                exposure="RESEARCH_LAB",
                allowed=False,
                reason_code="EXPOSURE_FORBIDDEN",
                at="t",
            )
        )
        assert obs.metrics.counter("policy_deny_total") == 1.0
        assert obs.metrics.counter("policy_allow_total") == 0.0

    def test_four_streams_structurally_separate(self) -> None:
        obs, sink = _service()
        obs.emit(operation="did", component="api")  # telemetry
        obs.record_policy_decision(
            PolicyAuditRecord(
                correlation_id="c", principal_id="u", authenticated=True,
                action="VIEW", resource_type="CANONICAL_OBJECT",
                resource_id="EV", exposure="PUBLIC_TEACHING", allowed=True,
                reason_code="GRANTED", at="t",
            )
        )  # security_audit
        obs.record_usage(provider_type="llm", provider_name="fake")  # usage
        obs.record_entitlement_event(  # entitlement
            event_type="grant", principal_id="u", entitlement_id="ent1"
        )
        streams = {e.stream for e in sink.events()}
        assert streams == {
            "telemetry", "security_audit", "usage_ledger", "entitlement_audit",
        }
        assert all(e.stream in STREAMS for e in sink.events())

    def test_no_second_policy_engine_exists(self) -> None:
        root = Path(__file__).resolve().parents[1] / "app" / "forge" / "observability"
        for path in root.glob("*.py"):
            source = path.read_text(encoding="utf-8")
            assert "decide(" not in source, f"{path.name} contains decision logic"
            assert "PolicyEngine" not in source, f"{path.name} imports an engine"

    def test_reconstructable_from_audit_metadata(self) -> None:
        """Acceptance N1: protected access reconstructable from metadata."""

        obs, _ = _service()
        obs.record_policy_decision(
            PolicyAuditRecord(
                correlation_id="fg-recon1",
                principal_id="u1",
                authenticated=True,
                action="VIEW",
                resource_type="CANONICAL_OBJECT",
                resource_id="EV.RECON.V1",
                exposure="RESEARCH_LAB",
                allowed=True,
                reason_code="GRANTED",
                at="2026-10-09T00:00:00+00:00",
            )
        )
        obs.record_retrieval_access(
            principal_id="u1",
            service="forge-retrieval",
            capability="read_evidence",
            canonical_object_ids=("EV.RECON.V1",),
            retrieval_object_ids=("RO.1",),
            exposure="RESEARCH_LAB",
            decision="ALLOW",
            correlation_id="fg-recon1",
        )
        retrieval = obs.retrieval_audit_records()[0]
        assert retrieval.principal_id == "u1"
        assert retrieval.service == "forge-retrieval"
        assert retrieval.capability == "read_evidence"
        assert retrieval.canonical_object_ids == ("EV.RECON.V1",)
        assert retrieval.retrieval_object_ids == ("RO.1",)
        assert retrieval.exposure == "RESEARCH_LAB"
        assert retrieval.decision == "ALLOW"
        assert retrieval.correlation_id == "fg-recon1"
        assert retrieval.at == "2026-10-09T00:00:00+00:00"


# ---------------------------------------------------------------------------
# E: retrieval access audit (Ch II.6.5)
# ---------------------------------------------------------------------------


class TestRetrievalAccessAudit:
    def test_record_fields(self) -> None:
        obs, _ = _service()
        record = obs.record_retrieval_access(
            principal_id="u1",
            service="forge-retrieval",
            capability="read_evidence",
            canonical_object_ids=("EV.1", "EV.2"),
            retrieval_object_ids=("RO.1",),
            exposure="INTERNAL_METHOD",
            decision="ALLOW",
            correlation_id="fg-ra1",
        )
        data = record.to_dict()
        assert data["kind"] == "retrieval_access"
        assert data["canonical_object_ids"] == ["EV.1", "EV.2"]
        assert data["retrieval_object_ids"] == ["RO.1"]
        assert data["decision"] == "ALLOW"

    def test_invalid_decision_refused(self) -> None:
        with pytest.raises(ValueError):
            RetrievalAccessAuditRecord(
                correlation_id="c", principal_id="u", service="s",
                capability="cap", decision="MAYBE",
            )

    def test_too_many_object_ids_refused(self) -> None:
        with pytest.raises(ValueError):
            RetrievalAccessAuditRecord(
                correlation_id="c", principal_id="u", service="s",
                capability="cap", decision="ALLOW",
                canonical_object_ids=tuple(f"EV.{i}" for i in range(33)),
            )

    def test_allow_counts_retrieval_metric(self) -> None:
        obs, _ = _service()
        obs.record_retrieval_access(
            principal_id="u1", service="s", capability="cap",
            canonical_object_ids=("EV.1", "EV.2"), decision="ALLOW",
        )
        assert obs.metrics.counter("retrieval_objects_total") == 2.0

    def test_denied_access_records_ids_only(self) -> None:
        obs, _ = _service()
        record = obs.record_retrieval_access(
            principal_id="u1", service="s", capability="cap",
            canonical_object_ids=(), decision="DENY",
        )
        assert record.decision == "DENY"
        assert record.canonical_object_ids == ()


# ---------------------------------------------------------------------------
# F: entitlement audit (Ch II.6.6)
# ---------------------------------------------------------------------------


class TestEntitlementAudit:
    def test_frozen_vocabulary(self) -> None:
        assert ENTITLEMENT_EVENT_TYPES == (
            "grant", "renew", "grace", "expire", "revoke", "admin_correction",
        )
        obs, _ = _service()
        for event_type in ENTITLEMENT_EVENT_TYPES:
            record = obs.record_entitlement_event(
                event_type=event_type,
                principal_id="u1",
                entitlement_id="ent1",
            )
            assert record.event_type == event_type

    def test_unknown_event_refused(self) -> None:
        obs, _ = _service()
        with pytest.raises(ValueError):
            obs.record_entitlement_event(
                event_type="steal", principal_id="u1", entitlement_id="ent1"
            )

    def test_source_event_and_provider_mapping_recorded(self) -> None:
        obs, _ = _service()
        record = obs.record_entitlement_event(
            event_type="grant",
            principal_id="u1",
            entitlement_id="ent1",
            source_event_id="evt-42",
            provider_type="commerce",
            provider_name="fake",
        )
        data = record.to_dict()
        assert data["source_event_id"] == "evt-42"
        assert data["provider_type"] == "commerce"
        assert data["provider_name"] == "fake"

    def test_no_mutation_authority_on_record_type(self) -> None:
        import dataclasses

        fields = {
            f.name for f in dataclasses.fields(EntitlementAuditRecord)
        }
        assert fields == {
            "at", "correlation_id", "entitlement_id", "event_type",
            "principal_id", "provider_name", "provider_type",
            "source_event_id",
        }
        public = {
            name for name in dir(EntitlementAuditRecord)
            if not name.startswith("_")
        }
        # The record type exposes only its frozen fields plus to_dict():
        # no setters, no apply(), no transition methods (records-only law).
        assert public - fields == {"to_dict"}

    def test_reconstructable_entitlement_sequence(self) -> None:
        """Acceptance N1: entitlement mutations reconstructable in order."""

        obs, _ = _service()
        for event_type in ("grant", "renew", "revoke"):
            obs.record_entitlement_event(
                event_type=event_type,
                principal_id="u1",
                entitlement_id="ent1",
                source_event_id=f"evt-{event_type}",
            )
        records = obs.entitlement_audit_records()
        assert [r.event_type for r in records] == ["grant", "renew", "revoke"]
        assert [r.source_event_id for r in records] == [
            "evt-grant", "evt-renew", "evt-revoke",
        ]

    def test_entitlement_events_increment_commerce_counter(self) -> None:
        obs, _ = _service()
        obs.record_entitlement_event(
            event_type="grant", principal_id="u1", entitlement_id="e"
        )
        assert obs.metrics.counter("commerce_events_total") == 1.0


# ---------------------------------------------------------------------------
# G-H + N3/N4: error contract (Ch II.6.7 / II.6.8)
# ---------------------------------------------------------------------------


class TestErrorContract:
    def test_exact_nine_class_taxonomy(self) -> None:
        assert ERROR_CLASSES == (
            "AUTHENTICATION", "AUTHORIZATION", "VALIDATION", "NOT_FOUND",
            "CONFLICT", "RATE_LIMIT", "DEPENDENCY", "DATA_INTEGRITY",
            "INTERNAL",
        )

    def test_provider_mapping_exact_and_total(self) -> None:
        assert set(PROVIDER_FAILURE_TO_ERROR_CLASS) == set(FAILURE_CLASSES)
        assert PROVIDER_FAILURE_TO_ERROR_CLASS == {
            "unavailable": ForgeErrorClass.DEPENDENCY,
            "timeout": ForgeErrorClass.DEPENDENCY,
            "rate_limited": ForgeErrorClass.RATE_LIMIT,
            "invalid_request": ForgeErrorClass.VALIDATION,
            "authentication_failed": ForgeErrorClass.AUTHENTICATION,
            "upstream_rejected": ForgeErrorClass.DEPENDENCY,
            "malformed_response": ForgeErrorClass.DATA_INTEGRITY,
            "unknown": ForgeErrorClass.DEPENDENCY,
        }

    def test_provider_error_retains_origin(self) -> None:
        exc = ProviderTimeoutError(
            "upstream timed out after 10s (details)",
            provider_type="llm",
            provider_name="fake",
        )
        mapped = from_provider_error(exc, request_id="fg-e1")
        assert mapped.origin == "provider"
        assert mapped.provider_failure_class == "timeout"
        assert mapped.provider_type == "llm"
        assert mapped.error_class is ForgeErrorClass.DEPENDENCY
        assert mapped.request_id == "fg-e1"

    def test_application_error_origin_distinct(self) -> None:
        provider = from_provider_error(
            ProviderTimeoutError(
                "t", provider_type="llm", provider_name="fake"
            )
        )
        application = from_exception(RuntimeError("boom"))
        assert provider.origin == "provider"
        assert application.origin == "application"
        assert provider.error_class is not application.error_class

    def test_safe_response_shape(self) -> None:
        exc = ForgeApplicationErrorForTest()
        body = safe_error_response(exc)
        assert set(body) == {"code", "message", "request_id"}
        assert body["code"] == "FORGE_DEPENDENCY"
        assert body["message"] == SAFE_MESSAGES[ForgeErrorClass.DEPENDENCY]
        assert body["request_id"] == "fg-e2"

    def test_no_internals_or_payloads_in_responses(self) -> None:
        dangerous = ProviderAuthenticationFailedError(
            f"401 from https://api.example/v1?token={SENTINEL_SECRET}",
            provider_type="commerce",
            provider_name="fake",
        )
        body = from_provider_error(dangerous).safe_response()
        serialized = json.dumps(body)
        assert SENTINEL_SECRET not in serialized
        assert "401" not in serialized
        assert "https" not in serialized
        assert "Traceback" not in serialized

    def test_exception_text_never_carried(self) -> None:
        class Weird(Exception):
            def __str__(self) -> str:
                return f"SQL error near {SENTINEL_SECRET}"

        classified = from_exception(Weird(), request_id="fg-e3")
        assert classified.error_class is ForgeErrorClass.INTERNAL
        assert SENTINEL_SECRET not in json.dumps(classified.safe_response())

    def test_provider_vs_application_distinguishable(self) -> None:
        """Acceptance N3."""

        provider = from_provider_error(
            ProviderUnknownError(
                "mystery", provider_type="llm", provider_name="fake"
            ),
            request_id="fg-x",
        )
        application = from_exception(RuntimeError("boom"), request_id="fg-x")
        assert provider.origin == "provider"
        assert application.origin == "application"
        assert provider.safe_response()["code"] == "FORGE_DEPENDENCY"
        assert application.safe_response()["code"] == "FORGE_INTERNAL"

    def test_codes_stable_and_prefixed(self) -> None:
        for cls in ForgeErrorClass:
            assert ERROR_CODES[cls] == f"FORGE_{cls.value}"

    def test_request_id_connects_error_to_trace(self) -> None:
        """Acceptance N4."""

        obs, sink = _service()
        with correlation_scope("fg-trace1"):
            exc = ProviderTimeoutError(
                "timeout", provider_type="llm", provider_name="fake"
            )
            mapped = from_provider_error(
                exc, request_id=effective_request_id()
            )
            obs.emit(
                severity="ERROR",
                component="provider",
                operation="llm.generate",
                outcome="failure",
                error_class=mapped.error_class.value,
                provider_failure_class="timeout",
            )
        body = mapped.safe_response()
        emitted = sink.events()[0]
        assert body["request_id"] == emitted.request_id == "fg-trace1"

    def test_safe_message_table_covers_all_classes(self) -> None:
        for cls in ForgeErrorClass:
            assert SAFE_MESSAGES[cls]
            assert isinstance(SAFE_MESSAGES[cls], str)


def ForgeApplicationErrorForTest():
    from app.forge.observability.errors import ForgeApplicationError

    return ForgeApplicationError(
        ForgeErrorClass.DEPENDENCY,
        request_id="fg-e2",
        origin="provider",
        provider_type="commerce",
        provider_name="fake",
        provider_failure_class="unavailable",
    )


# ---------------------------------------------------------------------------
# I: cost/usage ledger (Ch II.6.9)
# ---------------------------------------------------------------------------


class TestUsageLedger:
    def test_full_record(self) -> None:
        obs, _ = _service()
        record = obs.record_usage(
            provider_type="llm",
            provider_name="fake",
            request_id="fg-u1",
            model_id="fake-model-1",
            input_tokens=100,
            output_tokens=50,
            normalized_cost=0.002,
            latency_ms=12.5,
            success=True,
        )
        data = record.to_dict()
        assert data["request_id"] == "fg-u1"
        assert data["model_id"] == "fake-model-1"
        assert data["input_tokens"] == 100
        assert data["output_tokens"] == 50
        assert data["normalized_cost"] == 0.002
        assert data["latency_ms"] == 12.5
        assert data["success"] is True

    def test_partial_data_stays_none_never_fabricated(self) -> None:
        obs, _ = _service()
        record = obs.record_usage(
            provider_type="llm", provider_name="fake", success=False
        )
        assert record.input_tokens is None
        assert record.output_tokens is None
        assert record.normalized_cost is None
        assert record.success is False

    def test_usage_feeds_llm_metrics_only_when_supplied(self) -> None:
        obs, _ = _service()
        obs.record_usage(
            provider_type="llm", provider_name="fake",
            input_tokens=10, output_tokens=5, normalized_cost=0.01,
        )
        obs.record_usage(provider_type="llm", provider_name="fake")
        assert obs.metrics.counter("llm_input_tokens_total") == 10.0
        assert obs.metrics.counter("llm_output_tokens_total") == 5.0
        assert obs.metrics.counter("llm_cost_normalized_total") == 0.01

    def test_ledger_exposes_no_totals_or_balance_semantics(self) -> None:
        public = {n for n in dir(UsageLedger) if not n.startswith("_")}
        assert public == {"append", "records"}

    def test_negative_values_refused(self) -> None:
        with pytest.raises(ValueError):
            UsageRecord(
                request_id="r", provider_type="llm", provider_name="fake",
                input_tokens=-1,
            )
        with pytest.raises(ValueError):
            UsageRecord(
                request_id="r", provider_type="llm", provider_name="fake",
                normalized_cost=-0.1,
            )

    def test_records_append_bounded(self) -> None:
        obs, _ = _service()
        for _ in range(3):
            obs.record_usage(provider_type="llm", provider_name="fake")
        assert len(obs.usage_records()) == 3


# ---------------------------------------------------------------------------
# 11-14 + M1: provider observability & masquerade law
# ---------------------------------------------------------------------------


class TestProviderObservability:
    def _llm_call(self, behavior: FakeBehavior):
        fake = FakeLLMProvider(behavior=behavior, clock=SimulatedClock())
        request = LLMRequest(prompt="p", model="fake-model-1")

        def call():
            return fake.generate(request, timeout_seconds=5.0)

        return call

    def test_timeout_emits_classified_failure_event(self) -> None:
        obs, sink = _service()
        with pytest.raises(ProviderTimeoutError):
            _observe(
                obs,
                self._llm_call(FakeBehavior(failure_class="timeout")),
                port="llm", provider_type="llm", provider_name="fake",
                request_id="fg-p1",
            )
        events = [e for e in sink.events() if e.component == "provider"]
        assert events[0].outcome == "failure"
        assert events[0].error_class == "DEPENDENCY"
        assert events[0].provider_failure_class == "timeout"
        assert events[0].request_id == "fg-p1"
        assert obs.metrics.counter("provider_errors_total") == 1.0

    def test_rate_limit_counts_rate_limit_metric(self) -> None:
        obs, sink = _service()
        with pytest.raises(ProviderRateLimitedError):
            _observe(
                obs,
                self._llm_call(
                    FakeBehavior(
                        failure_class="rate_limited",
                        rate_limit_retry_after=5.0,
                    )
                ),
                port="llm", provider_type="llm", provider_name="fake",
            )
        assert obs.metrics.counter("provider_rate_limited_total") == 1.0
        events = [e for e in sink.events() if e.component == "provider"]
        assert events[0].error_class == "RATE_LIMIT"

    def test_circuit_open_short_circuits_and_is_observable(self) -> None:
        obs, sink = _service()
        clock = SimulatedClock()
        breaker = CircuitBreaker(
            name="llm", failure_threshold=2, recovery_seconds=30,
            clock=clock.now,
        )
        fake = FakeLLMProvider(
            behavior=FakeBehavior(failure_class="unavailable"), clock=clock
        )
        request = LLMRequest(prompt="p", model="fake-model-1")

        def call():
            return _observe(
                obs,
                lambda: breaker.call(
                    lambda: fake.generate(request, timeout_seconds=5.0)
                ),
                port="llm", provider_type="llm", provider_name="fake",
                request_id="fg-p2", clock=clock.now,
            )

        for _ in range(3):
            with pytest.raises(ProviderUnavailableError):
                call()
        events = [e for e in sink.events() if e.component == "provider"]
        assert len(events) == 3
        assert all(e.outcome == "failure" for e in events)
        assert breaker.state.value == "open"

    def test_recovery_emits_success_event(self) -> None:
        obs, sink = _service()
        clock = SimulatedClock()
        breaker = CircuitBreaker(
            name="llm", failure_threshold=1, recovery_seconds=10,
            clock=clock.now,
        )
        results: list[str] = []
        for behavior in (
            FakeBehavior(failure_class="unavailable"),
            FakeBehavior(),
        ):
            fake = FakeLLMProvider(behavior=behavior, clock=clock)
            request = LLMRequest(prompt="p", model="fake-model-1")
            try:
                _observe(
                    obs,
                    lambda: breaker.call(
                        lambda: fake.generate(request, timeout_seconds=5.0)
                    ),
                    port="llm", provider_type="llm", provider_name="fake",
                    request_id="fg-p3", clock=clock.now,
                )
                results.append("success")
            except ProviderError as exc:
                results.append(f"failure:{exc.failure_class}")
            clock.advance(15)
        assert results == ["failure:unavailable", "success"]
        events = [e for e in sink.events() if e.component == "provider"]
        assert [e.outcome for e in events] == ["failure", "success"]
        assert events[-1].error_class == ""
        assert breaker.state.value == "closed"

    def test_failure_never_swallowed_by_observer(self) -> None:
        obs, _ = _service()
        with pytest.raises(ProviderUnavailableError):
            _observe(
                obs,
                self._llm_call(
                    FakeBehavior(failure_class="unavailable")
                ),
                port="llm", provider_type="llm", provider_name="fake",
            )

    def test_success_emits_success_event_and_latency(self) -> None:
        obs, sink = _service()
        _observe(
            obs,
            self._llm_call(FakeBehavior()),
            port="llm", provider_type="llm", provider_name="fake",
        )
        events = [e for e in sink.events() if e.component == "provider"]
        assert events[0].outcome == "success"
        assert events[0].duration_ms is not None
        assert (
            obs.metrics.snapshot()["histograms"]["provider_latency_ms"]["count"]
            == 1
        )

    def test_provider_failure_cannot_masquerade_as_authorization(self) -> None:
        engine = DefaultDenyPolicyEngine()
        context = AuthorizationContext()
        resource = _resource(ProductExposure.PUBLIC_TEACHING)
        healthy = engine.decide(_principal(), context, PolicyAction.VIEW, resource)
        obs, _ = _service()
        with pytest.raises(ProviderError):
            _observe(
                obs,
                self._llm_call(FakeBehavior(failure_class="unavailable")),
                port="llm", provider_type="llm", provider_name="fake",
            )
        degraded = engine.decide(_principal(), context, PolicyAction.VIEW, resource)
        assert healthy.allowed == degraded.allowed
        assert healthy.reason_code == degraded.reason_code

    def test_provider_failure_cannot_masquerade_as_canonical_write(self) -> None:
        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_evidence_record("EV.PRE.V1"))
        before = gateway.list_object_ids()
        obs, _ = _service()
        with pytest.raises(ProviderError):
            _observe(
                obs,
                self._llm_call(FakeBehavior(failure_class="unavailable")),
                port="llm", provider_type="llm", provider_name="fake",
            )
        assert gateway.list_object_ids() == before

    def test_provider_failure_cannot_masquerade_as_healthy_capability(
        self,
    ) -> None:
        config = ForgeConfig(environment="test")
        healthy = ForgeServiceContainer(
            config=config,
            providers=providers_from_config(config),
            observability=_service()[0],
        )
        broken_registry = ProviderRegistry()
        source = providers_from_config(config)
        for port in PORTS:
            impl = (
                FakeLLMProvider(
                    behavior=FakeBehavior(failure_class="unavailable")
                )
                if port == "llm"
                else source.get(port)
            )
            broken_registry.register(port, "fake", impl)
        broken_registry.freeze()
        broken = ForgeServiceContainer(
            config=config,
            providers=broken_registry,
            observability=_service()[0],
        )
        healthy_deps = healthy.as_readiness_dependencies()
        broken_deps = broken.as_readiness_dependencies()
        assert healthy_deps["llm"]["status"] == "READY"
        assert broken_deps["llm"]["status"] == "UNAVAILABLE"
        # The overall readiness stays honest: a provider outage is disclosed,
        # never a fabricated READY and never a hidden failure.
        assert broken_deps["llm"]["required"] is False

    def test_commerce_outage_never_yields_success_result(self) -> None:
        obs, sink = _service()
        outage = FakeCommerceProvider(
            behavior=FakeBehavior(failure_class="unavailable")
        )
        result = None
        with pytest.raises(ProviderError):
            result = _observe(
                obs,
                lambda: outage.get_subscription("sub-1"),
                port="commerce", provider_type="commerce",
                provider_name="fake",
            )
        # No success-shaped object was ever constructed from the failure.
        assert result is None
        events = [e for e in sink.events() if e.component == "provider"]
        assert events and events[0].outcome == "failure"
        assert events[0].attributes["port"] == "commerce"


# ---------------------------------------------------------------------------
# 15-22: failure matrix
# ---------------------------------------------------------------------------


class TestFailureMatrix:
    def test_persistence_failure_observed(self) -> None:
        config = ForgeConfig(environment="test")
        container = ForgeServiceContainer(
            config=config,
            persistence=_PingDownGateway(),
            observability=_service()[0],
        )
        context = ForgeLifecycle(container).startup()
        assert context["started"] is True
        deps = container.as_readiness_dependencies()
        assert deps["postgresql"]["status"] == "UNAVAILABLE"
        assert deps["postgresql"]["required"] is True

    def test_canonical_write_rejection_observed(self) -> None:
        from app.forge.observability.errors import ForgeApplicationError
        from app.forge.persistence.port import DuplicateCanonicalObject

        gateway = InMemoryPersistenceGateway()
        gateway.create_object(_evidence_record("EV.DUP.V1"))
        obs, sink = _service()
        try:
            gateway.create_object(_evidence_record("EV.DUP.V1"))
        except DuplicateCanonicalObject as exc:
            classified = from_exception(exc)
            obs.emit(
                severity="WARNING",
                component="persistence",
                operation="canonical.write",
                outcome="failure",
                error_class=ForgeApplicationError(
                    ForgeErrorClass.DATA_INTEGRITY
                ).error_class.value,
                reason_code="DUPLICATE_CANONICAL_OBJECT",
            )
            del classified
        events = [e for e in sink.events() if e.component == "persistence"]
        assert events[0].outcome == "failure"
        assert events[0].error_class == "DATA_INTEGRITY"

    def test_qa_abstention_observed_as_outcome(self) -> None:
        """Item 17: abstention is a first-class successful observation."""

        obs, sink = _service()
        obs.emit(
            severity="INFO",
            component="retrieval",
            operation="qa.answer",
            outcome="success",
            reason_code="ABSTAIN",
            object_type="question",
        )
        events = [e for e in sink.events() if e.component == "retrieval"]
        assert events[0].outcome == "success"
        assert events[0].reason_code == "ABSTAIN"

    def test_qa_unsupported_answer_observed(self) -> None:
        from app.forge.qa.contract import AnswerOutcome

        assert AnswerOutcome.UNSUPPORTED.value == "UNSUPPORTED"
        obs, sink = _service()
        obs.emit(
            severity="INFO",
            component="retrieval",
            operation="qa.answer",
            outcome="success",
            reason_code=AnswerOutcome.UNSUPPORTED.value,
        )
        events = [e for e in sink.events() if e.component == "retrieval"]
        assert events[0].reason_code == "UNSUPPORTED"

    def test_health_degradation_emits_degraded_route_event(self) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.forge.service.routes import create_forge_router

        config = ForgeConfig(environment="test")
        obs, sink = _service()
        container = ForgeServiceContainer(
            config=config,
            persistence=_PingDownGateway(),
            observability=obs,
        )
        ForgeLifecycle(container).startup()
        app = FastAPI()
        app.include_router(create_forge_router(config=config, container=container))
        client = TestClient(app)
        response = client.get(
            "/forge/v1/ready", headers={"X-Request-Id": "fg-ready1"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "not_ready"
        events = [
            e for e in sink.events()
            if e.operation == "GET /forge/v1/ready"
        ]
        assert events and events[0].outcome == "degraded"
        assert events[0].request_id == "fg-ready1"

    def test_missing_correlation_context_is_disclosed_not_crashed(
        self,
    ) -> None:
        obs, sink = _service()
        obs.emit(operation="orphan", component="api")
        assert sink.events()[0].request_id == UNATTRIBUTED
        assert effective_request_id() == UNATTRIBUTED

    def test_malformed_event_refused_and_counted(self) -> None:
        obs, sink = _service()
        result = obs.emit(operation="op", component="api", severity="LOUD")
        assert result is None  # safe_emit refuses deterministically
        assert obs.snapshot()["rejected_events"] == 1
        assert sink.events() == ()

    def test_unknown_error_classified_internal(self) -> None:
        classified = from_exception(Exception("mystery explosion"))
        assert classified.error_class is ForgeErrorClass.INTERNAL
        assert classified.origin == "application"
        assert classified.safe_response()["message"] == "internal service error"

    def test_failing_sink_never_breaks_caller(self) -> None:
        class _ExplodingSink:
            def deliver(self, event):
                raise RuntimeError("sink down")

        obs = ForgeObservabilityService(
            ForgeEventEmitter(
                environment="test", sinks=(_ExplodingSink(),),
                clock=_fixed_clock(),
            ),
            environment="test",
        )
        obs.emit(operation="op", component="api")  # must not raise
        assert obs.snapshot()["dropped_events"] == 1


# ---------------------------------------------------------------------------
# 23-24: no logging-induced authorization change / canonical mutation
# ---------------------------------------------------------------------------


class TestSecurityInvariants:
    def test_no_logging_induced_authorization_change(self) -> None:
        engine = DefaultDenyPolicyEngine()
        context = AuthorizationContext()
        resource = _resource(ProductExposure.RESEARCH_LAB)

        unobserved = engine.decide(
            _principal(), context, PolicyAction.VIEW, resource
        )

        obs, _ = _service()
        enforcement = ForgePolicyEnforcementService(engine)
        observed = enforcement.authorize(
            _principal(), context, PolicyAction.VIEW, resource,
            correlation_id="fg-obs",
        )
        obs.record_policy_decision(enforcement.audit_records()[0])
        second = enforcement.authorize(
            _principal(), context, PolicyAction.VIEW, resource,
            correlation_id="fg-obs2",
        )
        assert unobserved.allowed == observed.allowed == second.allowed
        assert (
            unobserved.reason_code
            == observed.reason_code
            == second.reason_code
        )

    def test_no_logging_induced_canonical_mutation(self) -> None:
        unobserved_gateway = InMemoryPersistenceGateway()
        unobserved_gateway.create_object(_evidence_record("EV.OBS.V1"))

        observed_gateway = InMemoryPersistenceGateway()
        observed_gateway.create_object(_evidence_record("EV.OBS.V1"))
        obs, _ = _service()
        obs.emit(
            operation="canonical.write",
            component="persistence",
            outcome="success",
            object_id="EV.OBS.V1",
        )

        def snapshot(gateway):
            record = gateway.get_object("EV.OBS.V1")
            assert record is not None
            return (record.canonical_id, record.status, record.version)

        assert snapshot(unobserved_gateway) == snapshot(observed_gateway)


# ---------------------------------------------------------------------------
# 25: no telemetry dependency required for core execution
# ---------------------------------------------------------------------------


class TestNoTelemetryDependency:
    def test_forge_endpoints_work_without_observability(self) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.forge.service.routes import create_forge_router

        config = ForgeConfig(environment="test")
        container = ForgeServiceContainer(config=config)  # observability=None
        assert container.observability is None
        app = FastAPI()
        app.include_router(
            create_forge_router(config=config, container=container)
        )
        client = TestClient(app)
        for path in ("/forge/v1/health", "/forge/v1/ready", "/forge/v1/meta"):
            assert client.get(path).status_code == 200

    def test_readiness_honest_when_unwired(self) -> None:
        container = ForgeServiceContainer(config=ForgeConfig(environment="test"))
        deps = container.as_readiness_dependencies()
        assert deps["observability"] == {
            "status": "NOT_CONFIGURED",
            "required": False,
            "note": (
                "observability not wired; FORGE serves without telemetry (II.6)"
            ),
        }
        from app.forge.service.health import ForgeHealthService

        assert ForgeHealthService(container).readiness()["status"] == "ready"


# ---------------------------------------------------------------------------
# K: container integration & config
# ---------------------------------------------------------------------------


class TestContainerIntegration:
    def test_seam_rejects_foreign_objects(self) -> None:
        with pytest.raises(TypeError, match="ForgeObservabilityService"):
            ForgeServiceContainer(
                config=ForgeConfig(environment="test"), observability=object()
            )

    def test_seam_accepts_real_service(self) -> None:
        obs, _ = _service()
        container = ForgeServiceContainer(
            config=ForgeConfig(environment="test"), observability=obs
        )
        assert container.observability is obs
        deps = container.as_readiness_dependencies()
        assert deps["observability"]["status"] == "READY"
        assert deps["observability"]["required"] is False

    def test_telemetry_never_blocks_overall_readiness(self) -> None:
        from app.forge.service.health import ForgeHealthService

        for obs in (None, _service()[0]):
            container = ForgeServiceContainer(
                config=ForgeConfig(environment="test"), observability=obs
            )
            assert (
                ForgeHealthService(container).readiness()["status"] == "ready"
            )

    def test_diagnostics_disclose_presence_not_payloads(self) -> None:
        obs, _ = _service()
        obs.emit(
            operation="op", component="api",
            attributes={"k": SENTINEL_SECRET},
        )
        container = ForgeServiceContainer(
            config=ForgeConfig(environment="test"), observability=obs
        )
        diagnostics = container.redacted_diagnostics()
        assert diagnostics["observability_wired"] is True
        assert diagnostics["observability"]["events_recorded"] == 1
        assert SENTINEL_SECRET not in json.dumps(diagnostics, default=str)

    def test_config_flags_fail_closed(self) -> None:
        with pytest.raises(ValueError):
            ForgeConfig(environment="test", observability_event_capacity=0)

    def test_factory_builds_service(self) -> None:
        enabled = observability_from_config(ForgeConfig(environment="test"))
        assert isinstance(enabled, ForgeObservabilityService)

    def test_factory_wiring_emits(self) -> None:
        obs = observability_from_config(
            ForgeConfig(environment="test", observability_log_sinks=False)
        )
        obs.emit(operation="op", component="api")
        assert obs.snapshot()["events_recorded"] == 1

    def test_existing_provider_readiness_regression(self) -> None:
        config = ForgeConfig(environment="test")
        container = ForgeServiceContainer(
            config=config, providers=providers_from_config(config)
        )
        deps = container.as_readiness_dependencies()
        for port in PORTS:
            assert deps[port]["status"] == "READY"
            assert deps[port]["required"] is False
        assert deps["openrouter"]["status"] == "NOT_CONFIGURED"
        assert deps["whop"]["status"] == "NOT_CONFIGURED"


# ---------------------------------------------------------------------------
# D: metrics (Ch II.6.4)
# ---------------------------------------------------------------------------


class TestMetrics:
    def test_frozen_metric_names(self) -> None:
        snapshot = MetricsRegistry().snapshot()
        counters = set(snapshot["counters"])
        assert {
            "requests_total", "request_errors_total", "policy_allow_total",
            "policy_deny_total", "auth_failures_total",
            "retrieval_objects_total", "provider_errors_total",
            "provider_rate_limited_total", "commerce_events_total",
            "job_failures_total",
        } <= counters
        assert "llm_input_tokens_total" in counters
        assert "llm_output_tokens_total" in counters
        assert "llm_cost_normalized_total" in counters
        assert set(snapshot["histograms"]) == {
            "request_latency_ms", "db_latency_ms", "provider_latency_ms",
            "job_lag_ms",
        }
        assert set(snapshot["gauges"]) == {"db_pool_in_use"}

    def test_unknown_metric_refused(self) -> None:
        registry = MetricsRegistry()
        with pytest.raises(ValueError):
            registry.increment("not_a_metric")
        with pytest.raises(ValueError):
            registry.observe("not_a_metric", 1.0)
        with pytest.raises(ValueError):
            registry.set_gauge("not_a_metric", 1.0)

    def test_negative_values_refused(self) -> None:
        registry = MetricsRegistry()
        with pytest.raises(ValueError):
            registry.increment("requests_total", -1)
        with pytest.raises(ValueError):
            registry.observe("request_latency_ms", -1)
        with pytest.raises(ValueError):
            registry.set_gauge("db_pool_in_use", -1)

    def test_histogram_bounded(self) -> None:
        registry = MetricsRegistry()
        for i in range(MAX_HISTOGRAM_SAMPLES + 50):
            registry.observe("request_latency_ms", float(i))
        assert (
            registry.snapshot()["histograms"]["request_latency_ms"]["count"]
            == MAX_HISTOGRAM_SAMPLES
        )

    def test_request_events_increment_request_metrics(self) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.forge.service.routes import create_forge_router

        config = ForgeConfig(environment="test")
        obs, _ = _service()
        container = ForgeServiceContainer(config=config, observability=obs)
        app = FastAPI()
        app.include_router(create_forge_router(config=config, container=container))
        client = TestClient(app)
        client.get("/forge/v1/health")
        client.get("/forge/v1/health")
        assert obs.metrics.counter("requests_total") == 2.0

    def test_snapshot_deterministic_shape(self) -> None:
        registry = MetricsRegistry()
        registry.increment("requests_total")
        registry.observe("request_latency_ms", 1.0)
        registry.set_gauge("db_pool_in_use", 2.0)
        first = json.dumps(registry.snapshot(), sort_keys=True)
        second = json.dumps(registry.snapshot(), sort_keys=True)
        assert first == second


# ---------------------------------------------------------------------------
# Import discipline (AST)
# ---------------------------------------------------------------------------


class TestImportDiscipline:
    def test_observability_imports_no_transport_or_provider_clients(
        self,
    ) -> None:
        root = (
            Path(__file__).resolve().parents[1]
            / "app" / "forge" / "observability"
        )
        forbidden = ("fastapi", "starlette", "httpx", "requests", "psycopg")
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    for bad in forbidden:
                        assert not name.startswith(bad), (
                            f"{path.name} imports {name}"
                        )

    def test_domain_modules_import_no_observability(self) -> None:
        forge = Path(__file__).resolve().parents[1] / "app" / "forge"
        domain_files = [
            forge / "canonical.py",
            forge / "schemas.py",
            forge / "provenance.py",
            forge / "identity.py",
            forge / "policy.py",
            forge / "backfill" / "canonicalizer.py",
            forge / "retrieval" / "service.py",
            forge / "qa" / "kernel.py",
            forge / "persistence" / "memory.py",
        ]
        for path in domain_files:
            source = path.read_text(encoding="utf-8")
            assert "app.forge.observability" not in source, (
                f"{path.name} must not import observability"
            )

    def test_provenance_module_untouched_by_ii6(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "app" / "forge" / "provenance.py"
        ).read_text(encoding="utf-8")
        assert "observability" not in source
        assert "ForgeEvent" not in source
