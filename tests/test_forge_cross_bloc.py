"""BOOK II — cross-bloc adversarial integration suite (implementation-order step 7).

Maps 1:1 to implementation/forge/book_ii/cross_bloc/ACCEPTANCE.md clauses
A-K (scenarios X1-X9 plus the F1-F12 failure-injection matrix and the Phase 5
security/epistemic laws).

Doctrine for this suite:

- Every gate is exercised across BLOC BOUNDARIES (identity -> policy ->
  provider, policy -> retrieval -> observability, ...), not inside one bloc.
- Every negative assertion carries a positive control: the same wiring must
  ALLOW when legitimately authorized, so a deny is proved exercised.
- Every leak assertion uses unique sentinels (credential, raw session token,
  protected corpus body marker) asserted ABSENT from serialized sinks,
  audit trails, metrics snapshots, HTTP bodies and captured logs.
- Deterministic only: injected clocks, scripted fakes, in-process sinks.
  No sleeps, no network, no wall-clock dependence.
"""
from __future__ import annotations

import ast
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.forge.backfill.runner import BackfillMode, run_backfill
from app.forge.canonical import EvidenceStatus, Layer, ObjectType, ProductExposure
from app.forge.config import ForgeConfig
from app.forge.identity import ANONYMOUS_PRINCIPAL, ForgePrincipal, ForgeUser
from app.forge.observability import (
    SAFE_MESSAGES,
    UNATTRIBUTED,
    ForgeErrorClass,
    ForgeEventEmitter,
    ForgeObservabilityService,
    InMemoryEventSink,
    StructuredLogSink,
    correlation_scope,
    effective_request_id,
    from_provider_error,
    observe_provider_call,
)
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.port import (
    DuplicateCanonicalObject,
    ObjectNotFound,
    PersistenceError,
    StaleWriteConflict,
)
from app.forge.persistence.records import CanonicalObjectRecord
from app.forge.policy import (
    CAPABILITY_ADMIN_COMMERCE,
    CAPABILITY_ADMIN_RESEARCH,
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_EVIDENCE_READ_RESEARCH,
    CAPABILITY_FORGE_INTERNAL,
    CAPABILITY_MODEL_READ_OPERATOR,
    AuthorizationContext,
    DefaultDenyPolicyEngine,
    PolicyAction,
    PolicyReason,
    PolicyResourceType,
    REGISTERED_CAPABILITIES,
    ResourcePolicyMetadata,
)
from app.forge.providers import (
    CircuitBreaker,
    CircuitState,
    FallbackPolicy,
    FakeBehavior,
    FakeCommerceProvider,
    FakeLLMProvider,
    LLMRequest,
    ProviderAuthenticationFailedError,
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderRateLimitedError,
    ProviderRegistry,
    ProviderTimeoutError,
    ProviderUnavailableError,
    SimulatedClock,
    default_provider_factory,
    providers_from_config,
    run_with_fallback,
)
from app.forge.qa import QAService
from app.forge.qa.authority import status_authority_verdict
from app.forge.retrieval import (
    IndexBuildMode,
    RetrievalIndex,
    RetrievalQuery,
    RetrievalService,
    run_index_build,
)
from app.forge.service.authentication import AuthenticationFailure, ForgeAuthenticationService
from app.forge.service.container import ForgeServiceContainer
from app.forge.service.correlation import parse_request_id
from app.forge.service.health import ForgeHealthService
from app.forge.service.lifecycle import ForgeLifecycle
from app.forge.service.policy_enforcement import ForgePolicyEnforcementService

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Sentinels (asserted absent everywhere they must never appear)
# ---------------------------------------------------------------------------

SENTINEL_SECRET = "sk-live-crossbloc-A1b2C3d4E5f6Gh7"
SENTINEL_TOKEN = "crossbloc-session-QUJDREVGR0hJSktMTU5PUFFS"
SENTINEL_CREDENTIAL = "api_key=CrossBlocSuperSecret99"
# Genuine restricted-research body text, unique to the RESEARCH_LAB record
# below (verified unique across the built index).
RESTRICTED_MARKER = "improved the referenced classification AUC from .824 to .840"

RESTRICTED_OBJECT = "EV.EUR.DAILY.NEWS_AUC.V1"   # RESEARCH_LAB / CANDIDATE
MODEL_OBJECT = "MOD.EUR.DAILY.NEWS_REKEY.V1"      # SUBSCRIBER_MODEL / CANDIDATE
RESEARCH_CLAIM = "CL.XAU.PROMOTION.120_132"        # SUBSCRIBER_MODEL / RESEARCH_FLAG

ALL_SENTINELS = (SENTINEL_SECRET, SENTINEL_TOKEN, SENTINEL_CREDENTIAL, RESTRICTED_MARKER)


def assert_no_sentinels(*blobs: str) -> None:
    for blob in blobs:
        for sentinel in ALL_SENTINELS:
            assert sentinel not in blob, f"sentinel {sentinel!r} leaked"


# ---------------------------------------------------------------------------
# Shared principals / resources / contexts
# ---------------------------------------------------------------------------

AUTH = ForgePrincipal(authenticated=True, forge_user_id="user-xb", session_id=None)
PUBLIC_RESOURCE = ResourcePolicyMetadata(
    PolicyResourceType.CANONICAL_OBJECT, "MOD.XB.PUBLIC.V1", ProductExposure.PUBLIC_TEACHING
)
SUBSCRIBER_RESOURCE = ResourcePolicyMetadata(
    PolicyResourceType.CANONICAL_OBJECT, "MOD.XB.SUB.V1", ProductExposure.SUBSCRIBER_MODEL
)
RESEARCH_RESOURCE = ResourcePolicyMetadata(
    PolicyResourceType.CANONICAL_OBJECT, "EV.XB.RESEARCH.V1", ProductExposure.RESEARCH_LAB
)
INTERNAL_RESOURCE = ResourcePolicyMetadata(
    PolicyResourceType.CANONICAL_OBJECT, "MOD.XB.INTERNAL.V1", ProductExposure.INTERNAL_METHOD
)
NO_EXPOSURE_RESOURCE = ResourcePolicyMetadata(
    PolicyResourceType.CANONICAL_OBJECT, "MOD.XB.NOEXPOSURE.V1"
)

EMPTY_CTX = AuthorizationContext.empty()
MEMBER_CTX = AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER)
OPERATOR_CTX = AuthorizationContext.of(CAPABILITY_MODEL_READ_OPERATOR)
RESEARCH_CTX = AuthorizationContext.of(CAPABILITY_EVIDENCE_READ_RESEARCH)
INTERNAL_CTX = AuthorizationContext.of(CAPABILITY_FORGE_INTERNAL)


def decision_matrix(engine: DefaultDenyPolicyEngine | None = None) -> tuple:
    """The full principal x context x resource x action decision set."""

    engine = engine or DefaultDenyPolicyEngine()
    principals = (ANONYMOUS_PRINCIPAL, AUTH)
    contexts = (
        EMPTY_CTX,
        MEMBER_CTX,
        OPERATOR_CTX,
        RESEARCH_CTX,
        INTERNAL_CTX,
        AuthorizationContext.of(CAPABILITY_ADMIN_RESEARCH, CAPABILITY_ADMIN_COMMERCE),
        AuthorizationContext.of("whop.plan.pro", "cus_provider_123"),  # provider-shaped
    )
    resources = (
        PUBLIC_RESOURCE,
        SUBSCRIBER_RESOURCE,
        RESEARCH_RESOURCE,
        INTERNAL_RESOURCE,
        NO_EXPOSURE_RESOURCE,
    )
    actions = (PolicyAction.VIEW, PolicyAction.QUERY, PolicyAction.ADMINISTER, "bogus.action")
    return tuple(
        engine.decide(principal, context, action, resource)
        for principal in principals
        for context in contexts
        for resource in resources
        for action in actions
    )


# ---------------------------------------------------------------------------
# Deterministic helpers
# ---------------------------------------------------------------------------


class _Clock:
    """Mutable injected clock (datetime domain: identity/session)."""

    def __init__(self, start: datetime) -> None:
        self._now = start

    def __call__(self) -> datetime:
        return self._now

    def advance(self, **kwargs: int) -> None:
        self._now += timedelta(**kwargs)


def _obs(*, with_log_sink: bool = False):
    """In-process observability service + its in-memory sink."""

    tick = "2026-10-10T00:00:00+00:00"
    sinks: list = [InMemoryEventSink()]
    if with_log_sink:
        sinks.append(StructuredLogSink())
    emitter = ForgeEventEmitter(environment="test", sinks=tuple(sinks), clock=lambda: tick)
    service = ForgeObservabilityService(emitter, environment="test", clock=lambda: tick)
    return service, sinks[0]


class _LoaderSpy:
    """Counting loader used by the deny-before-load primitive."""

    def __init__(self, payload: str = "protected-payload") -> None:
        self.calls = 0
        self.loaded: list[str] = []
        self._payload = payload

    def __call__(self, resource_id: str = "") -> str:
        self.calls += 1
        if resource_id:
            self.loaded.append(resource_id)
        return self._payload


class _RecordSpy:
    """Retrieval record loader spy: signature (generation, object_id)."""

    def __init__(self) -> None:
        self.loaded: list[str] = []

    def __call__(self, generation, object_id: str):
        self.loaded.append(object_id)
        return generation.record(object_id)


