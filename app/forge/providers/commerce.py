"""Commerce provider port (Book II / Bloc II.5, Ch II.5.3).

Provider-neutral operations needed by Book VI:

- checkout/session handoff as applicable
- customer/subscription lookup
- provider event normalization
- health/reconciliation reads

Internal entitlement mutation does NOT live in the adapter — this protocol has
no entitlement-mutating method, and an exact method-set test enforces it.

The concrete Whop adapter is Book VI scope and does NOT exist at II.5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, runtime_checkable

from app.forge.providers.doctrine import ProviderHealth

# Frozen method set of the commerce port (no entitlement mutation).
COMMERCE_METHODS: frozenset[str] = frozenset(
    {"create_checkout", "get_customer", "get_subscription", "parse_event", "health"}
)

# Bounded vocabularies shared by fakes/adapters/tests.
CUSTOMER_STATUSES: tuple[str, ...] = ("active", "inactive")
SUBSCRIPTION_STATUSES: tuple[str, ...] = ("active", "past_due", "canceled")
CHECKOUT_STATUSES: tuple[str, ...] = ("open", "completed", "expired")
EVENT_TYPES: tuple[str, ...] = (
    "checkout.completed",
    "subscription.created",
    "subscription.updated",
    "subscription.canceled",
)


@dataclass(frozen=True)
class CommerceCustomer:
    customer_id: str
    status: str
    subscription_id: str | None = None


@dataclass(frozen=True)
class CommerceSubscription:
    subscription_id: str
    customer_id: str
    status: str


@dataclass(frozen=True)
class CheckoutSession:
    session_id: str
    customer_id: str
    handoff_url: str
    status: str


@dataclass(frozen=True)
class ProviderEvent:
    """Normalized provider event. `event_id` is the dedup key: duplicate and
    out-of-order webhook deliveries collapse on it downstream."""

    event_id: str
    event_type: str
    occurred_at: float
    payload: Mapping[str, str]


@runtime_checkable
class CommerceProvider(Protocol):
    """The frozen II.5 commerce port."""

    def create_checkout(
        self, customer_id: str, *, idempotency_key: str
    ) -> CheckoutSession:
        """Checkout/session handoff. Same key => same session, no duplicate."""
        ...

    def get_customer(self, customer_id: str) -> CommerceCustomer:
        """Provider-neutral customer lookup (reconciliation read)."""
        ...

    def get_subscription(self, subscription_id: str) -> CommerceSubscription:
        """Provider-neutral subscription lookup (reconciliation read)."""
        ...

    def parse_event(self, raw: bytes, signature: str) -> ProviderEvent:
        """Validate signature + shape, return the normalized event.

        Bad signature => ProviderAuthenticationFailedError.
        Bad shape => ProviderInvalidRequestError.
        """
        ...

    def health(self) -> ProviderHealth:
        """Pure health answer; never a network call by itself."""
        ...
