"""Provider contract doctrine (Book II / Bloc II.5, Ch II.5.1).

Ch II.5.1: "Every provider contract defines: request, response, timeout,
retry ownership, idempotency expectations, error taxonomy, health semantics,
redaction rules."

The doctrine is executable, not prose: each of the four FORGE ports publishes a
`ProviderContractSpec` carrying exactly those eight elements, and the II.5
suite fails if any element is missing or empty. `PORT_CONTRACTS` is the single
authority; docs and adapters must agree with it.

Redaction law (element 8): nothing leaving a port — health detail, error
message, diagnostics, logs — may contain provider payloads, credentials, signed
token material, or stack traces. Only doctrine-safe text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.forge.providers.errors import FAILURE_CLASSES

# The four FORGE provider ports frozen by II.5.
PORTS: tuple[str, ...] = ("llm", "commerce", "notification", "storage")

# Bounded health vocabulary (element 7). Readiness maps these to the frozen
# service vocabulary; nothing outside this set may ever appear.
HEALTH_STATUSES: frozenset[str] = frozenset(
    {"healthy", "degraded", "unavailable"}
)

_TAXONOMY_TEXT = (
    "failure_taxonomy_v1: "
    + ", ".join(FAILURE_CLASSES)
    + " (adapters classify into these exact classes)"
)

_RETRY_TEXT = (
    "adapters never retry; the caller owns retries; retryable classes are "
    "timeout/unavailable/rate_limited; retry_after_seconds only on rate_limited"
)

_REDACTION_TEXT = (
    "doctrine-safe text only: no provider payloads, credentials, signed "
    "tokens, or stack traces in messages, health details or diagnostics"
)


@dataclass(frozen=True)
class ProviderContractSpec:
    """The eight Ch II.5.1 elements of one provider contract."""

    name: str
    request: str
    response: str
    timeout: str
    retry_ownership: str
    idempotency: str
    error_taxonomy: str
    health_semantics: str
    redaction: str

    def elements(self) -> Mapping[str, str]:
        return {
            "request": self.request,
            "response": self.response,
            "timeout": self.timeout,
            "retry_ownership": self.retry_ownership,
            "idempotency": self.idempotency,
            "error_taxonomy": self.error_taxonomy,
            "health_semantics": self.health_semantics,
            "redaction": self.redaction,
        }


@dataclass(frozen=True)
class ProviderHealth:
    """Normalized health answer every port must be able to give (element 7)."""

    provider_type: str
    provider_name: str
    status: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in HEALTH_STATUSES:
            raise ValueError(f"invalid provider health status {self.status!r}")


PORT_CONTRACTS: Mapping[str, ProviderContractSpec] = {
    "llm": ProviderContractSpec(
        name="llm",
        request=(
            "LLMRequest(prompt, model, response_schema=None); transport-only "
            "abstraction — prompt/retrieval intelligence belongs to Book IV"
        ),
        response=(
            "LLMResponse(text, model, usage: LLMUsage(tokens+cost_usd), "
            "structured, finish_reason)"
        ),
        timeout=(
            "caller passes timeout_seconds per generate() call; exceeding it "
            "(or scripted latency) raises ProviderTimeoutError"
        ),
        retry_ownership=_RETRY_TEXT,
        idempotency=(
            "generate() is side-effect free at the port; identical requests "
            "produce identical deterministic-fake responses; usage accounting "
            "is per attempt and owned by the caller"
        ),
        error_taxonomy=_TAXONOMY_TEXT,
        health_semantics=(
            "health() -> ProviderHealth(healthy|degraded|unavailable), pure, "
            "no network at II.5; readiness probes it live"
        ),
        redaction=_REDACTION_TEXT,
    ),
    "commerce": ProviderContractSpec(
        name="commerce",
        request=(
            "create_checkout(customer_id, idempotency_key), "
            "get_customer(customer_id), get_subscription(subscription_id), "
            "parse_event(raw: bytes, signature: str)"
        ),
        response=(
            "CheckoutSession, CommerceCustomer, CommerceSubscription, "
            "ProviderEvent(event_id, event_type, occurred_at, payload)"
        ),
        timeout=(
            "caller passes/owns per-call timeouts; scripted latency exceeding "
            "the budget raises ProviderTimeoutError"
        ),
        retry_ownership=_RETRY_TEXT,
        idempotency=(
            "create_checkout with the same idempotency_key returns the same "
            "session (never a duplicate); provider events carry a stable "
            "event_id so duplicate/out-of-order deliveries dedupe downstream"
        ),
        error_taxonomy=_TAXONOMY_TEXT,
        health_semantics=(
            "health() -> ProviderHealth; also serves the reconciliation read "
            "shape; failures never mutate entitlement state (no entitlement "
            "mutation exists in the adapter)"
        ),
        redaction=_REDACTION_TEXT,
    ),
    "notification": ProviderContractSpec(
        name="notification",
        request="send(NotificationRequest(channel, recipient, subject, body))",
        response="NotificationResult(message_id, status: delivered|failed)",
        timeout=(
            "caller owns the per-send timeout budget; scripted latency over "
            "budget raises ProviderTimeoutError"
        ),
        retry_ownership=_RETRY_TEXT,
        idempotency=(
            "NotificationRequest may carry a caller key later; II.5 result "
            "identity is the returned message_id"
        ),
        error_taxonomy=_TAXONOMY_TEXT,
        health_semantics="health() -> ProviderHealth, pure at II.5",
        redaction=_REDACTION_TEXT,
    ),
    "storage": ProviderContractSpec(
        name="storage",
        request=(
            "put(key, data, content_type), get(key, version=None), "
            "delete(key), access_strategy(key, ttl_seconds)"
        ),
        response=(
            "StoredObject(key, version, size_bytes, content_type, checksum), "
            "StoredObjectData(object, data), AccessStrategy(kind, target, "
            "expires_at)"
        ),
        timeout=(
            "caller owns the per-operation timeout budget; scripted latency "
            "over budget raises ProviderTimeoutError"
        ),
        retry_ownership=_RETRY_TEXT,
        idempotency=(
            "put() is caller-keyed; re-putting identical bytes still mints a "
            "new version (append-only); get/delete are read/mutate by key+version"
        ),
        error_taxonomy=_TAXONOMY_TEXT,
        health_semantics=(
            "health() -> ProviderHealth, pure at II.5; Library/GitHub "
            "recovery sources are not blob storage and are never adapted here"
        ),
        redaction=_REDACTION_TEXT,
    ),
}
