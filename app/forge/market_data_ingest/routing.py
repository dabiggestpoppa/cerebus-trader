"""Per-instrument source routing and governed failover (WP-3B).

Failover is allowed only for retryable II.5 failures.  A series must not
silently interleave vendors: switching source inside one window requires a
declared boundary, otherwise the route refuses.  Provider identity stays on
every observation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from app.forge.market_data.errors import ConventionViolationError
from app.forge.providers.errors import ProviderError

from .contract import CandleRequest, MarketDataProvider, RawCandle


class SourceBlendError(ConventionViolationError):
    """A single window mixed providers without a declared boundary."""

    code = "SOURCE_BLEND"


@dataclass(frozen=True)
class SourcePolicy:
    """Ordered providers per instrument; first healthy source wins."""

    routes: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        if not self.routes:
            raise ConventionViolationError("routes must not be empty")
        for instrument_id, providers in self.routes.items():
            if not instrument_id or not providers:
                raise ConventionViolationError("route entries must be complete")
            if len(set(providers)) != len(providers):
                raise ConventionViolationError("duplicate provider in route")

    def providers_for(self, instrument_id: str) -> tuple[str, ...]:
        try:
            return self.routes[instrument_id]
        except KeyError:
            raise ConventionViolationError(
                f"no source route for {instrument_id!r}"
            ) from None


@dataclass(frozen=True)
class FailoverResult:
    """Observations plus the provider that actually served them."""

    provider_id: str
    candles: tuple[RawCandle, ...]
    attempted: tuple[str, ...]
    failed_over: bool


def fetch_with_failover(
    providers: Mapping[str, MarketDataProvider],
    policy: SourcePolicy,
    request: CandleRequest,
) -> FailoverResult:
    """Try each routed provider; only retryable failures advance the route."""
    attempted: list[str] = []
    last_error: ProviderError | None = None
    for provider_id in policy.providers_for(request.instrument_id):
        provider = providers.get(provider_id)
        if provider is None:
            raise ConventionViolationError(
                f"provider {provider_id!r} is not wired"
            )
        attempted.append(provider_id)
        try:
            page = provider.fetch(request)
        except ProviderError as exc:
            if not exc.retryable:
                raise
            last_error = exc
            continue
        return FailoverResult(
            provider_id=provider_id,
            candles=tuple(page.candles),
            attempted=tuple(attempted),
            failed_over=len(attempted) > 1,
        )
    assert last_error is not None
    raise last_error


def assert_single_source(
    candles: Sequence[RawCandle], *, boundary_declared: bool = False
) -> str:
    """Require one provider per canonical series unless a boundary is declared."""
    providers = {candle.provider_id for candle in candles}
    if len(providers) > 1 and not boundary_declared:
        raise SourceBlendError(
            f"window mixes providers {sorted(providers)} without a boundary"
        )
    if not providers:
        raise ConventionViolationError("empty series has no source identity")
    return sorted(providers)[0]


__all__ = [
    "FailoverResult",
    "SourceBlendError",
    "SourcePolicy",
    "assert_single_source",
    "fetch_with_failover",
]
