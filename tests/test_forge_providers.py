"""II.5 focused suite — provider ports & adapter boundaries (Ch II.5.1-II.5.10).

Maps to ACCEPTANCE.md clauses A-J (K = regression discipline, recorded in
EVIDENCE.md). The shared Ch II.5.10 replacement harness lives in
`tests/provider_contract.py`; this module covers fake-specific behavior, the
failure taxonomy, resilience policy, the container/config seam, and the five
verbatim frozen Acceptance II.5 clauses.

Ch II.5.9 scenario map ("one each", spread across the suite where they
naturally belong): success = TestFakeScenarios.test_scenario_success,
latency = test_scenario_latency_simulated, timeout =
TestLLMPort.test_timeout_uses_simulated_clock + TestFakeScenarios.
test_scenario_timeout_notification, duplicate events =
TestCommercePort.test_duplicate_events_collapse_on_event_id, out-of-order =
TestCommercePort.test_out_of_order_events_reduce_to_identical_state, invalid
signature = TestCommercePort.test_invalid_signature_is_authentication_failed,
invalid shape = TestCommercePort.test_invalid_shape_is_invalid_request, rate
limit = TestCommercePort.test_rate_limit_carries_retry_after +
TestLLMPort.test_hard_failure_normalizes_and_never_retries, hard failure =
TestFakeScenarios.test_scenario_hard_failure_all_ports.
"""

from __future__ import annotations

import ast
import inspect
import json
import time
from pathlib import Path

import pytest

from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalRegistry,
    EvidenceStatus,
    Layer,
    ProductExposure,
)
from app.forge.config import (
    ForgeConfig,
    forge_config_from_environment,
    forge_config_from_values,
)
from app.forge.identity import ANONYMOUS_PRINCIPAL
from app.forge.policy import (
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_CORPUS_READ_PUBLIC,
    AuthorizationContext,
    DefaultDenyPolicyEngine,
    PolicyAction,
    PolicyResourceType,
    ResourcePolicyMetadata,
)
from app.forge.providers import (
    ACCESS_STRATEGY_KINDS,
    CAPABILITY_STRUCTURED_OUTPUT,
    CHECKOUT_STATUSES,
    FAILURE_CLASSES,
    PORTS,
    PORT_CONTRACTS,
    LLMRequest,
    LLMResponse,
    LLMUsage,
    NotificationProvider,
    NotificationRequest,
    NotificationResult,
    ProviderAuthenticationFailedError,
    ProviderCancelledError,
    ProviderConfigurationError,
    ProviderContractSpec,
    ProviderError,
    ProviderEvent,
    ProviderHealth,
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderRateLimitedError,
    ProviderRegistry,
    ProviderTimeoutError,
    ProviderUnavailableError,
    SimulatedClock,
    FakeBehavior,
    FakeCommerceProvider,
    FakeLLMProvider,
    FakeNotificationProvider,
    FakeStorageProvider,
    CircuitBreaker,
    CircuitState,
    FallbackPolicy,
    default_provider_factory,
    providers_from_config,
    run_with_fallback,
)
from app.forge.providers.commerce import (
    COMMERCE_METHODS,
    CUSTOMER_STATUSES,
    SUBSCRIPTION_STATUSES,
    CommerceProvider,
)
from app.forge.providers.errors import ERROR_BY_CLASS
from app.forge.providers.notification import NOTIFICATION_METHODS
from app.forge.providers.storage import STORAGE_METHODS
from app.forge.service.container import ForgeServiceContainer
from tests.provider_contract import (
    run_commerce_contract,
    run_llm_contract,
    run_notification_contract,
    run_storage_contract,
)

APP_ROOT = Path(__file__).resolve().parents[1] / "app"

# Modules the provider package must never import (network/HTTP/SQL surface).
BANNED_PROVIDER_IMPORTS = frozenset(
    {
        "fastapi",
        "starlette",
        "httpx",
        "requests",
        "aiohttp",
        "urllib3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "socket",
        "sqlite3",
    }
)

# Concrete vendor identifiers that must never appear in domain code — the
# "no `if provider == whop` spread" law (Ch II.5.6) and the "no provider
# identifier as core domain PK" law (Acceptance II.5 clause 2).
VENDOR_TOKENS = (
    "whop",
    "openrouter",
    "stripe",
    "sendgrid",
    "twilio",
    "anthropic",
    "openai",
)

# Domain modules: never import app.forge.providers (composition root exempt).
COMPOSITION_ROOT_FILES = {
    APP_ROOT / "forge" / "service" / "container.py",
    APP_ROOT / "main.py",
}

# Vendor-identifier scan exemption: config.py is the composition/config
# boundary and declares credential PRESENCE for future adapters
# (openrouter_api_key / whop_api_key) — vendor naming at that boundary is
# intentional disclosure, not domain coupling. config.py still participates
# in the import-isolation scan (a config -> providers import would be a
# circular-dependency bug), and no domain model/PK carries vendor names.
VENDOR_SCAN_EXEMPT = {APP_ROOT / "forge" / "config.py"}


def _vendor_scan_files() -> list[Path]:
    return [p for p in _domain_py_files() if p not in VENDOR_SCAN_EXEMPT]


def _domain_py_files() -> list[Path]:
    forge = APP_ROOT / "forge"
    files = [p for p in forge.glob("*.py")]
    for sub in ("backfill", "retrieval", "qa", "persistence", "service"):
        files.extend(p for p in (forge / sub).glob("*.py"))
    return sorted(
        p for p in files if p not in COMPOSITION_ROOT_FILES
    )


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _imported_modules(tree: ast.Module) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def _string_constants(tree: ast.Module) -> list[str]:
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


def _event_raw(
    event_id: str,
    event_type: str = "subscription.created",
    occurred_at: int = 1700000000,
    **payload: str,
) -> bytes:
    body = {
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        **payload,
    }
    return json.dumps(body).encode("utf-8")


def _registry_with(behavior: FakeBehavior | None) -> ProviderRegistry:
    """All four fakes bound under one shared scripted behavior."""

    registry = ProviderRegistry()
    registry.register("llm", "fake", FakeLLMProvider(behavior=behavior))
    registry.register(
        "commerce", "fake", FakeCommerceProvider(behavior=behavior)
    )
    registry.register(
        "notification", "fake", FakeNotificationProvider(behavior=behavior)
    )
    registry.register(
        "storage", "fake", FakeStorageProvider(behavior=behavior)
    )
    registry.freeze()
    return registry


def _view(context: AuthorizationContext, exposure: ProductExposure):
    engine = DefaultDenyPolicyEngine()
    return engine.decide(
        ANONYMOUS_PRINCIPAL,
        context,
        PolicyAction.VIEW,
        ResourcePolicyMetadata(
            PolicyResourceType.CANONICAL_OBJECT, "MOD.TEST.X", exposure
        ),
    )


def _canonical_registry() -> CanonicalRegistry:
    def obj(cid: str) -> CanonicalObject:
        return CanonicalObject(
            canonical_id=CanonicalId.parse(cid),
            title=f"object {cid}",
            version="1",
            status=EvidenceStatus.CANDIDATE,
            exposure=ProductExposure.SUBSCRIBER_MODEL,
            layer=Layer.L1,
            references=(),
            metadata={"slug": cid},
        )

    return CanonicalRegistry([obj("MOD.EUR.DAILY.V1"), obj("MOD.EUR.WEEKLY.V1")])


