"""III.1 provider-compatibility amendment — 49 binding tests (A-01–A-49).

Binding inventory: ``implementation/forge/book_iii/provider_integration/
amendment/ACCEPTANCE.md`` §4.  Every name is implemented; none is skipped or
xfailed.  All inputs are offline, deterministic and credential-free: scripted
payloads and scripted adapter pages only.

The amendment extends the frozen field map (derived close, optional clock,
epoch milliseconds, three governed provider schemas) without changing ``Bar``,
quality vocabulary, finality, sessions or the production default registry.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from app.forge.market_data import (
    MARKET_DATA_SCHEMA_VERSION,
    CloseTimeRule,
    Finality,
    NormalizeStatus,
    PROVIDER_SCHEMA_REGISTRY_VERSION,
    PROVIDER_SCHEMAS,
    ProvenanceKind,
    ProviderFieldMap,
    QualityFlag,
    RefusalReason,
    TimestampStyle,
    UnsupportedProviderError,
    build_default_registry,
    normalize_feed,
    normalize_record,
    provider_schema,
)
from app.forge.market_data.normalize import _parse_timestamp
from app.forge.market_data.quality import QualityPolicy
from app.forge.market_data_ingest import build_ingest_registry
from app.forge.market_data_ingest.canonical import canonicalize
from app.forge.market_data_ingest.capture import capture_slice
from app.forge.market_data_ingest.contract import (
    ADAPTER_SCHEMA_VERSION,
    CandlePage,
    CandleRequest,
    RawCandle,
)
from app.forge.market_data_ingest.providers import (
    KrakenAdapter,
    PolygonAdapter,
    TwelveDataAdapter,
)
from app.forge.providers.errors import (
    ProviderMalformedResponseError,
    ProviderUpstreamRejectedError,
)

REPO = Path(__file__).resolve().parents[1]
INGEST = build_ingest_registry()
DEFAULT = build_default_registry()
UTC = timezone.utc
OPEN = datetime(2026, 3, 3, 0, 0, tzinfo=UTC)
CUTOFF = datetime(2026, 3, 3, 8, 3, tzinfo=UTC)
NEW_NORMALIZE = (
    "9b7ea855a3a90994ae325c44af40898e842a6fbef838a6dc5490b5a505919c24"
)
NEW_EXPORTS = (
    "94c88cd73abd03053ac2ba0b90ee95f7d204929e4206ffce04606fb111015f0f"
)

OLD_NORMALIZE = (
    "04c4ecfc97e111e281d90158df5ee7b6cff1aeb25e4df6eaf81f93a66e9d026b"
)
OLD_EXPORTS = (
    "7d57349bba68c6a090ab2f7739e9bd095e436ba01bf110da1ed1c1aa22611fd0"
)
FROZEN_INSTRUMENTS = (
    "8c6d6ad05db973122265bca76ea6b3c0c3e248974fa26cb6409ef4cce67ed94d"
)
FROZEN_BARS = "97fc99e44c7abab0545a33e2b0fbf0b3d354ae5bae2b4c6e446ff3b336666366"
FROZEN_QUALITY = (
    "6b77c6dfa11e6b22013b7f128e0d6b8095b5e035b660c93c309df220bcb58687"
)
FROZEN_ROUTES = (
    "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af"
)

POLICY = QualityPolicy.from_strings(
    "amendment",
    "2",
    blocking=["GAP", "UNSUPPORTED_CLOCK", "NONFINAL", "OUTLIER_SOURCE"],
    warning=["DUPLICATE", "REVISED", "STALE"],
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record(payload, provider, registry=INGEST, cutoff=CUTOFF):
    return normalize_record(
        payload,
        provider,
        registry,
        observation_cutoff=cutoff,
        provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
    )


def _alpha(**over):
    payload = {
        "pair": "EUR/USD",
        "tf": "M5",
        "epoch_open": int(OPEN.timestamp()),
        "epoch_close": int(OPEN.timestamp()) + 300,
        "feed_ts": int(OPEN.timestamp()) + 3,
        "o": "1.07980",
        "h": "1.08000",
        "l": "1.07975",
        "c": "1.07995",
        "vol": "500",
        "zone": "America/New_York",
    }
    payload.update(over)
    return payload


def _beta(**over):
    payload = {
        "sym": "EUR-USD",
        "int": "M5",
        "t0": "2026-03-03T00:00:00+00:00",
        "t1": "2026-03-03T00:05:00+00:00",
        "px_o": "1.07980",
        "px_h": "1.08000",
        "px_l": "1.07975",
        "px_c": "1.07995",
        "qty": "500",
        "src_t": "2026-03-03T00:05:03+00:00",
        "tz": "America/New_York",
    }
    payload.update(over)
    return payload


def _td(**over):
    payload = {
        "symbol": "EUR/USD",
        "interval": "M5",
        "datetime": "2026-03-03T00:00:00+00:00",
        "open": "1.07980",
        "high": "1.08000",
        "low": "1.07975",
        "close": "1.07995",
        "volume": "500",
    }
    payload.update(over)
    return payload


def _polygon(**over):
    payload = {
        "symbol": "C:EURUSD",
        "timeframe": "M5",
        "t": 1_772_496_000_000,
        "o": "1.07980",
        "h": "1.08000",
        "l": "1.07975",
        "c": "1.07995",
    }
    payload.update(over)
    return payload


def _kraken(**over):
    payload = {
        "symbol": "BTC/USD",
        "timeframe": "M5",
        "t": 1_772_496_000,
        "o": "68400.00",
        "h": "68410.00",
        "l": "68390.00",
        "c": "68405.00",
        "v": "12.50",
    }
    payload.update(over)
    return payload


def _request(instrument="EURUSD", timeframe="M5"):
    return CandleRequest(
        instrument_id=instrument,
        timeframe=timeframe,
        start=OPEN,
        end=OPEN + timedelta(hours=1),
    )


def _candle(**over):
    base = {
        "provider_id": "kraken",
        "source_symbol": "BTC/USD",
        "instrument_id": "BTCUSD",
        "timeframe": "M5",
        "open_time": OPEN,
        "close_time": OPEN + timedelta(minutes=5),
        "open": Decimal("68400.00"),
        "high": Decimal("68410.00"),
        "low": Decimal("68390.00"),
        "close": Decimal("68405.00"),
        "source_timestamp": OPEN,
        "volume": Decimal("12.50"),
        "provenance": ProvenanceKind.SYNTHETIC_FIXTURE,
    }
    base.update(over)
    return RawCandle(**base)


# ---------------------------------------------------------------------------
# T1 — backward compatibility (6)
# ---------------------------------------------------------------------------


def test_fake_alpha_schema_behavior_unchanged():
    schema = provider_schema("fake_alpha")
    assert schema.required_keys == (
        "pair",
        "tf",
        "epoch_open",
        "epoch_close",
        "o",
        "h",
        "l",
        "c",
        "feed_ts",
        "zone",
    )
    record = _record(_alpha(), "fake_alpha", DEFAULT)
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert record.bar.open_time == OPEN
    assert record.bar.close_time == OPEN + timedelta(minutes=5)
    assert record.bar.close == Decimal("1.07995")
    assert record.bar.quality_flags == frozenset({QualityFlag.COMPLETE})


def test_fake_beta_schema_behavior_unchanged():
    schema = provider_schema("fake_beta")
    assert schema.required_keys == (
        "sym",
        "int",
        "t0",
        "t1",
        "px_o",
        "px_h",
        "px_l",
        "px_c",
        "src_t",
        "tz",
    )
    record = _record(_beta(), "fake_beta", DEFAULT)
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert record.bar.open_time == OPEN
    assert record.bar.close_time == OPEN + timedelta(minutes=5)
    assert record.bar.source_timestamp == OPEN + timedelta(minutes=5, seconds=3)


def test_unknown_provider_refused():
    with pytest.raises(UnsupportedProviderError):
        provider_schema("definitely_not_a_provider")
    with pytest.raises(UnsupportedProviderError):
        _record(_td(), "definitely_not_a_provider")


def test_schema_registry_version_exposed():
    assert PROVIDER_SCHEMA_REGISTRY_VERSION == "PROVIDER_SCHEMAS_V2"
    assert MARKET_DATA_SCHEMA_VERSION == "MARKET_DATA_SCHEMA_V1"
    assert CloseTimeRule.SOURCE.value == "SOURCE"
    assert CloseTimeRule.OPEN_PLUS_TIMEFRAME.value == "OPEN_PLUS_TIMEFRAME"
    assert TimestampStyle.EPOCH_MILLISECONDS.value == "EPOCH_MILLISECONDS"


def test_existing_market_data_suite_green():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_forge_market_data.py",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
    assert "passed" in result.stdout
    assert " failed" not in result.stdout.lower()


def test_wp3b_contract_suite_green():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_forge_market_data_provider_integration.py",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
    assert "passed" in result.stdout
    assert " failed" not in result.stdout.lower()


# ---------------------------------------------------------------------------
# T2 — timestamp interpretation (6)
# ---------------------------------------------------------------------------


def test_epoch_seconds_unchanged():
    record = _record(_alpha(), "fake_alpha", DEFAULT)
    assert record.bar is not None
    assert record.bar.open_time == OPEN
    assert record.bar.source_timestamp == OPEN + timedelta(seconds=3)


def test_epoch_milliseconds_accepted():
    record = _record(_polygon(), "polygon")
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert record.bar.open_time == datetime(2026, 3, 3, 0, 0, tzinfo=UTC)
    assert record.bar.source_timestamp == record.bar.open_time


def test_seconds_and_milliseconds_not_confused():
    record = _record(_polygon(t=1_772_496_000), "polygon")
    assert record.status is NormalizeStatus.REFUSED
    assert record.reason is RefusalReason.INCOMPLETE_RECORD
    assert record.bar is None


def test_iso_offset_unchanged():
    record = _record(_beta(), "fake_beta", DEFAULT)
    assert record.bar is not None
    assert record.bar.open_time == OPEN
    assert record.bar.close_time == OPEN + timedelta(minutes=5)


def test_naive_timestamp_refused():
    naive_iso = _record(
        _td(datetime="2026-03-03T00:00:00"), "twelvedata"
    )
    assert naive_iso.status is NormalizeStatus.REFUSED
    assert naive_iso.reason is RefusalReason.INCOMPLETE_RECORD
    naive_beta = _record(
        _beta(t0="2026-03-03T00:00:00", t1="2026-03-03T00:05:00"),
        "fake_beta",
        DEFAULT,
    )
    assert naive_beta.status is NormalizeStatus.REFUSED


def test_unsupported_timestamp_unit_refused():
    fractional = _record(_polygon(t="1772496000000.5"), "polygon")
    assert fractional.status is NormalizeStatus.REFUSED
    assert fractional.reason is RefusalReason.INCOMPLETE_RECORD
    assert _parse_timestamp(0, "NOT_A_UNIT") is None


# ---------------------------------------------------------------------------
# T3 — derived close time (5)
# ---------------------------------------------------------------------------


def test_derived_close_m5():
    record = _record(_td(), "twelvedata")
    assert record.bar is not None
    assert record.bar.close_time == OPEN + timedelta(minutes=5)


def test_derived_close_h1():
    record = _record(_td(interval="H1"), "twelvedata")
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert record.bar.close_time == OPEN + timedelta(minutes=60)


def test_source_close_preferred_over_derivation():
    # The SOURCE rule has no derivation path at all; a fake's declared
    # close is used verbatim even when it disagrees with open + timeframe.
    record = _record(_alpha(epoch_close=int(OPEN.timestamp()) + 60), "fake_alpha", DEFAULT)
    assert record.bar is not None
    assert record.bar.close_time == OPEN + timedelta(minutes=1)
    assert provider_schema("fake_alpha").close_time_rule is CloseTimeRule.SOURCE


def test_derived_close_is_not_finality():
    early = _record(_td(), "twelvedata", cutoff=OPEN + timedelta(minutes=3))
    assert early.bar is not None and early.bar.finality is Finality.NONFINAL
    late = _record(_td(), "twelvedata", cutoff=OPEN + timedelta(minutes=5))
    assert late.bar is not None and late.bar.finality is Finality.FINAL


def test_derived_close_across_dst_instant():
    # US DST begins 2026-03-08; UTC arithmetic must not consult local walls.
    record = _record(
        _td(datetime="2026-03-08T06:58:00+00:00"), "twelvedata"
    )
    assert record.bar is not None
    assert record.bar.open_time.utcoffset() == timedelta(0)
    assert record.bar.close_time == datetime(2026, 3, 8, 7, 3, tzinfo=UTC)
    assert record.bar.close_time - record.bar.open_time == timedelta(minutes=5)


# ---------------------------------------------------------------------------
# T4 — provider schema mappings (6)
# ---------------------------------------------------------------------------


def test_twelvedata_schema_accepts_record():
    payload = _td()
    payload.pop("volume")
    record = _record(payload, "twelvedata")
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert record.bar.volume is None
    assert record.bar.provider == "twelvedata"


def test_polygon_schema_accepts_record():
    record = _record(_polygon(), "polygon")
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert provider_schema("polygon").timestamp_style is (
        TimestampStyle.EPOCH_MILLISECONDS
    )


def test_kraken_schema_accepts_record():
    record = _record(_kraken(), "kraken")
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert record.bar.instrument_id == "BTCUSD"
    assert provider_schema("kraken").timestamp_style is TimestampStyle.EPOCH_SECONDS


def test_unregistered_provider_refused():
    with pytest.raises(UnsupportedProviderError):
        _record(_td(), "binance")
    assert "binance" not in PROVIDER_SCHEMAS


def test_schema_table_immutable():
    with pytest.raises(TypeError):
        PROVIDER_SCHEMAS["intruder"] = provider_schema("twelvedata")
    with pytest.raises(FrozenInstanceError):
        PROVIDER_SCHEMAS["kraken"].provider = "other"


def test_higher_timeframe_rollup_still_refused():
    record = _record(_td(interval="H2"), "twelvedata")
    assert record.status is NormalizeStatus.REFUSED
    assert record.reason is RefusalReason.UNSUPPORTED_TIMEFRAME
    feed = normalize_feed(
        [_td(), _td(datetime="2026-03-03T00:05:00+00:00")],
        "twelvedata",
        INGEST,
        observation_cutoff=CUTOFF,
        provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
    )
    assert [bar.timeframe for bar in feed.bars] == ["M5", "M5"]
    assert len(feed.bars) == 2


# ---------------------------------------------------------------------------
# T5 — envelope and row adaptation (5)
# ---------------------------------------------------------------------------


def test_twelvedata_envelope_flattened():
    adapter = TwelveDataAdapter(
        pages=[
            {
                "values": [
                    {
                        "symbol": "EUR/USD",
                        "interval": "5min",
                        "datetime": "2026-03-03T00:00:00+00:00",
                        "open": "1.07980",
                        "high": "1.08000",
                        "low": "1.07975",
                        "close": "1.07995",
                        "volume": "500",
                    }
                ]
            }
        ]
    )
    page = adapter.fetch(_request())
    assert isinstance(page, CandlePage)
    assert len(page.candles) == 1
    candle = page.candles[0]
    assert candle.open_time == OPEN
    assert "values" not in json.dumps(candle.canonical_fields())


def test_polygon_envelope_flattened():
    row = {
        "sym": "C:EURUSD",
        "t": 1_772_496_000_000,
        "o": "1.07980",
        "h": "1.08000",
        "l": "1.07975",
        "c": "1.07995",
    }
    adapter = PolygonAdapter(pages=[{"status": "OK", "results": [row]}])
    page = adapter.fetch(_request())
    assert len(page.candles) == 1
    assert page.candles[0].close_time == OPEN + timedelta(minutes=5)
    rejected = PolygonAdapter(pages=[{"status": "ERROR", "results": []}])
    with pytest.raises(ProviderUpstreamRejectedError):
        rejected.fetch(_request())


def test_kraken_array_rows_mapped():
    row = [
        1_772_496_000,
        "68400.00",
        "68410.00",
        "68390.00",
        "68405.00",
        "68400.50",
        "12.50",
        42,
    ]
    adapter = KrakenAdapter(
        pages=[
            {"error": [], "result": {"XXBTZUSD": [row]}, "partial": False}
        ]
    )
    page = adapter.fetch(_request("BTCUSD"))
    assert len(page.candles) == 1
    candle = page.candles[0]
    assert candle.instrument_id == "BTCUSD"
    assert candle.open == Decimal("68400.00")
    assert candle.high == Decimal("68410.00")
    assert candle.low == Decimal("68390.00")
    assert candle.close == Decimal("68405.00")
    assert candle.volume == Decimal("12.50")
    assert candle.open_time == OPEN


def test_envelope_provenance_retained():
    adapter = TwelveDataAdapter(
        pages=[
            {
                "values": [
                    {
                        "symbol": "EUR/USD",
                        "interval": "5min",
                        "datetime": "2026-03-03T00:00:00+00:00",
                        "open": "1.07980",
                        "high": "1.08000",
                        "low": "1.07975",
                        "close": "1.07995",
                    }
                ]
            }
        ]
    )
    candle = adapter.fetch(_request()).candles[0]
    assert candle.adapter_version == ADAPTER_SCHEMA_VERSION
    licensed = replace(
        candle,
        provenance=ProvenanceKind.SOURCE_SLICE,
        source_ref="wp3a://source-slice/1",
    )
    labelled, metadata = capture_slice(
        (licensed,),
        instrument_id="EURUSD",
        timeframe="M5",
        licence_ref="licence://offline-test",
        captured_at=CUTOFF,
        source_ref="wp3a://source-slice/1",
    )
    assert metadata.source_ref == "wp3a://source-slice/1"
    assert labelled[0].adapter_version == ADAPTER_SCHEMA_VERSION


def test_malformed_envelope_refused():
    with pytest.raises(ProviderMalformedResponseError):
        TwelveDataAdapter(pages=[{"values": "not-a-list"}]).fetch(_request())
    with pytest.raises(ProviderMalformedResponseError):
        PolygonAdapter(pages=[{"status": "OK", "results": {}}]).fetch(_request())
    with pytest.raises(ProviderMalformedResponseError):
        KrakenAdapter(pages=[{"error": [], "result": []}]).fetch(
            _request("BTCUSD")
        )


# ---------------------------------------------------------------------------
# T6 — source lineage (5)
# ---------------------------------------------------------------------------


def test_provider_identity_per_bar():
    for provider, payload in (
        ("twelvedata", _td()),
        ("polygon", _polygon()),
        ("kraken", _kraken()),
    ):
        record = _record(payload, provider)
        assert record.bar is not None
        assert record.bar.provider == provider


def test_revision_ordering_preserved():
    early = _beta(
        px_c="1.07995",
        src_t="2026-03-03T00:05:03+00:00",
    )
    later = _beta(
        px_o="1.07990",
        px_c="1.08010",
        px_h="1.08020",
        px_l="1.07970",
        src_t="2026-03-03T00:05:10+00:00",
    )
    feed = normalize_feed(
        [later, early],
        "fake_beta",
        DEFAULT,
        observation_cutoff=CUTOFF,
        provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
    )
    assert len(feed.bars) == 1
    survivor = feed.bars[0]
    assert survivor.close == Decimal("1.08010")
    assert QualityFlag.REVISED in survivor.quality_flags


def test_source_timestamp_preserved():
    td = _record(_td(), "twelvedata")
    assert td.bar is not None
    assert td.bar.source_timestamp == OPEN
    polygon = _record(_polygon(), "polygon")
    assert polygon.bar is not None
    assert polygon.bar.source_timestamp == OPEN
    kraken = _record(_kraken(), "kraken")
    assert kraken.bar is not None
    assert kraken.bar.source_timestamp == OPEN


def test_source_symbol_retained_at_adapter():
    adapter = TwelveDataAdapter(
        pages=[
            {
                "values": [
                    {
                        "symbol": "EUR/USD",
                        "interval": "5min",
                        "datetime": "2026-03-03T00:00:00+00:00",
                        "open": "1.07980",
                        "high": "1.08000",
                        "low": "1.07975",
                        "close": "1.07995",
                    }
                ]
            }
        ]
    )
    candle = adapter.fetch(_request()).candles[0]
    assert candle.source_symbol == "EUR/USD"
    record = _record(_td(), "twelvedata")
    assert record.bar is not None
    assert "symbol" not in record.bar.to_dict()
    assert "EUR/USD" not in record.bar.dumps()


def test_adapter_version_retained():
    candle = _candle()
    assert candle.adapter_version == ADAPTER_SCHEMA_VERSION
    assert ADAPTER_SCHEMA_VERSION == "MARKET_DATA_INGEST_V1"
    licensed = replace(
        candle,
        provenance=ProvenanceKind.SOURCE_SLICE,
        source_ref="wp3a://source-slice/2",
    )
    labelled, metadata = capture_slice(
        (licensed,),
        instrument_id="BTCUSD",
        timeframe="M5",
        licence_ref="licence://offline-test",
        captured_at=CUTOFF,
        source_ref="wp3a://source-slice/2",
    )
    assert metadata.digest == __import__(
        "app.forge.market_data_ingest.capture", fromlist=["source_window_digest"]
    ).source_window_digest(labelled)


# ---------------------------------------------------------------------------
# T7 — finality (4)
# ---------------------------------------------------------------------------


def test_trailing_candle_nonfinal():
    rows = [
        [1_772_495_700, "68400.00", "68410.00", "68390.00", "68405.00", "1", "1", 1],
        [1_772_496_000, "68405.00", "68415.00", "68395.00", "68410.00", "1", "1", 1],
    ]
    adapter = KrakenAdapter(
        pages=[{"error": [], "result": {"XXBTZUSD": rows}, "partial": True}]
    )
    candles = adapter.fetch(_request("BTCUSD")).candles
    assert candles[0].finality_hint == "FINAL"
    assert candles[-1].finality_hint == "NONFINAL"
    outcome = canonicalize(
        candles, INGEST, POLICY, observation_cutoff=OPEN + timedelta(minutes=2)
    )
    assert outcome.bars[0].finality is Finality.FINAL
    assert outcome.bars[-1].finality is Finality.NONFINAL


def test_vendor_final_hint_cannot_override_cutoff():
    candle = replace(_candle(), finality_hint="FINAL")
    outcome = canonicalize(
        (candle,), INGEST, POLICY, observation_cutoff=OPEN + timedelta(minutes=3)
    )
    assert outcome.bars[0].finality is Finality.NONFINAL
    assert QualityFlag.NONFINAL in outcome.bars[0].quality_flags


def test_candle_after_cutoff_final():
    candle = replace(_candle(), finality_hint="NONFINAL")
    outcome = canonicalize(
        (candle,), INGEST, POLICY, observation_cutoff=OPEN + timedelta(minutes=6)
    )
    assert outcome.bars[0].finality is Finality.FINAL
    assert QualityFlag.NONFINAL not in outcome.bars[0].quality_flags


def test_provider_cannot_set_finality():
    assert "finality" not in {field.name for field in fields(RawCandle)}
    assert "finality_hint" in {field.name for field in fields(RawCandle)}
    assert "finality" not in {field.name for field in fields(ProviderFieldMap)}
    cutoff = OPEN + timedelta(minutes=3)
    final_hint = canonicalize(
        (replace(_candle(), finality_hint="FINAL"),),
        INGEST,
        POLICY,
        observation_cutoff=cutoff,
    )
    nonfinal_hint = canonicalize(
        (replace(_candle(), finality_hint="NONFINAL"),),
        INGEST,
        POLICY,
        observation_cutoff=cutoff,
    )
    assert final_hint.bars[0].finality is nonfinal_hint.bars[0].finality


# ---------------------------------------------------------------------------
# T8 — JPY instruments (4)
# ---------------------------------------------------------------------------


def test_jpy_instruments_injected():
    for instrument_id in ("USDJPY", "AUDJPY", "EURJPY"):
        instrument = INGEST.get(instrument_id)
        assert instrument.quote_currency == "JPY"
        assert instrument.provider_mappings["twelvedata"]
        assert instrument.provider_mappings["polygon"]


def test_jpy_aliases_resolve():
    assert INGEST.resolve_provider("twelvedata", "USD/JPY").instrument_id == "USDJPY"
    assert INGEST.resolve_provider("polygon", "C:AUDJPY").instrument_id == "AUDJPY"
    assert INGEST.resolve_provider("twelvedata", "EUR/JPY").instrument_id == "EURJPY"


def test_jpy_conventions_provisional():
    source = (
        REPO / "app/forge/market_data_ingest/registry.py"
    ).read_text(encoding="utf-8")
    assert "operator confirmation" in source
    for instrument_id in ("USDJPY", "AUDJPY", "EURJPY"):
        instrument = INGEST.get(instrument_id)
        assert instrument.price_precision == 3
        assert instrument.pip_size == Decimal("0.01")
        assert instrument.tick_size == Decimal("0.001")


def test_default_registry_unchanged():
    assert build_default_registry().instrument_ids == ("BTCUSD", "EURUSD", "XAUUSD")
    assert DEFAULT.instrument_ids == ("BTCUSD", "EURUSD", "XAUUSD")
    assert "USDJPY" not in DEFAULT.instrument_ids


# ---------------------------------------------------------------------------
# T9 — refusal behavior (4)
# ---------------------------------------------------------------------------


def test_missing_clock_fails_closed():
    record = _record(_td(), "twelvedata")
    assert record.status is NormalizeStatus.OK
    assert record.bar is not None
    assert QualityFlag.UNSUPPORTED_CLOCK not in record.bar.quality_flags
    assert "clock" not in record.bar.to_dict()
    refused = _record(_alpha(zone="Europe/London"), "fake_alpha", DEFAULT)
    assert refused.status is NormalizeStatus.REFUSED
    assert refused.reason is RefusalReason.UNSUPPORTED_CLOCK
    assert QualityFlag.UNSUPPORTED_CLOCK in refused.flags


def test_unsupported_timeframe_refused():
    record = _record(_td(interval="M2"), "twelvedata")
    assert record.status is NormalizeStatus.REFUSED
    assert record.reason is RefusalReason.UNSUPPORTED_TIMEFRAME
    assert record.bar is None


def test_malformed_timestamp_refused():
    bad_iso = _record(_td(datetime="not-a-date"), "twelvedata")
    assert bad_iso.status is NormalizeStatus.REFUSED
    assert bad_iso.reason is RefusalReason.INCOMPLETE_RECORD
    bad_ms = _record(_polygon(t="abc"), "polygon")
    assert bad_ms.status is NormalizeStatus.REFUSED
    assert bad_ms.reason is RefusalReason.INCOMPLETE_RECORD


def test_absent_source_field_refused():
    payload = _td()
    payload.pop("datetime")
    assert _record(payload, "twelvedata").reason is RefusalReason.INCOMPLETE_RECORD
    payload = _td()
    payload.pop("close")
    assert _record(payload, "twelvedata").reason is RefusalReason.INCOMPLETE_RECORD


# ---------------------------------------------------------------------------
# T10 — frozen integrity (4)
# ---------------------------------------------------------------------------


def _git_diff_head(*paths: str) -> str:
    """Worktree-vs-HEAD diff; valid in shallow CI checkouts too."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", *paths],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_book_i_and_ii_untouched():
    assert _git_diff_head(
        "implementation/forge/book_i",
        "implementation/forge/book_ii",
        "app/forge/service/routes.py",
    ) == ""
    manifest = (
        REPO
        / "implementation/forge/book_ii/ratification/CONTRACT_FREEZE_MANIFEST_V1.md"
    ).read_text(encoding="utf-8")
    assert len(re.findall(r"`[0-9a-f]{64}`", manifest)) >= 50


