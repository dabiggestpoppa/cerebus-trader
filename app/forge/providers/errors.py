"""FORGE provider failure taxonomy (Book II / Bloc II.5, Ch II.5.7).

Frozen failure classes (exact set and names):

    unavailable, timeout, rate_limited, invalid_request,
    authentication_failed, upstream_rejected, malformed_response, unknown

Doctrines enforced here (Ch II.5.1):

- Adapters NEVER retry. The caller owns retries; `retryable` only classifies
  which failures are worth retrying, it never triggers an internal retry.
- Error messages are doctrine-safe text only: never provider payloads,
  credentials, URLs with tokens, or stack traces. `redacted_summary()` is the
  single diagnostic shape.
- `retry_after_seconds` is meaningful only for `rate_limited`.

`ProviderCancelledError` is caller-initiated control flow (Ch II.5.2
"timeout/cancel"), NOT a provider failure: it carries `failure_class = None`
and is deliberately outside the frozen taxonomy.
"""

from __future__ import annotations

from typing import Any

# Frozen taxonomy (Ch II.5.7) — exact order and membership. Test-enforced.
FAILURE_CLASSES: tuple[str, ...] = (
    "unavailable",
    "timeout",
    "rate_limited",
    "invalid_request",
    "authentication_failed",
    "upstream_rejected",
    "malformed_response",
    "unknown",
)

# Only transient classes are retry-worthy; the caller decides whether to act.
RETRYABLE_CLASSES: frozenset[str] = frozenset(
    {"timeout", "unavailable", "rate_limited"}
)


class ProviderError(Exception):
    """Base class for every normalized provider failure."""

    failure_class: str | None = "unknown"

    def __init__(
        self,
        message: str,
        *,
        provider_type: str = "unknown",
        provider_name: str = "unknown",
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.provider_type = provider_type
        self.provider_name = provider_name
        failure_class = self.failure_class
        if failure_class is not None and failure_class not in FAILURE_CLASSES:
            raise ValueError(f"invalid failure class {failure_class!r}")
        if retry_after_seconds is not None and failure_class != "rate_limited":
            raise ValueError(
                "retry_after_seconds is only valid for rate_limited"
            )
        self.retry_after_seconds = retry_after_seconds

    @property
    def retryable(self) -> bool:
        """Transient-classified failure. Advisory only — adapters never retry."""

        return self.failure_class in RETRYABLE_CLASSES

    def redacted_summary(self) -> dict[str, Any]:
        """Safe diagnostic shape. Never payloads, credentials or internals."""

        return {
            "failure_class": self.failure_class,
            "provider_type": self.provider_type,
            "provider_name": self.provider_name,
            "retryable": self.retryable,
            "retry_after_seconds": self.retry_after_seconds,
            "message": str(self),
        }


class ProviderUnavailableError(ProviderError):
    failure_class = "unavailable"


class ProviderTimeoutError(ProviderError):
    failure_class = "timeout"


class ProviderRateLimitedError(ProviderError):
    failure_class = "rate_limited"


class ProviderInvalidRequestError(ProviderError):
    failure_class = "invalid_request"


class ProviderAuthenticationFailedError(ProviderError):
    failure_class = "authentication_failed"


class ProviderUpstreamRejectedError(ProviderError):
    failure_class = "upstream_rejected"


class ProviderMalformedResponseError(ProviderError):
    failure_class = "malformed_response"


class ProviderUnknownError(ProviderError):
    failure_class = "unknown"


class ProviderCancelledError(ProviderError):
    """Caller-initiated cancellation: control flow, not a provider failure."""

    failure_class = None  # type: ignore[assignment]


# One exception class per frozen failure class.
ERROR_BY_CLASS: dict[str, type[ProviderError]] = {
    "unavailable": ProviderUnavailableError,
    "timeout": ProviderTimeoutError,
    "rate_limited": ProviderRateLimitedError,
    "invalid_request": ProviderInvalidRequestError,
    "authentication_failed": ProviderAuthenticationFailedError,
    "upstream_rejected": ProviderUpstreamRejectedError,
    "malformed_response": ProviderMalformedResponseError,
    "unknown": ProviderUnknownError,
}


class ProviderConfigurationError(ValueError):
    """Fail-closed factory/registry configuration error.

    Not a provider failure: nothing was called. Distinct from ProviderError so
    wiring mistakes can never be mistaken for vendor outages (or vice versa).
    """
