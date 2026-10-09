"""Deterministic fake providers (Book II / Bloc II.5, Ch II.5.9).

Ch II.5.9 — fakes support: success, latency, timeout, duplicate events,
out-of-order events, invalid signature/event shape where applicable, rate
limit, hard failure.

Determinism laws (tested):

- No randomness: every id/digest is sha256 over the inputs.
- No real sleeping: time flows through `SimulatedClock`; latency is simulated
  by advancing the clock, so tests cost ~zero wall-clock.
- No network: fakes are in-process; handoff/signing targets use inert
  identifiers (`.invalid`, `fake-blob://`).
- Same config => byte-identical outputs.

Fakes never retry: `calls` increments once per attempt, so a scripted failure
proves no internal retry loop.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from app.forge.providers.commerce import (
    CHECKOUT_STATUSES,
    CUSTOMER_STATUSES,
    EVENT_TYPES,
    SUBSCRIPTION_STATUSES,
    CheckoutSession,
    CommerceCustomer,
    CommerceSubscription,
    ProviderEvent,
)
from app.forge.providers.doctrine import ProviderHealth
from app.forge.providers.errors import (
    ERROR_BY_CLASS,
    FAILURE_CLASSES,
    ProviderAuthenticationFailedError,
    ProviderCancelledError,
    ProviderInvalidRequestError,
    ProviderTimeoutError,
)
from app.forge.providers.llm import (
    CAPABILITY_STRUCTURED_OUTPUT,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from app.forge.providers.notification import (
    CHANNELS,
    NotificationRequest,
    NotificationResult,
)
from app.forge.providers.storage import (
    ACCESS_STRATEGY_KINDS,
    AccessStrategy,
    StoredObject,
    StoredObjectData,
)

# Default per-call budget for fake operations whose protocol signature has no
# explicit timeout parameter (LLM takes the caller's timeout explicitly).
DEFAULT_FAKE_TIMEOUT_BUDGET = 10.0

# Doctrine-safe failure messages — never payloads, never internals.
_SAFE_MESSAGES: dict[str, str] = {
    "unavailable": "provider unavailable",
    "timeout": "provider call exceeded timeout",
    "rate_limited": "provider rate limited",
    "invalid_request": "provider rejected invalid request",
    "authentication_failed": "provider authentication failed",
    "upstream_rejected": "provider upstream rejected request",
    "malformed_response": "provider returned malformed response",
    "unknown": "provider unknown failure",
}


def _hash(*parts: object) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(str(part).encode("utf-8"))
        digest.update(b"|")
    return digest.hexdigest()


class SimulatedClock:
    """Injected time source. Fakes advance it instead of sleeping."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = float(start)

    def now(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("clock cannot move backwards")
        self._now += float(seconds)


@dataclass(frozen=True)
class FakeBehavior:
    """Scripted behavior for every fake scenario."""

    failure_class: str | None = None
    latency_seconds: float = 0.0
    rate_limit_retry_after: float = 1.0

    def __post_init__(self) -> None:
        if self.failure_class is not None and (
            self.failure_class not in FAILURE_CLASSES
        ):
            raise ValueError(f"invalid failure class {self.failure_class!r}")
        if self.latency_seconds < 0:
            raise ValueError("latency_seconds must be >= 0")
        if self.rate_limit_retry_after < 0:
            raise ValueError("rate_limit_retry_after must be >= 0")


def _apply_transport(
    behavior: FakeBehavior,
    *,
    budget: float,
    clock: SimulatedClock,
    provider_type: str,
    provider_name: str,
) -> None:
    """Apply scripted latency then scripted failure. Raises classified errors.

    Timeout is evaluated against the simulated clock: latency exceeding the
    budget raises ProviderTimeoutError before any output is produced.
    """
    if behavior.latency_seconds > 0:
        clock.advance(behavior.latency_seconds)
        if behavior.latency_seconds > budget:
            raise ProviderTimeoutError(
                _SAFE_MESSAGES["timeout"],
                provider_type=provider_type,
                provider_name=provider_name,
            )
    failure_class = behavior.failure_class
    if failure_class is not None:
        error_cls = ERROR_BY_CLASS[failure_class]
        kwargs: dict[str, Any] = {}
        if failure_class == "rate_limited":
            kwargs["retry_after_seconds"] = behavior.rate_limit_retry_after
        raise error_cls(
            _SAFE_MESSAGES[failure_class],
            provider_type=provider_type,
            provider_name=provider_name,
            **kwargs,
        )


class FakeLLMProvider:
    """Deterministic fake LLM (Ch II.5.2/II.5.9). Transport only."""

    provider_type = "llm"

    def __init__(
        self,
        *,
        behavior: FakeBehavior | None = None,
        clock: SimulatedClock | None = None,
        model: str = "fake-model-1",
        structured: bool = True,
        name: str = "fake",
    ) -> None:
        self._behavior = behavior or FakeBehavior()
        self._clock = clock or SimulatedClock()
        self._model = model
        self._structured = structured
        self._name = name
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def capabilities(self) -> frozenset[str]:
        if self._structured:
            return frozenset({CAPABILITY_STRUCTURED_OUTPUT})
        return frozenset()

    def generate(
        self,
        request: LLMRequest,
        *,
        timeout_seconds: float,
        cancel: Any = None,
    ) -> LLMResponse:
        self.calls += 1
        if timeout_seconds <= 0:
            raise ProviderInvalidRequestError(
                "timeout_seconds must be > 0",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        if cancel is not None and cancel():
            raise ProviderCancelledError(
                "call cancelled by caller",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        _apply_transport(
            self._behavior,
            budget=timeout_seconds,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        prompt_tokens = max(1, len(request.prompt) // 4)
        text = f"fake-llm:{_hash(request.prompt, request.model)[:16]}"
        completion_tokens = max(1, len(text) // 4)
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = round(total_tokens * 0.002 / 1000.0, 8)
        structured: Mapping[str, Any] | None = None
        if request.response_schema is not None:
            if CAPABILITY_STRUCTURED_OUTPUT not in self.capabilities():
                raise ProviderInvalidRequestError(
                    "structured output capability not available",
                    provider_type=self.provider_type,
                    provider_name=self._name,
                )
            schema = request.response_schema
            required = schema.get("required") if isinstance(schema, Mapping) else None
            if not isinstance(schema, Mapping) or not isinstance(
                required, list
            ) or not required or not all(isinstance(k, str) for k in required):
                raise ProviderInvalidRequestError(
                    "malformed response schema",
                    provider_type=self.provider_type,
                    provider_name=self._name,
                )
            structured = {
                key: f"fake-value:{_hash(key, request.prompt)[:8]}"
                for key in required
            }
        return LLMResponse(
            text=text,
            model=request.model,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost_usd,
            ),
            structured=structured,
            finish_reason="stop",
        )

    def health(self) -> ProviderHealth:
        scripted = self._behavior.failure_class is not None
        return ProviderHealth(
            provider_type=self.provider_type,
            provider_name=self._name,
            status="unavailable" if scripted else "healthy",
            detail="scripted failure" if scripted else "deterministic fake",
        )


class FakeCommerceProvider:
    """Deterministic fake commerce provider (Ch II.5.3/II.5.9).

    Event scenarios (duplicate / out-of-order / invalid signature / invalid
    shape) are driven through the REAL `parse_event` path so contract tests
    exercise normalization, not a shortcut.
    """

    provider_type = "commerce"

    def __init__(
        self,
        *,
        behavior: FakeBehavior | None = None,
        clock: SimulatedClock | None = None,
        name: str = "fake",
        subscription_status: str = "active",
        event_script: Sequence[bytes] = (),
        signature_secret: str = "fake-signature-secret",
    ) -> None:
        if subscription_status not in SUBSCRIPTION_STATUSES:
            raise ValueError(f"invalid subscription status {subscription_status!r}")
        self._behavior = behavior or FakeBehavior()
        self._clock = clock or SimulatedClock()
        self._name = name
        self._subscription_status = subscription_status
        self._event_script = tuple(event_script)
        self._signature_secret = signature_secret
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def sign(self, raw: bytes) -> str:
        """Fake-only helper producing a valid signature for `raw`."""

        return "v1=" + _hash("sig", self._signature_secret, raw)

    def create_checkout(
        self, customer_id: str, *, idempotency_key: str
    ) -> CheckoutSession:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if not customer_id or not idempotency_key:
            raise ProviderInvalidRequestError(
                "customer_id and idempotency_key are required",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        session_id = f"cs-{_hash(customer_id, idempotency_key)[:16]}"
        return CheckoutSession(
            session_id=session_id,
            customer_id=customer_id,
            handoff_url=f"https://checkout.invalid/session/{session_id}",
            status="open",
        )

    def get_customer(self, customer_id: str) -> CommerceCustomer:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if not customer_id:
            raise ProviderInvalidRequestError(
                "customer_id is required",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        return CommerceCustomer(
            customer_id=customer_id,
            status=CUSTOMER_STATUSES[0],
            subscription_id=f"sub_{_hash(customer_id)[:12]}",
        )

    def get_subscription(self, subscription_id: str) -> CommerceSubscription:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if not subscription_id:
            raise ProviderInvalidRequestError(
                "subscription_id is required",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        return CommerceSubscription(
            subscription_id=subscription_id,
            customer_id=f"cus_{_hash(subscription_id)[:12]}",
            status=self._subscription_status,
        )

    def parse_event(self, raw: bytes, signature: str) -> ProviderEvent:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if signature != self.sign(raw):
            raise ProviderAuthenticationFailedError(
                "event signature verification failed",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ProviderInvalidRequestError(
                "event shape invalid: not json",
                provider_type=self.provider_type,
                provider_name=self._name,
            ) from None
        if not isinstance(data, dict):
            raise ProviderInvalidRequestError(
                "event shape invalid: not an object",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        event_id = data.get("event_id")
        event_type = data.get("event_type")
        occurred_at = data.get("occurred_at")
        if (
            not isinstance(event_id, str)
            or not event_id
            or not isinstance(event_type, str)
            or event_type not in EVENT_TYPES
            or isinstance(occurred_at, bool)
            or not isinstance(occurred_at, (int, float))
        ):
            raise ProviderInvalidRequestError(
                "event shape invalid: required fields",
                provider_type=self.provider_type,
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

    def scripted_events(self) -> tuple[ProviderEvent, ...]:
        """Fake-only harness: normalize the configured webhook script through
        the real `parse_event` path (duplicate/out-of-order deliveries)."""

        return tuple(
            self.parse_event(raw, self.sign(raw)) for raw in self._event_script
        )

    def health(self) -> ProviderHealth:
        scripted = self._behavior.failure_class is not None
        return ProviderHealth(
            provider_type=self.provider_type,
            provider_name=self._name,
            status="unavailable" if scripted else "healthy",
            detail="scripted failure" if scripted else "deterministic fake",
        )


class FakeNotificationProvider:
    """Deterministic fake transactional notifier (Ch II.5.4/II.5.9)."""

    provider_type = "notification"

    def __init__(
        self,
        *,
        behavior: FakeBehavior | None = None,
        clock: SimulatedClock | None = None,
        name: str = "fake",
    ) -> None:
        self._behavior = behavior or FakeBehavior()
        self._clock = clock or SimulatedClock()
        self._name = name
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def send(self, request: NotificationRequest) -> NotificationResult:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if request.channel not in CHANNELS:
            raise ProviderInvalidRequestError(
                "unsupported notification channel",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        if not request.recipient:
            raise ProviderInvalidRequestError(
                "recipient is required",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        return NotificationResult(
            message_id=f"msg-{_hash(request.channel, request.recipient, request.subject)[:16]}",
            status="delivered",
        )

    def health(self) -> ProviderHealth:
        scripted = self._behavior.failure_class is not None
        return ProviderHealth(
            provider_type=self.provider_type,
            provider_name=self._name,
            status="unavailable" if scripted else "healthy",
            detail="scripted failure" if scripted else "deterministic fake",
        )


class FakeStorageProvider:
    """Deterministic fake object/blob storage (Ch II.5.5/II.5.9).

    Append-only versions; delete tombstones the key (all reads then fail
    closed); `access_strategy` yields an inert signed target — no secret
    material, no network.
    """

    provider_type = "storage"

    def __init__(
        self,
        *,
        behavior: FakeBehavior | None = None,
        clock: SimulatedClock | None = None,
        name: str = "fake",
        access_kind: str = "signed_url",
    ) -> None:
        if access_kind not in ACCESS_STRATEGY_KINDS:
            raise ValueError(f"invalid access strategy kind {access_kind!r}")
        self._behavior = behavior or FakeBehavior()
        self._clock = clock or SimulatedClock()
        self._name = name
        self._access_kind = access_kind
        self._store: dict[str, list[tuple[int, bytes, str]]] = {}
        self._deleted: set[str] = set()
        self.calls = 0

    @property
    def provider_name(self) -> str:
        return self._name

    def put(self, key: str, data: bytes, *, content_type: str) -> StoredObject:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if not key:
            raise ProviderInvalidRequestError(
                "storage key is required",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        if key in self._deleted:
            raise ProviderInvalidRequestError(
                "storage key is deleted",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        versions = self._store.setdefault(key, [])
        version = len(versions) + 1
        versions.append((version, bytes(data), content_type))
        return StoredObject(
            key=key,
            version=version,
            size_bytes=len(data),
            content_type=content_type,
            checksum=hashlib.sha256(data).hexdigest(),
        )

    def get(self, key: str, *, version: int | None = None) -> StoredObjectData:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if not key or key not in self._store:
            raise ProviderInvalidRequestError(
                "storage key not found",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        if key in self._deleted:
            raise ProviderInvalidRequestError(
                "storage key is deleted",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        versions = self._store[key]
        if version is None:
            version = versions[-1][0]
        for stored_version, data, content_type in versions:
            if stored_version == version:
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
            provider_type=self.provider_type,
            provider_name=self._name,
        )

    def delete(self, key: str) -> None:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if not key or key not in self._store:
            raise ProviderInvalidRequestError(
                "storage key not found",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        if key in self._deleted:
            raise ProviderInvalidRequestError(
                "storage key is deleted",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        self._deleted.add(key)

    def access_strategy(
        self, key: str, *, ttl_seconds: float
    ) -> AccessStrategy:
        self.calls += 1
        _apply_transport(
            self._behavior,
            budget=DEFAULT_FAKE_TIMEOUT_BUDGET,
            clock=self._clock,
            provider_type=self.provider_type,
            provider_name=self._name,
        )
        if ttl_seconds <= 0:
            raise ProviderInvalidRequestError(
                "ttl_seconds must be > 0",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        if not key or key not in self._store or key in self._deleted:
            raise ProviderInvalidRequestError(
                "storage key not found",
                provider_type=self.provider_type,
                provider_name=self._name,
            )
        current_version = self._store[key][-1][0]
        expires_at = self._clock.now() + ttl_seconds
        signature = _hash("access", key, current_version, int(ttl_seconds))[:16]
        target = (
            f"fake-blob://{key}?version={current_version}"
            f"&expires={int(expires_at)}&sig={signature}"
        )
        return AccessStrategy(
            kind=self._access_kind,
            target=target,
            expires_at=expires_at,
        )

    def health(self) -> ProviderHealth:
        scripted = self._behavior.failure_class is not None
        return ProviderHealth(
            provider_type=self.provider_type,
            provider_name=self._name,
            status="unavailable" if scripted else "healthy",
            detail="scripted failure" if scripted else "deterministic fake",
        )


# Sanity: checkout status vocabulary stays frozen alongside the others.
assert set(CHECKOUT_STATUSES) == {"open", "completed", "expired"}
