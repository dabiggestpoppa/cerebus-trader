"""Polygon Currencies adapter (offline, secondary target).

Aggregates arrive with millisecond UTC timestamps ``t`` and OHLC(V).  Polygon's
FX aggregates are derived from best bid/offer quotes and no bar is emitted in a
window without quotes, so absence is a gap — never a flat candle.

Polygon publishes no candle-completion flag in the reviewed pages; finality is
therefore kernel-owned.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Mapping, Sequence

from app.forge.market_data.bars import TIMEFRAME_MINUTES
from app.forge.providers.doctrine import ProviderHealth
from app.forge.providers.errors import (
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderUpstreamRejectedError,
)

from ..contract import CandlePage, CandleRequest, ProviderCapabilities, RawCandle
from ..symbols import PROVIDER_SYMBOLS, instrument_for_source_symbol
from .transport import ScriptedTransport

_TIMEFRAMES = frozenset({"M5", "H1"})


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ProviderMalformedResponseError(f"missing {field}")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ProviderMalformedResponseError(f"invalid {field}") from None
    if not parsed.is_finite():
        raise ProviderMalformedResponseError(f"non-finite {field}")
    return parsed


class PolygonAdapter:
    """Offline Polygon Currencies transport adapter."""

    provider_id = "polygon"

    def __init__(
        self,
        pages: Sequence[Mapping[str, object]] = (),
        events: Sequence[Mapping[str, object]] = (),
        failures: Sequence[Exception | None] = (),
    ) -> None:
        self._transport = ScriptedTransport(
            pages, events, failures, provider_name=self.provider_id
        )
        self._last_failure: Exception | None = None

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_id=self.provider_id,
            instruments=frozenset(PROVIDER_SYMBOLS[self.provider_id]),
            timeframes=_TIMEFRAMES,
            historical=True,
            streaming=True,
            revision_support=False,
            finality_signal=False,
            max_page_size=50000,
            notes=(
                "FX aggregates are quote-derived; quiet windows emit no bar",
                "redistribution requires a business agreement",
            ),
        )

    def _parse(self, row: Mapping[str, object], request: CandleRequest) -> RawCandle:
        symbol = str(row.get("sym", ""))
        try:
            instrument_id = instrument_for_source_symbol(self.provider_id, symbol)
        except Exception:
            raise ProviderMalformedResponseError("unknown source symbol") from None
        if instrument_id != request.instrument_id:
            raise ProviderMalformedResponseError("symbol does not match request")
        stamp = row.get("t")
        if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
            raise ProviderMalformedResponseError("missing timestamp")
        open_time = datetime.fromtimestamp(float(stamp) / 1000.0, tz=timezone.utc)
        volume = row.get("v")
        return RawCandle(
            provider_id=self.provider_id,
            source_symbol=symbol,
            instrument_id=instrument_id,
            timeframe=request.timeframe,
            open_time=open_time,
            close_time=open_time
            + timedelta(minutes=TIMEFRAME_MINUTES[request.timeframe]),
            open=_decimal(row.get("o"), "open"),
            high=_decimal(row.get("h"), "high"),
            low=_decimal(row.get("l"), "low"),
            close=_decimal(row.get("c"), "close"),
            volume=_decimal(volume, "volume") if volume is not None else None,
            source_timestamp=open_time,
            source_revision=None,
            finality_hint=None,
            clock_id=None,
        )

    def fetch(self, request: CandleRequest) -> CandlePage:
        if request.timeframe not in _TIMEFRAMES:
            raise ProviderInvalidRequestError(
                f"unsupported timeframe {request.timeframe}",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        try:
            page = self._transport.next_page()
        except Exception as exc:
            self._last_failure = exc
            raise
        self._last_failure = None
        if page is None:
            return CandlePage(candles=(), next_cursor=None, exhausted=True)
        if str(page.get("status", "OK")).upper() != "OK":
            raise ProviderUpstreamRejectedError(
                "provider rejected the request",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        rows = page.get("results", [])
        if not isinstance(rows, list):
            raise ProviderMalformedResponseError("results must be a list")
        candles = tuple(self._parse(row, request) for row in rows)
        next_cursor = candles[-1].close_time if candles else None
        return CandlePage(
            candles=candles,
            next_cursor=next_cursor if page.get("next") else None,
            exhausted=not bool(page.get("next")),
        )

    def stream(self, request: CandleRequest):
        while True:
            row = self._transport.next_event()
            if row is None:
                return
            yield self._parse(row, request)

    def health(self) -> ProviderHealth:
        status = "unavailable" if self._last_failure is not None else "healthy"
        return ProviderHealth(
            provider_type="market_data",
            provider_name=self.provider_id,
            status=status,
            detail=(
                "last_request_failed"
                if self._last_failure is not None
                else "scripted_offline_transport"
            ),
        )

    def close(self) -> None:
        self._transport.close()


__all__ = ["PolygonAdapter"]
