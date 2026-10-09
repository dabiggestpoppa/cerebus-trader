"""Shared provider contract suite (Book II / Bloc II.5, Ch II.5.10).

"Run identical contract suite against fake adapters and each concrete adapter."

These functions are the single implementation of the provider contract. The
II.5 suite invokes them for every II.5 fake AND for locally defined alternate
adapters (the stand-ins proving replacement works today); Book IV/VI concrete
adapters add an invocation to the parametrized matrix — zero suite rewrites.

Assertions here are provider-NEUTRAL: port shapes, bounded vocabularies,
contract-promised idempotency, self-consistent capability claims, and
frozen-taxonomy classification for every failure path. No fake-specific
determinism, no fake internals (those live in tests/test_forge_providers.py).
"""

from __future__ import annotations

import json
from typing import Callable

import pytest

from app.forge.providers import (
    ACCESS_STRATEGY_KINDS,
    CAPABILITY_STRUCTURED_OUTPUT,
    CUSTOMER_STATUSES,
    DELIVERY_STATUSES,
    EVENT_TYPES,
    HEALTH_STATUSES,
    LLMRequest,
    LLMResponse,
    NotificationRequest,
    NotificationResult,
    ProviderAuthenticationFailedError,
    ProviderCancelledError,
    ProviderHealth,
    ProviderInvalidRequestError,
    StorageProvider,
)
from app.forge.providers.commerce import (
    CHECKOUT_STATUSES,
    CommerceProvider,
    CheckoutSession,
)
from app.forge.providers.llm import LLMProvider
from app.forge.providers.notification import NotificationProvider


def assert_health(health: ProviderHealth, provider_type: str) -> None:
    """Ch II.5.1 element 7: every port answers a bounded, typed health."""

    assert isinstance(health, ProviderHealth)
    assert health.provider_type == provider_type
    assert isinstance(health.provider_name, str) and health.provider_name
    assert health.status in HEALTH_STATUSES
    assert isinstance(health.detail, str)


def run_llm_contract(provider: LLMProvider) -> None:
    """Contract for Ch II.5.2. Runs identically on every LLM adapter."""

    assert isinstance(provider.capabilities(), frozenset)
    assert_health(provider.health(), "llm")

    request = LLMRequest(
        prompt="provider-contract-probe", model="contract-model"
    )
    response = provider.generate(request, timeout_seconds=10.0)
    assert isinstance(response, LLMResponse)
    assert isinstance(response.text, str)
    assert isinstance(response.model, str) and response.model
    usage = response.usage
    assert usage.prompt_tokens >= 0
    assert usage.completion_tokens >= 0
    assert usage.total_tokens == usage.prompt_tokens + usage.completion_tokens
    assert usage.cost_usd >= 0

    # Caller-error classification: zero timeout is a caller mistake and must
    # surface as the frozen invalid_request class, never a hang or raw error.
    with pytest.raises(ProviderInvalidRequestError):
        provider.generate(request, timeout_seconds=0)

    # Cancellation is control flow: a pre-cancelled call must not dispatch.
    with pytest.raises(ProviderCancelledError):
        provider.generate(request, timeout_seconds=10.0, cancel=lambda: True)

    # Optional structured output must be self-consistent: advertised => a
    # schema request is honored; not advertised => classified refusal.
    schema = {"type": "object", "required": ["alpha"]}
    schema_request = LLMRequest(
        prompt="structured probe", model="contract-model",
        response_schema=schema,
    )
    if CAPABILITY_STRUCTURED_OUTPUT in provider.capabilities():
        structured_response = provider.generate(
            schema_request, timeout_seconds=10.0
        )
        assert structured_response.structured is not None
        assert "alpha" in structured_response.structured
    else:
        with pytest.raises(ProviderInvalidRequestError):
            provider.generate(schema_request, timeout_seconds=10.0)


def run_commerce_contract(
    provider: CommerceProvider,
    *,
    sign: Callable[[bytes], str],
) -> None:
    """Contract for Ch II.5.3. `sign` is the per-adapter signing fixture."""

    assert_health(provider.health(), "commerce")

    # Checkout/session handoff with contract-promised idempotency.
    first = provider.create_checkout(
        "cus-contract", idempotency_key="contract-key-1"
    )
    repeat = provider.create_checkout(
        "cus-contract", idempotency_key="contract-key-1"
    )
    assert isinstance(first, CheckoutSession)
    assert first.session_id
    assert first.session_id == repeat.session_id
    assert first.status in CHECKOUT_STATUSES
    distinct = provider.create_checkout(
        "cus-contract", idempotency_key="contract-key-2"
    )
    assert distinct.session_id != first.session_id

    # Customer / subscription lookups (reconciliation reads).
    customer = provider.get_customer("cus-contract")
    assert customer.customer_id == "cus-contract"
    assert customer.status in CUSTOMER_STATUSES
    subscription = provider.get_subscription("sub-contract")
    assert subscription.subscription_id == "sub-contract"

    # Event normalization happy path.
    raw = json.dumps(
        {
            "event_id": "evt-contract-1",
            "event_type": "subscription.created",
            "occurred_at": 1700000000,
            "customer": "cus-contract",
        }
    ).encode("utf-8")
    event = provider.parse_event(raw, sign(raw))
    assert event.event_id == "evt-contract-1"
    assert event.event_type in EVENT_TYPES
    assert event.occurred_at == 1700000000.0
    assert event.payload.get("customer") == "cus-contract"

    # Frozen-taxonomy classification on both failure paths.
    with pytest.raises(ProviderAuthenticationFailedError):
        provider.parse_event(raw, "not-a-valid-signature")
    bad_raw = b"this is not json"
    with pytest.raises(ProviderInvalidRequestError):
        provider.parse_event(bad_raw, sign(bad_raw))


def run_notification_contract(provider: NotificationProvider) -> None:
    """Contract for Ch II.5.4."""

    assert_health(provider.health(), "notification")
    result = provider.send(
        NotificationRequest(
            channel="email",
            recipient="contract@example.invalid",
            subject="contract",
            body="probe",
        )
    )
    assert isinstance(result, NotificationResult)
    assert result.status in DELIVERY_STATUSES
    assert result.message_id
    # Unsupported channel is a classified caller error.
    with pytest.raises(ProviderInvalidRequestError):
        provider.send(
            NotificationRequest(
                channel="telepathy",
                recipient="contract@example.invalid",
                subject="contract",
                body="probe",
            )
        )


def run_storage_contract(provider: StorageProvider, *, key: str) -> None:
    """Contract for Ch II.5.5. `key` is unique per adapter (stateful port)."""

    assert_health(provider.health(), "storage")

    first = provider.put(key, b"one", content_type="text/plain")
    assert first.version >= 1
    assert first.size_bytes == 3
    assert len(first.checksum) == 64
    current = provider.get(key)
    assert current.data == b"one"
    assert current.object.version == first.version
    assert current.object.checksum == first.checksum

    second = provider.put(key, b"two!", content_type="text/plain")
    assert second.version > first.version
    assert provider.get(key).data == b"two!"
    pinned = provider.get(key, version=first.version)
    assert pinned.data == b"one"

    strategy = provider.access_strategy(key, ttl_seconds=60.0)
    assert strategy.kind in ACCESS_STRATEGY_KINDS
    assert strategy.target
    assert strategy.expires_at is not None

    with pytest.raises(ProviderInvalidRequestError):
        provider.get(key + "-missing")

    provider.delete(key)
    with pytest.raises(ProviderInvalidRequestError):
        provider.get(key)