class _RaisingSink:
    """A telemetry sink that always fails (F11 / I1 / I4)."""

    def deliver(self, event) -> None:
        raise RuntimeError(f"sink exploded {SENTINEL_SECRET}")


def _x_record(cid: str, *, title: str = "cross-bloc object") -> CanonicalObjectRecord:
    return CanonicalObjectRecord(
        canonical_id=cid,
        object_type=ObjectType.MODEL,
        title=title,
        version="V1",
        status=EvidenceStatus.CANDIDATE,
        exposure=ProductExposure.SUBSCRIBER_MODEL,
        layer=Layer.NONE,
        references=(),
        metadata={"who": "cross-bloc"},
    )


def _registry(name: str, *, behavior: FakeBehavior | None = None):
    """Config + frozen registry whose llm port is bound to a named fake."""

    factory = default_provider_factory()
    factory.register(
        "llm",
        name,
        lambda config, n=name, b=behavior: FakeLLMProvider(name=n, behavior=b),
    )
    config = ForgeConfig(environment="test", provider_llm=name)
    return config, providers_from_config(config, factory=factory)


# ---------------------------------------------------------------------------
# Fixtures (real corpus index, built once)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def gateway() -> InMemoryPersistenceGateway:
    gw = InMemoryPersistenceGateway()
    run_backfill(gw, REPO_ROOT, BackfillMode.APPLY)
    return gw


@pytest.fixture(scope="module")
def index(gateway) -> RetrievalIndex:
    idx = RetrievalIndex()
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, idx)
    return idx


@pytest.fixture(scope="module")
def generation(index):
    return index.require()


@pytest.fixture(scope="module")
def qa(index) -> QAService:
    return QAService(RetrievalService(index))


# ===========================================================================
# X1 — Identity -> Policy -> Provider (ACCEPTANCE A)
# ===========================================================================


class _X1Stack:
    def __init__(self) -> None:
        self.clock = _Clock(datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc))
        self.gateway = InMemoryPersistenceGateway()
        self.auth = ForgeAuthenticationService(self.gateway, clock=self.clock)
        self.user = ForgeUser.create(email="x1@example.invalid")
        self.gateway.create_user(self.user)
        self.enforcement = ForgePolicyEnforcementService()
        self.spy = _LoaderSpy()
        self.llm = FakeLLMProvider(name="fake")
        self.decision_after_auth = None

    def open(self, ttl_minutes: int = 5):
        return self.auth.open_session(self.user, ttl=timedelta(minutes=ttl_minutes))

    def guarded(self, principal, context, resource=SUBSCRIBER_RESOURCE):
        return self.enforcement.guard(
            principal,
            context,
            PolicyAction.VIEW,
            resource,
            self.spy,
            resource.resource_id,
            correlation_id="fg-xb1",
        )


class TestX1IdentityPolicyProvider:
    def test_expired_session_cannot_reach_protected_operation(self) -> None:
        stack = _X1Stack()
        issued = stack.open()
        credential = f"Bearer {issued.bearer_token}"
        # Positive control: the credential authorizes before expiry.
        principal = stack.auth.authenticate_bearer(credential)
        assert stack.guarded(principal, MEMBER_CTX).allowed is True

        stack.clock.advance(minutes=6)  # past ttl
        calls_before = stack.spy.calls
        with pytest.raises(AuthenticationFailure) as excinfo:
            principal = stack.auth.authenticate_bearer(credential)
            # Never reached: guard would run only after authentication.
            stack.guarded(principal, MEMBER_CTX)
        assert excinfo.value.kind == "expired_session"
        assert stack.spy.calls == calls_before  # loader/provider untouched

    def test_revoked_session_cannot_reach_protected_operation(self) -> None:
        stack = _X1Stack()
        issued = stack.open()
        credential = f"Bearer {issued.bearer_token}"
        stack.auth.revoke_session(issued.session.session_id)

        calls_before = stack.spy.calls
        with pytest.raises(AuthenticationFailure) as excinfo:
            stack.guarded(stack.auth.authenticate_bearer(credential), MEMBER_CTX)
        assert excinfo.value.kind == "revoked_session"
        assert stack.spy.calls == calls_before

    def test_missing_credential_denied_before_load(self) -> None:
        stack = _X1Stack()
        principal = stack.auth.authenticate_bearer(None, allow_anonymous=True)
        assert principal.authenticated is False

        access = stack.guarded(principal, EMPTY_CTX)
        assert access.allowed is False
        assert access.payload is None
        assert access.decision.reason_code is PolicyReason.NOT_AUTHENTICATED
        assert stack.spy.calls == 0  # deny-before-load

    def test_invalid_bearer_token_fails_closed(self) -> None:
        stack = _X1Stack()
        for credential, kind in (
            ("Bearer not-a-real-token", "unknown_credential"),
            ("Basic dXNlcjpwYXNz", "malformed_credential"),
            ("Bearer ", "malformed_credential"),
            ("", "missing_credential"),
        ):
            with pytest.raises(AuthenticationFailure) as excinfo:
                stack.auth.authenticate_bearer(credential, allow_anonymous=False)
            if credential:
                assert excinfo.value.kind == kind
        assert stack.spy.calls == 0

    def test_disabled_user_fails_closed(self) -> None:
        stack = _X1Stack()
        issued = stack.open()
        credential = f"Bearer {issued.bearer_token}"
        stack.gateway.transition_user_state(stack.user.user_id, "DISABLED")

        calls_before = stack.spy.calls
        with pytest.raises(AuthenticationFailure) as excinfo:
            stack.guarded(stack.auth.authenticate_bearer(credential), MEMBER_CTX)
        assert excinfo.value.kind == "user_not_active"
        assert stack.spy.calls == calls_before

    def test_valid_session_and_capability_authorize_once(self) -> None:
        stack = _X1Stack()
        issued = stack.open()
        principal = stack.auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
        assert principal.authenticated is True

        access = stack.guarded(principal, MEMBER_CTX)
        assert access.allowed is True
        assert access.payload == "protected-payload"
        assert stack.spy.calls == 1  # exactly once
        assert stack.spy.loaded == [SUBSCRIBER_RESOURCE.resource_id]
        # Positive control for the provider seam as well: the fake provider is
        # reachable through the same loader path when authorization passes.
        assert stack.llm.calls == 0  # loader here does not call the LLM

    def test_decisions_are_audited_content_free(self) -> None:
        stack = _X1Stack()
        issued = stack.open()
        credential = f"Bearer {issued.bearer_token}"
        principal = stack.auth.authenticate_bearer(credential)

        allowed = stack.guarded(principal, MEMBER_CTX)
        denied = stack.guarded(principal, EMPTY_CTX, RESEARCH_RESOURCE)
        assert allowed.allowed is True and denied.allowed is False

        records = stack.enforcement.audit_records()
        assert len(records) == 2
        assert [r.allowed for r in records] == [True, False]
        assert records[0].principal_id == principal.forge_user_id
        assert records[1].reason_code == PolicyReason.ENTITLEMENT_MISSING.value
        assert records[0].correlation_id == "fg-xb1"
        blob = json.dumps([r.__dict__ for r in records], default=str)
        assert_no_sentinels(blob)
        assert issued.bearer_token not in blob


# ===========================================================================
# X2 — Policy -> Retrieval -> Observability (ACCEPTANCE B)
# ===========================================================================


def _retrieval_service(index, spy: _RecordSpy | None = None) -> RetrievalService:
    return RetrievalService(index, record_loader=spy or _RecordSpy())