def test_only_authorized_frozen_files_changed():
    # A shallow checkout cannot diff the pre-amendment commit; integrity is
    # proven instead by pinning all 11 market_data files and requiring a clean
    # worktree. The two authorized files carry the new hashes, the other nine
    # still match the recorded III.1 baseline.
    assert _git_diff_head("app/forge") == ""
    baseline = json.loads(
        (
            REPO
            / "implementation/forge/book_iii/bloc_iii_5/fixtures/FROZEN_BASELINE.json"
        ).read_text(encoding="utf-8")
    )
    pinned = {
        path: digest
        for path, digest in baseline["files"].items()
        if path.startswith("app/forge/market_data/")
    }
    assert len(pinned) == 11
    assert pinned["app/forge/market_data/normalize.py"] == NEW_NORMALIZE
    assert pinned["app/forge/market_data/__init__.py"] == NEW_EXPORTS
    for relative, expected in pinned.items():
        assert _sha(REPO / relative) == expected, relative
    assert _sha(REPO / "app/forge/market_data/normalize.py") == NEW_NORMALIZE
    assert _sha(REPO / "app/forge/market_data/__init__.py") == NEW_EXPORTS
    assert _sha(REPO / "app/forge/market_data/instruments.py") == FROZEN_INSTRUMENTS
    assert _sha(REPO / "app/forge/market_data/bars.py") == FROZEN_BARS
    assert _sha(REPO / "app/forge/market_data/quality.py") == FROZEN_QUALITY
    assert _sha(REPO / "app/forge/service/routes.py") == FROZEN_ROUTES


def test_hash_record_updated():
    record = (
        REPO
        / "implementation/forge/book_iii/provider_integration/amendment/FREEZE_DELTA_V2.md"
    ).read_text(encoding="utf-8")
    normalize_hash = _sha(REPO / "app/forge/market_data/normalize.py")
    exports_hash = _sha(REPO / "app/forge/market_data/__init__.py")
    assert normalize_hash != OLD_NORMALIZE
    assert exports_hash != OLD_EXPORTS
    for digest in (OLD_NORMALIZE, OLD_EXPORTS, normalize_hash, exports_hash):
        assert digest in record
    assert "PROVIDER_SCHEMAS_V2" in record


def test_re_ratification_and_licence_gate_recorded():
    base = REPO / "implementation/forge/book_iii/provider_integration/amendment"
    ratification = (base / "RATIFICATION.md").read_text(encoding="utf-8")
    evidence = (base / "EVIDENCE.md").read_text(encoding="utf-8")
    for text in (ratification, evidence):
        assert "WP-3C" in text
        assert "NOT EXECUTED" in text
        assert "licence" in text.lower()
    assert "PASS" in ratification
