"""Bounded retry policy helpers. Adapters never retry; the gateway does."""

from __future__ import annotations

from app.forge.providers.errors import (
    ProviderAuthenticationFailedError,
    ProviderError,
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderRateLimitedError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProviderUpstreamRejectedError,
)

from app.forge.ask_cerebus.llm_gateway.enums import GatewayRefusalCode


def is_retryable(error: ProviderError) -> bool:
    return isinstance(
        error,
        (ProviderTimeoutError, ProviderUnavailableError, ProviderRateLimitedError),
    ) and error.retryable


def refusal_for_error(error: ProviderError) -> GatewayRefusalCode:
    if isinstance(error, ProviderTimeoutError):
        return GatewayRefusalCode.PROVIDER_TIMEOUT
    if isinstance(error, ProviderRateLimitedError):
        return GatewayRefusalCode.PROVIDER_UNAVAILABLE
    if isinstance(error, ProviderUnavailableError):
        return GatewayRefusalCode.PROVIDER_UNAVAILABLE
    if isinstance(error, ProviderMalformedResponseError):
        return GatewayRefusalCode.PROVIDER_MALFORMED
    if isinstance(error, (ProviderInvalidRequestError, ProviderAuthenticationFailedError)):
        return GatewayRefusalCode.PROVIDER_NOT_CONFIGURED
    if isinstance(error, ProviderUpstreamRejectedError):
        return GatewayRefusalCode.PROVIDER_ERROR
    return GatewayRefusalCode.PROVIDER_ERROR


def retry_after_fits(*, retry_after: float | None, remaining_seconds: float) -> bool:
    return retry_after is None or retry_after < remaining_seconds


__all__ = ["is_retryable", "refusal_for_error", "retry_after_fits"]
