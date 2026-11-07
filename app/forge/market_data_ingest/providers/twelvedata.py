"""Twelve Data adapter (offline, provisional primary target).

Documented response shape: ``/time_series`` returns a ``values`` array whose
entries carry ``datetime``, ``open``, ``high``, ``low``, ``close`` and optional
``volume``.  Twelve Data does **not** publish a candle-completion flag in the
pages reviewed for WP-3A, so this adapter emits ``finality_hint=None`` and the
kernel decides finality from the observation cutoff.

Timestamps must carry an explicit UTC offset.  A naive ``datetime`` is refused:
guessing a zone is exactly the failure mode III.1 forbids.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Mapping, Sequence

from app.forge.market_data.bars import TIMEFRAME_MINUTES
from app.forge.market_data.errors import ConventionViolationError
from app.forge.providers.doctrine import ProviderHealth
from app.forge.providers.errors import (
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderUnavailableError,
    ProviderUpstreamRejectedError,
)

from ..contract import (
    CandlePage,
    CandleRequest,
    ProviderCapabilities,
    RawCandle,
)
from ..symbols import PROVIDER_SYMBOLS, instrument_for_source_symbol
from .transport import ScriptedTransport

_INTERVALS = {"M5": "5min", "H1": "1h"}


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


def _datetime(value: object) -> datetime:
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ProviderMalformedResponseError("invalid datetime") from None
    if parsed.tzinfo is None:
        raise ProviderMalformedResponseError("naive provider timestamp")
    return parsed


class TwelveDataAdapter:
    """Offline Twelve Data transport adapter."""

    provider_id = "twelvedata"

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
            timeframes=frozenset(_INTERVALS),
            historical=True,
            streaming=True,
            revision_support=False,
            finality_signal=False,
            max_page_size=5000,
            notes=(
                "commercial display requires a business-tier agreement",
                "candle completion not documented; kernel owns finality",
            ),
        )

    def _request_interval(self, request: CandleRequest) -> str:
        if request.timeframe not in _INTERVALS:
            raise ProviderInvalidRequestError(
                f"unsupported timeframe {request.timeframe}",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        if request.limit > 5000:
            raise ProviderInvalidRequestError(
                "page limit exceeds provider maximum",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        return _INTERVALS[request.timeframe]

    def _parse(self, value: Mapping[str, object], request: CandleRequest) -> RawCandle:
        symbol = str(value.get("symbol", ""))
        try:
            instrument_id = instrument_for_source_symbol(self.provider_id, symbol)
        except Exception:
            raise ProviderMalformedResponseError("unknown source symbol") from None
        interval = str(value.get("interval", ""))
        timeframe = next(
            (name for name, mapped in _INTERVALS.items() if mapped == interval),
            None,
        )
        if timeframe is None:
            raise ProviderMalformedResponseError("unknown interval")
        open_time = _datetime(value.get("datetime"))
        close_time = open_time + timedelta(minutes=TIMEFRAME_MINUTES[timeframe])
        volume = value.get("volume")
        return RawCandle(
            provider_id=self.provider_id,
            source_symbol=symbol,
            instrument_id=instrument_id,
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=_decimal(value.get("open"), "open"),
            high=_decimal(value.get("high"), "high"),
            low=_decimal(value.get("low"), "low"),
            close=_decimal(value.get("close"), "close"),
            volume=_decimal(volume, "volume") if volume is not None else None,
            source_timestamp=_datetime(value.get("source_timestamp", value.get("datetime"))),
            source_revision=(
                str(value["revision"]) if value.get("revision") is not None else None
            ),
            finality_hint=None,
            clock_id=None,
        )

    def fetch(self, request: CandleRequest) -> CandlePage:
        self._request_interval(request)
        try:
            page = self._transport.next_page()
        except Exception as exc:
            self._last_failure = exc
            raise
        self._last_failure = None
        if page is None:
            return CandlePage(candles=(), next_cursor=None, exhausted=True)
        if str(page.get("status", "ok")).lower() == "error":
            raise ProviderUpstreamRejectedError(
                "provider rejected the request",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        values = page.get("values", [])
        if not isinstance(values, list):
            raise ProviderMalformedResponseError("values must be a list")
        candles = tuple(self._parse(value, request) for value in values)
        has_next = bool(page.get("next", False))
        next_cursor = candles[-1].close_time if candles and has_next else None
        return CandlePage(
            candles=candles, next_cursor=next_cursor, exhausted=not has_next
        )

    def stream(self, request: CandleRequest):
        self._request_interval(request)
        while True:
            event = self._transport.next_event()
            if event is None:
                return
            yield self._parse(event, request)

    def health(self) -> ProviderHealth:
        if self._transport.closed:
            return ProviderHealth(
                provider_type="market_data",
                provider_name=self.provider_id,
                status="unavailable",
                detail="transport_closed",
            )
        if self._last_failure is not None:
            return ProviderHealth(
                provider_type="market_data",
                provider_name=self.provider_id,
                status="unavailable",
                detail="last_request_failed",
            )
        return ProviderHealth(
            provider_type="market_data",
            provider_name=self.provider_id,
            status="healthy",
            detail="scripted_offline_transport",
        )

    def close(self) -> None:
        self._transport.close()


__all__ = ["TwelveDataAdapter"]
