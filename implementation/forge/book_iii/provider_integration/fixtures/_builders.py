"""Deterministic builders for the twelve WP-3B fixture cases.

Pure standard library: no repository imports, no network, no clock.  Every
payload is synthetic and labelled as such by ``generate.py``; nothing here is
market evidence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

ADAPTER_VERSION = "MARKET_DATA_INGEST_V1"


def _utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


CONVENTIONS = {
    "EURUSD": {"symbol": "EUR/USD", "places": 5, "base": "1.08420", "step": "0.00010", "volume": "100"},
    "XAUUSD": {"symbol": "XAU/USD", "places": 2, "base": "2385.00", "step": "0.35", "volume": "12.5"},
    "BTCUSD": {"symbol": "BTC/USD", "places": 2, "base": "68400.00", "step": "12.00", "volume": "3.2"},
    "USDJPY": {"symbol": "USD/JPY", "places": 3, "base": "157.250", "step": "0.005", "volume": "250"},
}


def _q(value: Decimal, places: int) -> str:
    quantum = Decimal(1).scaleb(-places)
    return format(value.quantize(quantum, rounding=ROUND_HALF_UP), "f")


def make_value(
    instrument: str,
    start: str,
    *,
    index: int = 0,
    close_shift: str = "0",
    revision: str | None = None,
    source_offset_seconds: int = 3,
) -> dict:
    """One Twelve Data shaped value."""
    convention = CONVENTIONS[instrument]
    places = convention["places"]
    step = Decimal(convention["step"])
    open_price = Decimal(convention["base"]) + step * index
    close_price = (open_price + step / 2 + Decimal(close_shift)).quantize(
        Decimal(1).scaleb(-places)
    )
    high = max(open_price, close_price) + step
    low = min(open_price, close_price) - step
    opened = _utc(start) + timedelta(minutes=5 * index)
    value = {
        "symbol": convention["symbol"],
        "interval": "5min",
        "datetime": _iso(opened),
        "open": _q(open_price, places),
        "high": _q(high, places),
        "low": _q(low, places),
        "close": _q(close_price, places),
        "volume": convention["volume"],
        "source_timestamp": _iso(opened + timedelta(seconds=source_offset_seconds)),
    }
    if revision is not None:
        value["revision"] = revision
    return value


def page(values: list[dict], *, next_page: bool = False, status: str = "ok") -> dict:
    return {"status": status, "values": values, "next": next_page}


def series(instrument: str, start: str, count: int, **kwargs) -> list[dict]:
    return [
        make_value(instrument, start, index=index, **kwargs)
        for index in range(count)
    ]


def _case(
    case_id: str,
    description: str,
    *,
    provider: str,
    instrument_id: str,
    timeframe: str,
    cutoff: str,
    pages: list[dict],
    expected: dict,
    events: list[dict] | None = None,
    disconnect_after: int | None = None,
    expected_opens: list[str] | None = None,
) -> dict:
    payload = {
        "case_id": case_id,
        "description": description,
        "provenance": "SYNTHETIC_FIXTURE",
        "adapter_version": ADAPTER_VERSION,
        "provider": provider,
        "instrument_id": instrument_id,
        "timeframe": timeframe,
        "observation_cutoff": cutoff,
        "pages": pages,
        "expected": expected,
    }
    if events is not None:
        payload["events"] = events
    if disconnect_after is not None:
        payload["disconnect_after"] = disconnect_after
    if expected_opens is not None:
        payload["expected_opens"] = expected_opens
    return payload


def build_cases() -> dict[str, dict]:
    """The twelve cases, in stable order."""
    fx_start = "2026-03-03T00:00:00Z"
    cases = [
        _case(
            "FIX-01",
            "Normal EURUSD M5 sequence",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[page(series("EURUSD", fx_start, 6))],
            expected={"bar_count": 6, "outcome": "OK", "quality_flags": ["COMPLETE"]},
        ),
        _case(
            "FIX-02",
            "XAUUSD bars across the 19:00 NY transition without a canonical session",
            provider="twelvedata",
            instrument_id="XAUUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[page(series("XAUUSD", fx_start, 4))],
            expected={
                "bar_count": 4,
                "outcome": "OK",
                "ownership": "NO_SESSION",
            },
        ),
        _case(
            "FIX-03",
            "BTCUSD Saturday sequence (24/7, no weekend gap)",
            provider="twelvedata",
            instrument_id="BTCUSD",
            timeframe="M5",
            cutoff="2026-03-07T01:00:00Z",
            pages=[page(series("BTCUSD", "2026-03-07T00:00:00Z", 6))],
            expected={"bar_count": 6, "missing_count": 0, "quality_flags": ["COMPLETE"]},
        ),
        _case(
            "FIX-04",
            "EURUSD spring-forward final-bar instant",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-08T08:03:00Z",
            pages=[page(series("EURUSD", "2026-03-08T06:40:00Z", 4))],
            expected={
                "bar_count": 4,
                "final_close": "2026-03-08T07:00:00Z",
            },
        ),
        _case(
            "FIX-05",
            "Duplicate EURUSD rows",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[
                page(
                    [
                        make_value("EURUSD", fx_start, index=0),
                        make_value("EURUSD", fx_start, index=0),
                        make_value("EURUSD", fx_start, index=1),
                    ]
                )
            ],
            expected={"bar_count": 2, "duplicates": 1, "quality_flags": ["DUPLICATE"]},
        ),
        _case(
            "FIX-06",
            "Out-of-order EURUSD arrivals",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[page(list(reversed(series("EURUSD", fx_start, 4))))],
            expected={"bar_count": 4, "order_independent": True},
        ),
        _case(
            "FIX-07",
            "Missing-bar window (index 2 absent)",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[
                page(
                    [
                        make_value("EURUSD", fx_start, index=0),
                        make_value("EURUSD", fx_start, index=1),
                        make_value("EURUSD", fx_start, index=3),
                        make_value("EURUSD", fx_start, index=4),
                    ]
                )
            ],
            expected_opens=[
                _iso(_utc(fx_start) + timedelta(minutes=5 * index))
                for index in range(5)
            ],
            expected={"bar_count": 4, "missing_count": 1, "outcome": "DEGRADED"},
        ),
        _case(
            "FIX-08",
            "Nonfinal-to-final update at the cutoff",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T00:12:00Z",
            pages=[page(series("EURUSD", fx_start, 3))],
            expected={"bar_count": 2, "excluded_nonfinal": 1, "outcome": "DEGRADED"},
        ),
        _case(
            "FIX-09",
            "Corrected source candle (later source timestamp)",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[
                page(
                    [
                        make_value("EURUSD", fx_start, index=0),
                        make_value(
                            "EURUSD",
                            fx_start,
                            index=0,
                            close_shift="0.00020",
                            revision="2",
                            source_offset_seconds=63,
                        ),
                    ]
                )
            ],
            expected={"bar_count": 1, "revisions": 1, "quality_flags": ["REVISED"]},
        ),
        _case(
            "FIX-10",
            "Disconnect and reconnect with buffered replay",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[page(series("EURUSD", fx_start, 4))],
            events=series("EURUSD", fx_start, 4),
            disconnect_after=2,
            expected={"bar_count": 4, "state_preserved": True},
        ),
        _case(
            "FIX-11",
            "Synthetic historical/live parity pair",
            provider="twelvedata",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[page(series("EURUSD", fx_start, 8))],
            events=series("EURUSD", fx_start, 8),
            expected={"parity": True, "bar_count": 8},
        ),
        _case(
            "FIX-12",
            "Cross-provider discrepancy beyond one tick",
            provider="polygon",
            instrument_id="EURUSD",
            timeframe="M5",
            cutoff="2026-03-03T08:03:00Z",
            pages=[
                {
                    "status": "OK",
                    "results": [
                        {
                            "sym": "C:EURUSD",
                            "t": int(
                                (_utc(fx_start) + timedelta(minutes=5 * index)).timestamp()
                                * 1000
                            ),
                            "o": _q(Decimal("1.08420") + Decimal("0.00010") * index, 5),
                            "h": _q(Decimal("1.08440") + Decimal("0.00010") * index, 5),
                            "l": _q(Decimal("1.08400") + Decimal("0.00010") * index, 5),
                            "c": _q(
                                Decimal("1.08425") + Decimal("0.00030")
                                + Decimal("0.00010") * index,
                                5,
                            ),
                        }
                        for index in range(4)
                    ],
                }
            ],
            expected={"disagreement": True, "flag": "OUTLIER_SOURCE"},
        ),
    ]
    return {case["case_id"]: case for case in cases}


CASE_NAMES: tuple[str, ...] = tuple(build_cases())