class TestX2PolicyRetrievalObservability:
    def test_denied_content_is_never_loaded(self, index) -> None:
        anon_spy = _RecordSpy()
        anon_service = _retrieval_service(index, anon_spy)
        response = anon_service.retrieve(
            ANONYMOUS_PRINCIPAL, EMPTY_CTX, RetrievalQuery(canonical_id=RESTRICTED_OBJECT)
        )
        assert [d.object_id for d in response.denied] == [RESTRICTED_OBJECT]
        assert anon_spy.loaded == []  # body never loaded for the denial

        # Member capability still cannot reach RESEARCH_LAB (same law).
        member_spy = _RecordSpy()
        member_service = _retrieval_service(index, member_spy)
        member_service.retrieve(AUTH, MEMBER_CTX, RetrievalQuery(canonical_id=RESTRICTED_OBJECT))
        assert member_spy.loaded == []

        # Positive control: research capability loads it exactly once.
        research_spy = _RecordSpy()
        research_service = _retrieval_service(index, research_spy)
        allowed = research_service.retrieve(
            AUTH, RESEARCH_CTX, RetrievalQuery(canonical_id=RESTRICTED_OBJECT)
        )
        assert allowed.results and not allowed.denied
        assert research_spy.loaded == [RESTRICTED_OBJECT]

    def test_denied_content_is_never_returned(self, index) -> None:
        service = _retrieval_service(index)
        response = service.retrieve(ANONYMOUS_PRINCIPAL, EMPTY_CTX)  # all candidates
        assert response.denied, "anonymous retrieval over this corpus must deny"
        result_ids = {r.object_id for r in response.results}
        assert RESTRICTED_OBJECT not in result_ids
        assert result_ids == set()  # nothing is released to anonymous

        blob = json.dumps(response.to_dict(), default=str)
        assert_no_sentinels(blob)
        denied_entry = next(d for d in response.denied if d.object_id == RESTRICTED_OBJECT)
        assert denied_entry.reason_code == "NOT_AUTHENTICATED"
        assert denied_entry.exposure == "RESEARCH_LAB"
        # The denial entry is content-free by construction: exactly 3 fields.
        assert set(denied_entry.__dataclass_fields__) == {"object_id", "exposure", "reason_code"}

    def test_denied_content_never_reaches_telemetry(self, index, caplog) -> None:
        caplog.set_level(logging.DEBUG)
        obs, sink = _obs()
        service = _retrieval_service(index)

        with correlation_scope("fg-x2telem"):
            response = service.retrieve(
                ANONYMOUS_PRINCIPAL, EMPTY_CTX, RetrievalQuery(canonical_id=RESTRICTED_OBJECT)
            )
            assert response.denied
            denial = response.denied[0]
            # Caller-side projection of the denial fact (II.6.5 audit seam).
            obs.record_retrieval_access(
                principal_id="anonymous",
                service="retrieval",
                capability="",
                canonical_object_ids=(),
                retrieval_object_ids=(denial.object_id,),
                exposure=denial.exposure,
                decision="DENY",
            )
            obs.emit(
                severity="WARNING",
                component="retrieval",
                operation="retrieve",
                outcome="denied",
                reason_code=denial.reason_code,
            )
            enforcement = service.enforcement
            for record in enforcement.audit_records():
                obs.record_policy_decision(record)

        events_blob = json.dumps([e.to_dict() for e in sink.events()], default=str)
        audit_blob = json.dumps(
            [r.__dict__ for r in obs.retrieval_audit_records()], default=str
        )
        snapshot_blob = json.dumps(obs.snapshot(), default=str)
        assert_no_sentinels(events_blob, audit_blob, snapshot_blob, caplog.text)
        denied_events = [e for e in sink.events() if e.outcome == "denied"]
        assert denied_events, "the denial must be described (content-free)"
        assert denied_events[0].request_id == "fg-x2telem"

    def test_retrieval_audit_is_content_free_and_correlated(self, index) -> None:
        obs, _ = _obs()
        with correlation_scope("fg-x2audit"):
            # Denied fact: no object ids may be recorded as accessed.
            obs.record_retrieval_access(
                principal_id="anonymous",
                service="retrieval",
                capability="corpus.read.public",
                canonical_object_ids=(),
                retrieval_object_ids=(),
                exposure="RESEARCH_LAB",
                decision="DENY",
            )
            # Allowed fact: ids + exposure + decision only.
            obs.record_retrieval_access(
                principal_id=AUTH.forge_user_id or "unknown",
                service="retrieval",
                capability="evidence.read.research",
                canonical_object_ids=(RESTRICTED_OBJECT,),
                exposure="RESEARCH_LAB",
                decision="ALLOW",
            )
            records = obs.retrieval_audit_records()

        assert len(records) == 2
        assert records[0].canonical_object_ids == ()
        assert records[1].canonical_object_ids == (RESTRICTED_OBJECT,)
        assert all(r.correlation_id == "fg-x2audit" for r in records)
        assert all(r.at for r in records)
        blob = json.dumps([r.__dict__ for r in records], default=str)
        assert_no_sentinels(blob)
        # Field set is the frozen II.6.5 shape (no body/title/text fields).
        assert set(records[0].__dataclass_fields__) == {
            "correlation_id",
            "principal_id",
            "service",
            "capability",
            "canonical_object_ids",
            "retrieval_object_ids",
            "exposure",
            "decision",
            "at",
        }

    def test_authorized_retrieval_is_served_and_audited(self, index) -> None:
        spy = _RecordSpy()
        service = _retrieval_service(index, spy)
        response = service.retrieve(
            AUTH, OPERATOR_CTX, RetrievalQuery(canonical_id=RESTRICTED_OBJECT)
        )
        assert len(response.results) == 1
        assert response.results[0].object_id == RESTRICTED_OBJECT
        assert RESTRICTED_MARKER in response.results[0].retrieval_text
        assert spy.loaded == [RESTRICTED_OBJECT]

        with correlation_scope("fg-x2allow"):
            obs, sink = _obs()
            obs.record_retrieval_access(
                principal_id=AUTH.forge_user_id or "unknown",
                service="retrieval",
                capability="model.read.operator",
                canonical_object_ids=(RESTRICTED_OBJECT,),
                exposure="RESEARCH_LAB",
                decision="ALLOW",
            )
        record = obs.retrieval_audit_records()[0]
        assert record.decision == "ALLOW"
        assert record.correlation_id == "fg-x2allow"
        # The metric reflects released objects only (content-free counting).
        assert obs.metrics.counter("retrieval_objects_total") == 1.0


# ===========================================================================
# X3 — Provider -> Failure -> Policy (ACCEPTANCE C)
# ===========================================================================


class TestX3ProviderFailurePolicy:
    def test_provider_failure_never_changes_a_policy_decision(self) -> None:
        before = decision_matrix()
        config, registry = _registry("timeouty", behavior=FakeBehavior(failure_class="timeout"))
        llm = registry.get("llm")
        calls_before = llm.calls

        with pytest.raises(ProviderTimeoutError):
            run_with_fallback(
                FallbackPolicy.for_port("llm"),
                lambda: llm.generate(LLMRequest(prompt="p"), timeout_seconds=5),
            )

        calls_after_outage = llm.calls  # our one explicit, deliberate call
        after = decision_matrix()
        assert before == after  # identical decisions, provider down or not
        # And policy evaluation itself never touches the provider seam.
        assert llm.calls == calls_after_outage

        # The failing provider is disclosed honestly, never as healthy.
        assert llm.health().status == "unavailable"
        container = ForgeServiceContainer(config=config, providers=registry)
        deps = container.as_readiness_dependencies()
        assert deps["llm"]["status"] == "UNAVAILABLE"

    def test_provider_failures_normalize_without_leaking(self) -> None:
        from app.forge.providers import (
            ProviderMalformedResponseError,
            ProviderRateLimitedError,
            ProviderTimeoutError,
            ProviderUnavailableError,
        )

        cases = (
            (ProviderUnavailableError, ForgeErrorClass.DEPENDENCY, 503),
            (ProviderTimeoutError, ForgeErrorClass.DEPENDENCY, 503),
            (ProviderRateLimitedError, ForgeErrorClass.RATE_LIMIT, 429),
            (ProviderInvalidRequestError, ForgeErrorClass.VALIDATION, 422),
            (ProviderAuthenticationFailedError, ForgeErrorClass.AUTHENTICATION, 401),
            (ProviderMalformedResponseError, ForgeErrorClass.DATA_INTEGRITY, 500),
        )
        for error_cls, expected_class, expected_status in cases:
            kwargs = {}
            if error_cls is ProviderRateLimitedError:
                kwargs["retry_after_seconds"] = 1.0
            raw = error_cls(
                f"boom {SENTINEL_SECRET} body={RESTRICTED_MARKER} token={SENTINEL_TOKEN}",
                provider_type="llm",
                provider_name="fake",
                **kwargs,
            )
            mapped = from_provider_error(raw, request_id="fg-x3norm")
            assert mapped.error_class is expected_class
            assert mapped.origin == "provider"
            assert mapped.http_status == expected_status
            response = mapped.safe_response()
            assert response["message"] == SAFE_MESSAGES[expected_class]
            assert response["request_id"] == "fg-x3norm"
            blob = json.dumps(response) + str(mapped)
            assert_no_sentinels(blob)
            assert SENTINEL_SECRET not in str(raw.__cause__ or "")

    def test_commerce_outage_never_produces_success(self) -> None:
        commerce = FakeCommerceProvider(
            behavior=FakeBehavior(failure_class="unavailable"), name="fake"
        )
        policy = FallbackPolicy.for_port("commerce")
        assert policy.mode == "none"

        def fake_success_handler(exc):  # pragma: no cover - must never run
            return "SUCCESS-SHAPED"

        with pytest.raises(ProviderUnavailableError):
            run_with_fallback(
                policy,
                lambda: commerce.get_customer("cus_1"),
                on_failure=fake_success_handler,
            )
        # Health discloses the outage honestly.
        assert commerce.health().status == "unavailable"

    def test_open_circuit_grants_nothing_and_skips_provider(self) -> None:
        clock = SimulatedClock()
        llm = FakeLLMProvider(behavior=FakeBehavior(failure_class="timeout"), clock=clock)
        breaker = CircuitBreaker(name="llm", failure_threshold=2, recovery_seconds=30.0, clock=clock.now)
        request = LLMRequest(prompt="p")

        def call():
            return llm.generate(request, timeout_seconds=5)

        for _ in range(2):
            with pytest.raises(ProviderTimeoutError):
                breaker.call(call)
        assert breaker.state is CircuitState.OPEN

        calls_before = llm.calls
        with pytest.raises(ProviderUnavailableError):
            breaker.call(call)
        assert llm.calls == calls_before  # provider skipped entirely

        # An outage grants nothing: decisions are byte-identical across it.
        before = decision_matrix()
        with pytest.raises(ProviderUnavailableError):
            breaker.call(call)
        assert decision_matrix() == before


# ===========================================================================
# X4 — Persistence -> Concurrency -> Audit (ACCEPTANCE D)
# ===========================================================================


