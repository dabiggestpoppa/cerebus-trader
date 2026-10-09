"""FORGE provider ports & adapter boundaries (Book II / Bloc II.5).

Domain/application code imports these ports — never a vendor client. Concrete
vendor adapters (OpenRouter, Whop, ...) do not exist at II.5; only the four
neutral ports, the failure taxonomy, resilience policy, deterministic fakes,
and the config-driven registry/factory live here.
"""

from __future__ import annotations

from app.forge.providers.commerce import (
    COMMERCE_METHODS,
    CUSTOMER_STATUSES,
    EVENT_TYPES,
    SUBSCRIPTION_STATUSES,
    CheckoutSession,
    CommerceCustomer,
    CommerceProvider,
    CommerceSubscription,
    ProviderEvent,
)
from app.forge.providers.doctrine import (
    HEALTH_STATUSES,
    PORTS,
    PORT_CONTRACTS,
    ProviderContractSpec,
    ProviderHealth,
)
from app.forge.providers.errors import (
    ERROR_BY_CLASS,
    FAILURE_CLASSES,
    RETRYABLE_CLASSES,
    ProviderAuthenticationFailedError,
    ProviderCancelledError,
    ProviderConfigurationError,
    ProviderError,
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
    ProviderUnknownError,
    ProviderUnavailableError,
    ProviderUpstreamRejectedError,
)
from app.forge.providers.fakes import (
    DEFAULT_FAKE_TIMEOUT_BUDGET,
    FakeBehavior,
    FakeCommerceProvider,
    FakeLLMProvider,
    FakeNotificationProvider,
    FakeStorageProvider,
    SimulatedClock,
)
from app.forge.providers.llm import (
    CAPABILITY_STRUCTURED_OUTPUT,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)
from app.forge.providers.notification import (
    DELIVERY_STATUSES,
    NOTIFICATION_METHODS,
    NotificationProvider,
    NotificationRequest,
    NotificationResult,
)
from app.forge.providers.registry import (
    PORT_PROTOCOLS,
    ProviderFactory,
    ProviderRegistry,
    default_provider_factory,
    provider_selection,
    providers_from_config,
)
from app.forge.providers.resilience import (
    FALLBACK_MODES,
    CircuitBreaker,
    CircuitState,
    FallbackPolicy,
    run_with_fallback,
)
from app.forge.providers.storage import (
    ACCESS_STRATEGY_KINDS,
    STORAGE_METHODS,
    AccessStrategy,
    StorageProvider,
    StoredObject,
    StoredObjectData,
)

__all__ = [
    "ACCESS_STRATEGY_KINDS",
    "CAPABILITY_STRUCTURED_OUTPUT",
    "COMMERCE_METHODS",
    "CUSTOMER_STATUSES",
    "DEFAULT_FAKE_TIMEOUT_BUDGET",
    "DELIVERY_STATUSES",
    "ERROR_BY_CLASS",
    "EVENT_TYPES",
    "FAILURE_CLASSES",
    "FALLBACK_MODES",
    "HEALTH_STATUSES",
    "NOTIFICATION_METHODS",
    "PORTS",
    "PORT_CONTRACTS",
    "PORT_PROTOCOLS",
    "RETRYABLE_CLASSES",
    "STORAGE_METHODS",
    "SUBSCRIPTION_STATUSES",
    "AccessStrategy",
    "CheckoutSession",
    "CircuitBreaker",
    "CircuitState",
    "CommerceCustomer",
    "CommerceProvider",
    "CommerceSubscription",
    "FakeBehavior",
    "FakeCommerceProvider",
    "FakeLLMProvider",
    "FakeNotificationProvider",
    "FakeStorageProvider",
    "FallbackPolicy",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "LLMUsage",
    "NotificationProvider",
    "NotificationRequest",
    "NotificationResult",
    "ProviderAuthenticationFailedError",
    "ProviderCancelledError",
    "ProviderConfigurationError",
    "ProviderContractSpec",
    "ProviderError",
    "ProviderEvent",
    "ProviderHealth",
    "ProviderInvalidRequestError",
    "ProviderMalformedResponseError",
    "ProviderRateLimitedError",
    "ProviderRegistry",
    "ProviderTimeoutError",
    "ProviderUnknownError",
    "ProviderUnavailableError",
    "ProviderUpstreamRejectedError",
    "SimulatedClock",
    "StorageProvider",
    "StoredObject",
    "StoredObjectData",
    "default_provider_factory",
    "provider_selection",
    "providers_from_config",
    "run_with_fallback",
]