def _canonical_snapshot(registry: CanonicalRegistry) -> dict:
    return {
        cid: (
            registry.get(cid).content_hash(),
            registry.get(cid).status.value,
        )
        for cid in registry.ids()
    }


# ---------------------------------------------------------------------------
# Alternate adapters: locally defined implementations with different
# internals, used to prove Ch II.5.10 replacement (composition change, not
# domain rewrite) without any real vendor.
# ---------------------------------------------------------------------------


class _AlternateLLMProvider:
    def __init__(self, name: str = "alternate") -> None:
        self._name = name
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def capabilities(self) -> frozenset[str]:
        return frozenset({CAPABILITY_STRUCTURED_OUTPUT})

    def generate(
        self,
        request: LLMRequest,
        *,
        timeout_seconds: float,
        cancel=None,
    ) -> LLMResponse:
        self.calls += 1
        if timeout_seconds <= 0:
            raise ProviderInvalidRequestError(
                "timeout_seconds must be > 0",
                provider_type="llm",
                provider_name=self._name,
            )
        if cancel is not None and cancel():
            raise ProviderCancelledError(
                "call cancelled by caller",
                provider_type="llm",
                provider_name=self._name,
            )
        text = "alt:" + request.prompt[::-1][:40]
        prompt_tokens = len(request.prompt) // 4 + 1
        completion_tokens = len(text) // 4 + 1
        structured = None
        if request.response_schema is not None:
            required = request.response_schema.get("required")
            if not isinstance(required, list) or not required:
                raise ProviderInvalidRequestError(
                    "malformed response schema",
                    provider_type="llm",
                    provider_name=self._name,
                )
            structured = {key: "alt-value" for key in required}
        return LLMResponse(
            text=text,
            model=request.model,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost_usd=round((prompt_tokens + completion_tokens) * 0.001, 8),
            ),
            structured=structured,
            finish_reason="stop",
        )

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_type="llm",
            provider_name=self._name,
            status="healthy",
            detail="alternate test adapter",
        )


class _AlternateCommerceProvider:
    def __init__(self, name: str = "alternate") -> None:
        self._name = name
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def sign(self, raw: bytes) -> str:
        import hashlib

        return "alt=" + hashlib.sha256(raw).hexdigest()

    def create_checkout(
        self, customer_id: str, *, idempotency_key: str
    ):
        self.calls += 1
        import hashlib

        digest = hashlib.sha256(
            f"{customer_id}|{idempotency_key}".encode("utf-8")
        ).hexdigest()[:12]
        from app.forge.providers.commerce import CheckoutSession

        return CheckoutSession(
            session_id=f"acs-{digest}",
            customer_id=customer_id,
            handoff_url=f"https://alt-checkout.invalid/session/{digest}",
            status="open",
        )

    def get_customer(self, customer_id: str):
        from app.forge.providers.commerce import CommerceCustomer

        return CommerceCustomer(
            customer_id=customer_id, status="active", subscription_id=None
        )

    def get_subscription(self, subscription_id: str):
        from app.forge.providers.commerce import CommerceSubscription

        return CommerceSubscription(
            subscription_id=subscription_id,
            customer_id="cus-alt",
            status="active",
        )

    def parse_event(self, raw: bytes, signature: str) -> ProviderEvent:
        if signature != self.sign(raw):
            raise ProviderAuthenticationFailedError(
                "event signature verification failed",
                provider_type="commerce",
                provider_name=self._name,
            )
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ProviderInvalidRequestError(
                "event shape invalid: not json",
                provider_type="commerce",
                provider_name=self._name,
            ) from None
        if not isinstance(data, dict):
            raise ProviderInvalidRequestError(
                "event shape invalid: not an object",
                provider_type="commerce",
                provider_name=self._name,
            )
        event_id = data.get("event_id")
        event_type = data.get("event_type")
        occurred_at = data.get("occurred_at")
        if (
            not isinstance(event_id, str)
            or not event_id
            or not isinstance(event_type, str)
            or isinstance(occurred_at, bool)
            or not isinstance(occurred_at, (int, float))
        ):
            raise ProviderInvalidRequestError(
                "event shape invalid: required fields",
                provider_type="commerce",
                provider_name=self._name,
            )
        payload = {
            str(k): str(v)
            for k, v in data.items()
            if k not in {"event_id", "event_type", "occurred_at"}
        }
        return ProviderEvent(
            event_id=event_id,
            event_type=event_type,
            occurred_at=float(occurred_at),
            payload=payload,
        )

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_type="commerce",
            provider_name=self._name,
            status="healthy",
            detail="alternate test adapter",
        )


class _AlternateNotificationProvider:
    def __init__(self, name: str = "alternate") -> None:
        self._name = name
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def send(self, request: NotificationRequest) -> NotificationResult:
        self.calls += 1
        if request.channel != "email":
            raise ProviderInvalidRequestError(
                "unsupported notification channel",
                provider_type="notification",
                provider_name=self._name,
            )
        import hashlib

        digest = hashlib.sha256(
            f"{request.recipient}|{request.subject}".encode("utf-8")
        ).hexdigest()[:12]
        return NotificationResult(
            message_id=f"alt-msg-{digest}", status="delivered"
        )

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_type="notification",
            provider_name=self._name,
            status="healthy",
            detail="alternate test adapter",
        )


class _AlternateStorageProvider:
    def __init__(self, name: str = "alternate") -> None:
        self._name = name
        self.calls = 0
        self._store: dict[str, list[tuple[int, bytes, str]]] = {}
        self._deleted: set[str] = set()

    @property
    def provider_name(self) -> str:
        return self._name

    def put(self, key: str, data: bytes, *, content_type: str):
        self.calls += 1
        from app.forge.providers.storage import StoredObject

        if not key or key in self._deleted:
            raise ProviderInvalidRequestError(
                "storage key unavailable",
                provider_type="storage",
                provider_name=self._name,
            )
        versions = self._store.setdefault(key, [])
        version = len(versions) + 1
        versions.append((version, bytes(data), content_type))
        import hashlib

        return StoredObject(
            key=key,
            version=version,
            size_bytes=len(data),
            content_type=content_type,
            checksum=hashlib.sha256(data).hexdigest(),
        )

    def get(self, key: str, *, version: int | None = None):
        self.calls += 1
        from app.forge.providers.storage import StoredObject, StoredObjectData

        if not key or key not in self._store or key in self._deleted:
            raise ProviderInvalidRequestError(
                "storage key not found",
                provider_type="storage",
                provider_name=self._name,
            )
        versions = self._store[key]
        target = versions[-1][0] if version is None else version
        for stored_version, data, content_type in versions:
            if stored_version == target:
                import hashlib

                return StoredObjectData(
                    object=StoredObject(
                        key=key,
                        version=stored_version,
                        size_bytes=len(data),
                        content_type=content_type,
                        checksum=hashlib.sha256(data).hexdigest(),
                    ),
                    data=data,
                )
        raise ProviderInvalidRequestError(
            "storage version not found",
            provider_type="storage",
            provider_name=self._name,
        )

    def delete(self, key: str) -> None:
        self.calls += 1
        if not key or key not in self._store:
            raise ProviderInvalidRequestError(
                "storage key not found",
                provider_type="storage",
                provider_name=self._name,
            )
        self._deleted.add(key)

    def access_strategy(self, key: str, *, ttl_seconds: float):
        self.calls += 1
        from app.forge.providers.storage import AccessStrategy

        if not key or key not in self._store or key in self._deleted:
            raise ProviderInvalidRequestError(
                "storage key not found",
                provider_type="storage",
                provider_name=self._name,
            )
        return AccessStrategy(
            kind="authorized_stream",
            target=f"alt-blob://{key}?ttl={int(ttl_seconds)}",
            expires_at=float(ttl_seconds),
        )

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_type="storage",
            provider_name=self._name,
            status="healthy",
            detail="alternate test adapter",
        )