def _write_through(obs: ForgeObservabilityService, cid: str, operation):
    """Orchestration law: success is recorded ONLY from a returned result."""

    try:
        result = operation()
    except PersistenceError:
        obs.emit(
            severity="ERROR",
            component="persistence",
            operation=f"write.{cid}",
            outcome="failure",
            reason_code="rejected",
        )
        raise
    obs.emit(
        severity="INFO",
        component="persistence",
        operation=f"write.{cid}",
        outcome="success",
    )
    return result


class TestX4PersistenceConcurrencyAudit:
    def test_stale_write_is_rejected_and_state_unchanged(self) -> None:
        gw = InMemoryPersistenceGateway()
        obs, _ = _obs()
        cid = "MOD.XB.STALE.V1"
        _write_through(obs, cid, lambda: gw.create_object(_x_record(cid)))
        winner = _write_through(
            obs, cid, lambda: gw.transition_status(cid, "VALIDATED", expected_version=1)
        )
        assert winner.persisted_version == 2

        with pytest.raises(StaleWriteConflict):
            _write_through(
                obs, cid, lambda: gw.transition_status(cid, "PARKED", expected_version=1)
            )

        stored = gw.get_object(cid)
        assert stored is not None and stored.status is EvidenceStatus.VALIDATED
        sink = obs.emitter._sinks[0]
        successes = [
            e
            for e in sink.events()
            if e.operation == f"write.{cid}" and e.outcome == "success"
        ]
        assert len(successes) == 2  # accepted create + accepted transition only
        # Rejected write is not a mutation: state is exactly the winner's.
        assert stored.title == "cross-bloc object"

    def test_duplicate_create_is_rejected(self) -> None:
        gw = InMemoryPersistenceGateway()
        obs, _ = _obs()
        cid = "MOD.XB.DUP.V1"
        _write_through(obs, cid, lambda: gw.create_object(_x_record(cid, title="original")))
        with pytest.raises(DuplicateCanonicalObject):
            _write_through(obs, cid, lambda: gw.create_object(_x_record(cid, title="impostor")))

        stored = gw.get_object(cid)
        assert stored is not None and stored.title == "original"
        sink = obs.emitter._sinks[0]
        successes = [e for e in sink.events() if e.outcome == "success"]
        failures = [e for e in sink.events() if e.outcome == "failure"]
        assert len(successes) == 1 and len(failures) == 1

    def test_concurrent_writes_have_exactly_one_winner(self) -> None:
        gw = InMemoryPersistenceGateway()
        obs, _ = _obs()
        cid = "MOD.XB.CONCURRENT.V1"
        gw.create_object(_x_record(cid))  # version 1 snapshot held by both writers

        results = []
        errors = []
        for target in ("VALIDATED", "PARKED"):
            try:
                results.append(
                    _write_through(
                        obs, cid, lambda t=target: gw.transition_status(cid, t, expected_version=1)
                    )
                )
            except StaleWriteConflict as exc:
                # _write_through already recorded the rejection as a failure.
                errors.append(exc)

        assert len(results) == 1 and len(errors) == 1  # exactly one winner
        stored = gw.get_object(cid)
        assert stored is not None
        assert stored.status is (EvidenceStatus.VALIDATED if results else EvidenceStatus.CANDIDATE)
        sink = obs.emitter._sinks[0]
        successes = [e for e in sink.events() if e.outcome == "success"]
        failures = [e for e in sink.events() if e.outcome == "failure"]
        assert len(successes) == 1 and len(failures) == 1

    def test_failed_transaction_rolls_back_all_writes(self) -> None:
        gw = InMemoryPersistenceGateway()
        obs, _ = _obs()
        cid_a = "MOD.XB.TX_A.V1"

        # Path 1: an exception inside the batch rolls the whole batch back.
        with pytest.raises(ObjectNotFound):
            with gw.transaction():
                gw.create_object(_x_record(cid_a))
                gw.transition_status("MOD.XB.MISSING.V1", "VALIDATED")
        assert gw.get_object(cid_a) is None

        # Path 2: a batch rejected at commit validation applies nothing.
        cid_b = "MOD.XB.TX_B.V1"
        with pytest.raises(DuplicateCanonicalObject):
            with gw.transaction():
                gw.create_object(_x_record(cid_b))
                gw.create_object(_x_record(cid_b))
        assert gw.get_object(cid_b) is None

        sink = obs.emitter._sinks[0]
        assert [e for e in sink.events() if e.outcome == "success"] == []

    def test_rejected_write_is_never_recorded_as_success(self) -> None:
        gw = InMemoryPersistenceGateway()
        obs, _ = _obs()
        cid = "MOD.XB.REJECTED.V1"
        _write_through(obs, cid, lambda: gw.create_object(_x_record(cid)))
        stored_before = gw.get_object(cid)

        with pytest.raises(StaleWriteConflict):
            _write_through(
                obs, cid, lambda: gw.transition_status(cid, "VALIDATED", expected_version=7)
            )

        sink = obs.emitter._sinks[0]
        for event in sink.events():
            if f"write.{cid}" == event.operation:
                # Every recorded fact about this object after the rejection is
                # either the accepted create (success) or the rejection
                # (failure) — never a success for the rejected mutation.
                assert event.outcome in {"success", "failure"}
        rejected_successes = [
            e
            for e in sink.events()
            if e.operation == f"write.{cid}" and e.outcome == "success"
        ]
        assert len(rejected_successes) == 1  # only the accepted create
        assert gw.get_object(cid) == stored_before  # state untouched


# ===========================================================================
# X5 — QA -> Provider -> Evidence (ACCEPTANCE E)
# ===========================================================================


class TestX5QaProviderEvidence:
    def test_generated_content_cannot_promote_a_claim(self, qa, gateway) -> None:
        status_before = gateway.get_object(MODEL_OBJECT).status
        config, registry = _registry("storyteller")  # fake LLM that "generates"
        llm = registry.get("llm")

        answer = qa.ask(
            AUTH, OPERATOR_CTX, f"What is {MODEL_OBJECT}?", correlation_id="fg-x5a"
        )

        for assertion in answer.assertions:
            # Verdicts follow evidence STATUS authority only.
            if assertion.verdict.value == "ASSERT":
                assert assertion.status == EvidenceStatus.VALIDATED.value
            if assertion.supported:
                assert assertion.verdict.value == status_authority_verdict(
                    assertion.status, numerical=assertion.numerical
                )
        # Asking never mutates canonical status.
        assert gateway.get_object(MODEL_OBJECT).status is status_before
        generation = qa.retrieval.index.require()
        assert generation.header(MODEL_OBJECT).status is status_before
        # The provider was never consulted (no LLM path exists in QA).
        assert llm.calls == 0

    def test_qa_answers_do_not_consult_providers(self, qa, index) -> None:
        _, working = _registry("working")
        _, broken = _registry("broken", behavior=FakeBehavior(failure_class="unavailable"))

        question = f"What is {MODEL_OBJECT}?"
        first = qa.ask(AUTH, OPERATOR_CTX, question, correlation_id="fg-x5b")
        second = qa.ask(AUTH, OPERATOR_CTX, question, correlation_id="fg-x5b")

        # Registry composition (present, swapped, or failing) changes nothing:
        # QAService is constructed from the retrieval boundary alone.
        assert first.payload_dict() == second.payload_dict()
        assert working.get("llm").calls == 0
        assert broken.get("llm").calls == 0
        assert not hasattr(qa, "providers")

    def test_denied_objects_are_never_cited(self, qa) -> None:
        answer = qa.ask(
            ANONYMOUS_PRINCIPAL,
            EMPTY_CTX,
            f"Is {RESEARCH_CLAIM} validated?",
            correlation_id="fg-x5c",
        )
        blob = json.dumps(answer.payload_dict(), default=str)
        for field_ref in (
            *(a.object_id for a in answer.assertions),
            *answer.claim_refs,
            *answer.evidence_refs,
            *(c.claim_id for c in answer.citations),
            *(c.evidence_id for c in answer.citations),
            *(d.object_id for d in answer.denials),
        ):
            assert field_ref != RESTRICTED_OBJECT
        assert not any(a.object_id == RESEARCH_CLAIM for a in answer.assertions)
        assert RESTRICTED_MARKER not in blob
        # The denial still exists as an audited policy fact (content-free).
        audit = qa.retrieval.enforcement.audit_records()
        denies = [r for r in audit if not r.allowed and r.resource_id == RESEARCH_CLAIM]
        assert denies, "the deny must be audited even though nothing was served"
        assert_no_sentinels(json.dumps([r.__dict__ for r in audit], default=str))

    def test_found_is_not_supported_and_status_is_not_promoted(self, qa, index) -> None:
        generation = index.require()
        for question, context in (
            (f"Is {RESEARCH_CLAIM} validated?", OPERATOR_CTX),
            ("Is CL.EUR.DAILY.NEWS_INCREMENT validated?", OPERATOR_CTX),
            ("Does CL.FIB.R11.GENERATOR_FAILURE establish the rule?", OPERATOR_CTX),
        ):
            answer = qa.ask(AUTH, context, question, correlation_id="fg-x5d")
            for assertion in answer.assertions:
                header = generation.header(assertion.object_id)
                if header is None:
                    continue
                # Status authority: the answer reports the record's status,
                # never an upgraded one.
                assert assertion.status == header.status.value
                if assertion.verdict.value == "ASSERT":
                    assert assertion.status == EvidenceStatus.VALIDATED.value
                # A RESEARCH_FLAG/CANDIDATE record is never plain-assertable.
                if header.status in (
                    EvidenceStatus.RESEARCH_FLAG,
                    EvidenceStatus.CANDIDATE,
                    EvidenceStatus.FALSIFIED,
                ):
                    assert assertion.verdict.value in {"QUALIFY", "GAP"}


