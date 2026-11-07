"""Kraken adapter (offline, BTC/USD verification target).

Kraken's public OHLC returns up to 720 rows and always includes the current,
not-yet-committed interval as the last entry.  This adapter marks that trailing
candle ``NONFINAL`` and refuses requests beyond the documented page cap; it does
not pretend the limitation away.

The canonical BTCUSD contract is USD-denominated, so Kraken's true ``BTC/USD``
pair is preferred over USDT-quoted venues.
"""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Mapping, Sequence

from app.forge.market_data.bars import TIMEFRAME_MINUTES
from app.forge.market_data.errors import ConventionViolationError
from app.forge.providers.doctrine import ProviderHealth
from app.forge.providers.errors import (
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderUpstreamRejectedError,
)

from ..contract import CandlePage, CandleRequest, ProviderCapabilities, RawCandle
from ..symbols import PROVIDER_SYMBOLS, instrument_for_source_symbol
from .transport import ScriptedTransport

KRAKEN_REST_OHLC_LIMIT = 720
_TIMEFRAMES = frozenset({"M5", "H1"})
_RESULT_KEYS = ("XXBTZUSD", "XBTUSD", "BTCUSD")


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


class KrakenAdapter:
    """Offline Kraken public-OHLC transport adapter."""

    provider_id = "kraken"

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
            finality_signal=True,
            max_page_size=KRAKEN_REST_OHLC_LIMIT,
            notes=(
                "REST OHLC returns at most 720 rows; backfill needs the CSV archive",
                "trailing candle is provisional",
            ),
        )

    def _parse(
        self, row: Sequence[object], request: CandleRequest, *, provisional: bool
    ) -> RawCandle:
        if not isinstance(row, (list, tuple)) or len(row) < 6:
            raise ProviderMalformedResponseError("malformed OHLC row")
        stamp = row[0]
        if isinstance(stamp, bool) or not isinstance(stamp, (int, float)):
            raise ProviderMalformedResponseError("missing timestamp")
        open_time = datetime.fromtimestamp(float(stamp), tz=timezone.utc)
        close_time = open_time + timedelta(
            minutes=TIMEFRAME_MINUTES[request.timeframe]
        )
        return RawCandle(
            provider_id=self.provider_id,
            source_symbol=PROVIDER_SYMBOLS[self.provider_id][request.instrument_id],
            instrument_id=request.instrument_id,
            timeframe=request.timeframe,
            open_time=open_time,
            close_time=close_time,
            open=_decimal(row[1], "open"),
            high=_decimal(row[2], "high"),
            low=_decimal(row[3], "low"),
            close=_decimal(row[4], "close"),
            volume=_decimal(row[6], "volume") if len(row) > 6 else None,
            source_timestamp=open_time,
            source_revision=None,
            finality_hint="NONFINAL" if provisional else "FINAL",
            clock_id=None,
        )

    def _rows(self, payload: Mapping[str, object]) -> tuple[Sequence[object], bool]:
        errors = payload.get("error", [])
        if errors:
            raise ProviderUpstreamRejectedError(
                "provider returned an error", provider_type="market_data",
                provider_name=self.provider_id,
            )
        result = payload.get("result", {})
        if not isinstance(result, MappingABC):
            raise ProviderMalformedResponseError("result must be an object")
        for key in _RESULT_KEYS:
            rows = result.get(key)
            if isinstance(rows, list):
                return rows, bool(payload.get("partial", True))
        raise ProviderMalformedResponseError("no OHLC series in response")

    def fetch(self, request: CandleRequest) -> CandlePage:
        if request.instrument_id not in PROVIDER_SYMBOLS[self.provider_id]:
            raise ProviderInvalidRequestError(
                f"unsupported instrument {request.instrument_id}",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        if request.timeframe not in _TIMEFRAMES:
            raise ProviderInvalidRequestError(
                f"unsupported timeframe {request.timeframe}",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        if request.limit > KRAKEN_REST_OHLC_LIMIT:
            raise ProviderInvalidRequestError(
                "request exceeds Kraken's 720-candle REST cap",
                provider_type="market_data",
                provider_name=self.provider_id,
            )
        try:
            payload = self._transport.next_page()
        except Exception as exc:
            self._last_failure = exc
            raise
        self._last_failure = None
        if payload is None:
            return CandlePage(candles=(), next_cursor=None, exhausted=True)
        rows, provisional = self._rows(payload)
        candles = tuple(
            self._parse(row, request, provisional=provisional and index == len(rows) - 1)
            for index, row in enumerate(rows)
        )
        next_cursor = candles[-1].close_time if bool(payload.get("next")) else None
        return CandlePage(
            candles=candles,
            next_cursor=next_cursor,
            exhausted=not bool(payload.get("next")),
        )

    def stream(self, request: CandleRequest):
        while True:
            payload = self._transport.next_event()
            if payload is None:
                return
            rows, provisional = self._rows(payload)
            for index, row in enumerate(rows):
                yield self._parse(
                    row, request, provisional=provisional and index == len(rows) - 1
                )

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


__all__ = ["KRAKEN_REST_OHLC_LIMIT", "KrakenAdapter"]