def _alternate_factory():
    from app.forge.providers import ProviderFactory

    factory = default_provider_factory()
    assert isinstance(factory, ProviderFactory)
    factory.register("llm", "alternate", lambda cfg: _AlternateLLMProvider())
    factory.register(
        "commerce", "alternate", lambda cfg: _AlternateCommerceProvider()
    )
    factory.register(
        "notification", "alternate", lambda cfg: _AlternateNotificationProvider()
    )
    factory.register(
        "storage", "alternate", lambda cfg: _AlternateStorageProvider()
    )
    return factory


def _registry_for(variant: str) -> ProviderRegistry:
    if variant == "fake":
        return providers_from_config(ForgeConfig(environment="test"))
    cfg = forge_config_from_values(
        provider_llm="alternate",
        provider_commerce="alternate",
        provider_notification="alternate",
        provider_storage="alternate",
    )
    return providers_from_config(cfg, factory=_alternate_factory())


# ---------------------------------------------------------------------------
# A — doctrine, taxonomy, purity
# ---------------------------------------------------------------------------


class TestContractDoctrine:
    """Ch II.5.1 + Ch II.5.7."""

    def test_contract_specs_cover_all_ports_with_eight_elements(self) -> None:
        assert set(PORT_CONTRACTS) == set(PORTS)
        expected = {
            "request",
            "response",
            "timeout",
            "retry_ownership",
            "idempotency",
            "error_taxonomy",
            "health_semantics",
            "redaction",
        }
        for port, spec in PORT_CONTRACTS.items():
            assert isinstance(spec, ProviderContractSpec)
            elements = spec.elements()
            assert set(elements) == expected, port
            for name, text in elements.items():
                assert isinstance(text, str) and text.strip(), (port, name)

    def test_failure_taxonomy_is_frozen_eight(self) -> None:
        assert FAILURE_CLASSES == (
            "unavailable",
            "timeout",
            "rate_limited",
            "invalid_request",
            "authentication_failed",
            "upstream_rejected",
            "malformed_response",
            "unknown",
        )
        assert set(ERROR_BY_CLASS) == set(FAILURE_CLASSES)
        assert "cancelled" not in FAILURE_CLASSES

    def test_error_classes_map_one_to_one(self) -> None:
        for name, cls in ERROR_BY_CLASS.items():
            error = cls("probe", provider_type="llm", provider_name="fake")
            assert isinstance(error, ProviderError)
            assert error.failure_class == name
        cancelled = ProviderCancelledError("stop")
        assert cancelled.failure_class is None
        assert cancelled.retryable is False

    def test_retry_ownership_is_advisory_and_bounded(self) -> None:
        for name, cls in ERROR_BY_CLASS.items():
            error = cls("probe")
            expected_retryable = name in {
                "timeout",
                "unavailable",
                "rate_limited",
            }
            assert error.retryable is expected_retryable, name
        with pytest.raises(ValueError, match="rate_limited"):
            ProviderUnavailableError("probe", retry_after_seconds=5.0)
        limited = ProviderRateLimitedError(
            "probe", retry_after_seconds=2.5
        )
        assert limited.retry_after_seconds == 2.5

    def test_provider_errors_redact_payloads_and_credentials(self) -> None:
        sentinel = "sk-SENTINEL_CREDENTIAL_VALUE"
        fake = FakeLLMProvider(
            behavior=FakeBehavior(failure_class="malformed_response")
        )
        with pytest.raises(ProviderMalformedResponseError) as excinfo:
            fake.generate(
                LLMRequest(prompt=f"payload {sentinel}"), timeout_seconds=5.0
            )
        error = excinfo.value
        assert sentinel not in str(error)
        summary = error.redacted_summary()
        assert set(summary) == {
            "failure_class",
            "provider_type",
            "provider_name",
            "retryable",
            "retry_after_seconds",
            "message",
        }
        assert sentinel not in json.dumps(summary, default=str)
        assert summary["message"] == "provider returned malformed response"

    def test_providers_package_import_purity(self) -> None:
        package = APP_ROOT / "forge" / "providers"
        for path in sorted(package.glob("*.py")):
            tree = _parse(path)
            for module in _imported_modules(tree):
                root = module.split(".")[0]
                assert root not in BANNED_PROVIDER_IMPORTS, (
                    f"{path.name} imports {module}"
                )
                assert not module.startswith("app.forge.service"), (
                    f"{path.name} imports service layer {module}"
                )

    def test_domain_modules_never_import_providers(self) -> None:
        for path in _domain_py_files():
            tree = _parse(path)
            for module in _imported_modules(tree):
                assert module != "app.forge.providers" and not module.startswith(
                    "app.forge.providers."
                ), f"{path} imports {module} (composition root is exempt)"


# ---------------------------------------------------------------------------
# B — LLM port (Ch II.5.2)
# ---------------------------------------------------------------------------