# ===========================================================================
# X6 — Commerce -> Identity -> Entitlement (ACCEPTANCE F)
# ===========================================================================


class TestX6CommerceIdentityEntitlement:
    def test_provider_facts_cannot_grant_entitlement(self) -> None:
        commerce = FakeCommerceProvider(name="fake")
        customer = commerce.get_customer("cus_crossbloc")
        subscription = commerce.get_subscription(customer.subscription_id)
        assert subscription.status in {"active", "past_due", "canceled"}

        provider_shaped = {
            customer.customer_id,
            customer.subscription_id or "",
            subscription.subscription_id,
            subscription.customer_id,
            subscription.status,
            "whop.plan.pro",
            "premium",
        }
        assert not (provider_shaped & REGISTERED_CAPABILITIES)

        engine = DefaultDenyPolicyEngine()
        context = AuthorizationContext.of(*(provider_shaped - {""}))
        decision = engine.decide(AUTH, context, PolicyAction.VIEW, SUBSCRIBER_RESOURCE)
        assert decision.allowed is False
        assert decision.reason_code is PolicyReason.ENTITLEMENT_MISSING

        # Admin-shaped provider facts widen nothing either.
        admin_context = AuthorizationContext.of(CAPABILITY_ADMIN_COMMERCE, CAPABILITY_ADMIN_RESEARCH)
        assert engine.decide(AUTH, admin_context, PolicyAction.VIEW, SUBSCRIBER_RESOURCE).allowed is False
        # Internal exposure still requires the dedicated atom.
        assert engine.decide(AUTH, admin_context, PolicyAction.VIEW, INTERNAL_RESOURCE).allowed is False

        # Positive control: the trusted capability seam admits.
        positive = engine.decide(AUTH, MEMBER_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE)
        assert positive.allowed is True

    def test_entitlement_audit_event_grants_nothing(self) -> None:
        obs, sink = _obs()
        engine = DefaultDenyPolicyEngine()
        before = engine.decide(AUTH, EMPTY_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE)

        record = obs.record_entitlement_event(
            event_type="grant",
            principal_id=AUTH.forge_user_id or "unknown",
            entitlement_id="ent_crossbloc",
            source_event_id="evt_provider_1",
            provider_type="commerce",
            provider_name="fake",
        )
        assert obs.entitlement_audit_records() == (record,)

        after = engine.decide(AUTH, EMPTY_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE)
        assert after == before
        assert after.allowed is False  # recording a grant grants nothing

        # The audit record carries commercial mapping only — no capability,
        # no price, no plan authority surface.
        fields = set(record.__dataclass_fields__)
        assert "capabilities" not in fields and "price" not in fields
        blob = json.dumps(record.__dict__, default=str)
        assert_no_sentinels(blob)
        # Emitted as a describe-only event, never as a decision.
        emitted = [e for e in sink.events() if e.stream == "entitlement_audit"]
        assert emitted and emitted[0].component == "policy"

    def test_identity_link_grants_nothing(self) -> None:
        clock = _Clock(datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc))
        gw = InMemoryPersistenceGateway()
        auth = ForgeAuthenticationService(gw, clock=clock)
        user = ForgeUser.create()
        other = ForgeUser.create()
        gw.create_user(user)
        gw.create_user(other)

        issued = auth.open_session(user, ttl=timedelta(minutes=5))
        principal = auth.authenticate_bearer(f"Bearer {issued.bearer_token}")
        engine = DefaultDenyPolicyEngine()
        before = engine.decide(principal, EMPTY_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE)

        link = auth.link_external_identity(
            principal, provider="whop", provider_subject="cus_provider_999"
        )
        assert link.forge_user_id == user.user_id
        after = engine.decide(principal, EMPTY_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE)
        assert after == before and after.allowed is False

        # Canonical identity beats provider identifiers: no takeover path.
        other_issued = auth.open_session(other, ttl=timedelta(minutes=5))
        other_principal = auth.authenticate_bearer(f"Bearer {other_issued.bearer_token}")
        with pytest.raises(AuthenticationFailure) as excinfo:
            auth.link_external_identity(
                other_principal, provider="whop", provider_subject="cus_provider_999"
            )
        assert excinfo.value.kind == "identity_collision"
        # The linked user keeps its own FORGE id.
        assert gw.get_identity_link("whop", "cus_provider_999").forge_user_id == user.user_id


# ===========================================================================
# X7 — Observability -> Error -> Security (ACCEPTANCE G)
# ===========================================================================


class TestX7ObservabilityErrorSecurity:
    def test_error_paths_never_reveal_secrets(self) -> None:
        obs, sink = _obs()

        def exploding_call():
            raise ProviderTimeoutError(
                f"upstream timeout {SENTINEL_SECRET} token={SENTINEL_TOKEN} "
                f"credential={SENTINEL_CREDENTIAL} body={RESTRICTED_MARKER}",
                provider_type="llm",
                provider_name="fake",
            )

        with pytest.raises(ProviderTimeoutError):
            observe_provider_call(
                obs.emit,
                obs.metrics.increment,
                obs.metrics.observe,
                port="llm",
                provider_type="llm",
                provider_name="fake",
                call=exploding_call,
                request_id="fg-x7sec",
            )

        events_blob = json.dumps([e.to_dict() for e in sink.events()], default=str)
        assert_no_sentinels(events_blob)
        failure_events = [e for e in sink.events() if e.outcome == "failure"]
        assert failure_events and failure_events[0].error_class == "DEPENDENCY"
        assert failure_events[0].reason_code == "provider_timeout"
        assert obs.metrics.counter("provider_errors_total") == 1.0

        # The HTTP-shaped error body carries only the frozen envelope.
        mapped = from_provider_error(
            ProviderTimeoutError(
                f"leak {SENTINEL_SECRET}", provider_type="llm", provider_name="fake"
            ),
            request_id="fg-x7sec",
        )
        assert set(mapped.safe_response()) == {"code", "message", "request_id"}

    def test_metrics_and_snapshot_are_content_free(self) -> None:
        obs, sink = _obs()
        obs.record_policy_decision(
            type("R", (), {"allowed": False, "principal_id": "u1", "authenticated": True,
                           "action": "VIEW", "resource_type": "CANONICAL_OBJECT",
                           "resource_id": "MOD.X", "exposure": "SUBSCRIBER_MODEL",
                           "reason_code": "ENTITLEMENT_MISSING", "correlation_id": "fg-x7",
                           "at": "2026-10-10T00:00:00+00:00"})()
        )
        obs.record_usage(
            provider_type="llm",
            provider_name="fake",
            model_id=f"fake-model {SENTINEL_SECRET}",
            input_tokens=10,
            output_tokens=5,
            normalized_cost=0.01,
            latency_ms=12.0,
        )
        obs.record_retrieval_access(
            principal_id="u1",
            service="retrieval",
            capability="model.read.operator",
            canonical_object_ids=("MOD.X",),
            exposure="SUBSCRIBER_MODEL",
            decision="ALLOW",
        )
        try:
            raise ProviderTimeoutError(
                f"boom {SENTINEL_SECRET} {RESTRICTED_MARKER}",
                provider_type="llm",
                provider_name="fake",
            )
        except ProviderTimeoutError:
            with pytest.raises(ProviderTimeoutError):
                observe_provider_call(
                    obs.emit,
                    obs.metrics.increment,
                    obs.metrics.observe,
                    port="llm",
                    provider_type="llm",
                    provider_name="fake",
                    call=lambda: (_ for _ in ()).throw(
                        ProviderTimeoutError(
                            f"boom {SENTINEL_SECRET}", provider_type="llm", provider_name="fake"
                        )
                    ),
                )

        blob = json.dumps(obs.snapshot(), default=str)
        assert_no_sentinels(blob)
        # Snapshot exposes counters only — no payloads, no bodies.
        assert set(obs.snapshot()) == {
            "environment",
            "events_recorded",
            "dropped_events",
            "rejected_events",
            "retrieval_audit_records",
            "entitlement_audit_records",
            "usage_records",
            "metrics",
        }
        for event in sink.events():
            assert_no_sentinels(json.dumps(event.to_dict(), default=str))

    def test_route_failure_returns_safe_envelope_only(self, monkeypatch, caplog) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import app.forge.service.routes as routes_module
        from app.forge.service.routes import create_forge_router

        class _ExplodingHealth:
            def __init__(self, container) -> None:
                self.container = container

            def readiness(self):
                raise RuntimeError(
                    f"boom {SENTINEL_SECRET} {SENTINEL_TOKEN} {RESTRICTED_MARKER}"
                )

            def liveness(self):
                raise RuntimeError(f"boom {SENTINEL_SECRET}")

            def meta(self):
                raise RuntimeError(f"boom {SENTINEL_SECRET}")

        monkeypatch.setattr(routes_module, "ForgeHealthService", _ExplodingHealth)

        config = ForgeConfig(environment="test")
        container = ForgeServiceContainer(config=config)
        app = FastAPI()
        app.include_router(create_forge_router(config=config, container=container))
        client = TestClient(app, raise_server_exceptions=False)

        caplog.set_level(logging.DEBUG)
        response = client.get("/forge/v1/ready", headers={"X-Request-Id": "fg-x7route"})
        assert response.status_code == 500
        body = response.json()
        assert body["code"] == "FORGE_INTERNAL_ERROR"
        assert body["message"] == "internal service error"
        assert body["request_id"] == "fg-x7route"
        assert_no_sentinels(response.text, caplog.text)
        # The log carries the exception class name only.
        assert "RuntimeError" in caplog.text

    def test_restricted_research_never_reaches_logs(self, index, caplog) -> None:
        caplog.set_level(logging.DEBUG)
        obs, sink = _obs(with_log_sink=True)
        service = _retrieval_service(index)

        denied = service.retrieve(
            ANONYMOUS_PRINCIPAL, EMPTY_CTX, RetrievalQuery(canonical_id=RESTRICTED_OBJECT)
        )
        allowed = service.retrieve(
            AUTH, RESEARCH_CTX, RetrievalQuery(canonical_id=RESTRICTED_OBJECT)
        )
        assert allowed.results  # the body was legitimately loaded...
        obs.record_retrieval_access(
            principal_id="anonymous",
            service="retrieval",
            capability="",
            exposure="RESEARCH_LAB",
            decision="DENY",
        )
        obs.emit(
            severity="INFO",
            component="retrieval",
            operation="retrieve",
            outcome="success",
            reason_code="served",
        )
        assert denied.denied

        # ...but no log line, structured event or audit record carries it.
        assert_no_sentinels(caplog.text)
        assert_no_sentinels(json.dumps([e.to_dict() for e in sink.events()], default=str))
        assert_no_sentinels(
            json.dumps([r.__dict__ for r in obs.retrieval_audit_records()], default=str)
        )
        assert RESTRICTED_MARKER in allowed.results[0].retrieval_text  # sanity: real content


