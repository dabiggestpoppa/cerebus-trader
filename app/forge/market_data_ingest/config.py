"""Secret-safe ingestion configuration (WP-3B).

No key is read at import time and no key is ever serialized.  The dataclass
mirrors the II.5 doctrine: selection names and budgets are diagnosable; the
credential is presence-only in diagnostics.  ``require_credentials`` fails
closed *before* any network attempt.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from app.forge.providers.errors import (
    ProviderAuthenticationFailedError,
    ProviderConfigurationError,
)

from .symbols import PROVIDER_SYMBOLS

_ENVIRONMENTS: frozenset[str] = frozenset({"local", "test", "staging", "production"})


@dataclass(frozen=True)
class MarketDataIngestConfig:
    """Environment-injected provider selection and budgets."""

    provider: str = "twelvedata"
    api_key: str = field(default="", repr=False)
    environment: str = "local"
    enabled: bool = False
    timeout_seconds: float = 10.0
    max_retries: int = 3
    monthly_call_ceiling: int = 100_000

    def __post_init__(self) -> None:
        if self.provider not in PROVIDER_SYMBOLS:
            raise ProviderConfigurationError(
                f"unknown market-data provider {self.provider!r}"
            )
        if self.environment not in _ENVIRONMENTS:
            raise ProviderConfigurationError(
                f"unknown environment {self.environment!r}"
            )
        if self.timeout_seconds <= 0:
            raise ProviderConfigurationError("timeout_seconds must be > 0")
        if self.max_retries < 0:
            raise ProviderConfigurationError("max_retries must be >= 0")
        if self.monthly_call_ceiling < 1:
            raise ProviderConfigurationError("monthly_call_ceiling must be >= 1")

    @property
    def configured(self) -> bool:
        return bool(self.enabled and self.api_key)

    def require_credentials(self) -> None:
        """Fail closed before any request when credentials are absent."""
        if not self.enabled:
            raise ProviderAuthenticationFailedError(
                "market-data ingestion is disabled",
                provider_type="market_data",
                provider_name=self.provider,
            )
        if not self.api_key:
            raise ProviderAuthenticationFailedError(
                "market-data credential is not configured",
                provider_type="market_data",
                provider_name=self.provider,
            )

    def redacted(self) -> dict:
        """Safe diagnostic shape — presence booleans only."""
        return {
            "provider": self.provider,
            "environment": self.environment,
            "enabled": self.enabled,
            "api_key_configured": bool(self.api_key),
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "monthly_call_ceiling": self.monthly_call_ceiling,
        }


def config_from_environment() -> MarketDataIngestConfig:
    """Build configuration from ``FORGE_MARKET_DATA_*`` variables."""
    return MarketDataIngestConfig(
        provider=os.environ.get("FORGE_MARKET_DATA_PROVIDER", "twelvedata")
        .strip()
        .lower(),
        api_key=os.environ.get("FORGE_MARKET_DATA_API_KEY", ""),
        environment=os.environ.get("FORGE_ENVIRONMENT", "local").strip().lower(),
        enabled=os.environ.get("FORGE_MARKET_DATA_ENABLED", "false").strip().lower()
        in {"1", "true", "yes", "on"},
        timeout_seconds=float(
            os.environ.get("FORGE_MARKET_DATA_TIMEOUT_SECONDS", "10.0")
        ),
        max_retries=int(os.environ.get("FORGE_MARKET_DATA_MAX_RETRIES", "3")),
        monthly_call_ceiling=int(
            os.environ.get("FORGE_MARKET_DATA_MONTHLY_CALL_CEILING", "100000")
        ),
    )


__all__ = ["MarketDataIngestConfig", "config_from_environment"]
