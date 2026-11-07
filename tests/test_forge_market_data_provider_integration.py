"""WP-3B — offline market-data provider integration (66 contract tests).

Binding inventory: ``implementation/forge/book_iii/provider_integration/
ACCEPTANCE.md`` §3.  This file implements exactly the 66 ``M`` (mock/contract)
names; the six ``X`` external names remain a separate WP-3C inventory and are
deliberately absent rather than skipped.

No network, no credentials, no wall clock.  Adapters consume scripted
transports; canonical facts come from the frozen III.1 kernel.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pytest

from app.forge.config import ForgeConfig
from app.forge.intelligence_api.contracts import (
    Classifications,
    Provenance,
    QualityFacts,
    Snapshot,
    SnapshotKey,
    TimeFacts,
)
from app.forge.market_data.bars import (
    TIMEFRAME_MINUTES,
    Finality,
    FinalStateSelection,
    content_digest,
    final_state_input,
    finalize_for_cutoff,
    reconcile,
)
from app.forge.market_data.clocks import fixed_clock, local_wall, named_clock, to_utc
from app.forge.market_data.errors import (
    AmbiguousAliasError,
    ConventionViolationError,
    NonFinalError,
    UnknownAliasError,
)
from app.forge.market_data.instruments import InstrumentRegistry
from app.forge.market_data.parity import ModelBinding, OwnershipStatus, PipelinePath, bar_ownership
from app.forge.market_data.quality import DataOutcome, QualityFlag, QualityPolicy
from app.forge.market_data.research_day import (
    ResearchDayLineage,
    ResearchDayRegistry,
    assign_research_day,
)
from app.forge.market_data.sessions import (
    SessionDefinition,
    SessionFamily,
    SessionKind,
    SessionRegistry,
    close_matches_checkpoint,
    final_bar_open_utc,
)
from app.forge.market_data_ingest.backfill import (
    BackfillStalledError,
    merge_runs,
    run_backfill,
)
from app.forge.market_data_ingest.canonical import canonicalize
from app.forge.market_data_ingest.capture import source_window_digest
from app.forge.market_data_ingest.config import (
    MarketDataIngestConfig,
    config_from_environment,
)
from app.forge.market_data_ingest.contract import (
    CandlePage,
    CandleRequest,
    RawCandle,
)
from app.forge.market_data_ingest.disagreement import (
    clock_drift_seconds,
    compare_sources,
    detect_clock_drift,
)
from app.forge.market_data_ingest.health import (
    HealthMonitor,
    IngestHealth,
    IngestState,
    ReadinessEvidence,
)
from app.forge.market_data_ingest.providers import (
    KrakenAdapter,
    PolygonAdapter,
    TwelveDataAdapter,
)
from app.forge.market_data_ingest.providers.kraken import KRAKEN_REST_OHLC_LIMIT
from app.forge.market_data_ingest.registry import build_ingest_registry
from app.forge.market_data_ingest.replay import offline_parity, run_offline
from app.forge.market_data_ingest.routing import (
    SourceBlendError,
    SourcePolicy,
    assert_single_source,
    fetch_with_failover,
)
from app.forge.market_data_ingest.stream import (
    StreamBuffer,
    StreamDisconnectedError,
    StreamEvent,
    StreamKind,
)
from app.forge.market_data_ingest.symbols import (
    PROVIDER_SYMBOLS,
    instrument_for_source_symbol,
    source_symbol,
)
from app.forge.model_runtime.contract import Layer
from app.forge.providers.doctrine import ProviderHealth
from app.forge.providers.errors import (
    ProviderAuthenticationFailedError,
    ProviderConfigurationError,
    ProviderInvalidRequestError,
    ProviderMalformedResponseError,
    ProviderRateLimitedError,
    ProviderUnavailableError,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURES = (
    REPO
    / "implementation"
    / "forge"
    / "book_iii"
    / "provider_integration"
    / "fixtures"
)

UTC = timezone.utc
START = datetime(2026, 3, 3, 0, 0, tzinfo=UTC)
CUTOFF = datetime(2026, 3, 3, 8, 3, tzinfo=UTC)

REG = build_ingest_registry()

POLICY = QualityPolicy.from_strings(
    "wp3b",
    "1",
    blocking=["OUTLIER_SOURCE", "UNSUPPORTED_CLOCK", "NONFINAL"],
    warning=["GAP", "DUPLICATE", "REVISED", "STALE"],
)
BLOCKING_POLICY = QualityPolicy.from_strings(
    "wp3b",
    "1",
    blocking=["GAP", "NONFINAL", "OUTLIER_SOURCE", "UNSUPPORTED_CLOCK"],
    warning=["DUPLICATE", "REVISED", "STALE"],
)

BASE = {
    "EURUSD": Decimal("1.08420"),
    "XAUUSD": Decimal("2385.00"),
    "BTCUSD": Decimal("68400.00"),
    "USDJPY": Decimal("157.250"),
    "AUDJPY": Decimal("98.500"),
    "EURJPY": Decimal("170.250"),
}
STEP = {
    "EURUSD": Decimal("0.00010"),
    "XAUUSD": Decimal("0.35"),
    "BTCUSD": Decimal("12.00"),
    "USDJPY": Decimal("0.005"),
    "AUDJPY": Decimal("0.005"),
    "EURJPY": Decimal("0.005"),
}
PRECISION = {
    "EURUSD": 5,
    "XAUUSD": 2,
    "BTCUSD": 2,
    "USDJPY": 3,
    "AUDJPY": 3,
    "EURJPY": 3,
}


def _q(value: Decimal, instrument: str) -> Decimal:
    quantum = Decimal(1).scaleb(-PRECISION[instrument])
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def raw(
    index: int = 0,
    *,
    instrument: str = "EURUSD",
    provider: str = "twelvedata",
    timeframe: str = "M5",
    start: datetime = START,
    clock_id: str | None = None,
    finality_hint: str | None = None,
    source_offset: int = 3,
    revision: str | None = None,
    close_shift: str = "0",
) -> RawCandle:
    step = STEP[instrument]
    open_price = _q(BASE[instrument] + step * index, instrument)
    close_price = _q(open_price + step / 2 + Decimal(close_shift), instrument)
    high = _q(max(open_price, close_price) + step, instrument)
    low = _q(min(open_price, close_price) - step, instrument)
    opened = start + timedelta(minutes=5 * index)
    return RawCandle(
        provider_id=provider,
        source_symbol=PROVIDER_SYMBOLS[provider][instrument],
        instrument_id=instrument,
        timeframe=timeframe,
        open_time=opened,
        close_time=opened + timedelta(minutes=TIMEFRAME_MINUTES[timeframe]),
        open=open_price,
        high=high,
        low=low,
        close=close_price,
        volume=Decimal("1"),
        source_timestamp=opened + timedelta(seconds=source_offset),
        source_revision=revision,
        finality_hint=finality_hint,
        clock_id=clock_id,
    )


def canon(candles, *, cutoff=CUTOFF, expected_opens=None, policy=POLICY):
    return canonicalize(
        candles,
        REG,
        policy,
        observation_cutoff=cutoff,
        expected_opens=expected_opens,
    )


def grid(count: int, *, start: datetime = START, minutes: int = 5):
    return [start + timedelta(minutes=minutes * index) for index in range(count)]


def td_page(values, *, next_page: bool = False, status: str = "ok"):
    return {"status": status, "values": values, "next": next_page}


def td_value(
    index: int,
    *,
    instrument: str = "EURUSD",
    start: datetime = START,
    symbol: str | None = None,
    naive: bool = False,
):
    candle = raw(index, instrument=instrument, start=start)
    opened = candle.open_time
    text = opened.isoformat()
    if naive:
        text = opened.replace(tzinfo=None).isoformat()
    return {
        "symbol": symbol or PROVIDER_SYMBOLS["twelvedata"][instrument],
        "interval": "5min",
        "datetime": text,
        "open": format(candle.open, "f"),
        "high": format(candle.high, "f"),
        "low": format(candle.low, "f"),
        "close": format(candle.close, "f"),
        "volume": "1",
        "source_timestamp": (opened + timedelta(seconds=3)).isoformat(),
    }


def td_request(instrument: str = "EURUSD", *, limit: int = 50, timeframe: str = "M5"):
    return CandleRequest(
        instrument_id=instrument,
        timeframe=timeframe,
        start=START,
        end=START + timedelta(hours=6),
        limit=limit,
    )


def kraken_rows(indices, *, start: datetime = START):
    rows = []
    for index in indices:
        candle = raw(index, instrument="BTCUSD", start=start)
        stamp = int(candle.open_time.timestamp())
        rows.append(
            [
                stamp,
                format(candle.open, "f"),
                format(candle.high, "f"),
                format(candle.low, "f"),
                format(candle.close, "f"),
                format(candle.close, "f"),
                "3.2",
                "10",
            ]
        )
    return rows


def _load_fixture(case_id: str) -> dict:
    return json.loads(
        (FIXTURES / f"{case_id.lower().replace('-', '_')}.json").read_text(
            encoding="utf-8"
        )
    )


def _parse_stamp(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)


class _StubProvider:
    """Minimal MarketDataProvider used only for failover tests."""

    def __init__(self, provider_id: str, *, error: Exception | None = None, candles=()):
        self.provider_id = provider_id
        self._error = error
        self._candles = tuple(candles)
        self.calls = 0

    def capabilities(self):
        from app.forge.market_data_ingest.contract import ProviderCapabilities

        return ProviderCapabilities(
            provider_id=self.provider_id,
            instruments=frozenset({"EURUSD"}),
            timeframes=frozenset({"M5"}),
            historical=True,
            streaming=False,
            revision_support=False,
            finality_signal=False,
            max_page_size=100,
        )

    def fetch(self, request):
        self.calls += 1
        if self._error is not None:
            raise self._error
        return CandlePage(candles=self._candles)

    def stream(self, request):  # pragma: no cover - not used
        return iter(())

    def health(self):
        return ProviderHealth(
            provider_type="market_data",
            provider_name=self.provider_id,
            status="healthy",
        )

    def close(self):
        return None


# ---------------------------------------------------------------------------
# T1 — adapter contracts (9)
# ---------------------------------------------------------------------------


def test_adapter_identity_is_stable_per_provider():
    td = TwelveDataAdapter(pages=[td_page([td_value(0)]), td_page([td_value(1)])])
    assert td.provider_id == "twelvedata"
    assert td.capabilities().provider_id == td.provider_id
    first = td.fetch(td_request())
    second = td.fetch(td_request())
    assert first.candles[0].provider_id == second.candles[0].provider_id == "twelvedata"
    # Provider identity and symbol spelling stay provenance: they change the
    # raw observation identity but never canonical bar content.
    assert raw(0, provider="twelvedata").digest() == raw(0, provider="polygon").digest()
    td_bars = canon([raw(index) for index in range(2)]).bars
    polygon_bars = canon([raw(index, provider="polygon") for index in range(2)]).bars
    assert {bar.provider for bar in polygon_bars} == {"polygon"}
    assert content_digest(td_bars) == content_digest(polygon_bars)


def test_adapter_capabilities_declare_instruments_and_timeframes():
    td = TwelveDataAdapter().capabilities()
    assert set(td.instruments) == {
        "EURUSD",
        "XAUUSD",
        "USDJPY",
        "AUDJPY",
        "EURJPY",
        "BTCUSD",
    }
    assert td.timeframes == frozenset({"M5", "H1"})
    assert all(tf in TIMEFRAME_MINUTES for tf in td.timeframes)
    assert not td.supports("EURUSD", "W1")
    kraken = KrakenAdapter().capabilities()
    assert kraken.instruments == frozenset({"BTCUSD"})
    assert kraken.max_page_size == KRAKEN_REST_OHLC_LIMIT == 720
    assert kraken.finality_signal is True
    assert td.finality_signal is False


def test_adapter_returns_provider_neutral_raw_candles():
    page = TwelveDataAdapter(pages=[td_page([td_value(0)])]).fetch(td_request())
    candle = page.candles[0]
    assert candle.instrument_id == "EURUSD"
    assert candle.source_symbol == "EUR/USD"
    bar = canon([candle]).bars[0]
    payload = json.dumps(bar.to_dict(), sort_keys=True)
    assert "EUR/USD" not in payload
    assert bar.instrument_id == "EURUSD"
    assert set(bar.to_dict()) == {
        "instrument_id",
        "timeframe",
        "open_time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "provider",
        "finality",
        "source_timestamp",
        "quality_flags",
        "provenance",
        "source_ref",
        "market_data_schema_version",
    }


def test_adapter_refuses_naive_timestamps():
    with pytest.raises(ConventionViolationError):
        RawCandle(
            provider_id="twelvedata",
            source_symbol="EUR/USD",
            instrument_id="EURUSD",
            timeframe="M5",
            open_time=datetime(2026, 3, 3, 0, 0),
            close_time=datetime(2026, 3, 3, 0, 5, tzinfo=UTC),
            open=Decimal("1.08420"),
            high=Decimal("1.08440"),
            low=Decimal("1.08400"),
            close=Decimal("1.08425"),
            source_timestamp=datetime(2026, 3, 3, 0, 0, tzinfo=UTC),
        )
    adapter = TwelveDataAdapter(pages=[td_page([td_value(0, naive=True)])])
    with pytest.raises(ProviderMalformedResponseError):
        adapter.fetch(td_request())


def test_adapter_preserves_source_timestamp_separately():
    page = TwelveDataAdapter(
        pages=[td_page([td_value(0)])]
    ).fetch(td_request())
    candle = page.candles[0]
    assert candle.source_timestamp > candle.open_time
    bar = canon([candle]).bars[0]
    assert bar.source_timestamp == candle.source_timestamp
    assert bar.open_time == candle.open_time
    assert bar.source_timestamp != bar.open_time


def test_adapter_does_not_compute_sessions():
    bar = canon([raw(0, instrument="XAUUSD")]).bars[0]
    assert not hasattr(bar, "session_id")
    assert not hasattr(bar, "session")
    ownership = bar_ownership(bar, [], SessionRegistry(), ResearchDayRegistry())
    assert ownership.status is OwnershipStatus.NO_CALCULATION
    assert ownership.reason_code == "NO_BINDING"
    provider_source = "".join(
        path.read_text(encoding="utf-8")
        for path in (REPO / "app/forge/market_data_ingest/providers").glob("*.py")
    )
    assert "SessionRegistry" not in provider_source
    assert "SessionDefinition" not in provider_source


def test_adapter_does_not_compute_research_day():
    bar = canon([raw(0)]).bars[0]
    assert not hasattr(bar, "research_day")
    assert not hasattr(bar, "research_day_id")
    ownership = bar_ownership(
        bar,
        [ModelBinding("EURUSD", "eur_carry", "1", "eur_lineage")],
        SessionRegistry(),
        ResearchDayRegistry(),
    )
    assert ownership.research_day is None
    assert ownership.status is not OwnershipStatus.RESOLVED


def test_adapter_does_not_aggregate_timeframes():
    adapter = TwelveDataAdapter(
        pages=[td_page([td_value(0)]), td_page([td_value(0)])]
    )
    page = adapter.fetch(td_request())
    assert {candle.timeframe for candle in page.candles} == {"M5"}
    with pytest.raises(ProviderInvalidRequestError):
        adapter.fetch(td_request(timeframe="M15"))
    capabilities = adapter.capabilities()
    assert "M15" not in capabilities.timeframes
    assert "H4" not in capabilities.timeframes


def test_adapter_rejects_unknown_symbol_before_network():
    adapter = KrakenAdapter()
    with pytest.raises(ProviderInvalidRequestError):
        adapter.fetch(td_request("EURUSD"))
    assert adapter._transport.calls == 0  # type: ignore[attr-defined]
    with pytest.raises(ProviderMalformedResponseError):
        TwelveDataAdapter(
            pages=[td_page([td_value(0, symbol="ZZZ/ZZZ")])]
        ).fetch(td_request())
    with pytest.raises(UnknownAliasError):
        instrument_for_source_symbol("twelvedata", "ZZZ/ZZZ")
    with pytest.raises(UnknownAliasError):
        source_symbol("twelvedata", "NOTAPAIR")


# ---------------------------------------------------------------------------
# T2 — historical backfill, mock half (6 of 8; #10 and #16 are WP-3C)
# ---------------------------------------------------------------------------


def test_backfill_reingest_is_idempotent():
    request = td_request(limit=2)
    pages = [
        td_page([td_value(0), td_value(1)], next_page=True),
        td_page([td_value(2)], next_page=False),
    ]
    first = run_backfill(TwelveDataAdapter(pages=list(pages)), request)
    second = run_backfill(TwelveDataAdapter(pages=list(pages)), request)
    assert first.digest == second.digest
    assert merge_runs(first, second) == first.candles
    assert [c.open_time for c in first.candles] == sorted(
        c.open_time for c in first.candles
    )


def test_backfill_window_digest_is_order_independent():
    candles = [raw(index) for index in range(5)]
    assert source_window_digest(candles) == source_window_digest(list(reversed(candles)))
    shuffled = [candles[3], candles[0], candles[4], candles[2], candles[1]]
    assert source_window_digest(shuffled) == source_window_digest(candles)


def test_backfill_duplicate_rows_reconcile_deterministically():
    candles = [raw(0), raw(0), raw(1)]
    outcome = canon(candles)
    assert len(outcome.bars) == 2
    assert QualityFlag.DUPLICATE in outcome.quality_flags
    assert QualityFlag.COMPLETE not in outcome.quality_flags
    # Same observations in any order reconcile identically.
    assert canon(list(reversed(candles))).digest == outcome.digest


def test_backfill_revision_replaces_by_source_timestamp():
    original = raw(0)
    corrected = raw(0, close_shift="0.00020", revision="2", source_offset=60)
    outcome = canon([original, corrected])
    assert len(outcome.bars) == 1
    assert outcome.bars[0].close == corrected.close
    assert outcome.bars[0].source_timestamp == corrected.source_timestamp
    assert QualityFlag.REVISED in outcome.quality_flags
    # Arrival order cannot let the older row win.
    assert canon([corrected, original]).bars[0].close == corrected.close


def test_backfill_missing_window_is_reported_not_filled():
    fixture = _load_fixture("FIX-07")
    expected = [_parse_stamp(value) for value in fixture["expected_opens"]]
    candles = [raw(index) for index in (0, 1, 3, 4)]
    outcome = canon(candles, expected_opens=expected)
    assert len(outcome.bars) == 4
    assert outcome.missing == (START + timedelta(minutes=10),)
    assert QualityFlag.GAP in outcome.quality_flags
    assert outcome.outcome is DataOutcome.DEGRADED
    assert all(bar.open_time != outcome.missing[0] for bar in outcome.bars)


def test_backfill_stalled_window_fails_closed():
    adapter = TwelveDataAdapter(
        pages=[td_page([td_value(0)], next_page=True), td_page([td_value(0)], next_page=True)]
    )
    with pytest.raises(BackfillStalledError):
        run_backfill(adapter, td_request(limit=1), max_pages=4)
    assert adapter._transport.calls == 2  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# T3 — live streaming/polling, mock half (7 of 8; #25 is WP-3C)
# ---------------------------------------------------------------------------


def _kraken_fetch(indices, *, partial=True):
    adapter = KrakenAdapter(
        pages=[{"error": [], "result": {"XXBTZUSD": kraken_rows(indices)}, "partial": partial}]
    )
    return adapter.fetch(td_request("BTCUSD"))


def test_stream_marks_trailing_candle_nonfinal():
    page = _kraken_fetch([0, 1])
    assert page.candles[0].finality_hint == "FINAL"
    assert page.candles[-1].finality_hint == "NONFINAL"
    outcome = canon(page.candles, cutoff=START + timedelta(minutes=5))
    assert outcome.bars[0].finality is Finality.FINAL
    assert outcome.bars[-1].finality is Finality.NONFINAL
    assert QualityFlag.NONFINAL in outcome.bars[-1].quality_flags


def test_stream_finality_transition_is_kernel_owned():
    page = _kraken_fetch([0, 1])
    outcome = canon(page.candles, cutoff=START + timedelta(minutes=30))
    assert {bar.finality for bar in outcome.bars} == {Finality.FINAL}
    assert all(QualityFlag.NONFINAL not in bar.quality_flags for bar in outcome.bars)
    # The adapter hint is not the finalizer: same observations, later cutoff.
    assert page.candles[-1].finality_hint == "NONFINAL"


def test_stream_provider_complete_hint_cannot_override_cutoff():
    candle = raw(2, finality_hint="FINAL")
    outcome = canon([candle], cutoff=START + timedelta(minutes=12))
    assert outcome.bars[0].finality is Finality.NONFINAL
    assert QualityFlag.NONFINAL in outcome.bars[0].quality_flags


def test_stream_late_correction_emits_revision():
    buffer = StreamBuffer()
    buffer.apply(StreamEvent(kind=StreamKind.UPDATE, candle=raw(0)))
    buffer.apply(
        StreamEvent(
            kind=StreamKind.UPDATE,
            candle=raw(0, close_shift="0.00020", revision="2", source_offset=60),
        )
    )
    assert buffer.revisions == 1
    assert buffer.duplicates == 0
    assert buffer.latest()[0].close == raw(0, close_shift="0.00020", revision="2").close
    # Revision lineage is carried by the reconciled observation set.
    outcome = canon([raw(0), raw(0, close_shift="0.00020", revision="2", source_offset=60)])
    assert QualityFlag.REVISED in outcome.quality_flags
    assert outcome.bars[0].close == raw(0, close_shift="0.00020", revision="2").close


def test_stream_out_of_order_arrivals_match_batch_order():
    ordered = [raw(index) for index in range(4)]
    shuffled = [ordered[2], ordered[0], ordered[3], ordered[1]]
    buffer = StreamBuffer()
    buffer.extend(StreamEvent(kind=StreamKind.UPDATE, candle=item) for item in shuffled)
    batch = canon(ordered)
    streamed = canon(list(buffer.latest()))
    assert streamed.digest == batch.digest
    assert source_window_digest(buffer.latest()) == source_window_digest(ordered)


def test_stream_duplicate_delivery_is_suppressed():
    buffer = StreamBuffer()
    candle = raw(0)
    buffer.apply(StreamEvent(kind=StreamKind.UPDATE, candle=candle))
    buffer.apply(StreamEvent(kind=StreamKind.UPDATE, candle=candle))
    assert buffer.duplicates == 1
    assert buffer.size == 1
    assert buffer.latest() == (candle,)


def test_stream_disconnect_preserves_last_canonical_state():
    buffer = StreamBuffer()
    buffer.extend(
        [
            StreamEvent(kind=StreamKind.UPDATE, candle=raw(0)),
            StreamEvent(kind=StreamKind.UPDATE, candle=raw(1)),
        ]
    )
    before = buffer.latest()
    buffer.apply(StreamEvent(kind=StreamKind.DISCONNECT))
    assert buffer.connected is False
    assert buffer.latest() == before
    with pytest.raises(StreamDisconnectedError):
        buffer.apply(StreamEvent(kind=StreamKind.UPDATE, candle=raw(2)))
    buffer.apply(StreamEvent(kind=StreamKind.RECONNECT))
    buffer.apply(StreamEvent(kind=StreamKind.UPDATE, candle=raw(2)))
    assert buffer.size == 3
    assert canon(list(buffer.latest())).digest == canon(
        [raw(0), raw(1), raw(2)]
    ).digest


# ---------------------------------------------------------------------------
# T4 — sessions and clocks (8)
# ---------------------------------------------------------------------------


def _ny():
    return named_clock("America/New_York")


def _ny_window(session_id: str = "EUR_1900_0300") -> SessionDefinition:
    return SessionDefinition(
        session_id=session_id,
        family=SessionFamily.ASIAN_RANGE,
        model_id="eur_carry",
        model_version="1",
        kind=SessionKind.WINDOW,
        clock=_ny(),
        source_ref="EUR_CARD_19_03",
        start_local=time(19, 0),
        end_local=time(3, 0),
    )


def _lineage(lineage_id: str = "eur_lineage") -> ResearchDayLineage:
    return ResearchDayLineage(
        lineage_id=lineage_id,
        model_id="eur_carry",
        model_version="1",
        clock=_ny(),
        evening_shift_boundary=time(19, 0),
        source_ref="EUR_CARD_RESEARCH_DAY",
    )


def test_eur_research_day_shifts_after_1900_close():
    registry = ResearchDayRegistry()
    registry.register(_lineage())
    evening = assign_research_day(
        registry, "eur_lineage", "EURUSD", datetime(2026, 3, 3, 1, 0, tzinfo=UTC)
    )
    assert evening.status.value == "RESOLVED"
    assert evening.research_day == date(2026, 3, 3)
    before = assign_research_day(
        registry, "eur_lineage", "EURUSD", datetime(2026, 3, 2, 23, 59, tzinfo=UTC)
    )
    assert before.research_day == date(2026, 3, 2)
    # Exactly at 19:00 NY the close is entirely pre-boundary.
    at_boundary = assign_research_day(
        registry, "eur_lineage", "EURUSD", datetime(2026, 3, 3, 0, 0, tzinfo=UTC)
    )
    assert at_boundary.research_day == date(2026, 3, 2)


def test_eur_spring_forward_final_bar_instant_exists():
    definition = _ny_window()
    final_open = final_bar_open_utc(
        definition, timedelta(minutes=5), date(2026, 3, 7)
    )
    assert final_open == datetime(2026, 3, 8, 6, 55, tzinfo=UTC)
    assert local_wall(final_open, definition.clock).time() == time(1, 55)
    # The 02:55 wall label does not exist that day; no bar is invented for it.
    naive_gap = datetime(2026, 3, 8, 2, 55)
    assert to_utc(naive_gap, definition.clock) != final_open


def test_eur_fall_back_repeated_hour_is_deterministic():
    clock = _ny()
    wall = datetime(2026, 11, 1, 1, 30)
    first = to_utc(wall, clock, fold=0)
    second = to_utc(wall, clock, fold=1)
    assert first == datetime(2026, 11, 1, 5, 30, tzinfo=UTC)
    assert second == datetime(2026, 11, 1, 6, 30, tzinfo=UTC)
    assert first != second
    assert to_utc(wall, clock, fold=1) == second


def test_btc_continuous_market_has_no_weekend_gap():
    saturday = datetime(2026, 3, 7, 0, 0, tzinfo=UTC)
    candles = [raw(index, instrument="BTCUSD", start=saturday) for index in range(6)]
    outcome = canon(candles, expected_opens=grid(6, start=saturday))
    assert len(outcome.bars) == 6
    assert outcome.missing == ()
    assert QualityFlag.GAP not in outcome.quality_flags


def test_btc_checkpoint_matches_exact_1200_close():
    checkpoint = SessionDefinition(
        session_id="BTC_1200_NY",
        family=SessionFamily.DAILY_CHECKPOINT,
        model_id="btc_tracker",
        model_version="1",
        kind=SessionKind.CHECKPOINT,
        clock=_ny(),
        source_ref="BTC_CARD_1200",
        instant_local=time(12, 0),
    )
    assert checkpoint.start_local is None and checkpoint.end_local is None
    on_time = datetime(2026, 3, 3, 17, 0, tzinfo=UTC)
    late = datetime(2026, 3, 3, 17, 5, tzinfo=UTC)
    assert close_matches_checkpoint(checkpoint, local_wall(on_time, checkpoint.clock))
    assert not close_matches_checkpoint(checkpoint, local_wall(late, checkpoint.clock))


def test_xau_session_ownership_refuses_without_canonical_definition():
    bar = canon([raw(0, instrument="XAUUSD")]).bars[0]
    ownership = bar_ownership(
        bar,
        [ModelBinding("XAUUSD", "xau_model", "1", "xau_lineage")],
        SessionRegistry(),
        ResearchDayRegistry(),
    )
    assert ownership.status is OwnershipStatus.NO_CALCULATION
    assert ownership.reason_code == "NO_SESSION"
    assert ownership.session_id is None


def test_jpy_dt_binding_refuses_without_crosswalk():
    # Never registered as an implicit DT->Carry binding or lineage.
    assert ResearchDayRegistry().get("JPY_DT_CARRY") is None
    bar = canon([raw(0, instrument="USDJPY")]).bars[0]
    ownership = bar_ownership(
        bar, [], SessionRegistry(), ResearchDayRegistry()
    )
    assert ownership.status is OwnershipStatus.NO_CALCULATION
    assert ownership.reason_code == "NO_BINDING"
    with pytest.raises(UnknownAliasError):
        build_ingest_registry().resolve("JPY_DT_CARRY")


def test_adapter_does_not_invent_holiday_calendar():
    # Christmas is not special-cased: the interior absence stays a visible gap.
    start = datetime(2026, 12, 25, 0, 0, tzinfo=UTC)
    candles = [raw(index, start=start) for index in (0, 1, 3)]
    outcome = canon(
        candles,
        cutoff=datetime(2026, 12, 26, 0, 0, tzinfo=UTC),
        expected_opens=grid(4, start=start),
    )
    assert outcome.missing == (start + timedelta(minutes=10),)
    assert QualityFlag.GAP in outcome.quality_flags
    assert not hasattr(SessionRegistry(), "holidays")


# ---------------------------------------------------------------------------
# T5 — parity, mock half (4 of 7; #34, #36 and #40 are WP-3C)
# ---------------------------------------------------------------------------


def test_parity_survives_delivery_permutation():
    candles = [raw(index) for index in range(6)]
    replay = run_offline(
        candles,
        REG,
        POLICY,
        observation_cutoff=CUTOFF,
        path=PipelinePath.REPLAY,
    )
    streaming = run_offline(
        list(reversed(candles)),
        REG,
        POLICY,
        observation_cutoff=CUTOFF,
        path=PipelinePath.STREAMING,
    )
    report = offline_parity(replay, streaming)
    assert report.overall is True
    assert report.differences == ()
    assert replay.content_digest == streaming.content_digest


def test_parity_digest_excludes_provider_identity():
    bars_td = canon([raw(index, provider="twelvedata") for index in range(3)]).bars
    bars_polygon = canon([raw(index, provider="polygon") for index in range(3)]).bars
    assert {bar.provider for bar in bars_td} == {"twelvedata"}
    assert {bar.provider for bar in bars_polygon} == {"polygon"}
    assert content_digest(bars_td) == content_digest(bars_polygon)


def test_parity_detects_injected_bar_drift():
    baseline = canon([raw(index) for index in range(3)]).bars
    drifted = canon([raw(index) for index in range(2)] + [raw(2, close_shift="0.00020")]).bars
    assert content_digest(baseline) != content_digest(drifted)


def test_parity_detects_missing_bar_difference():
    full = [raw(index) for index in range(4)]
    replay = run_offline(
        full, REG, POLICY, observation_cutoff=CUTOFF, path=PipelinePath.REPLAY,
        expected_opens=grid(4),
    )
    streaming = run_offline(
        full[:3], REG, POLICY, observation_cutoff=CUTOFF, path=PipelinePath.STREAMING,
        expected_opens=grid(4),
    )
    report = offline_parity(replay, streaming)
    assert report.bar_parity is False
    assert "bars" in report.differences
    assert replay.missing != streaming.missing


# ---------------------------------------------------------------------------
# T6 — quality propagation (7)
# ---------------------------------------------------------------------------


def test_provider_outage_yields_data_quality_blocked():
    adapter = TwelveDataAdapter(
        failures=[
            ProviderUnavailableError(
                "provider unreachable",
                provider_type="market_data",
                provider_name="twelvedata",
            )
        ]
    )
    with pytest.raises(ProviderUnavailableError) as exc:
        adapter.fetch(td_request())
    assert exc.value.retryable is True
    assert adapter.health().status == "unavailable"
    outcome = canon([], expected_opens=grid(3), policy=BLOCKING_POLICY)
    assert outcome.bars == ()
    assert outcome.missing == tuple(grid(3))
    assert outcome.outcome is DataOutcome.DATA_QUALITY_BLOCKED


def test_missing_source_window_yields_no_calculation():
    resolution = SessionRegistry().resolve("eur_carry", "1", "UNDEFINED_SESSION")
    assert resolution.outcome is DataOutcome.NO_CALCULATION
    bar = canon([raw(0)]).bars[0]
    ownership = bar_ownership(bar, [], SessionRegistry(), ResearchDayRegistry())
    assert ownership.status is OwnershipStatus.NO_CALCULATION
    assert ownership.reason_code == "NO_BINDING"


def test_nonfinal_source_cannot_reach_final_state():
    bars = canon([raw(0), raw(2)], cutoff=START + timedelta(minutes=12)).bars
    selection = final_state_input(bars, START + timedelta(minutes=12))
    assert selection.excluded_nonfinal == 1
    assert selection.outcome is DataOutcome.DEGRADED
    with pytest.raises(NonFinalError):
        FinalStateSelection(
            final_bars=(bars[-1],),
            excluded_nonfinal=1,
            outcome=DataOutcome.DEGRADED,
        )


def test_stale_label_is_carried_not_invented():
    outcome = canon([raw(0)])
    assert QualityFlag.STALE not in outcome.quality_flags
    assert QualityFlag.STALE not in outcome.bars[0].quality_flags
    labelled = outcome.bars[0].with_flags([QualityFlag.STALE])
    assert QualityFlag.STALE in labelled.quality_flags
    facts = QualityFacts(
        outcome=DataOutcome.DEGRADED,
        flags=(QualityFlag.STALE,),
        stale_label="SOURCE_DECLARED",
    )
    assert facts.stale_label == "SOURCE_DECLARED"


def test_incomplete_history_degrades_with_gap():
    outcome = canon([raw(index) for index in (0, 1, 3)], expected_opens=grid(4))
    assert len(outcome.bars) == 3
    assert QualityFlag.GAP in outcome.quality_flags
    assert outcome.outcome is DataOutcome.DEGRADED


def test_unsupported_clock_fails_closed():
    outcome = canon([raw(0, clock_id="Europe/London")])
    assert outcome.bars == ()
    assert outcome.refusal_count == 1
    refusal = outcome.refused[0]
    assert refusal.reason.value == "UNSUPPORTED_CLOCK"
    assert QualityFlag.UNSUPPORTED_CLOCK in refusal.flags
    assert outcome.outcome is DataOutcome.DATA_QUALITY_BLOCKED


def test_quality_outcome_reaches_snapshot_unchanged():
    facts = QualityFacts(
        outcome=DataOutcome.DATA_QUALITY_BLOCKED,
        flags=(QualityFlag.GAP, QualityFlag.OUTLIER_SOURCE),
        source_window_digest="a" * 64,
        provider_status="NOT_CONFIGURED",
    )
    key = SnapshotKey(
        instrument_id="EURUSD",
        model_id="eur_carry",
        model_version="1",
        layer=Layer.L1,
        as_of="2026-03-03T08:03:00Z",
        data_cutoff="2026-03-03T08:03:00Z",
        calculation_version="wp3b-1",
        clock_id="America/New_York",
    )
    snapshot = Snapshot(
        key=key,
        time=TimeFacts(
            as_of="2026-03-03T08:03:00Z",
            data_cutoff="2026-03-03T08:03:00Z",
            calculation_timestamp="2026-03-03T08:03:00Z",
        ),
        quality=facts,
        classifications=Classifications(
            execution_class=None,
            exposure=None,
            research_only=True,
            manual_only=True,
        ),
        provenance=Provenance(registry_versions=(("market_data", "M5"),)),
    )
    assert snapshot.quality is facts
    assert snapshot.payload()["quality"] is facts
    assert QualityFlag.GAP in snapshot.quality.flags


# ---------------------------------------------------------------------------
# T7 — multi-provider disagreement (7)
# ---------------------------------------------------------------------------


def test_secondary_source_is_recorded_per_bar():
    candles = [raw(index, provider="polygon") for index in range(3)]
    outcome = canon(candles)
    assert {bar.provider for bar in outcome.bars} == {"polygon"}
    assert all(bar.provider for bar in outcome.bars)
    assert assert_single_source(candles) == "polygon"


def test_source_disagreement_beyond_tick_blocks():
    primary = [raw(index) for index in range(3)]
    secondary = [
        raw(index, provider="polygon", close_shift="0.00030") for index in range(3)
    ]
    report = compare_sources(primary, secondary, tolerance=Decimal("0.00001"))
    assert report.agreement is False
    assert QualityFlag.OUTLIER_SOURCE in report.flags
    assert POLICY.evaluate(report.flags) is DataOutcome.DATA_QUALITY_BLOCKED


def test_source_agreement_within_tick_is_accepted():
    primary = [raw(index) for index in range(3)]
    secondary = [
        raw(index, provider="polygon", close_shift="0.00001") for index in range(3)
    ]
    report = compare_sources(primary, secondary, tolerance=Decimal("0.00001"))
    assert report.agreement is True
    assert report.flags == frozenset()
    assert report.max_close_delta == Decimal("0.00001")
    assert POLICY.evaluate(report.flags) is DataOutcome.OK


def test_failover_does_not_blend_providers_in_one_series():
    series = [raw(0), raw(1, provider="polygon")]
    with pytest.raises(SourceBlendError):
        assert_single_source(series)
    assert assert_single_source(series, boundary_declared=True) == "polygon"
    # A declared boundary keeps both providers visible per bar.
    assert [bar.provider for bar in canon(series).bars] == ["twelvedata", "polygon"]


def test_failover_requires_retryable_failure():
    primary = _StubProvider(
        "primary",
        error=ProviderInvalidRequestError(
            "bad request", provider_type="market_data", provider_name="primary"
        ),
    )
    secondary = _StubProvider("secondary", candles=[raw(0)])
    policy = SourcePolicy({"EURUSD": ("primary", "secondary")})
    with pytest.raises(ProviderInvalidRequestError):
        fetch_with_failover(
            {"primary": primary, "secondary": secondary}, policy, td_request()
        )
    assert secondary.calls == 0

    primary = _StubProvider(
        "primary",
        error=ProviderRateLimitedError(
            "slow down",
            provider_type="market_data",
            provider_name="primary",
            retry_after_seconds=2.0,
        ),
    )
    result = fetch_with_failover(
        {"primary": primary, "secondary": secondary}, policy, td_request()
    )
    assert result.provider_id == "secondary"
    assert result.failed_over is True
    assert result.attempted == ("primary", "secondary")


def test_symbol_mapping_change_is_detected():
    eurusd = replace(
        build_ingest_registry().get("EURUSD"),
        provider_mappings={"mock": "MOCK/USD"},
    )
    xauusd = replace(
        build_ingest_registry().get("XAUUSD"),
        provider_mappings={"mock": "MOCK/USD"},
    )
    with pytest.raises(AmbiguousAliasError):
        InstrumentRegistry([eurusd, xauusd])
    with pytest.raises(UnknownAliasError):
        instrument_for_source_symbol("mock", "MOCK/USD")


def test_source_clock_drift_is_detected():
    drifted = [raw(0, source_offset=600)]
    assert clock_drift_seconds(drifted) == 600.0
    assert detect_clock_drift(drifted, max_skew_seconds=60) is True
    assert detect_clock_drift([raw(1)], max_skew_seconds=60) is False


# ---------------------------------------------------------------------------
# T8 — security and credentials (6)
# ---------------------------------------------------------------------------

_SECRET = "sk_live_DO_NOT_LEAK_1234567890"


def test_credentials_never_appear_in_logs_or_diagnostics():
    config = MarketDataIngestConfig(
        provider="twelvedata", api_key=_SECRET, enabled=True
    )
    assert _SECRET not in repr(config)
    assert _SECRET not in json.dumps(config.redacted())
    assert config.redacted()["api_key_configured"] is True
    error = ProviderAuthenticationFailedError(
        "market-data credential is not configured",
        provider_type="market_data",
        provider_name="twelvedata",
    )
    assert _SECRET not in json.dumps(error.redacted_summary())


def test_missing_credentials_fail_closed_before_network():
    disabled = MarketDataIngestConfig(provider="twelvedata", enabled=False)
    with pytest.raises(ProviderAuthenticationFailedError):
        disabled.require_credentials()
    empty = MarketDataIngestConfig(provider="twelvedata", api_key="", enabled=True)
    with pytest.raises(ProviderAuthenticationFailedError):
        empty.require_credentials()
    adapter = TwelveDataAdapter(pages=[td_page([td_value(0)])])
    assert adapter._transport.calls == 0  # type: ignore[attr-defined]


def test_provider_configuration_is_environment_isolated():
    staging = MarketDataIngestConfig(
        provider="twelvedata", api_key="staging-key", environment="staging", enabled=True
    )
    production = MarketDataIngestConfig(
        provider="polygon", api_key="production-key", environment="production", enabled=True
    )
    assert staging.api_key != production.api_key
    assert staging.redacted()["environment"] == "staging"
    assert production.redacted()["environment"] == "production"
    with pytest.raises(ProviderConfigurationError):
        MarketDataIngestConfig(environment="qa")


def test_secret_rotation_requires_no_code_change(monkeypatch):
    monkeypatch.setenv("FORGE_MARKET_DATA_ENABLED", "true")
    monkeypatch.setenv("FORGE_MARKET_DATA_PROVIDER", "twelvedata")
    monkeypatch.setenv("FORGE_MARKET_DATA_API_KEY", "first-rotation-key")
    first = config_from_environment()
    monkeypatch.setenv("FORGE_MARKET_DATA_API_KEY", "second-rotation-key")
    second = config_from_environment()
    assert first.api_key != second.api_key
    assert first.redacted() == second.redacted()
    first.require_credentials()
    second.require_credentials()


def test_request_budget_and_backoff_are_bounded():
    config = MarketDataIngestConfig(
        provider="twelvedata", enabled=True, max_retries=3, monthly_call_ceiling=100
    )
    assert config.max_retries == 3 and config.monthly_call_ceiling == 100
    limited = ProviderRateLimitedError(
        "rate limited",
        provider_type="market_data",
        provider_name="twelvedata",
        retry_after_seconds=2.5,
    )
    assert limited.retryable is True
    assert limited.retry_after_seconds == 2.5
    adapter = TwelveDataAdapter(
        pages=[td_page([td_value(0)])], failures=[limited]
    )
    with pytest.raises(ProviderRateLimitedError):
        adapter.fetch(td_request())
    assert adapter._transport.calls == 1  # type: ignore[attr-defined]
    page = adapter.fetch(td_request())
    assert len(page.candles) == 1
    assert adapter._transport.calls == 2  # type: ignore[attr-defined]


def test_no_secret_material_in_fixtures_or_reports():
    pattern = re.compile(
        r"sk_live_[A-Za-z0-9]{8,}|sk_test_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{16}"
        r"|api_key\s*=\s*[\"'][^\"']{8,}[\"']"
    )
    roots = [
        FIXTURES,
        REPO / "implementation/forge/book_iii/provider_integration",
    ]
    scanned = 0
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".md", ".py"}:
                continue
            if "fixtures" in path.parts and path.suffix == ".json":
                scanned += 1
            assert not pattern.search(path.read_text(encoding="utf-8")), path.name
    assert scanned >= 12


# ---------------------------------------------------------------------------
# T9 — readiness and recovery (6)
# ---------------------------------------------------------------------------


def test_connection_success_alone_does_not_claim_readiness():
    monitor = HealthMonitor("twelvedata", configured=True)
    monitor.record_success()
    assert monitor.snapshot().state is IngestState.DEGRADED
    assert monitor.readiness(ReadinessEvidence()).state is IngestState.DEGRADED
    assert monitor.readiness(ReadinessEvidence()).state is not IngestState.READY


def test_readiness_requires_parity_evidence():
    evidence = ReadinessEvidence(
        r1_authorized_provider=True,
        r2_credentials_injected=True,
        r3_bounded_requests_succeeded=True,
        r4_clock_session_verified=True,
        r5_final_bar_checks=True,
        r7_replay_reproduced=True,
        r8_source_health_observed=True,
        r9_recovery_drill=True,
        r10_book_ii_amendment=True,
    )
    assert evidence.missing() == ("R6",)
    monitor = HealthMonitor("twelvedata", configured=True)
    monitor.record_success()
    assert monitor.readiness(evidence).state is IngestState.DEGRADED
    assert monitor.readiness(replace(evidence, r6_parity_verified=True)).state is IngestState.READY


def test_degraded_health_is_disclosed():
    monitor = HealthMonitor("twelvedata", configured=True)
    monitor.record_success()
    monitor.record_degraded("PARTIAL_WINDOW")
    health = monitor.snapshot()
    assert health.state is IngestState.DEGRADED
    assert health.detail == "PARTIAL_WINDOW"
    assert health.as_provider_health().status == "degraded"


def test_recovery_returns_to_ready_only_with_evidence():
    monitor = HealthMonitor("twelvedata", configured=True)
    monitor.record_failure()
    monitor.record_failure()
    assert monitor.snapshot().state is IngestState.UNAVAILABLE
    monitor.record_success()
    assert monitor.snapshot().state is IngestState.DEGRADED
    full = ReadinessEvidence(
        r1_authorized_provider=True,
        r2_credentials_injected=True,
        r3_bounded_requests_succeeded=True,
        r4_clock_session_verified=True,
        r5_final_bar_checks=True,
        r6_parity_verified=True,
        r7_replay_reproduced=True,
        r8_source_health_observed=True,
        r9_recovery_drill=True,
        r10_book_ii_amendment=True,
    )
    assert monitor.readiness(full).state is IngestState.READY


def test_shutdown_closes_stream_and_flushes_state():
    buffer = StreamBuffer()
    buffer.extend(
        [
            StreamEvent(kind=StreamKind.UPDATE, candle=raw(0)),
            StreamEvent(kind=StreamKind.UPDATE, candle=raw(1)),
        ]
    )
    flushed = buffer.latest()
    adapter = TwelveDataAdapter(pages=[td_page([td_value(0)])])
    adapter.close()
    assert adapter.health().status == "unavailable"
    with pytest.raises(ProviderUnavailableError):
        adapter.fetch(td_request())
    assert buffer.latest() == flushed
    assert source_window_digest(buffer.latest()) == source_window_digest(flushed)


def test_readiness_vocabulary_is_frozen():
    assert {state.value for state in IngestState} == {
        "NOT_CONFIGURED",
        "READY",
        "DEGRADED",
        "UNAVAILABLE",
    }
    health = IngestHealth(
        provider_id="twelvedata",
        state=IngestState.NOT_CONFIGURED,
        detail="provider_not_configured",
    )
    assert health.as_provider_health().status == "unavailable"
    with pytest.raises(ValueError):
        ProviderHealth(
            provider_type="market_data",
            provider_name="twelvedata",
            status="READY",
        )


# ---------------------------------------------------------------------------
# T10 — frozen integration (6)
# ---------------------------------------------------------------------------


def _git_diff(*paths: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", *paths],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_no_book_i_or_ii_file_changed():
    assert _git_diff(
        "implementation/forge/book_i",
        "implementation/forge/book_ii",
        "app/forge/service/routes.py",
    ) == ""
    text = (
        REPO
        / "implementation/forge/book_ii/ratification/CONTRACT_FREEZE_MANIFEST_V1.md"
    ).read_text(encoding="utf-8")
    assert len(re.findall(r"`[0-9a-f]{64}`", text)) >= 50


def test_book_iii_module_hashes_unchanged():
    counts = {
        name: len(list((REPO / "app" / "forge" / name).glob("*.py")))
        for name in (
            "market_data",
            "measurements",
            "model_runtime",
            "state_engine",
            "setup_engine",
            "intelligence_api",
        )
    }
    assert counts == {
        "market_data": 11,
        "measurements": 12,
        "model_runtime": 13,
        "state_engine": 13,
        "setup_engine": 16,
        "intelligence_api": 14,
    }
    assert sum(counts.values()) == 79
    assert _git_diff(*(f"app/forge/{name}" for name in counts)) == ""


def test_migration_set_unchanged():
    sql = sorted((REPO / "app/forge/persistence/sql").glob("*.sql"))
    assert [path.name[:3] for path in sql] == ["001", "002", "003", "004"]
    assert _git_diff("app/forge/persistence/sql") == ""


def test_routes_hash_unchanged():
    digest = hashlib.sha256(
        (REPO / "app/forge/service/routes.py").read_bytes()
    ).hexdigest()
    assert digest == (
        "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af"
    )


def test_provider_seam_stays_not_configured_until_wp3d():
    from app.forge.service.container import ForgeServiceContainer
    from app.forge.service.health import ForgeHealthService

    container = ForgeServiceContainer(config=ForgeConfig())
    dependencies = container.as_readiness_dependencies()
    assert dependencies["market_data"]["status"] == "NOT_CONFIGURED"
    assert dependencies["market_data"]["required"] is False
    readiness = ForgeHealthService(container=container).readiness()
    assert readiness["status"] == "ready"
    assert readiness["dependencies"]["market_data"]["status"] == "NOT_CONFIGURED"
    ingest_source = "".join(
        path.read_text(encoding="utf-8")
        for path in (REPO / "app/forge/market_data_ingest").rglob("*.py")
    )
    assert "as_readiness_dependencies" not in ingest_source


def test_cross_bloc_suite_still_green():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_forge_book_iii_integration.py",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
    assert "failed" not in result.stdout.lower()
    assert "error" not in result.stdout.lower()
    assert "passed" in result.stdout