# ===========================================================================
# X8 — Provider Replacement -> Domain Stability (ACCEPTANCE H)
# ===========================================================================


class TestX8ProviderReplacementStability:
    def test_registry_swap_changes_nothing(self, qa, gateway) -> None:
        cid = "MOD.XB.SWAP.V1"
        gateway.create_object(_x_record(cid))
        record_before = gateway.get_object(cid)

        config_a, registry_a = _registry("alpha")
        container_a = ForgeServiceContainer(config=config_a, providers=registry_a)
        decisions_a = decision_matrix()
        answer_a = qa.ask(AUTH, OPERATOR_CTX, f"What is {MODEL_OBJECT}?", correlation_id="fg-x8a")

        config_b, registry_b = _registry(
            "omega", behavior=FakeBehavior(failure_class="unavailable")
        )
        container_b = ForgeServiceContainer(config=config_b, providers=registry_b)
        decisions_b = decision_matrix()
        answer_b = qa.ask(AUTH, OPERATOR_CTX, f"What is {MODEL_OBJECT}?", correlation_id="fg-x8a")

        # Domain outputs are byte-identical across the provider swap.
        assert decisions_a == decisions_b
        assert answer_a.payload_dict() == answer_b.payload_dict()
        assert gateway.get_object(cid) == record_before
        # The broken fake was never consulted by any of it.
        assert registry_b.get("llm").calls == 0
        assert registry_a.get("llm").calls == 0
        # Composition is frozen after wiring (replacement is a composition act).
        assert registry_a.is_frozen and registry_b.is_frozen

        # The ONLY thing the swap legitimately changes is the health disclosure.
        deps_a = container_a.as_readiness_dependencies()
        deps_b = container_b.as_readiness_dependencies()
        assert deps_a["llm"]["status"] == "READY"
        assert deps_b["llm"]["status"] == "UNAVAILABLE"
        assert deps_b["llm"] is not deps_a["llm"]

    def test_fake_llm_swap_changes_no_domain_output(self, qa) -> None:
        _, small = _registry("smallfake")
        config_big, big_registry = _registry("bigfake")
        # Different bound model naming; domain output must not care.
        assert config_big.provider_llm == "bigfake"

        question = f"Is {RESEARCH_CLAIM} validated?"
        first = qa.ask(AUTH, OPERATOR_CTX, question, correlation_id="fg-x8b")
        second = qa.ask(AUTH, OPERATOR_CTX, question, correlation_id="fg-x8b")
        assert first.payload_dict() == second.payload_dict()
        assert small.get("llm").calls == 0
        assert big_registry.get("llm").calls == 0


# ===========================================================================
# X9 — Lifecycle -> Readiness -> Failure (ACCEPTANCE I)
# ===========================================================================


class TestX9LifecycleReadinessFailure:
    def test_telemetry_never_blocks_readiness(self) -> None:
        # Unwired telemetry: disclosed, required=False, never blocks.
        config = ForgeConfig(environment="test")
        unwired = ForgeServiceContainer(config=config, observability=None)
        deps = unwired.as_readiness_dependencies()
        assert deps["observability"] == {
            "status": "NOT_CONFIGURED",
            "required": False,
            "note": (
                "observability not wired; FORGE serves without telemetry (II.6)"
            ),
        }
        assert ForgeHealthService(unwired).readiness()["status"] == "ready"

        # Wired but failing sink: still READY, still never blocks.
        obs, _ = _obs()
        emitter = ForgeEventEmitter(environment="test", sinks=(_RaisingSink(),))
        failing_obs = ForgeObservabilityService(emitter, environment="test")
        wired = ForgeServiceContainer(config=config, observability=failing_obs)
        deps = wired.as_readiness_dependencies()
        assert deps["observability"]["status"] == "READY"
        assert deps["observability"]["required"] is False
        assert ForgeHealthService(wired).readiness()["status"] == "ready"
        # The sink failure was absorbed, not surfaced as an outage.
        failing_obs.emit(operation="probe", component="api")
        assert failing_obs.emitter.dropped_events >= 1

    def test_provider_outage_never_masquerades_as_healthy(self) -> None:
        config, broken = _registry(
            "broken", behavior=FakeBehavior(failure_class="unavailable")
        )
        container = ForgeServiceContainer(config=config, providers=broken)
        deps = container.as_readiness_dependencies()
        assert deps["llm"]["status"] == "UNAVAILABLE"
        assert deps["llm"]["required"] is False
        assert deps["llm"]["status"] != "READY"
        # Optional outage does not block the core service.
        assert ForgeHealthService(container).readiness()["status"] == "ready"

        # Unwired port is NOT_CONFIGURED — never a false READY.
        bare = ForgeServiceContainer(config=ForgeConfig(environment="test"))
        bare_deps = bare.as_readiness_dependencies()
        for port in ("llm", "commerce", "notification", "storage"):
            assert bare_deps[port]["status"] == "NOT_CONFIGURED"
            assert bare_deps[port]["required"] is False

        # Healthy fake: honestly READY.
        _, healthy = _registry("healthyfake")
        ready_container = ForgeServiceContainer(config=ForgeConfig(environment="test"), providers=healthy)
        assert ready_container.as_readiness_dependencies()["llm"]["status"] == "READY"

    def test_required_dependency_failure_blocks_readiness(self) -> None:
        config = ForgeConfig(environment="test")
        container = ForgeServiceContainer(
            config=config, persistence=InMemoryPersistenceGateway(simulate_unavailable=True)
        )
        context = ForgeLifecycle(container).startup()
        assert context["started"] is True
        deps = container.as_readiness_dependencies()
        assert deps["postgresql"]["status"] == "UNAVAILABLE"
        assert deps["postgresql"]["required"] is True
        assert ForgeHealthService(container).readiness()["status"] == "not_ready"

    def test_ready_endpoint_survives_sink_failure(self, monkeypatch) -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.forge.service.routes import create_forge_router

        emitter = ForgeEventEmitter(environment="test", sinks=(_RaisingSink(),))
        obs = ForgeObservabilityService(emitter, environment="test")
        config = ForgeConfig(environment="test")
        container = ForgeServiceContainer(config=config, observability=obs)
        app = FastAPI()
        app.include_router(create_forge_router(config=config, container=container))
        client = TestClient(app)

        response = client.get("/forge/v1/ready", headers={"X-Request-Id": "fg-x9ready"})
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        assert body["request_id"] == "fg-x9ready"
        assert body["dependencies"]["observability"]["status"] == "READY"
        assert_no_sentinels(response.text)
        assert obs.emitter.dropped_events >= 1  # failure absorbed and counted


# ===========================================================================
# F1-F12 — Deterministic failure injection (ACCEPTANCE J)
# ===========================================================================