class TestLLMPort:
    def test_generate_is_deterministic_and_echoes_model(self) -> None:
        request = LLMRequest(prompt="determinism probe", model="m-1")
        first = FakeLLMProvider().generate(request, timeout_seconds=5.0)
        second = FakeLLMProvider().generate(request, timeout_seconds=5.0)
        assert isinstance(first, LLMResponse)
        assert first == second
        assert first.model == request.model == "m-1"
        assert first.text.startswith("fake-llm:")

    def test_usage_and_cost_metadata_is_deterministic(self) -> None:
        request = LLMRequest(prompt="usage probe prompt", model="m-1")
        response = FakeLLMProvider().generate(request, timeout_seconds=5.0)
        usage = response.usage
        assert usage.prompt_tokens == max(1, len(request.prompt) // 4)
        assert usage.completion_tokens == max(1, len(response.text) // 4)
        assert usage.total_tokens == (
            usage.prompt_tokens + usage.completion_tokens
        )
        assert usage.cost_usd == round(
            usage.total_tokens * 0.002 / 1000.0, 8
        )
        assert usage.cost_usd > 0

    def test_structured_output_capability_advertised_validated(self) -> None:
        structured_fake = FakeLLMProvider()
        assert CAPABILITY_STRUCTURED_OUTPUT in structured_fake.capabilities()
        response = structured_fake.generate(
            LLMRequest(
                prompt="schema probe",
                model="m-1",
                response_schema={"type": "object", "required": ["alpha"]},
            ),
            timeout_seconds=5.0,
        )
        assert response.structured is not None
        assert set(response.structured) == {"alpha"}

        plain_fake = FakeLLMProvider(structured=False)
        assert plain_fake.capabilities() == frozenset()
        with pytest.raises(ProviderInvalidRequestError):
            plain_fake.generate(
                LLMRequest(
                    prompt="schema probe",
                    model="m-1",
                    response_schema={"required": ["alpha"]},
                ),
                timeout_seconds=5.0,
            )
        with pytest.raises(ProviderInvalidRequestError):
            structured_fake.generate(
                LLMRequest(
                    prompt="schema probe",
                    model="m-1",
                    response_schema={"required": "not-a-list"},
                ),
                timeout_seconds=5.0,
            )

    def test_timeout_uses_simulated_clock(self) -> None:
        clock = SimulatedClock()
        fake = FakeLLMProvider(
            behavior=FakeBehavior(latency_seconds=5.0), clock=clock
        )
        with pytest.raises(ProviderTimeoutError) as excinfo:
            fake.generate(
                LLMRequest(prompt="slow", model="m-1"), timeout_seconds=3.0
            )
        assert excinfo.value.failure_class == "timeout"
        assert excinfo.value.retryable is True
        assert clock.now() == 5.0
        assert fake.calls == 1  # the failed attempt was not retried

    def test_cancel_is_control_flow_outside_taxonomy(self) -> None:
        fake = FakeLLMProvider()
        with pytest.raises(ProviderCancelledError) as excinfo:
            fake.generate(
                LLMRequest(prompt="cancel", model="m-1"),
                timeout_seconds=5.0,
                cancel=lambda: True,
            )
        assert excinfo.value.failure_class is None
        assert excinfo.value.failure_class not in FAILURE_CLASSES
        assert fake.calls == 1

    def test_hard_failure_normalizes_and_never_retries(self) -> None:
        unavailable = FakeLLMProvider(
            behavior=FakeBehavior(failure_class="unavailable")
        )
        with pytest.raises(ProviderUnavailableError):
            unavailable.generate(
                LLMRequest(prompt="x", model="m-1"), timeout_seconds=5.0
            )
        assert unavailable.calls == 1  # adapters never retry (Ch II.5.1)

        limited = FakeLLMProvider(
            behavior=FakeBehavior(
                failure_class="rate_limited", rate_limit_retry_after=7.5
            )
        )
        with pytest.raises(ProviderRateLimitedError) as excinfo:
            limited.generate(
                LLMRequest(prompt="x", model="m-1"), timeout_seconds=5.0
            )
        assert excinfo.value.retry_after_seconds == 7.5
        assert limited.calls == 1

    def test_llm_port_imports_no_intelligence_modules(self) -> None:
        tree = _parse(APP_ROOT / "forge" / "providers" / "llm.py")
        for module in _imported_modules(tree):
            assert not module.startswith("app.forge.retrieval")
            assert not module.startswith("app.forge.qa")
            assert not module.startswith("app.forge.backfill")


# ---------------------------------------------------------------------------
# C — commerce port (Ch II.5.3)
# ---------------------------------------------------------------------------


class TestCommercePort:
    def test_checkout_handoff_is_deterministic(self) -> None:
        fake = FakeCommerceProvider()
        session = fake.create_checkout("cus-7", idempotency_key="key-7")
        assert session.session_id.startswith("cs-")
        assert session.customer_id == "cus-7"
        assert session.status in CHECKOUT_STATUSES
        assert "checkout.invalid" in session.handoff_url
        again = FakeCommerceProvider().create_checkout(
            "cus-7", idempotency_key="key-7"
        )
        assert again == session

    def test_checkout_idempotency_no_duplicates(self) -> None:
        fake = FakeCommerceProvider()
        first = fake.create_checkout("cus-7", idempotency_key="key-7")
        repeat = fake.create_checkout("cus-7", idempotency_key="key-7")
        other = fake.create_checkout("cus-7", idempotency_key="key-8")
        assert first.session_id == repeat.session_id
        assert other.session_id != first.session_id
        assert fake.calls == 3

    def test_customer_and_subscription_lookup_shapes(self) -> None:
        fake = FakeCommerceProvider()
        customer = fake.get_customer("cus-7")
        assert customer.customer_id == "cus-7"
        assert customer.status in CUSTOMER_STATUSES
        assert customer.subscription_id and customer.subscription_id.startswith(
            "sub_"
        )
        subscription = fake.get_subscription(customer.subscription_id)
        assert subscription.subscription_id == customer.subscription_id
        assert subscription.status in SUBSCRIPTION_STATUSES

    def test_parse_event_normalizes(self) -> None:
        fake = FakeCommerceProvider()
        raw = _event_raw("evt-1", occurred_at=1700000123, plan="pro")
        event = fake.parse_event(raw, fake.sign(raw))
        assert isinstance(event, ProviderEvent)
        assert event.event_id == "evt-1"
        assert event.occurred_at == 1700000123.0
        assert event.payload == {"plan": "pro"}

    def test_invalid_signature_is_authentication_failed(self) -> None:
        fake = FakeCommerceProvider()
        raw = _event_raw("evt-1")
        with pytest.raises(ProviderAuthenticationFailedError):
            fake.parse_event(raw, "v1=forged")

    def test_invalid_shape_is_invalid_request(self) -> None:
        fake = FakeCommerceProvider()
        not_json = b"definitely not json"
        with pytest.raises(ProviderInvalidRequestError):
            fake.parse_event(not_json, fake.sign(not_json))
        missing_fields = json.dumps({"event_id": "evt-1"}).encode("utf-8")
        with pytest.raises(ProviderInvalidRequestError):
            fake.parse_event(
                missing_fields, fake.sign(missing_fields)
            )
        wrong_type = json.dumps(
            {
                "event_id": "evt-1",
                "event_type": "not-a-real-event",
                "occurred_at": 1,
            }
        ).encode("utf-8")
        with pytest.raises(ProviderInvalidRequestError):
            fake.parse_event(wrong_type, fake.sign(wrong_type))

    def test_duplicate_events_collapse_on_event_id(self) -> None:
        raw = _event_raw("evt-dup", occurred_at=1700000500)
        fake = FakeCommerceProvider(event_script=(raw, raw))
        events = fake.scripted_events()
        assert len(events) == 2
        assert events[0].event_id == events[1].event_id
        deduped = {event.event_id: event for event in events}
        assert len(deduped) == 1

    def test_out_of_order_events_reduce_to_identical_state(self) -> None:
        def reducer(events):
            deduped: dict[str, ProviderEvent] = {}
            for event in events:
                deduped.setdefault(event.event_id, event)
            return sorted(
                deduped.values(), key=lambda e: (e.occurred_at, e.event_id)
            )

        a = _event_raw("evt-a", occurred_at=300)
        b = _event_raw("evt-b", occurred_at=100)
        c = _event_raw("evt-c", occurred_at=200)
        in_order = FakeCommerceProvider(
            event_script=(b, c, a)
        ).scripted_events()
        out_of_order = FakeCommerceProvider(
            event_script=(a, c, b, a)
        ).scripted_events()  # inverted arrival + one duplicate
        assert [e.event_id for e in out_of_order] != [
            e.event_id for e in in_order
        ]
        assert reducer(in_order) == reducer(out_of_order)

    def test_rate_limit_carries_retry_after(self) -> None:
        fake = FakeCommerceProvider(
            behavior=FakeBehavior(
                failure_class="rate_limited", rate_limit_retry_after=3.0
            )
        )
        with pytest.raises(ProviderRateLimitedError) as excinfo:
            fake.create_checkout("cus-7", idempotency_key="key-7")
        assert excinfo.value.retryable is True
        assert excinfo.value.retry_after_seconds == 3.0
        assert fake.calls == 1

    def test_commerce_method_set_excludes_entitlement_mutation(self) -> None:
        methods = {
            name
            for name in dir(CommerceProvider)
            if not name.startswith("_")
        }
        assert methods == set(COMMERCE_METHODS)
        for forbidden in (
            "grant",
            "revoke",
            "set_entitlement",
            "mutate_entitlement",
            "update_subscription_status",
        ):
            assert forbidden not in methods


# ---------------------------------------------------------------------------
# D — notification port (Ch II.5.4)
# ---------------------------------------------------------------------------


class TestNotificationPort:
    def test_send_is_deterministic_with_normalized_result(self) -> None:
        request = NotificationRequest(
            channel="email",
            recipient="ops@example.invalid",
            subject="froze",
            body="the corpus froze",
        )
        first = FakeNotificationProvider().send(request)
        second = FakeNotificationProvider().send(request)
        assert isinstance(first, NotificationResult)
        assert first == second
        assert first.status == "delivered"
        assert first.message_id.startswith("msg-")

    def test_unsupported_channel_classified(self) -> None:
        fake = FakeNotificationProvider()
        with pytest.raises(ProviderInvalidRequestError):
            fake.send(
                NotificationRequest(
                    channel="telepathy",
                    recipient="ops@example.invalid",
                    subject="s",
                    body="b",
                )
            )
        assert fake.calls == 1

    def test_notification_method_set_is_transactional_only(self) -> None:
        methods = {
            name
            for name in dir(NotificationProvider)
            if not name.startswith("_")
        }
        assert methods == set(NOTIFICATION_METHODS)
        for forbidden in (
            "campaign",
            "schedule",
            "subscribe",
            "broadcast",
            "marketing",
        ):
            assert forbidden not in methods


# ---------------------------------------------------------------------------
# E — storage port (Ch II.5.5)
# ---------------------------------------------------------------------------


class TestStoragePort:
    def test_put_get_roundtrip_checksum(self) -> None:
        fake = FakeStorageProvider()
        data = b"protected artifact"
        stored = fake.put("artifacts/a.txt", data, content_type="text/plain")
        assert stored.version == 1
        assert stored.size_bytes == len(data)
        assert stored.checksum == __import__("hashlib").sha256(
            data
        ).hexdigest()
        loaded = fake.get("artifacts/a.txt")
        assert loaded.data == data
        assert loaded.object == stored

    def test_versions_are_append_only_and_pinned_reads_work(self) -> None:
        fake = FakeStorageProvider()
        first = fake.put("a", b"one", content_type="text/plain")
        second = fake.put("a", b"two", content_type="text/plain")
        assert second.version == first.version + 1
        assert fake.get("a").data == b"two"
        assert fake.get("a", version=first.version).data == b"one"

    def test_delete_fails_closed(self) -> None:
        fake = FakeStorageProvider()
        fake.put("a", b"one", content_type="text/plain")
        fake.delete("a")
        with pytest.raises(ProviderInvalidRequestError):
            fake.get("a")
        with pytest.raises(ProviderInvalidRequestError):
            fake.get("a", version=1)

    def test_access_strategy_is_deterministic_and_secretless(self) -> None:
        clock = SimulatedClock(start=100.0)
        fake = FakeStorageProvider(clock=clock)
        fake.put("a", b"one", content_type="text/plain")
        strategy = fake.access_strategy("a", ttl_seconds=60.0)
        assert strategy.kind in ACCESS_STRATEGY_KINDS
        assert strategy.target.startswith("fake-blob://")
        assert strategy.expires_at == 160.0
        clone = FakeStorageProvider(clock=SimulatedClock(start=100.0))
        clone.put("a", b"one", content_type="text/plain")
        assert (
            clone.access_strategy("a", ttl_seconds=60.0).target
            == strategy.target
        )
        for token in ("api_key", "secret", "token=", "credential"):
            assert token not in strategy.target

    def test_put_after_delete_fails_closed(self) -> None:
        fake = FakeStorageProvider()
        fake.put("a", b"one", content_type="text/plain")
        fake.delete("a")
        with pytest.raises(ProviderInvalidRequestError):
            fake.put("a", b"two", content_type="text/plain")


# ---------------------------------------------------------------------------
# F — registry / factory (Ch II.5.6)
# ---------------------------------------------------------------------------


class TestRegistryFactory:
    def test_registry_register_get_freeze(self) -> None:
        registry = ProviderRegistry()
        fake = FakeLLMProvider()
        registry.register("llm", "fake", fake)
        assert registry.get("llm") is fake
        assert registry.name("llm") == "fake"
        assert registry.ports() == ("llm",)
        assert registry.is_frozen is False
        registry.freeze()
        assert registry.is_frozen is True
        with pytest.raises(RuntimeError, match="frozen"):
            registry.register(
                "commerce", "fake", FakeCommerceProvider()
            )

    def test_registry_type_enforcement_names_port(self) -> None:
        registry = ProviderRegistry()
        with pytest.raises(TypeError, match="llm"):
            registry.register("llm", "fake", object())

    def test_registry_fails_closed_on_unknown_duplicate_invalid_name(
        self,
    ) -> None:
        registry = ProviderRegistry()
        with pytest.raises(ProviderConfigurationError):
            registry.register("bogus", "fake", FakeLLMProvider())
        registry.register("llm", "fake", FakeLLMProvider())
        with pytest.raises(ProviderConfigurationError, match="already bound"):
            registry.register("llm", "fake", FakeLLMProvider())
        with pytest.raises(ProviderConfigurationError, match="invalid"):
            registry.register("commerce", "Bad Name", FakeCommerceProvider())
        with pytest.raises(ProviderConfigurationError, match="not bound"):
            registry.get("storage")

    def test_config_selects_builders_at_composition_root(self) -> None:
        from app.forge.providers import ProviderFactory

        captured: list[ForgeConfig] = []

        def builder(config: ForgeConfig):
            captured.append(config)
            return _AlternateLLMProvider(name="chosen")

        factory = default_provider_factory()
        factory.register("llm", "chosen", builder)
        config = forge_config_from_values(provider_llm="chosen")
        registry = providers_from_config(config, factory=factory)
        assert registry.name("llm") == "chosen"
        assert registry.get("llm").provider_name == "chosen"
        assert captured == [config]
        assert registry.is_frozen is True

    def test_unknown_provider_name_fails_closed(self) -> None:
        config = forge_config_from_values(provider_llm="openrouter")
        with pytest.raises(
            ProviderConfigurationError, match="no provider builder"
        ):
            providers_from_config(config)

    def test_default_factory_binds_fakes_for_all_ports(self) -> None:
        config = ForgeConfig(environment="test")
        registry = providers_from_config(config)
        assert registry.bound_names() == {
            "llm": "fake",
            "commerce": "fake",
            "notification": "fake",
            "storage": "fake",
        }
        # every binding satisfies its port protocol
        from app.forge.providers.registry import PORT_PROTOCOLS

        for port in PORTS:
            assert isinstance(registry.get(port), PORT_PROTOCOLS[port])

    def test_no_provider_identifier_branching_in_domain(self) -> None:
        """Ch II.5.6: no `if provider == whop` spread through domain code."""

        for path in _vendor_scan_files():
            tree = _parse(path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare):
                    continue
                operands = [node.left, *node.comparators]
                for operand in operands:
                    if isinstance(operand, ast.Constant) and isinstance(
                        operand.value, str
                    ):
                        lowered = operand.value.lower()
                        for token in VENDOR_TOKENS:
                            assert token not in lowered, (
                                f"{path} compares against vendor id "
                                f"{operand.value!r}"
                            )


# ---------------------------------------------------------------------------
# G — circuit / fallback (Ch II.5.8)
# ---------------------------------------------------------------------------


class TestCircuitFallback:
    def test_breaker_opens_and_short_circuits_without_invoking(self) -> None:
        clock = SimulatedClock()
        breaker = CircuitBreaker(
            name="llm",
            failure_threshold=3,
            recovery_seconds=30.0,
            clock=clock.now,
        )
        attempts: list[int] = []

        def failing() -> str:
            attempts.append(1)
            raise ProviderTimeoutError("timeout", provider_type="llm")

        for _ in range(3):
            with pytest.raises(ProviderTimeoutError):
                breaker.call(failing)
        assert breaker.state is CircuitState.OPEN
        assert attempts == [1, 1, 1]
        with pytest.raises(ProviderUnavailableError):
            breaker.call(failing)
        assert attempts == [1, 1, 1]  # short-circuited: call never invoked

    def test_breaker_recovery_half_open_probe_closes(self) -> None:
        clock = SimulatedClock()
        breaker = CircuitBreaker(
            name="llm",
            failure_threshold=1,
            recovery_seconds=30.0,
            clock=clock.now,
        )

        def failing() -> str:
            raise ProviderTimeoutError("timeout", provider_type="llm")

        with pytest.raises(ProviderTimeoutError):
            breaker.call(failing)
        assert breaker.state is CircuitState.OPEN
        clock.advance(30.0)
        assert breaker.state is CircuitState.HALF_OPEN
        assert breaker.call(lambda: "probe-ok") == "probe-ok"
        assert breaker.state is CircuitState.CLOSED
        assert breaker.consecutive_failures == 0

    def test_breaker_reopens_after_failed_probe(self) -> None:
        clock = SimulatedClock()
        breaker = CircuitBreaker(
            name="commerce",
            failure_threshold=1,
            recovery_seconds=10.0,
            clock=clock.now,
        )

        def failing() -> str:
            raise ProviderUnavailableError(
                "down", provider_type="commerce"
            )

        with pytest.raises(ProviderUnavailableError):
            breaker.call(failing)
        clock.advance(10.0)
        assert breaker.state is CircuitState.HALF_OPEN
        with pytest.raises(ProviderUnavailableError):
            breaker.call(failing)
        assert breaker.state is CircuitState.OPEN

    def test_breaker_ignores_non_availability_failures(self) -> None:
        breaker = CircuitBreaker(
            name="commerce",
            failure_threshold=1,
            recovery_seconds=10.0,
            clock=SimulatedClock().now,
        )

        def caller_error() -> str:
            raise ProviderInvalidRequestError(
                "caller mistake", provider_type="commerce"
            )

        for _ in range(3):
            with pytest.raises(ProviderInvalidRequestError):
                breaker.call(caller_error)
        assert breaker.state is CircuitState.CLOSED

    def test_llm_fallback_selects_alternate_provider(self) -> None:
        primary = FakeLLMProvider(
            behavior=FakeBehavior(failure_class="unavailable"),
            name="fake-primary",
        )
        alternate = FakeLLMProvider(name="fake-alternate")
        request = LLMRequest(prompt="fallback probe", model="m-1")
        # expected output computed on a FRESH instance so the alternate's
        # call counter is not touched by the comparison itself:
        expected = FakeLLMProvider(name="fake-alternate").generate(
            request, timeout_seconds=5.0
        ).text
        response = run_with_fallback(
            FallbackPolicy.for_port("llm"),
            lambda: primary.generate(request, timeout_seconds=5.0),
            alternate=lambda: alternate.generate(request, timeout_seconds=5.0),
        )
        assert response.text == expected
        assert primary.calls == 1
        assert alternate.calls == 1

    def test_commerce_outage_propagates_without_fabricated_success(self) -> None:
        down = FakeCommerceProvider(
            behavior=FakeBehavior(failure_class="unavailable")
        )
        with pytest.raises(ProviderUnavailableError):
            run_with_fallback(
                FallbackPolicy.for_port("commerce"),
                lambda: down.create_checkout(
                    "cus-1", idempotency_key="key-1"
                ),
            )

    def test_notification_outage_records_failure_never_delivery(self) -> None:
        down = FakeNotificationProvider(
            behavior=FakeBehavior(failure_class="unavailable")
        )
        request = NotificationRequest(
            channel="email",
            recipient="ops@example.invalid",
            subject="s",
            body="b",
        )

        def on_failure(exc: ProviderError) -> NotificationResult:
            return NotificationResult(
                message_id="msg-failed",
                status="failed",
                failure_class=exc.failure_class,
            )

        result = run_with_fallback(
            FallbackPolicy.for_port("notification"),
            lambda: down.send(request),
            on_failure=on_failure,
        )
        assert result.status == "failed"
        assert result.status != "delivered"
        assert result.failure_class == "unavailable"
        # without an explicit failure handler the failure propagates:
        with pytest.raises(ProviderUnavailableError):
            run_with_fallback(
                FallbackPolicy.for_port("notification"),
                lambda: down.send(request),
            )

    def test_no_fallback_policy_fabricates_success(self) -> None:
        def boom() -> str:
            raise ProviderUnavailableError("down", provider_type="probe")

        for port in PORTS:
            with pytest.raises(ProviderError):
                run_with_fallback(FallbackPolicy.for_port(port), boom)

    def test_authorization_decisions_ignore_provider_state(self) -> None:
        """Ch II.5.8: authorization never fails open because a provider is down.

        Provider state is structurally absent from the policy engine (no
        provider input exists), and decisions are identical under healthy vs.
        downed registries.
        """

        engine = DefaultDenyPolicyEngine()
        params = inspect.signature(engine.decide).parameters
        assert not any("provider" in name for name in params)

        exposures = (
            ProductExposure.PUBLIC_TEACHING,
            ProductExposure.SUBSCRIBER_MODEL,
            ProductExposure.INTERNAL_CODE,
        )

        def decisions(registry: ProviderRegistry) -> list[bool]:
            # container carries this registry; decisions are pure over
            # (principal, context, action, resource) regardless.
            ForgeServiceContainer(
                config=ForgeConfig(environment="test"), providers=registry
            )
            return [
                _view(
                    AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER),
                    exposure,
                ).allowed
                for exposure in exposures
            ]

        healthy = decisions(providers_from_config(ForgeConfig()))
        downed = decisions(_registry_with(FakeBehavior(
            failure_class="unavailable"
        )))
        assert healthy == downed
        # default-deny still holds while providers are down:
        assert (
            _view(
                AuthorizationContext.empty(),
                ProductExposure.SUBSCRIBER_MODEL,
            ).allowed
            is False
        )


# ---------------------------------------------------------------------------
# H — fake determinism & scenario laws (Ch II.5.9)
# ---------------------------------------------------------------------------


class TestFakeScenarios:
    def test_scenario_success_and_determinism_all_ports(self) -> None:
        request = LLMRequest(prompt="success", model="m-1")
        llm_a, llm_b = FakeLLMProvider(), FakeLLMProvider()
        assert llm_a.generate(request, timeout_seconds=5.0) == llm_b.generate(
            request, timeout_seconds=5.0
        )

        commerce_a, commerce_b = (
            FakeCommerceProvider(),
            FakeCommerceProvider(),
        )
        assert commerce_a.create_checkout(
            "c", idempotency_key="k"
        ) == commerce_b.create_checkout("c", idempotency_key="k")

        note_request = NotificationRequest(
            channel="email", recipient="a@b.invalid", subject="s", body="b"
        )
        assert FakeNotificationProvider().send(
            note_request
        ) == FakeNotificationProvider().send(note_request)

        storage_a, storage_b = FakeStorageProvider(), FakeStorageProvider()
        assert storage_a.put(
            "k", b"v", content_type="text/plain"
        ) == storage_b.put("k", b"v", content_type="text/plain")

    def test_scenario_latency_simulated(self) -> None:
        clock = SimulatedClock()
        fake = FakeLLMProvider(
            behavior=FakeBehavior(latency_seconds=2.0), clock=clock
        )
        started = time.monotonic()
        response = fake.generate(
            LLMRequest(prompt="slow but within budget", model="m-1"),
            timeout_seconds=10.0,
        )
        wall = time.monotonic() - started
        assert response.text  # success: latency within budget
        assert clock.now() == 2.0
        assert wall < 0.5  # simulated, never slept

    def test_scenario_timeout_notification(self) -> None:
        clock = SimulatedClock()
        fake = FakeNotificationProvider(
            behavior=FakeBehavior(latency_seconds=20.0), clock=clock
        )
        with pytest.raises(ProviderTimeoutError):
            fake.send(
                NotificationRequest(
                    channel="email", recipient="a@b.invalid", subject="s",
                    body="b",
                )
            )
        assert clock.now() == 20.0
        assert fake.calls == 1

    def test_scenario_hard_failure_all_ports(self) -> None:
        for failure_class in FAILURE_CLASSES:
            behavior = FakeBehavior(failure_class=failure_class)
            expected = ERROR_BY_CLASS[failure_class]

            llm = FakeLLMProvider(behavior=behavior)
            with pytest.raises(expected):
                llm.generate(
                    LLMRequest(prompt="x", model="m-1"), timeout_seconds=5.0
                )
            assert llm.calls == 1

            commerce = FakeCommerceProvider(behavior=behavior)
            with pytest.raises(expected):
                commerce.get_customer("cus-1")
            assert commerce.calls == 1

            note = FakeNotificationProvider(behavior=behavior)
            with pytest.raises(expected):
                note.send(
                    NotificationRequest(
                        channel="email", recipient="a@b.invalid",
                        subject="s", body="b",
                    )
                )
            assert note.calls == 1

            storage = FakeStorageProvider(behavior=behavior)
            with pytest.raises(expected):
                storage.put("k", b"v", content_type="text/plain")
            assert storage.calls == 1

    def test_fakes_never_sleep_wall_clock(self) -> None:
        shared = SimulatedClock()
        latency = FakeBehavior(latency_seconds=8.0)
        started = time.monotonic()
        FakeLLMProvider(behavior=latency, clock=shared).generate(
            LLMRequest(prompt="x", model="m-1"), timeout_seconds=10.0
        )
        FakeCommerceProvider(behavior=latency, clock=shared).get_customer(
            "c"
        )
        FakeNotificationProvider(behavior=latency, clock=shared).send(
            NotificationRequest(
                channel="email", recipient="a@b.invalid", subject="s",
                body="b",
            )
        )
        FakeStorageProvider(behavior=latency, clock=shared).put(
            "k", b"v", content_type="text/plain"
        )
        wall = time.monotonic() - started
        assert shared.now() == 32.0  # 4 x 8s of *simulated* latency
        assert wall < 1.0


# ---------------------------------------------------------------------------
# I — container seam, readiness, diagnostics, endpoints, config
# ---------------------------------------------------------------------------


class TestContainerReadiness:
    def test_unwired_ports_report_not_configured(self) -> None:
        container = ForgeServiceContainer(config=ForgeConfig(environment="test"))
        assert container.providers is None
        deps = container.as_readiness_dependencies()
        for port in PORTS:
            assert deps[port] == {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": f"{port} port not wired at the composition root",
            }

    def test_wired_fakes_report_ready_without_blocking(self) -> None:
        container = ForgeServiceContainer(
            config=ForgeConfig(environment="test"),
            providers=providers_from_config(ForgeConfig(environment="test")),
        )
        deps = container.as_readiness_dependencies()
        for port in PORTS:
            assert deps[port]["status"] == "READY"
            assert deps[port]["required"] is False
        readiness = _readiness_of(container)
        assert readiness["status"] == "ready"

    def test_scripted_outage_reports_unavailable_but_never_blocks(self) -> None:
        container = ForgeServiceContainer(
            config=ForgeConfig(environment="test"),
            providers=_registry_with(
                FakeBehavior(failure_class="unavailable")
            ),
        )
        deps = container.as_readiness_dependencies()
        for port in PORTS:
            assert deps[port]["status"] == "UNAVAILABLE"
            assert deps[port]["required"] is False
        assert _readiness_of(container)["status"] == "ready"

    def test_health_probe_exception_is_absorbed_redacted(self) -> None:
        sentinel = "SENTINEL_SECRET_VALUE"

        class _ExplodingHealth:
            def generate(self, *args, **kwargs):  # pragma: no cover
                raise AssertionError("must not be called here")

            def capabilities(self) -> frozenset[str]:
                return frozenset()

            def health(self):
                raise RuntimeError(sentinel)

        registry = ProviderRegistry()
        registry.register("llm", "fake", _ExplodingHealth())
        registry.freeze()
        container = ForgeServiceContainer(
            config=ForgeConfig(environment="test"), providers=registry
        )
        deps = container.as_readiness_dependencies()
        entry = deps["llm"]
        assert entry["status"] == "UNAVAILABLE"
        assert "RuntimeError" in entry["note"]
        assert sentinel not in entry["note"]
        assert _readiness_of(container)["status"] == "ready"

    def test_future_vendor_dependencies_stay_not_configured(self) -> None:
        container = ForgeServiceContainer(
            config=ForgeConfig(environment="test"),
            providers=providers_from_config(ForgeConfig(environment="test")),
        )
        deps = container.as_readiness_dependencies()
        assert set(PORTS) <= set(deps)
        non_healthy = {
            "NOT_CONFIGURED",
            "NOT_APPLICABLE",
            "NOT_IMPLEMENTED",
        }
        for key in ("openrouter", "whop", "market_data", "ask_cerebus", "pgvector"):
            assert deps[key]["status"] in non_healthy
            assert deps[key]["required"] is False

    def test_diagnostics_redact_credential_values(self) -> None:
        sentinel_or = "SENTINEL_OR_KEY"
        sentinel_wh = "SENTINEL_WH_KEY"
        config = ForgeConfig(
            environment="test",
            openrouter_api_key=sentinel_or,
            whop_api_key=sentinel_wh,
        )
        container = ForgeServiceContainer(
            config=config,
            providers=providers_from_config(config),
        )
        diagnostics = container.redacted_diagnostics()
        assert diagnostics["providers_wired"] is True
        assert diagnostics["provider_bindings"] == {
            "llm": "fake",
            "commerce": "fake",
            "notification": "fake",
            "storage": "fake",
        }
        config_diagnostics = diagnostics["config"]
        assert config_diagnostics["openrouter_api_key_configured"] is True
        assert config_diagnostics["whop_api_key_configured"] is True
        assert config_diagnostics["provider_llm"] == "fake"
        for sentinel in (sentinel_or, sentinel_wh):
            assert sentinel not in json.dumps(diagnostics, default=str)
            assert sentinel not in repr(config)
            assert sentinel not in repr(diagnostics)

    def test_ready_endpoint_surfaces_honest_provider_entries(self) -> None:
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.get("/forge/v1/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"
        deps = body["dependencies"]
        for port in PORTS:
            assert deps[port]["status"] == "READY"
            assert deps[port]["required"] is False
        assert deps["openrouter"]["status"] == "NOT_CONFIGURED"
        assert deps["whop"]["status"] == "NOT_CONFIGURED"

    def test_config_env_provider_selection_and_validation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FORGE_PROVIDER_LLM", "Alternate")
        monkeypatch.setenv("FORGE_PROVIDER_TIMEOUT_SECONDS", "2.5")
        monkeypatch.setenv("FORGE_CIRCUIT_FAILURE_THRESHOLD", "7")
        config = forge_config_from_environment()
        assert config.provider_llm == "alternate"  # normalized token
        assert config.provider_commerce == "fake"
        assert config.provider_timeout_seconds == 2.5
        assert config.circuit_failure_threshold == 7

        monkeypatch.setenv("FORGE_PROVIDER_COMMERCE", "Bad Name")
        with pytest.raises(ValueError, match="invalid provider name env"):
            forge_config_from_environment()
        monkeypatch.delenv("FORGE_PROVIDER_COMMERCE")
        monkeypatch.setenv("FORGE_PROVIDER_TIMEOUT_SECONDS", "abc")
        with pytest.raises(ValueError, match="invalid float env"):
            forge_config_from_environment()

        with pytest.raises(ValueError, match="invalid provider name"):
            ForgeConfig(environment="test", provider_storage="UPPER")
        with pytest.raises(ValueError, match="provider_timeout_seconds"):
            ForgeConfig(environment="test", provider_timeout_seconds=0)


def _readiness_of(container: ForgeServiceContainer) -> dict:
    from app.forge.service.health import ForgeHealthService

    return ForgeHealthService(container=container).readiness()


# ---------------------------------------------------------------------------
# J — frozen Acceptance II.5 (verbatim five clauses)
# ---------------------------------------------------------------------------


class TestFrozenAcceptanceII5:
    def test_core_application_passes_with_only_fake_providers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from fastapi.testclient import TestClient

        from app.main import _build_forge_container, app

        for var in ("FORGE_OPENROUTER_API_KEY", "FORGE_WHOP_API_KEY"):
            monkeypatch.delenv(var, raising=False)

        container = _build_forge_container()
        assert container.providers is not None
        assert set(container.providers.bound_names().values()) == {"fake"}

        client = TestClient(app)
        for path in ("/forge/v1/health", "/forge/v1/ready", "/forge/v1/meta"):
            assert client.get(path).status_code == 200, path

        # credential env present does NOT change fake selection (carried,
        # unread) and never leaks into diagnostics:
        sentinel = "SENTINEL_OR_KEY"
        monkeypatch.setenv("FORGE_OPENROUTER_API_KEY", sentinel)
        config = forge_config_from_environment()
        assert config.provider_llm == "fake"
        registry = providers_from_config(config)
        assert registry.bound_names()["llm"] == "fake"
        diagnostics = config.redacted_diagnostics()
        assert diagnostics["openrouter_api_key_configured"] is True
        assert sentinel not in json.dumps(diagnostics, default=str)
        assert sentinel not in repr(config)

    def test_no_provider_identifier_is_required_as_core_domain_pk(self) -> None:
        for path in _vendor_scan_files():
            tree = _parse(path)
            for text in _string_constants(tree):
                lowered = text.lower()
                for token in VENDOR_TOKENS:
                    assert token not in lowered, (
                        f"{path} carries vendor identifier in {text!r}"
                    )
            # no field/variable in domain code is named after a provider
            for node in ast.walk(tree):
                if isinstance(node, ast.AnnAssign) and isinstance(
                    node.target, ast.Name
                ):
                    lowered = node.target.id.lower()
                    for token in VENDOR_TOKENS:
                        assert token not in lowered, (
                            f"{path} field {node.target.id} is vendor-bound"
                        )

    def test_commerce_outage_cannot_grant_access(self) -> None:
        down = FakeCommerceProvider(
            behavior=FakeBehavior(failure_class="unavailable")
        )
        grant_state = {"granted": False}

        def checkout_and_grant():
            session = down.create_checkout(
                "cus-1", idempotency_key="grant-key"
            )
            grant_state["granted"] = True
            return session

        with pytest.raises(ProviderUnavailableError):
            run_with_fallback(
                FallbackPolicy.for_port("commerce"), checkout_and_grant
            )
        assert grant_state["granted"] is False

        # access decisions remain deny-by-default with providers down:
        decision = _view(
            AuthorizationContext.empty(),
            ProductExposure.SUBSCRIBER_MODEL,
        )
        assert decision.allowed is False

    def test_llm_outage_cannot_corrupt_canonical_state(self) -> None:
        registry = _canonical_registry()
        before = _canonical_snapshot(registry)
        assert len(before) == 2

        failing_llm = FakeLLMProvider(
            behavior=FakeBehavior(failure_class="unavailable")
        )
        with pytest.raises(ProviderUnavailableError):
            failing_llm.generate(
                LLMRequest(prompt="mutate canonical state", model="m-1"),
                timeout_seconds=5.0,
            )

        after = _canonical_snapshot(registry)
        assert after == before

        # structural isolation: canonical-state modules never import the LLM
        # port (so no code path can route an outage into a state write).
        for relative in (
            "forge/canonical.py",
            "forge/schemas.py",
            "forge/provenance.py",
        ):
            tree = _parse(APP_ROOT / relative)
            for module in _imported_modules(tree):
                assert "app.forge.providers" not in module, (
                    f"{relative} imports {module}"
                )
        for path in sorted((APP_ROOT / "forge" / "persistence").glob("*.py")):
            tree = _parse(path)
            for module in _imported_modules(tree):
                assert "app.forge.providers" not in module, (
                    f"{path.name} imports {module}"
                )

    def test_adapter_replacement_is_composition_change(self) -> None:
        config = forge_config_from_values(
            provider_llm="alternate",
            provider_commerce="alternate",
            provider_notification="alternate",
            provider_storage="alternate",
        )
        registry = providers_from_config(config, factory=_alternate_factory())
        assert registry.bound_names() == {
            "llm": "alternate",
            "commerce": "alternate",
            "notification": "alternate",
            "storage": "alternate",
        }
        # swapping back is equally a config-only change:
        swapped = providers_from_config(
            forge_config_from_values(provider_llm="fake"),
            factory=_alternate_factory(),
        )
        assert swapped.name("llm") == "fake"
        # and domain modules never reference the factory/registry at all
        # (composition root only) — re-checked structurally here:
        for path in _domain_py_files():
            tree = _parse(path)
            for module in _imported_modules(tree):
                assert module != "app.forge.providers.registry", (
                    f"{path} binds providers directly"
                )


# ---------------------------------------------------------------------------
# Ch II.5.10 — identical contract suite across implementations
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant", ["fake", "alternate"])
class TestReplacementContractMatrix:
    """The same harness runs against every fake and every alternate adapter —
    concrete adapters (Book IV/VI) join this matrix without suite changes."""

    def test_llm_contract_matrix(self, variant: str) -> None:
        run_llm_contract(_registry_for(variant).get("llm"))

    def test_commerce_contract_matrix(self, variant: str) -> None:
        provider = _registry_for(variant).get("commerce")
        run_commerce_contract(provider, sign=provider.sign)

    def test_notification_contract_matrix(self, variant: str) -> None:
        run_notification_contract(_registry_for(variant).get("notification"))

    def test_storage_contract_matrix(self, variant: str) -> None:
        run_storage_contract(
            _registry_for(variant).get("storage"),
            key=f"contract-{variant}",
        )