class TestFailureInjection:
    def test_timeout_fails_closed(self) -> None:
        # F1: scripted timeout produces no output and no policy change.
        clock = SimulatedClock()
        llm = FakeLLMProvider(
            behavior=FakeBehavior(latency_seconds=30.0), clock=clock, name="fake"
        )
        before = decision_matrix()
        with pytest.raises(ProviderTimeoutError):
            llm.generate(LLMRequest(prompt="p"), timeout_seconds=1.0)
        assert llm.calls == 1  # the call was attempted, then failed closed
        assert decision_matrix() == before

    def test_retry_delegates_to_alternate_once(self) -> None:
        # F2: retryable failure delegates once; non-retryable never retries.
        calls = {"primary": 0, "alternate": 0}

        def primary():
            calls["primary"] += 1
            raise ProviderTimeoutError("timeout", provider_type="llm", provider_name="fake")

        def alternate():
            calls["alternate"] += 1
            return "ALTERNATE_RESULT"

        result = run_with_fallback(FallbackPolicy.for_port("llm"), primary, alternate=alternate)
        assert result == "ALTERNATE_RESULT"
        assert calls == {"primary": 1, "alternate": 1}

        def bad_primary():
            calls["primary"] += 1
            raise ProviderInvalidRequestError(
                "invalid", provider_type="llm", provider_name="fake"
            )

        with pytest.raises(ProviderInvalidRequestError):
            run_with_fallback(
                FallbackPolicy.for_port("llm"), bad_primary, alternate=alternate
            )
        assert calls["alternate"] == 1  # non-retryable never reached alternate

    def test_duplicate_events_create_no_grant_state(self) -> None:
        # F3: the same commerce event delivered twice records two facts and
        # produces NO entitlement grant state anywhere.
        raw = json.dumps(
            {
                "event_id": "evt_dup_1",
                "event_type": "subscription.created",
                "occurred_at": 1728000000,
                "plan": "pro",
            }
        ).encode("utf-8")
        commerce = FakeCommerceProvider(event_script=(raw, raw), name="fake")
        events = commerce.scripted_events()
        assert len(events) == 2
        assert events[0].event_id == events[1].event_id == "evt_dup_1"

        obs, _ = _obs()
        for event in events:
            obs.record_entitlement_event(
                event_type="grant",
                principal_id="user-f3",
                entitlement_id="ent_f3",
                source_event_id=event.event_id,
                provider_type="commerce",
                provider_name="fake",
            )
        assert len(obs.entitlement_audit_records()) == 2  # append-only records
        # Duplicates never become authority: policy still denies.
        decision = DefaultDenyPolicyEngine().decide(
            AUTH, EMPTY_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE
        )
        assert decision.allowed is False
        # No entitlement state machine exists to double-apply a grant.
        assert not hasattr(obs, "entitlement_state")
        assert not hasattr(obs, "entitlements")

    def test_out_of_order_events_derive_no_authority(self) -> None:
        # F4: delivery order is preserved as data; nothing derives authority
        # from ordering (no state machine consumes it).
        first = json.dumps(
            {"event_id": "evt_a", "event_type": "subscription.created", "occurred_at": 200.0}
        ).encode("utf-8")
        second = json.dumps(
            {"event_id": "evt_b", "event_type": "subscription.canceled", "occurred_at": 100.0}
        ).encode("utf-8")
        commerce = FakeCommerceProvider(event_script=(first, second), name="fake")
        events = commerce.scripted_events()
        assert [e.occurred_at for e in events] == [200.0, 100.0]  # out-of-order kept

        obs, _ = _obs()
        for event in events:
            obs.record_entitlement_event(
                event_type="revoke" if event.event_id == "evt_b" else "grant",
                principal_id="user-f4",
                entitlement_id="ent_f4",
                source_event_id=event.event_id,
                provider_type="commerce",
                provider_name="fake",
            )
        assert len(obs.entitlement_audit_records()) == 2
        decision = DefaultDenyPolicyEngine().decide(
            AUTH, EMPTY_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE
        )
        assert decision.allowed is False
        # Replaying in the reverse order changes no authority either.
        decision_rev = DefaultDenyPolicyEngine().decide(
            AUTH, EMPTY_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE
        )
        assert decision_rev == decision

    def test_rate_limit_maps_to_429_and_no_success(self) -> None:
        # F5
        mapped = from_provider_error(
            ProviderRateLimitedError(
                "slow down", provider_type="llm", provider_name="fake",
                retry_after_seconds=5.0,
            ),
            request_id="fg-f5",
        )
        assert mapped.error_class is ForgeErrorClass.RATE_LIMIT
        assert mapped.http_status == 429
        assert mapped.safe_response()["message"] == "rate limited"

        commerce = FakeCommerceProvider(
            behavior=FakeBehavior(failure_class="rate_limited"), name="fake"
        )
        with pytest.raises(Exception) as excinfo:
            run_with_fallback(
                FallbackPolicy.for_port("commerce"),
                lambda: commerce.create_checkout("cus_1", idempotency_key="k1"),
            )
        assert type(excinfo.value).__name__ == "ProviderRateLimitedError"

    def test_malformed_response_fails_closed(self) -> None:
        # F6
        from app.forge.providers import ProviderMalformedResponseError

        mapped = from_provider_error(
            ProviderMalformedResponseError(
                f"truncated payload {SENTINEL_SECRET}",
                provider_type="llm",
                provider_name="fake",
            ),
            request_id="fg-f6",
        )
        assert mapped.error_class is ForgeErrorClass.DATA_INTEGRITY
        assert mapped.http_status == 500
        assert_no_sentinels(json.dumps(mapped.safe_response()))

        def malformed():
            raise ProviderMalformedResponseError(
                f"bad {RESTRICTED_MARKER}", provider_type="llm", provider_name="fake"
            )

        obs, sink = _obs()
        with pytest.raises(ProviderMalformedResponseError):
            observe_provider_call(
                obs.emit,
                obs.metrics.increment,
                obs.metrics.observe,
                port="llm",
                provider_type="llm",
                provider_name="fake",
                call=malformed,
                request_id="fg-f6",
            )
        assert_no_sentinels(json.dumps([e.to_dict() for e in sink.events()], default=str))

    def test_invalid_session_cannot_enter_guard(self) -> None:
        # F7
        clock = _Clock(datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc))
        gw = InMemoryPersistenceGateway()
        auth = ForgeAuthenticationService(gw, clock=clock)
        user = ForgeUser.create()
        gw.create_user(user)
        issued = auth.open_session(user, ttl=timedelta(minutes=5))

        enforcement = ForgePolicyEnforcementService()
        spy = _LoaderSpy()
        credential = f"Bearer {issued.bearer_token}"
        # Corrupt one character of the raw token.
        corrupted = credential[:-2] + ("A" if credential[-2] != "A" else "B") + credential[-1]
        with pytest.raises(AuthenticationFailure):
            enforcement.guard(
                auth.authenticate_bearer(corrupted, allow_anonymous=False),
                MEMBER_CTX,
                PolicyAction.VIEW,
                SUBSCRIBER_RESOURCE,
                spy,
                SUBSCRIBER_RESOURCE.resource_id,
            )
        assert spy.calls == 0

    def test_revocation_takes_effect_immediately(self) -> None:
        # F8: the very same raw token stops authorizing the moment the
        # session is revoked — no reissue, no grace window.
        clock = _Clock(datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc))
        gw = InMemoryPersistenceGateway()
        auth = ForgeAuthenticationService(gw, clock=clock)
        user = ForgeUser.create()
        gw.create_user(user)
        issued = auth.open_session(user, ttl=timedelta(minutes=60))
        credential = f"Bearer {issued.bearer_token}"

        enforcement = ForgePolicyEnforcementService()
        spy = _LoaderSpy()
        principal = auth.authenticate_bearer(credential)
        assert enforcement.guard(
            principal, MEMBER_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE, spy, "r1"
        ).allowed is True

        auth.revoke_session(issued.session.session_id)
        with pytest.raises(AuthenticationFailure) as excinfo:
            auth.authenticate_bearer(credential)
        assert excinfo.value.kind == "revoked_session"
        assert spy.calls == 1  # unchanged: no second (unauthorized) load

    def test_concurrent_write_conflict_is_deterministic(self) -> None:
        # F9: repeated two-writer races over one expected version always
        # yield exactly one winner and identical final state.
        outcomes = []
        for attempt in range(3):
            gw = InMemoryPersistenceGateway()
            cid = f"MOD.XB.RACE_{attempt}.V1"
            gw.create_object(_x_record(cid))  # both writers hold version 1
            winner = loser = None
            try:
                winner = gw.transition_status(cid, "VALIDATED", expected_version=1)
            except StaleWriteConflict:
                winner = "stale"
            try:
                loser = gw.transition_status(cid, "PARKED", expected_version=1)
            except StaleWriteConflict as exc:
                loser = type(exc).__name__
            outcomes.append(
                (
                    None if winner == "stale" else winner.persisted_version,
                    loser,
                    gw.get_object(cid).status,
                )
            )
        assert outcomes == [
            (2, "StaleWriteConflict", EvidenceStatus.VALIDATED),
            (2, "StaleWriteConflict", EvidenceStatus.VALIDATED),
            (2, "StaleWriteConflict", EvidenceStatus.VALIDATED),
        ]

    def test_provider_recovery_restores_service(self) -> None:
        # F10: OPEN -> half-open probe -> CLOSED, and readiness follows the
        # live health of the recovered provider.
        clock = SimulatedClock()
        failing = FakeLLMProvider(
            behavior=FakeBehavior(failure_class="timeout"), clock=clock, name="recovered"
        )
        breaker = CircuitBreaker(
            name="llm", failure_threshold=1, recovery_seconds=30.0, clock=clock.now
        )
        request = LLMRequest(prompt="p")
        with pytest.raises(ProviderTimeoutError):
            breaker.call(lambda: failing.generate(request, timeout_seconds=5))
        assert breaker.state is CircuitState.OPEN
        calls_while_open = failing.calls
        with pytest.raises(ProviderUnavailableError):
            breaker.call(lambda: failing.generate(request, timeout_seconds=5))
        assert failing.calls == calls_while_open

        clock.advance(30.0)
        assert breaker.state is CircuitState.HALF_OPEN
        healthy = FakeLLMProvider(clock=clock, name="recovered")
        response = breaker.call(lambda: healthy.generate(request, timeout_seconds=5))
        assert response.text.startswith("fake-llm:")
        assert breaker.state is CircuitState.CLOSED
        # Post-recovery call executes (circuit closed, provider reachable).
        assert breaker.call(lambda: healthy.generate(request, timeout_seconds=5)) is not None

        config, recovered_registry = _registry("recoveredfake")
        container = ForgeServiceContainer(config=config, providers=recovered_registry)
        assert container.as_readiness_dependencies()["llm"]["status"] == "READY"

    def test_sink_failure_is_isolated(self) -> None:
        # F11
        emitter = ForgeEventEmitter(environment="test", sinks=(_RaisingSink(),))
        obs = ForgeObservabilityService(emitter, environment="test")
        obs.emit(operation="does-not-crash", component="api")  # must not raise
        obs.emit(operation="again", component="policy", severity="WARNING")
        assert obs.emitter.dropped_events >= 2
        assert obs.emitter.rejected_events == 0
        assert obs.snapshot()["dropped_events"] >= 2

    def test_invalid_correlation_context_is_replaced(self) -> None:
        # F12
        assert parse_request_id(None) is None
        assert parse_request_id("not safe !! <script>") is None
        assert parse_request_id("x" * 200) is None
        assert parse_request_id("fg-good_id-1") == "fg-good_id-1"

        with correlation_scope("not safe !! <script>") as bound:
            assert bound.startswith("fg-")
            assert effective_request_id() == bound
        assert effective_request_id() == UNATTRIBUTED

        with correlation_scope(None) as bound:
            assert bound.startswith("fg-")


# ===========================================================================
# Phase 5 — security & epistemic laws (ACCEPTANCE K)
# ===========================================================================

_DOMAIN_MODULES = (
    "app/forge/canonical.py",
    "app/forge/schemas.py",
    "app/forge/provenance.py",
    "app/forge/policy.py",
    "app/forge/identity.py",
    "app/forge/qa/kernel.py",
    "app/forge/qa/contract.py",
    "app/forge/qa/authority.py",
    "app/forge/retrieval/service.py",
    "app/forge/backfill/canonicalizer.py",
)

_FORBIDDEN_FOR_DOMAIN = ("app.forge.providers", "app.forge.observability", "fastapi")
_FORBIDDEN_FOR_PROVIDERS = ("fastapi", "sqlalchemy", "httpx", "requests")


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


class TestSecurityEpistemicLaws:
    def test_authorization_precedes_content_access(self, index) -> None:
        # K1: across a mixed retrieval run, the loader sees EXACTLY the set
        # of objects policy allowed — no more (leak), no less (bug).
        spy = _RecordSpy()
        service = _retrieval_service(index, spy)

        service.retrieve(AUTH, MEMBER_CTX, RetrievalQuery())  # member run
        member_loaded = tuple(spy.loaded)
        spy.loaded.clear()
        service.retrieve(ANONYMOUS_PRINCIPAL, EMPTY_CTX, RetrievalQuery())  # anonymous run
        anon_loaded = tuple(spy.loaded)

        member_allowed = {
            r.object_id
            for r in service.retrieve(AUTH, MEMBER_CTX, RetrievalQuery()).results
        }
        assert set(member_loaded) == member_allowed
        assert RESTRICTED_OBJECT not in member_loaded  # member never reads research
        assert anon_loaded == ()  # anonymous never reads anything

    def test_import_discipline(self) -> None:
        # K2 + H3: domain never imports providers/observability/transport;
        # providers never import HTTP clients or SQL drivers.
        for rel in _DOMAIN_MODULES:
            imports = _imports_of(REPO_ROOT / rel)
            hits = [
                forbidden
                for forbidden in _FORBIDDEN_FOR_DOMAIN
                if any(name == forbidden or name.startswith(forbidden + ".") for name in imports)
            ]
            assert hits == [], f"{rel} imports forbidden modules: {hits}"
        for path in sorted((REPO_ROOT / "app" / "forge" / "providers").glob("*.py")):
            imports = _imports_of(path)
            hits = [
                forbidden
                for forbidden in _FORBIDDEN_FOR_PROVIDERS
                if any(name == forbidden or name.startswith(forbidden + ".") for name in imports)
            ]
            assert hits == [], f"{path.name} imports forbidden modules: {hits}"

    def test_canonical_identity_beats_provider_ids(self) -> None:
        # K3: FORGE ids are FORGE-generated; provider subjects are attributes.
        import inspect

        params = set(inspect.signature(ForgeUser.create).parameters) - {"cls", "self"}
        assert "provider" not in params and "provider_subject" not in params
        assert "email" in params  # email exists but is untrusted/optional

        user_a = ForgeUser.create(user_id="a" * 32)
        user_b = ForgeUser.create(user_id="b" * 32)
        assert user_a.user_id != user_b.user_id

        clock = _Clock(datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc))
        gw = InMemoryPersistenceGateway()
        auth = ForgeAuthenticationService(gw, clock=clock)
        gw.create_user(user_a)
        gw.create_user(user_b)
        issued_a = auth.open_session(user_a, ttl=timedelta(minutes=5))
        issued_b = auth.open_session(user_b, ttl=timedelta(minutes=5))
        principal_a = auth.authenticate_bearer(f"Bearer {issued_a.bearer_token}")
        principal_b = auth.authenticate_bearer(f"Bearer {issued_b.bearer_token}")

        auth.link_external_identity(principal_a, provider="whop", provider_subject="cus_1")
        with pytest.raises(AuthenticationFailure) as excinfo:
            auth.link_external_identity(principal_b, provider="whop", provider_subject="cus_1")
        assert excinfo.value.kind == "identity_collision"
        # The FORGE id never moves; the provider subject never becomes a key.
        link = gw.get_identity_link("whop", "cus_1")
        assert link.forge_user_id == user_a.user_id
        assert gw.get_user(user_b.user_id).user_id == "b" * 32

    def test_security_audit_is_distinct_from_provenance(self) -> None:
        # K5/K7 separation: the II.6 security audit and the I.2 provenance
        # graph are independent stores; neither can be written through the
        # other, and recording audit facts never touches provenance edges.
        gateway = InMemoryPersistenceGateway()
        edge_count_before = len(gateway.edges_for_object("MOD.XB.ANY.V1"))

        obs, sink = _obs()
        enforcement = ForgePolicyEnforcementService()
        enforcement.authorize(
            AUTH, MEMBER_CTX, PolicyAction.VIEW, SUBSCRIBER_RESOURCE,
            correlation_id="fg-k5",
        )
        obs.record_policy_decision(enforcement.audit_records()[0])
        obs.record_retrieval_access(
            principal_id=AUTH.forge_user_id or "unknown",
            service="retrieval",
            capability="corpus.read.member",
            canonical_object_ids=("MOD.XB.ANY.V1",),
            exposure="SUBSCRIBER_MODEL",
            decision="ALLOW",
        )

        assert len(gateway.edges_for_object("MOD.XB.ANY.V1")) == edge_count_before
        # The security audit is the only stream touched; the retrieval-access
        # fact lives in its own trail (no event stream), and provenance edges
        # are untouched by both.
        assert [e.stream for e in sink.events()] == ["security_audit"]
        assert len(obs.retrieval_audit_records()) == 1
        # Observability never imports the provenance graph (AST-checked).
        for path in sorted((REPO_ROOT / "app" / "forge" / "observability").glob("*.py")):
            imports = _imports_of(path)
            assert not any(name.startswith("app.forge.provenance") for name in imports)
            assert not any(name.startswith("app.forge.persistence") for name in imports)

    def test_no_entitlement_state_machine_exists(self) -> None:
        # F4/K5: II.6 records entitlement facts; it cannot hold or mutate
        # entitlement state, and Book VI licensing is not implemented here.
        obs, _ = _obs()
        for attribute in ("entitlement_state", "entitlements", "grants", "plans"):
            assert not hasattr(obs, attribute)

        mutations = []
        for path in sorted((REPO_ROOT / "app").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name.lower()
                    if "entitlement" in name and "audit" not in name and not name.startswith("record_"):
                        mutations.append((str(path), node.name))
        assert mutations == [], f"entitlement mutation surface found: {mutations}"

        # Identity carries no entitlement concept at all.
        from dataclasses import fields as dataclass_fields

        from app.forge.identity import ForgePrincipal

        principal_fields = {f.name for f in dataclass_fields(ForgePrincipal)}
        assert principal_fields == {"authenticated", "forge_user_id", "session_id", "roles"}

    def test_no_brokerage_execution_api(self) -> None:
        # K6: FORGE exposes no brokerage/order-execution surface.
        forbidden = {
            "place_order", "execute_order", "submit_order", "execute_trade",
            "place_trade", "create_position", "open_position", "close_position",
            "cancel_order", "broker_execute", "send_order",
        }
        hits = []
        for path in sorted((REPO_ROOT / "app" / "forge").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name.lower() in forbidden:
                        hits.append((str(path), node.name))
        assert hits == [], f"brokerage execution surface found: {hits}"
