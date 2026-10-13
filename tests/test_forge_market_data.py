"""Focused Bloc III.1 suite: Market Data & Clock Contracts.

Binding specification: ``implementation/forge/book_iii/bloc_iii_1/
ACCEPTANCE.md`` — every frozen clause T1–T11 (A–O) maps to a test in
this file (the mapping may gain tests, never lose or weaken one).

All tests are deterministic and offline.  Inputs come only from the
committed fixtures under ``implementation/forge/book_iii/bloc_iii_1/
fixtures/`` (synthetic bar slices labeled ``SYNTHETIC_FIXTURE``; session
definitions quoted as ``CANONICAL_SOURCE_SLICE``).  No network, no
credentials, no provider SDK, no wall clock.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import pkgutil
import re
import socket
import subprocess
from dataclasses import FrozenInstanceError, dataclass, fields, replace
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from app.forge.backfill.canonicalizer import canonicalize_files
from app.forge.backfill.runner import load_corpus_files
from app.forge.config import ForgeConfig
from app.forge.market_data import (
    CLOCK_REGISTRY_VERSION,
    FROZEN_QUALITY_FLAGS,
    MARKET_DATA_SCHEMA_VERSION,
    SESSION_REGISTRY_VERSION,
    AssetClass,
    Bar,
    ClockIdentity,
    ClockKind,
    DataOutcome,
    DstPolicy,
    Finality,
    FinalStateSelection,
    Instrument,
    NativePrice,
    NativeUnit,
    NormalizeStatus,
    NonFinalError,
    OwnershipResult,
    OwnershipStatus,
    PipelineContext,
    PipelineResult,
    ProvenanceKind,
    QualityFlag,
    QualityPolicy,
    QualityVocabularyError,
    RefusalReason,
    ResearchDayAssignment,
    ResearchDayLineage,
    ResearchDayRegistry,
    ResearchDayStatus,
    SessionDefinition,
    SessionFamily,
    SessionKind,
    SessionRegistry,
    SessionStatus,
    add_native,
    assign_research_day,
    bar_ownership,
    build_default_registry,
    close_matches_checkpoint,
    compare_parity,
    content_digest,
    convert_native,
    definitions_from_records,
    final_bar_open_utc,
    final_state_input,
    fixed_clock,
    local_open_in_session,
    local_wall,
    missing_opens,
    named_clock,
    normalize_feed,
    normalize_record,
    provider_schema,
    reconcile,
    replay_historical,
    session_bounds_utc,
    stream_live,
    to_utc,
    validate_quote_base,
)
from app.forge.persistence.sql.migrations import discover_migrations
from app.forge.retrieval import QuarantineCatalog
from app.forge.service.container import ForgeServiceContainer

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = (
    REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_1" / "fixtures"
)
PACKAGE_DIR = REPO_ROOT / "app" / "forge" / "market_data"
BOOK_II_FREEZE_MANIFEST = (
    REPO_ROOT / "implementation" / "forge" / "book_ii" / "ratification"
    / "CONTRACT_FREEZE_MANIFEST_V1.md"
)
PLANNING_FREEZE_MANIFEST = (
    REPO_ROOT / "planning" / "forge" / "PLANNING_FREEZE_MANIFEST_V1.md"
)
BOOK_I_FREEZE_MANIFEST = (
    REPO_ROOT / "implementation" / "forge" / "book_i" / "bloc_i_5"
    / "BOOK_I_FREEZE_MANIFEST_V1.md"
)

EUR_CUTOFF = "2026-03-03T08:03:00Z"
BTC_CUTOFF = "2026-03-03T17:00:30Z"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _utc(iso_stamp: str) -> datetime:
    return datetime.fromisoformat(iso_stamp.replace("Z", "+00:00"))


def _z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _expected_opens(start_iso: str, end_iso: str, minutes: int) -> tuple[datetime, ...]:
    step = timedelta(minutes=minutes)
    current = _utc(start_iso)
    end = _utc(end_iso)
    out: list[datetime] = []
    while current < end:
        out.append(current)
        current = current + step
    return tuple(out)


def _package_sources() -> list[tuple[str, str]]:
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in sorted(PACKAGE_DIR.glob("*.py"))
    ]


# ---------------------------------------------------------------------------
# Module-scope fixtures (deterministic, offline)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def registry():
    return build_default_registry()


@pytest.fixture(scope="module")
def ny_clock():
    return named_clock("America/New_York")


@pytest.fixture(scope="module")
def sessions_fx() -> dict:
    return _load_fixture("sessions_canonical.json")


@pytest.fixture(scope="module")
def eur_slice() -> dict:
    return _load_fixture("eurusd_m5_slice.json")


@pytest.fixture(scope="module")
def btc_slice() -> dict:
    return _load_fixture("btcusd_m5_slice.json")


@pytest.fixture(scope="module")
def alpha_feed() -> dict:
    return _load_fixture("raw_feed_fake_alpha.json")


@pytest.fixture(scope="module")
def beta_feed() -> dict:
    return _load_fixture("raw_feed_fake_beta.json")


@pytest.fixture(scope="module")
def btc_feed() -> dict:
    return _load_fixture("raw_feed_btcusd_fake_alpha.json")


@pytest.fixture(scope="module")
def session_registry(sessions_fx, ny_clock) -> SessionRegistry:
    clocks = {"America/New_York": ny_clock}
    definitions = definitions_from_records(sessions_fx["definitions"], clocks)
    registry_ = SessionRegistry()
    registry_.add_all(definitions)
    return registry_


@pytest.fixture(scope="module")
def documented_gaps(sessions_fx) -> dict:
    return {
        SessionFamily(key): value
        for key, value in sessions_fx["documented_gaps"].items()
    }


@pytest.fixture(scope="module")
def lineage_registry(sessions_fx, ny_clock) -> ResearchDayRegistry:
    registry_ = ResearchDayRegistry()
    for record in sessions_fx["research_day_lineages"]:
        boundary = record.get("evening_shift_boundary")
        registry_.register(
            ResearchDayLineage(
                lineage_id=record["lineage_id"],
                model_id=record["model_id"],
                model_version=record["model_version"],
                clock=ny_clock,
                evening_shift_boundary=(
                    time.fromisoformat(boundary) if boundary else None
                ),
                source_ref=record["source_ref"],
            )
        )
    return registry_


@pytest.fixture(scope="module")
def bindings(sessions_fx):
    from app.forge.market_data import ModelBinding

    return tuple(ModelBinding(**record) for record in sessions_fx["model_bindings"])


@pytest.fixture(scope="module")
def model_policy() -> QualityPolicy:
    # Declared block-vs-warn split for the EUR/BTC test models (G2).
    return QualityPolicy.from_strings(
        "EUR.DAILY.NEWS_REKEY.V1",
        "PHASE1",
        blocking=["GAP", "STALE", "OUTLIER_SOURCE", "UNSUPPORTED_CLOCK"],
        warning=["DUPLICATE", "REVISED", "NONFINAL"],
    )


@pytest.fixture(scope="module")
def eur_ctx(registry, session_registry, lineage_registry, bindings, model_policy):
    return PipelineContext(
        registry=registry,
        sessions=session_registry,
        lineages=lineage_registry,
        bindings=bindings,
        policy=model_policy,
        observation_cutoff=_utc(EUR_CUTOFF),
        provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        expected_opens=_expected_opens(
            "2026-03-03T00:00:00Z", "2026-03-03T08:00:00Z", 5
        ),
    )


@pytest.fixture(scope="module")
def btc_ctx(registry, session_registry, lineage_registry, bindings, model_policy, btc_slice):
    opens = tuple(_utc(row["open_time"]) for row in btc_slice["rows"])
    return PipelineContext(
        registry=registry,
        sessions=session_registry,
        lineages=lineage_registry,
        bindings=bindings,
        policy=model_policy,
        observation_cutoff=_utc(BTC_CUTOFF),
        provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        expected_opens=opens,
    )


def _normalize_eur(alpha_feed, registry, eur_ctx, records=None):
    return normalize_feed(
        records if records is not None else alpha_feed["records"],
        "fake_alpha",
        registry,
        observation_cutoff=eur_ctx.observation_cutoff,
        provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        expected_opens=eur_ctx.expected_opens,
    )


# ---------------------------------------------------------------------------
# T1 — Instrument identity and native units (A1–A5, M2)
# ---------------------------------------------------------------------------


class TestT1InstrumentIdentity:
    def test_instrument_schema_has_all_frozen_fields(self, registry):
        frozen_fields = {
            "instrument_id",
            "symbol",
            "asset_class",
            "base_currency",
            "quote_currency",
            "native_unit",
            "price_precision",
            "supported_timeframes",
            "supported_clocks",
            "provider_mappings",
            "pip_size",
            "point_size",
            "tick_size",
        }
        for instrument_id in registry.instrument_ids:
            instrument = registry.get(instrument_id)
            names = {item.name for item in fields(instrument)}
            assert frozen_fields <= names, (instrument_id, frozen_fields - names)
            assert set(instrument.provider_mappings) == {"fake_alpha", "fake_beta"}
            assert instrument.supported_timeframes
            assert instrument.supported_clocks

    def test_native_unit_enum_per_instrument(self, registry):
        assert {unit.value for unit in NativeUnit} == {"PIP", "POINT", "DOLLAR"}
        assert registry.get("EURUSD").native_unit is NativeUnit.PIP
        assert registry.get("XAUUSD").native_unit is NativeUnit.POINT
        assert registry.get("BTCUSD").native_unit is NativeUnit.DOLLAR
        # Per-instance sizes: no sharing, no global.
        assert registry.get("EURUSD").native_step == Decimal("0.0001")
        assert registry.get("XAUUSD").native_step == Decimal("1.00")
        assert registry.get("BTCUSD").native_step == Decimal("1")

    def test_cross_native_unit_arithmetic_refuses(self, registry):
        eur = NativePrice("EURUSD", NativeUnit.PIP, Decimal("1"))
        xau = NativePrice("XAUUSD", NativeUnit.POINT, Decimal("1"))
        btc = NativePrice("BTCUSD", NativeUnit.DOLLAR, Decimal("1"))
        # EUR pip vs Gold point vs BTC dollar: all refuse.
        with pytest.raises(Exception) as exc1:
            add_native(eur, xau)
        assert type(exc1.value).__name__ == "UnitMismatchError"
        with pytest.raises(Exception) as exc2:
            add_native(eur, btc)
        assert type(exc2.value).__name__ == "UnitMismatchError"
        with pytest.raises(Exception) as exc3:
            add_native(xau, btc)
        assert type(exc3.value).__name__ == "UnitMismatchError"
        # Same instrument, wrong unit tag still refuses.
        mislabeled = NativePrice("EURUSD", NativeUnit.POINT, Decimal("1"))
        with pytest.raises(Exception) as exc4:
            add_native(eur, mislabeled)
        assert type(exc4.value).__name__ == "UnitMismatchError"
        # Conversion across domains is refused (no conversion authority).
        with pytest.raises(Exception) as exc5:
            convert_native(eur, NativeUnit.POINT)
        assert type(exc5.value).__name__ == "UnsupportedConversionError"
        with pytest.raises(Exception) as exc6:
            convert_native(xau, NativeUnit.DOLLAR)
        assert type(exc6.value).__name__ == "UnsupportedConversionError"
        # Same-unit identity is not a conversion.
        assert convert_native(eur, NativeUnit.PIP) is eur

    def test_no_global_unit_constant(self):
        import app.forge.market_data as market_data_pkg

        numeric_hits = []
        for module_info in pkgutil.iter_modules(market_data_pkg.__path__):
            imported = importlib.import_module(f"app.forge.market_data.{module_info.name}")
            for attr, value in vars(imported).items():
                if attr.startswith("__"):
                    continue
                if isinstance(value, bool):
                    continue
                if isinstance(value, (int, float, Decimal)):
                    numeric_hits.append(f"{imported.__name__}.{attr}")
        assert numeric_hits == [], f"module-level numeric constants exist: {numeric_hits}"

    def test_alias_resolves_to_single_canonical_id(self, registry):
        for alias in ("EURUSD", "EUR/USD", "EUR-USD", "eurusd", "eur/usd"):
            assert registry.resolve(alias).instrument_id == "EURUSD"
        assert registry.resolve_provider("fake_alpha", "EUR/USD").instrument_id == "EURUSD"
        assert registry.resolve_provider("fake_beta", "EUR-USD").instrument_id == "EURUSD"
        with pytest.raises(Exception) as exc:
            registry.resolve("NOPE/NOPE")
        assert type(exc.value).__name__ == "UnknownAliasError"
        # Ambiguity fails closed at build time: one alias, two targets.
        first = Instrument(
            instrument_id="T1",
            symbol="T1",
            asset_class=AssetClass.FX,
            base_currency="A",
            quote_currency="B",
            native_unit=NativeUnit.PIP,
            price_precision=5,
            supported_timeframes=frozenset({"M5"}),
            supported_clocks=frozenset({"America/New_York"}),
            pip_size=Decimal("0.0001"),
        )
        second = Instrument(
            instrument_id="T2",
            symbol="T2",
            asset_class=AssetClass.FX,
            base_currency="C",
            quote_currency="D",
            native_unit=NativeUnit.PIP,
            price_precision=5,
            supported_timeframes=frozenset({"M5"}),
            supported_clocks=frozenset({"America/New_York"}),
            pip_size=Decimal("0.0001"),
        )
        with pytest.raises(Exception) as exc:
            __import__("app.forge.market_data.instruments", fromlist=["x"]).InstrumentRegistry(
                [first, second], aliases={"SHARED": "T1", "shared": "T2"}
            )
        assert type(exc.value).__name__ == "AmbiguousAliasError"
        # Provider-level collision (same raw spelling mapped twice) also fails.
        collide_a = Instrument(
            instrument_id="T3",
            symbol="T3",
            asset_class=AssetClass.FX,
            base_currency="A",
            quote_currency="B",
            native_unit=NativeUnit.PIP,
            price_precision=5,
            supported_timeframes=frozenset({"M5"}),
            supported_clocks=frozenset({"America/New_York"}),
            pip_size=Decimal("0.0001"),
            provider_mappings={"fake_alpha": "SAME"},
        )
        collide_b = Instrument(
            instrument_id="T4",
            symbol="T4",
            asset_class=AssetClass.FX,
            base_currency="C",
            quote_currency="D",
            native_unit=NativeUnit.PIP,
            price_precision=5,
            supported_timeframes=frozenset({"M5"}),
            supported_clocks=frozenset({"America/New_York"}),
            pip_size=Decimal("0.0001"),
            provider_mappings={"fake_alpha": "SAME"},
        )
        with pytest.raises(Exception) as exc:
            __import__("app.forge.market_data.instruments", fromlist=["x"]).InstrumentRegistry(
                [collide_a, collide_b]
            )
        assert type(exc.value).__name__ == "AmbiguousAliasError"

    def test_price_precision_and_quote_base_enforced(self, registry):
        eurusd = registry.get("EURUSD")
        xauusd = registry.get("XAUUSD")
        assert eurusd.validate_price(Decimal("1.08123")) == Decimal("1.08123")
        with pytest.raises(Exception) as exc:
            eurusd.validate_price(Decimal("1.081234"))
        assert type(exc.value).__name__ == "PrecisionViolationError"
        with pytest.raises(Exception) as exc2:
            xauusd.validate_price(Decimal("4123.456"))
        assert type(exc.value).__name__ == "PrecisionViolationError"
        # No silent rounding: the refusal raises instead of truncating.
        validate_quote_base(eurusd, "EUR", "USD")
        with pytest.raises(Exception) as exc3:
            validate_quote_base(eurusd, "USD", "EUR")
        assert type(exc3.value).__name__ == "ConventionViolationError"

    def test_declared_clocks_only(self, registry):
        eurusd = registry.get("EURUSD")
        assert eurusd.supported_clocks == {"America/New_York", "EST_NO_DST"}
        assert eurusd.supports_timeframe("M5")
        eurusd.require_timeframe("M5")
        with pytest.raises(Exception) as exc:
            eurusd.require_timeframe("M7")
        assert type(exc.value).__name__ == "UnsupportedTimeframeError"
        eurusd.require_clock("America/New_York")
        with pytest.raises(Exception) as exc2:
            eurusd.require_clock("Asia/Tokyo")
        assert type(exc2.value).__name__ == "UnsupportedClockError"


# ---------------------------------------------------------------------------
# T2 — Normalized bar contract (B1–B5, J-e)
# ---------------------------------------------------------------------------


class TestT2BarContract:
    def test_bar_contract_frozen_fields(self, alpha_feed, registry, eur_ctx):
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        assert feed.bars, "fixture must normalize"
        frozen = {
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
        }
        for bar in feed.bars:
            names = {item.name for item in fields(bar)}
            assert frozen <= names, frozen - names
            assert bar.instrument_id == "EURUSD"
            assert bar.timeframe == "M5"
            assert bar.provider == "fake_alpha"
            assert isinstance(bar.volume, Decimal)
            assert isinstance(bar.finality, Finality)
            assert isinstance(bar.quality_flags, frozenset)
            assert bar.open_time.tzinfo is not None

    def test_future_incomplete_bar_never_final(self, alpha_feed, registry, eur_ctx):
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        partial = [bar for bar in feed.bars if _z(bar.open_time).endswith("08:00:00Z")]
        assert len(partial) == 1
        bar = partial[0]
        assert bar.close_time > eur_ctx.observation_cutoff
        assert bar.finality is Finality.NONFINAL
        assert QualityFlag.NONFINAL in bar.quality_flags
        # No cutoff at or before the bar's close can ever make it final.
        for cutoff in (
            eur_ctx.observation_cutoff,
            bar.open_time,
            bar.close_time - timedelta(seconds=1),
        ):
            from app.forge.market_data import assess_finality

            assert assess_finality(bar.close_time, cutoff) is Finality.NONFINAL
        from app.forge.market_data import finalize_for_cutoff

        assert finalize_for_cutoff(bar, eur_ctx.observation_cutoff).finality is Finality.NONFINAL
        # Only an actually-passed cutoff finalizes it.
        advanced = finalize_for_cutoff(bar, bar.close_time)
        assert advanced.finality is Finality.FINAL
        assert QualityFlag.NONFINAL not in advanced.quality_flags

    def test_duplicate_bars_deterministic_single_result(self, alpha_feed, registry, eur_ctx):
        rows = alpha_feed["records"]
        dup_open = int(_utc("2026-03-03T00:20:00Z").timestamp())
        dup_rows = [row for row in rows if row["epoch_open"] == dup_open]
        assert len(dup_rows) == 2
        bars = []
        for order in (dup_rows, list(reversed(dup_rows))):
            feed = _normalize_eur(alpha_feed, registry, eur_ctx, records=order)
            assert len(feed.bars) == 1
            result = feed.bars[0]
            assert QualityFlag.DUPLICATE in result.quality_flags
            bars.append(result.dumps())
        assert bars[0] == bars[1], "duplicate resolution must be order-independent"
        # Full-feed permutation: identical reconciled content.
        full = _normalize_eur(alpha_feed, registry, eur_ctx)
        shuffled = _normalize_eur(
            alpha_feed, registry, eur_ctx, records=list(reversed(rows))
        )
        assert content_digest(full.bars) == content_digest(shuffled.bars)
        assert [b.dumps() for b in full.bars] == [b.dumps() for b in shuffled.bars]

    def test_revision_is_explicit_revised(self, alpha_feed, registry, eur_ctx):
        rows = alpha_feed["records"]
        rev_open = int(_utc("2026-03-03T00:30:00Z").timestamp())
        rev_rows = [row for row in rows if row["epoch_open"] == rev_open]
        assert len(rev_rows) == 2
        winners = []
        for order in (rev_rows, list(reversed(rev_rows))):
            feed = _normalize_eur(alpha_feed, registry, eur_ctx, records=order)
            assert len(feed.bars) == 1
            winner = feed.bars[0]
            assert QualityFlag.REVISED in winner.quality_flags
            assert str(winner.close) == "1.08088"  # later source timestamp wins
            assert _z(winner.source_timestamp) == "2026-03-03T00:35:12Z"
            winners.append(winner.dumps())
        assert winners[0] == winners[1], "revision outcome must be order-independent"
        # Silent overwrite is impossible: the older row can never win.
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        revised = [b for b in feed.bars if QualityFlag.REVISED in b.quality_flags]
        assert len(revised) == 1

    def test_missing_bar_is_gap_never_synthesized(self, alpha_feed, registry, eur_ctx):
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        opens = {_z(bar.open_time) for bar in feed.bars}
        assert "2026-03-03T00:15:00Z" not in opens, "gap must remain absent"
        assert feed.missing == (_utc("2026-03-03T00:15:00Z"),)
        assert QualityFlag.GAP in feed.quality_flags
        # Zero bars synthesized: bar count equals distinct source keys.
        distinct_keys = {
            (row["epoch_open"], row["epoch_close"]) for row in alpha_feed["records"]
        }
        assert len(feed.bars) == len(distinct_keys)
        markers = missing_opens(feed.bars, eur_ctx.expected_opens, timeframe="M5")
        assert markers == (_utc("2026-03-03T00:15:00Z"),)

    def test_missing_or_ambiguous_never_invents_bars(self, alpha_feed, registry, eur_ctx):
        # Feed ends early: tail gap visible, no invented bars (L3).
        tail_cut = int(_utc("2026-03-03T07:55:00Z").timestamp())
        truncated = [
            row for row in alpha_feed["records"] if row["epoch_open"] < tail_cut
        ]
        feed = _normalize_eur(alpha_feed, registry, eur_ctx, records=truncated)
        assert any(_z(stamp) == "2026-03-03T07:55:00Z" for stamp in feed.missing)
        assert QualityFlag.GAP in feed.quality_flags
        distinct = {(row["epoch_open"], row["epoch_close"]) for row in truncated}
        assert len(feed.bars) == len(distinct)  # nothing added
        # Incomplete record: explicit quality state, zero synthesized OHLC.
        broken = dict(alpha_feed["records"][1])
        broken.pop("c")
        record = normalize_record(
            broken,
            "fake_alpha",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        )
        assert record.refused
        assert record.reason is RefusalReason.INCOMPLETE_RECORD
        assert record.bar is None
        assert QualityFlag.GAP in record.flags


# ---------------------------------------------------------------------------
# T3 — Timezone / DST engine (C1–C4, J-a, M1)
# ---------------------------------------------------------------------------


class TestT3ClocksAndDst:
    def test_session_math_uses_iana_named_zone(self, ny_clock):
        assert ny_clock.kind is ClockKind.NAMED_IANA
        assert ny_clock.dst_policy is DstPolicy.IANA_DST
        assert ny_clock.utc_offset_minutes is None, "named zone must carry no offset"
        assert ny_clock.timezone_rule == "America/New_York"
        wall = datetime(2026, 3, 2, 19, 0)
        expected = wall.replace(tzinfo=ZoneInfo("America/New_York")).astimezone(
            timezone.utc
        )
        assert to_utc(wall, ny_clock) == expected
        assert session_bounds_utc(date(2026, 3, 2), time(19, 0), time(3, 0), ny_clock) == (
            expected,
            expected + timedelta(hours=8),
        )
        # Named math differs from fixed-offset arithmetic on a DST date.
        fixed = fixed_clock("EST_NO_DST", -300)
        _start_n, end_named = session_bounds_utc(
            date(2026, 3, 7), time(19, 0), time(3, 0), ny_clock
        )
        _start_f, end_fixed = session_bounds_utc(
            date(2026, 3, 7), time(19, 0), time(3, 0), fixed
        )
        assert end_named == datetime(2026, 3, 8, 7, 0, tzinfo=timezone.utc)
        assert end_fixed == datetime(2026, 3, 8, 8, 0, tzinfo=timezone.utc)
        assert end_named != end_fixed

    def test_fixed_offset_artifact_retains_clock_identity(self):
        artifact = fixed_clock("EST_NO_DST", -300)
        assert artifact.kind is ClockKind.FIXED_OFFSET
        assert artifact.dst_policy is DstPolicy.NO_DST
        assert artifact.utc_offset_minutes == -300
        assert artifact.registry_version == CLOCK_REGISTRY_VERSION
        # Round-trip preserves every field — no conversion to a named zone.
        restored = ClockIdentity.from_dict(artifact.to_dict())
        assert restored == artifact
        assert restored.kind is ClockKind.FIXED_OFFSET
        # No silent reinterpretation: the artifact keeps its offset while a
        # named zone moves with DST.
        artifact_instant = to_utc(datetime(2026, 3, 8, 19, 0), artifact)
        named_instant = to_utc(
            datetime(2026, 3, 8, 19, 0), named_clock("America/New_York")
        )
        assert artifact_instant == datetime(2026, 3, 9, 0, 0, tzinfo=timezone.utc)
        assert named_instant == datetime(2026, 3, 8, 23, 0, tzinfo=timezone.utc)
        assert artifact_instant != named_instant

    def test_dst_spring_forward_session_boundary(self, ny_clock):
        start, end = session_bounds_utc(
            date(2026, 3, 7), time(19, 0), time(3, 0), ny_clock
        )
        assert start == datetime(2026, 3, 8, 0, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 3, 8, 7, 0, tzinfo=timezone.utc)
        local_span = timedelta(hours=8)
        utc_span = end - start
        assert utc_span == local_span - timedelta(hours=1), "DST gap shortens UTC span"

    def test_dst_fall_back_session_boundary(self, ny_clock):
        start, end = session_bounds_utc(
            date(2026, 10, 31), time(19, 0), time(3, 0), ny_clock
        )
        assert start == datetime(2026, 10, 31, 23, 0, tzinfo=timezone.utc)
        assert end == datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)
        utc_span = end - start
        assert utc_span == timedelta(hours=9), "repeated hour lengthens UTC span"
        # Repeated hour resolves deterministically via fold.
        first = to_utc(datetime(2026, 11, 1, 1, 30), ny_clock, fold=0)
        second = to_utc(datetime(2026, 11, 1, 1, 30), ny_clock, fold=1)
        assert first == datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc)
        assert second == datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc)
        assert to_utc(datetime(2026, 11, 1, 1, 30), ny_clock, fold=0) == first

    def test_dst_adversarial_suite(self, ny_clock, session_registry, registry, alpha_feed, eur_ctx):
        definition = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        ).definition
        # (a) Spring-forward day: final bar instant exists even though the
        # local 02:55 wall label does not exist that day.
        spring_open = final_bar_open_utc(
            definition, timedelta(minutes=5), date(2026, 3, 7)
        )
        assert spring_open == datetime(2026, 3, 8, 6, 55, tzinfo=timezone.utc)
        assert local_wall(spring_open, ny_clock) == datetime(2026, 3, 8, 1, 55)
        assert local_wall(spring_open + timedelta(minutes=5), ny_clock) == datetime(
            2026, 3, 8, 3, 0
        )
        assert local_wall(spring_open, ny_clock).hour != 2
        # (b) Fall-back day: local 02:55 exists (EST side) and resolves.
        fall_open = final_bar_open_utc(
            definition, timedelta(minutes=5), date(2026, 10, 31)
        )
        assert fall_open == datetime(2026, 11, 1, 7, 55, tzinfo=timezone.utc)
        assert local_wall(fall_open, ny_clock) == datetime(2026, 11, 1, 2, 55)
        # (c) Boundary-time bars: start edge in, end edge out.
        assert local_open_in_session(definition, datetime(2026, 3, 2, 19, 0))
        assert not local_open_in_session(definition, datetime(2026, 3, 3, 3, 0))
        # (d) Repeated-hour wall times are inside the session on both folds.
        for instant in (
            datetime(2026, 11, 1, 5, 30, tzinfo=timezone.utc),
            datetime(2026, 11, 1, 6, 30, tzinfo=timezone.utc),
        ):
            assert local_open_in_session(definition, local_wall(instant, ny_clock))
        # (e) Fixed-offset artifact alongside named-zone data in one slice:
        # the artifact clock is accepted as declared, never remapped.
        assert registry.get("EURUSD").supports_clock("EST_NO_DST")
        artifact_row = dict(alpha_feed["records"][1])
        artifact_row["zone"] = "EST_NO_DST"
        artifact_record = normalize_record(
            artifact_row,
            "fake_alpha",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        )
        assert artifact_record.bar is not None
        assert artifact_record.status.value == "OK"
        named_record = normalize_record(
            alpha_feed["records"][1],
            "fake_alpha",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        )
        assert named_record.bar is not None
        # Both records normalize; neither clock is rewritten to the other.
        assert definition.kind.value == "WINDOW"

    def test_clock_identity_is_first_class_value(self, ny_clock, session_registry, eur_ctx, alpha_feed, registry):
        assert ny_clock.to_dict()["registry_version"] == CLOCK_REGISTRY_VERSION
        assert ClockIdentity.from_dict(ny_clock.to_dict()) == ny_clock
        resolution = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        )
        resolved_dict = resolution.to_dict()
        assert resolved_dict["definition"]["clock"]["registry_version"] == (
            CLOCK_REGISTRY_VERSION
        )
        replay = replay_historical(alpha_feed["records"], "fake_alpha", eur_ctx)
        result = replay.to_dict()
        assert result["clock_registry_version"] == CLOCK_REGISTRY_VERSION
        assert result["session_registry_version"] == SESSION_REGISTRY_VERSION
        assert result["market_data_schema_version"] == MARKET_DATA_SCHEMA_VERSION


# ---------------------------------------------------------------------------
# T4 — Research-day ownership (D1–D5, J-b)
# ---------------------------------------------------------------------------


class TestT4ResearchDay:
    def test_research_day_assignment_explicit(
        self, lineage_registry, sessions_fx, ny_clock
    ):
        # (lineage, instrument, bar close time) -> research day; pure function.
        close = _utc("2026-03-03T00:05:00Z")
        assignment = assign_research_day(
            lineage_registry, "EUR_DAILY_LINEAGE", "EURUSD", close
        )
        assert assignment.status is ResearchDayStatus.RESOLVED
        assert assignment.research_day == date(2026, 3, 3)
        assert assignment.instrument_id == "EURUSD"
        assert assignment.clock_identity == ny_clock
        assert assignment.source_ref
        assert assignment.market_data_schema_version == MARKET_DATA_SCHEMA_VERSION
        # It is not a calendar-date derivation: the same close time with a
        # lineage that declares no boundary yields the local date, not +1.
        local_registry = ResearchDayRegistry()
        local_registry.register(
            ResearchDayLineage(
                lineage_id="SAME_DAY_LINEAGE",
                model_id="TEST.MODEL.V1",
                model_version="V1",
                clock=ny_clock,
                evening_shift_boundary=None,
                source_ref="test: same-day declaration",
            )
        )
        local_registry.register(lineage_registry.get("EUR_DAILY_LINEAGE"))
        same_day = assign_research_day(
            local_registry, "SAME_DAY_LINEAGE", "EURUSD", close
        )
        shifted = assign_research_day(
            local_registry, "EUR_DAILY_LINEAGE", "EURUSD", close
        )
        assert same_day.research_day == date(2026, 3, 2)
        assert shifted.research_day == date(2026, 3, 3)
        assert same_day.research_day != shifted.research_day

    def test_evening_bar_following_research_day(self, lineage_registry, sessions_fx):
        # EUR lineage: cited to the canonical evidence card (D2).
        eur_lineage = lineage_registry.get("EUR_DAILY_LINEAGE")
        assert "EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1" in eur_lineage.source_ref
        assert eur_lineage.model_id == "EUR.DAILY.NEWS_REKEY.V1"
        btc_lineage = lineage_registry.get("BTC_TRACKER_LINEAGE")
        assert "BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1" in btc_lineage.source_ref
        # Evening close (local 19:05 on Mar 2) -> following research day.
        evening = _utc("2026-03-03T00:05:00Z")
        eur_day = assign_research_day(
            lineage_registry, "EUR_DAILY_LINEAGE", "EURUSD", evening
        )
        btc_day = assign_research_day(
            lineage_registry, "BTC_TRACKER_LINEAGE", "BTCUSD", evening
        )
        assert eur_day.research_day == date(2026, 3, 3)
        assert btc_day.research_day == date(2026, 3, 3)
        # No other lineage silently inherits the rule: an unregistered
        # lineage never receives the EUR/BTC shift.
        inherited = assign_research_day(
            lineage_registry, "XAU_GAME_LINEAGE", "XAUUSD", evening
        )
        assert inherited.status is ResearchDayStatus.UNRESOLVED
        assert inherited.research_day is None
        # Pre-boundary close (exactly 19:00 local) stays on its date.
        boundary = assign_research_day(
            lineage_registry, "EUR_DAILY_LINEAGE", "EURUSD",
            _utc("2026-03-03T00:00:00Z"),
        )
        assert boundary.research_day == date(2026, 3, 2)

    def test_research_day_differs_from_naive_calendar_date(self, lineage_registry):
        # EST evening: UTC and NY dates disagree with the research day.
        est_close = _utc("2026-03-03T00:05:00Z")
        est_assignment = assign_research_day(
            lineage_registry, "EUR_DAILY_LINEAGE", "EURUSD", est_close
        )
        assert est_assignment.research_day == date(2026, 3, 3)
        assert est_close.date() == date(2026, 3, 3)
        assert est_close.astimezone(ZoneInfo("America/New_York")).date() == date(2026, 3, 2)
        assert est_close.astimezone(ZoneInfo("America/New_York")).date() != (
            est_assignment.research_day
        )
        # EDT evening: both naive dates disagree with the research day.
        edt_close = _utc("2026-07-02T23:05:00Z")
        edt_assignment = assign_research_day(
            lineage_registry, "EUR_DAILY_LINEAGE", "EURUSD", edt_close
        )
        assert edt_assignment.research_day == date(2026, 7, 3)
        assert edt_close.date() == date(2026, 7, 2)
        assert edt_close.astimezone(ZoneInfo("America/New_York")).date() == date(2026, 7, 2)
        assert edt_close.date() != edt_assignment.research_day

    def test_research_day_deterministic(self, lineage_registry):
        # Close at local 19:05 (evening) -> following research day, every time.
        close = _utc("2026-03-04T00:05:00Z")
        results = [
            assign_research_day(
                lineage_registry, "EUR_DAILY_LINEAGE", "EURUSD", close
            )
            for _ in range(3)
        ]
        assert results[0] == results[1] == results[2]
        assert results[0].research_day == date(2026, 3, 4)

    def test_ambiguous_lineage_fails_closed(self, lineage_registry):
        assignment = assign_research_day(
            lineage_registry, "UNKNOWN_LINEAGE", "EURUSD",
            _utc("2026-03-03T00:05:00Z"),
        )
        assert assignment.status is ResearchDayStatus.UNRESOLVED
        assert assignment.research_day is None
        assert assignment.clock_identity is None
        assert assignment.source_ref is None
        assert assignment.resolved is False


# ---------------------------------------------------------------------------
# T5 — Versioned session registry (E1–E4, L2)
# ---------------------------------------------------------------------------


class TestT5Sessions:
    def test_registry_covers_canonical_session_families(
        self, session_registry, documented_gaps
    ):
        expected = {
            "ASIAN_RANGE",
            "LONDON_MLR",
            "DAILY_CHECKPOINT",
            "WEEKLY_SEED",
            "DT_WINDOW",
            "MONTH_BOUNDARY",
            "QUARTER_BOUNDARY",
        }
        assert {family.value for family in SessionFamily} == expected
        coverage = session_registry.coverage(documented_gaps)
        assert set(coverage) == expected
        # Only canonical definitions are registered...
        assert coverage["ASIAN_RANGE"] == "DEFINED"
        assert coverage["DAILY_CHECKPOINT"] == "DEFINED"
        # ...every other family is a disclosed gap, never invented (GAP-2).
        for family in (
            "LONDON_MLR",
            "WEEKLY_SEED",
            "DT_WINDOW",
            "MONTH_BOUNDARY",
            "QUARTER_BOUNDARY",
        ):
            assert coverage[family].startswith("GAP:"), family
        assert "crosswalk" in coverage["DT_WINDOW"]
        # Exactly the canonical definitions exist — nothing more.
        assert len(session_registry.definitions_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")) == 1
        assert len(session_registry.definitions_for("BTC.TRACKER.DWM.V1", "V1")) == 2
        assert len(session_registry.definitions_for("XAU.GAME.L1_L2_L3.V1", "V1")) == 0

    def test_session_bound_to_model_and_version(self, session_registry):
        resolved = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        )
        assert resolved.status is SessionStatus.RESOLVED
        assert resolved.definition is not None
        assert resolved.definition.model_version == "PHASE1"
        assert resolved.definition.source_ref
        # Cross-version reuse fails closed (VERSION_MISMATCH).
        wrong_version = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE2", "EUR_DAILY.ASIAN_RANGE"
        )
        assert wrong_version.status is SessionStatus.NO_CALCULATION
        assert wrong_version.definition is None
        assert wrong_version.reason_code == "VERSION_MISMATCH"
        # A checkpoint definition is bound the same way.
        checkpoint = session_registry.resolve(
            "BTC.TRACKER.DWM.V1", "V1", "BTC_TRACKER.DAILY_CHECKPOINT_12PM"
        )
        assert checkpoint.status is SessionStatus.RESOLVED
        assert checkpoint.definition.kind is SessionKind.CHECKPOINT
        assert checkpoint.definition.instant_local == time(12, 0)

    def test_session_registry_version_recorded(self, session_registry, eur_ctx, alpha_feed):
        assert session_registry.registry_version == SESSION_REGISTRY_VERSION
        resolution = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        )
        recorded = resolution.to_dict()
        assert recorded["session_registry_version"] == SESSION_REGISTRY_VERSION
        assert recorded["market_data_schema_version"] == MARKET_DATA_SCHEMA_VERSION
        replay = replay_historical(alpha_feed["records"], "fake_alpha", eur_ctx)
        assert replay.to_dict()["session_registry_version"] == SESSION_REGISTRY_VERSION

    def test_unknown_session_no_calculation(self, session_registry):
        resolution = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "NO_SUCH_SESSION"
        )
        assert resolution.status is SessionStatus.NO_CALCULATION
        assert resolution.definition is None
        assert resolution.reason_code == "UNKNOWN_SESSION"
        # Explicit failure outcome, never an empty success (L2).
        assert resolution.outcome is DataOutcome.NO_CALCULATION


# ---------------------------------------------------------------------------
# T6 — Final-bar semantics (F1–F3, J-c)
# ---------------------------------------------------------------------------


class TestT6FinalBar:
    def test_boundary_inclusive_exclusive_edges(self, session_registry, ny_clock):
        definition = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        ).definition
        # Window [19:00, 03:00): start edge in, end edge out.
        assert local_open_in_session(definition, datetime(2026, 3, 2, 19, 0)) is True
        assert local_open_in_session(definition, datetime(2026, 3, 3, 2, 55)) is True
        assert local_open_in_session(definition, datetime(2026, 3, 3, 3, 0)) is False
        assert local_open_in_session(definition, datetime(2026, 3, 2, 18, 59)) is False
        # Declared end-inclusive windows make the end edge a member.
        inclusive = replace(definition, end_inclusive=True)
        assert local_open_in_session(inclusive, datetime(2026, 3, 3, 3, 0)) is True
        # Session bounds: a bar may close exactly at the end instant.
        start_u, end_u = session_bounds_utc(
            date(2026, 3, 2), time(19, 0), time(3, 0), ny_clock
        )
        assert start_u == _utc("2026-03-03T00:00:00Z")
        assert end_u == _utc("2026-03-03T08:00:00Z")
        assert to_utc(datetime(2026, 3, 3, 3, 0), ny_clock) == end_u
        # Checkpoint: exactly one wall time matches, no invented duration.
        checkpoint = session_registry.resolve(
            "BTC.TRACKER.DWM.V1", "V1", "BTC_TRACKER.DAILY_CHECKPOINT_12PM"
        ).definition
        assert close_matches_checkpoint(checkpoint, datetime(2026, 3, 3, 12, 0)) is True
        assert close_matches_checkpoint(checkpoint, datetime(2026, 3, 3, 11, 59)) is False
        assert close_matches_checkpoint(checkpoint, datetime(2026, 3, 3, 12, 1)) is False

    def test_canonical_m5_0255_final_bar(
        self, session_registry, ny_clock, alpha_feed, registry, eur_ctx
    ):
        definition = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        ).definition
        final_open = final_bar_open_utc(
            definition, timedelta(minutes=5), date(2026, 3, 2)
        )
        assert final_open == _utc("2026-03-03T07:55:00Z")
        assert local_wall(final_open, ny_clock) == datetime(2026, 3, 3, 2, 55)
        assert local_wall(final_open + timedelta(minutes=5), ny_clock) == datetime(
            2026, 3, 3, 3, 0
        )
        # Cited to its canonical sources (G3: no rule invented here).
        assert "EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1" in definition.source_ref
        assert "PLAN.md Ch III.1.6" in definition.source_ref
        # The fixture contains exactly that bar, final at cutoff.
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        protected = [
            bar
            for bar in feed.bars
            if bar.open_time == final_open
            and bar.close_time == _utc("2026-03-03T08:00:00Z")
        ]
        assert len(protected) == 1
        assert protected[0].finality is Finality.FINAL

    def test_final_bar_rules_not_generalized_beyond_canonical(
        self, session_registry, documented_gaps
    ):
        # Another lineage cannot borrow the EUR rule (G3 / stop conditions).
        borrowed = session_registry.resolve(
            "XAU.GAME.L1_L2_L3.V1", "V1", "EUR_DAILY.ASIAN_RANGE"
        )
        assert borrowed.status is SessionStatus.NO_CALCULATION
        assert borrowed.definition is None
        coverage = session_registry.coverage(documented_gaps)
        assert coverage["DT_WINDOW"].startswith("GAP:")

    def test_nonfinal_excluded_from_final_state(self, alpha_feed, registry, eur_ctx):
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        selection = final_state_input(feed.bars, eur_ctx.observation_cutoff)
        assert all(bar.finality is Finality.FINAL for bar in selection.final_bars)
        assert all(QualityFlag.NONFINAL not in bar.quality_flags for bar in selection.final_bars)
        assert selection.excluded_nonfinal == 1
        assert selection.outcome is DataOutcome.DEGRADED
        # Nothing final at all -> blocked, not an empty success.
        only_partial = [bar for bar in feed.bars if bar.finality is Finality.NONFINAL]
        assert only_partial
        blocked = final_state_input(
            only_partial, eur_ctx.observation_cutoff - timedelta(hours=1)
        )
        assert blocked.final_bars == ()
        assert blocked.outcome is DataOutcome.DATA_QUALITY_BLOCKED

    def test_nonfinal_cannot_contaminate_final_state(self, alpha_feed, registry, eur_ctx):
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        partial = next(
            bar for bar in feed.bars if bar.finality is Finality.NONFINAL
        )
        # Selection objects structurally refuse nonfinal members.
        with pytest.raises(NonFinalError):
            FinalStateSelection(
                final_bars=(partial,), excluded_nonfinal=0, outcome=DataOutcome.OK
            )
        selection = final_state_input(feed.bars, eur_ctx.observation_cutoff)
        assert partial not in selection.final_bars
        assert partial.open_time not in {
            bar.open_time for bar in selection.final_bars
        }


# ---------------------------------------------------------------------------
# T7 — Data quality (G1–G5, L1/L2)
# ---------------------------------------------------------------------------


class TestT7Quality:
    def test_quality_flag_vocabulary_exact(self):
        expected = {
            "COMPLETE",
            "GAP",
            "DUPLICATE",
            "REVISED",
            "STALE",
            "NONFINAL",
            "OUTLIER_SOURCE",
            "UNSUPPORTED_CLOCK",
        }
        assert {flag.value for flag in QualityFlag} == expected
        assert FROZEN_QUALITY_FLAGS == frozenset(QualityFlag)
        from app.forge.market_data import parse_quality_flag

        assert parse_quality_flag("GAP") is QualityFlag.GAP
        with pytest.raises(QualityVocabularyError):
            parse_quality_flag("CATASTROPHIC")
        with pytest.raises(QualityVocabularyError):
            parse_quality_flag("complete")  # case is not coerced

    def test_blocking_vs_warning_declaration_honored(self, model_policy):
        assert model_policy.blocking == {
            QualityFlag.GAP,
            QualityFlag.STALE,
            QualityFlag.OUTLIER_SOURCE,
            QualityFlag.UNSUPPORTED_CLOCK,
        }
        assert model_policy.warning == {
            QualityFlag.DUPLICATE,
            QualityFlag.REVISED,
            QualityFlag.NONFINAL,
        }
        # Declarations that overlap, omit, or misuse COMPLETE fail closed.
        with pytest.raises(QualityVocabularyError):
            QualityPolicy.from_strings(
                "M.V1",
                "V1",
                blocking=["GAP", "DUPLICATE", "REVISED", "STALE", "NONFINAL", "OUTLIER_SOURCE", "UNSUPPORTED_CLOCK"],
                warning=["DUPLICATE"],
            )
        with pytest.raises(QualityVocabularyError):
            QualityPolicy.from_strings(
                "M.V1",
                "V1",
                blocking=["GAP", "STALE", "OUTLIER_SOURCE", "UNSUPPORTED_CLOCK"],
                warning=["DUPLICATE", "REVISED"],  # NONFINAL undeclared
            )
        with pytest.raises(QualityVocabularyError):
            QualityPolicy.from_strings(
                "M.V1",
                "V1",
                blocking=["COMPLETE", "GAP", "STALE", "OUTLIER_SOURCE", "UNSUPPORTED_CLOCK", "NONFINAL", "DUPLICATE", "REVISED"],
                warning=[],
            )

    def test_blocking_vs_degraded_outcomes(
        self, model_policy, alpha_feed, btc_feed, registry, eur_ctx, btc_ctx
    ):
        # EUR slice carries GAP (missing 00:15) -> blocking -> blocked.
        eur_feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        assert QualityFlag.GAP in eur_feed.quality_flags
        assert model_policy.evaluate(eur_feed.quality_flags) is (
            DataOutcome.DATA_QUALITY_BLOCKED
        )
        # BTC slice carries only NONFINAL (warning) -> degraded, disclosed.
        btc_feed_result = normalize_feed(
            btc_feed["records"],
            "fake_alpha",
            registry,
            observation_cutoff=btc_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
            expected_opens=btc_ctx.expected_opens,
        )
        assert btc_feed_result.quality_flags == {QualityFlag.NONFINAL}
        assert model_policy.evaluate(btc_feed_result.quality_flags) is DataOutcome.DEGRADED
        assert model_policy.evaluate([QualityFlag.COMPLETE]) is DataOutcome.OK
        assert model_policy.evaluate([]) is DataOutcome.OK

    def test_unsupported_clock_never_silently_remapped(
        self, registry, alpha_feed, eur_ctx
    ):
        row = dict(alpha_feed["records"][1])
        row["zone"] = "Asia/Kolkata"
        record = normalize_record(
            row,
            "fake_alpha",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        )
        assert record.refused
        assert record.reason is RefusalReason.UNSUPPORTED_CLOCK
        assert record.flags == frozenset({QualityFlag.UNSUPPORTED_CLOCK})
        assert record.bar is None, "no bar may exist for an unsupported clock"
        # The raw clock value was refused, never swapped for a supported one.
        assert row["zone"] == "Asia/Kolkata"

    def test_unsupported_clock_fails_closed(self, registry):
        eurusd = registry.get("EURUSD")
        with pytest.raises(Exception) as exc:
            eurusd.require_clock("Europe/Paris")
        assert type(exc.value).__name__ == "UnsupportedClockError"
        from app.forge.market_data import named_clock as _named

        with pytest.raises(Exception) as exc2:
            _named("Nowhere/Nothing")
        assert type(exc2.value).__name__ == "UnsupportedClockError"

    def test_quality_flags_bounded_no_free_text(self, alpha_feed, registry, eur_ctx):
        allowed = {flag.value for flag in QualityFlag}
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        for bar in feed.bars:
            for flag in bar.quality_flags:
                assert isinstance(flag, QualityFlag)
                assert flag.value in allowed
            listed = bar.to_dict()["quality_flags"]
            assert listed == sorted(listed)
            for value in listed:
                assert value in allowed
        # The policy object has no free-text payload carrier.
        assert {item.name for item in fields(QualityPolicy)} == {
            "model_id",
            "model_version",
            "blocking",
            "warning",
        }
        # Serialized outcome vocabulary is bounded too.
        assert {outcome.value for outcome in DataOutcome} == {
            "OK",
            "DEGRADED",
            "DATA_QUALITY_BLOCKED",
            "NO_CALCULATION",
        }


# ---------------------------------------------------------------------------
# T8 — Provider normalization (H1–H4, J-d)
# ---------------------------------------------------------------------------


class TestT8ProviderNormalization:
    def test_raw_feed_normalizes_to_contract(self, alpha_feed, registry, eur_ctx):
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        assert feed.refusal_count == 0
        distinct_keys = {
            (row["epoch_open"], row["epoch_close"]) for row in alpha_feed["records"]
        }
        assert len(feed.bars) == len(distinct_keys)  # dup/revision collapsed
        assert feed.timeframe == "M5"
        assert feed.evaluate(eur_ctx.policy) is DataOutcome.DATA_QUALITY_BLOCKED
        for bar in feed.bars:
            assert bar.provider == "fake_alpha"
            assert bar.instrument_id == "EURUSD"
            assert bar.market_data_schema_version == MARKET_DATA_SCHEMA_VERSION

    def test_no_provider_fields_in_normalized_output(
        self, alpha_feed, beta_feed, registry, eur_ctx
    ):
        alpha_keys = set(provider_schema("fake_alpha").raw_keys)
        beta_keys = set(provider_schema("fake_beta").raw_keys)
        raw_keys = alpha_keys | beta_keys
        feeds = {
            "fake_alpha": alpha_feed,
            "fake_beta": beta_feed,
        }
        for provider, fixture in feeds.items():
            feed = normalize_feed(
                fixture["records"],
                provider,
                registry,
                observation_cutoff=eur_ctx.observation_cutoff,
                provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
                expected_opens=eur_ctx.expected_opens,
            )
            dump = json.dumps([bar.to_dict() for bar in feed.bars])
            for key in raw_keys:
                assert f'"{key}"' not in dump, (provider, key)
            # Raw spellings and timestamp conventions are quarantined too.
            for raw_value in ("EUR/USD", "EUR-USD", "America/New_York"):
                assert raw_value not in dump, (provider, raw_value)
            assert "+00:00" not in dump, provider  # normalized form is Z

    def test_fake_feeds_normalize_identically(self, alpha_feed, beta_feed, registry, eur_ctx):
        for provider, fixture in (
            ("fake_alpha", alpha_feed),
            ("fake_beta", beta_feed),
        ):
            dumps = []
            for _run in range(2):
                feed = normalize_feed(
                    fixture["records"],
                    provider,
                    registry,
                    observation_cutoff=eur_ctx.observation_cutoff,
                    provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
                    expected_opens=eur_ctx.expected_opens,
                )
                dumps.append(json.dumps([bar.dumps() for bar in feed.bars]))
            assert dumps[0] == dumps[1], provider

    def test_provider_normalization_parity(self, alpha_feed, beta_feed, registry, eur_ctx):
        alpha = _normalize_eur(alpha_feed, registry, eur_ctx)
        beta = normalize_feed(
            beta_feed["records"],
            "fake_beta",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
            expected_opens=eur_ctx.expected_opens,
        )
        # Feeds are genuinely distinct...
        assert {bar.provider for bar in alpha.bars} == {"fake_alpha"}
        assert {bar.provider for bar in beta.bars} == {"fake_beta"}
        assert beta_feed["records"] != alpha_feed["records"]
        # ...but the canonical content is identical (alias conversion +
        # different arrival order + different conventions all normalize).
        assert len(alpha.bars) == len(beta.bars)
        assert {bar.instrument_id for bar in beta.bars} == {"EURUSD"}
        assert content_digest(alpha.bars) == content_digest(beta.bars)

    def test_provider_alias_normalizes_to_canonical_id(self, registry, beta_feed, eur_ctx):
        assert registry.resolve_provider("fake_beta", "EUR-USD").instrument_id == "EURUSD"
        assert registry.resolve_provider("fake_alpha", "EUR/USD").instrument_id == "EURUSD"
        feed = normalize_feed(
            beta_feed["records"][:1],
            "fake_beta",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        )
        assert feed.bars
        assert feed.bars[0].instrument_id == "EURUSD"

    def test_unknown_provider_and_symbol_refused(self, registry, alpha_feed, eur_ctx):
        from app.forge.market_data import UnsupportedProviderError

        with pytest.raises(UnsupportedProviderError):
            provider_schema("mystery_feed")
        with pytest.raises(UnsupportedProviderError):
            normalize_feed(
                alpha_feed["records"][:1],
                "mystery_feed",
                registry,
                observation_cutoff=eur_ctx.observation_cutoff,
                provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
            )
        unknown_symbol = dict(alpha_feed["records"][1])
        unknown_symbol["pair"] = "NOPE/USD"
        record = normalize_record(
            unknown_symbol,
            "fake_alpha",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        )
        assert record.refused and record.reason is RefusalReason.UNKNOWN_SYMBOL
        unknown_tf = dict(alpha_feed["records"][1])
        unknown_tf["tf"] = "M3"
        record_tf = normalize_record(
            unknown_tf,
            "fake_alpha",
            registry,
            observation_cutoff=eur_ctx.observation_cutoff,
            provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        )
        assert record_tf.refused
        assert record_tf.reason is RefusalReason.UNSUPPORTED_TIMEFRAME


# ---------------------------------------------------------------------------
# T9 — Historical / streaming parity (I1–I3)
# ---------------------------------------------------------------------------


class TestT9Parity:
    def test_fixture_manifest_hash_recorded(self):
        manifest = json.loads(
            (FIXTURE_DIR / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8")
        )
        assert manifest["algorithm"] == "sha256"
        recorded = manifest["files"]
        json_files = {
            path.name for path in FIXTURE_DIR.glob("*.json")
        } - {"FIXTURE_MANIFEST.json"}
        assert set(recorded) == json_files
        for name, expected in recorded.items():
            # EOL-normalized comparison (same reading as the frozen-surface
            # checks): the generator writes LF; checkouts may render CRLF.
            content = (FIXTURE_DIR / name).read_bytes().replace(b"\r\n", b"\n")
            actual = hashlib.sha256(content).hexdigest()
            assert actual == expected, name
        # Real-slice fixture cites canonical sources; every cited path exists.
        sessions_fx = _load_fixture("sessions_canonical.json")
        assert sessions_fx["provenance"] == "CANONICAL_SOURCE_SLICE"
        assert sessions_fx["cited_evidence_ids"] == ["EV.EUR.DAILY.PHASE1_TIERS.V1"]
        refs = [
            record["source_ref"]
            for record in sessions_fx["definitions"] + sessions_fx["research_day_lineages"]
        ]
        assert refs and all(refs)
        cited = set()
        for ref in refs:
            cited.update(re.findall(r"(?:corpus|implementation)/[A-Za-z0-9_/.]+\.md", ref))
        assert cited, "fixture must cite concrete source paths"
        for rel_path in cited:
            assert (REPO_ROOT / rel_path).exists(), rel_path
        # The cited evidence id resolves to a real canonical evidence card.
        evidence_dir = REPO_ROOT / "corpus" / "canonical" / "evidence"
        evidence_text = "\n".join(
            path.read_text(encoding="utf-8") for path in evidence_dir.glob("*.md")
        )
        assert "EV.EUR.DAILY.PHASE1_TIERS.V1" in evidence_text

    def test_replay_streaming_session_parity(self, eur_ctx, alpha_feed, btc_ctx, btc_feed):
        replay = replay_historical(alpha_feed["records"], "fake_alpha", eur_ctx)
        streaming = stream_live(alpha_feed["records"], "fake_alpha", eur_ctx)
        report = compare_parity(replay, streaming)
        assert report.session_parity and report.overall, report.differences
        own = replay.ownership_map()
        assert streaming.ownership_map() == own
        distinct_keys = {
            (row["epoch_open"], row["epoch_close"]) for row in alpha_feed["records"]
        }
        assert len(own) == len(distinct_keys)
        resolved = [
            result for result in own.values() if result.status is OwnershipStatus.RESOLVED
        ]
        # every in-session bar resolves; the pre-boundary bar and the
        # 03:00-open bar sit outside the window (NO_SESSION, explicit).
        assert len(resolved) == len(distinct_keys) - 2
        assert {result.research_day for result in resolved} == {date(2026, 3, 3)}
        assert {result.session_id for result in resolved} == {"EUR_DAILY.ASIAN_RANGE"}
        unowned = [
            result
            for result in own.values()
            if result.status is OwnershipStatus.NO_CALCULATION
        ]
        assert len(unowned) == 2
        assert {result.reason_code for result in unowned} == {"NO_SESSION"}
        for result in own.values():
            assert result.session_registry_version == SESSION_REGISTRY_VERSION
            assert result.market_data_schema_version == MARKET_DATA_SCHEMA_VERSION
        # BTC checkpoint ownership: exactly the 12:00 close resolves.
        btc_replay = replay_historical(btc_feed["records"], "fake_alpha", btc_ctx)
        btc_stream = stream_live(btc_feed["records"], "fake_alpha", btc_ctx)
        assert compare_parity(btc_replay, btc_stream).overall
        btc_own = btc_replay.ownership_map()
        resolved_btc = [
            result for result in btc_own.values() if result.resolved
        ]
        assert {result.session_id for result in resolved_btc} == {
            "BTC_TRACKER.ASIAN_WINDOW",
            "BTC_TRACKER.DAILY_CHECKPOINT_12PM",
        }
        assert {result.research_day for result in resolved_btc} == {date(2026, 3, 3)}

    def test_replay_streaming_quality_parity(self, eur_ctx, alpha_feed, btc_ctx, btc_feed):
        replay = replay_historical(alpha_feed["records"], "fake_alpha", eur_ctx)
        streaming = stream_live(alpha_feed["records"], "fake_alpha", eur_ctx)
        report = compare_parity(replay, streaming)
        assert report.quality_parity
        assert report.bar_parity
        assert report.outcome_parity
        assert replay.quality_flags == streaming.quality_flags
        assert replay.feed_outcome == streaming.feed_outcome
        assert replay.refused_count == streaming.refused_count == 0
        assert replay.missing == streaming.missing
        # BTC slice parity (NONFINAL-only quality -> degraded).
        btc_replay = replay_historical(btc_feed["records"], "fake_alpha", btc_ctx)
        btc_stream = stream_live(btc_feed["records"], "fake_alpha", btc_ctx)
        assert compare_parity(btc_replay, btc_stream).quality_parity
        assert btc_replay.quality_flags == btc_stream.quality_flags == {
            QualityFlag.NONFINAL
        }
        assert btc_replay.feed_outcome is DataOutcome.DEGRADED
        assert btc_stream.feed_outcome is DataOutcome.DEGRADED

    def test_streaming_arrival_order_independence(self, eur_ctx, alpha_feed):
        records = alpha_feed["records"]
        rotated = records[4:] + records[:4]
        base_replay = replay_historical(records, "fake_alpha", eur_ctx)
        rotated_replay = replay_historical(rotated, "fake_alpha", eur_ctx)
        base_stream = stream_live(records, "fake_alpha", eur_ctx)
        rotated_stream = stream_live(rotated, "fake_alpha", eur_ctx)
        assert content_digest(base_replay.bars) == content_digest(rotated_replay.bars)
        assert content_digest(base_replay.bars) == content_digest(base_stream.bars)
        assert content_digest(base_replay.bars) == content_digest(rotated_stream.bars)
        assert base_replay.ownership_map() == rotated_stream.ownership_map()
        assert base_replay.quality_flags == rotated_stream.quality_flags
        assert compare_parity(rotated_replay, rotated_stream).overall


# ---------------------------------------------------------------------------
# T10 — Cross-model invariants (M3–M5)
# ---------------------------------------------------------------------------


class TestT10Invariants:
    def test_status_labels_factual_enum_only(self):
        enums = (
            QualityFlag,
            DataOutcome,
            OwnershipStatus,
            SessionStatus,
            SessionFamily,
            SessionKind,
            NormalizeStatus,
            RefusalReason,
            Finality,
            ResearchDayStatus,
            ClockKind,
            DstPolicy,
            ProvenanceKind,
            AssetClass,
            NativeUnit,
        )
        rhetoric = re.compile(
            r"(guaranteed|certain|always|reliable|sure|profitable)", re.IGNORECASE
        )
        for enum in enums:
            for member in enum:
                assert not rhetoric.search(member.value), (enum, member.value)
                assert re.fullmatch(r"[A-Z][A-Z0-9_]*", member.value), member.value

    def test_market_data_records_immutable(
        self, alpha_feed, registry, eur_ctx, session_registry
    ):
        classes = (
            Bar,
            ClockIdentity,
            Instrument,
            NativePrice,
            ResearchDayAssignment,
            ResearchDayLineage,
            SessionDefinition,
            QualityPolicy,
            FinalStateSelection,
            OwnershipResult,
            PipelineResult,
        )
        for cls in classes:
            assert cls.__dataclass_params__.frozen is True, cls.__name__
        feed = _normalize_eur(alpha_feed, registry, eur_ctx)
        bar = feed.bars[0]
        with pytest.raises((FrozenInstanceError, AttributeError)):
            bar.close = Decimal("9.99999")
        definition = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        ).definition
        with pytest.raises((FrozenInstanceError, AttributeError)):
            definition.session_id = "MUTATED"
        # Redefinition requires a new version field, never an in-place edit.
        assert bar.market_data_schema_version == MARKET_DATA_SCHEMA_VERSION

    def test_market_data_schema_version_recorded(
        self, eur_ctx, alpha_feed, session_registry, lineage_registry, registry
    ):
        replay = replay_historical(alpha_feed["records"], "fake_alpha", eur_ctx)
        result = replay.to_dict()
        assert result["market_data_schema_version"] == MARKET_DATA_SCHEMA_VERSION
        assert result["session_registry_version"] == SESSION_REGISTRY_VERSION
        assert result["clock_registry_version"] == CLOCK_REGISTRY_VERSION
        for bar_dict in result["bars"]:
            assert bar_dict["market_data_schema_version"] == MARKET_DATA_SCHEMA_VERSION
        for _key, own in replay.ownership:
            assert own.to_dict()["market_data_schema_version"] == (
                MARKET_DATA_SCHEMA_VERSION
            )
            assert own.to_dict()["session_registry_version"] == SESSION_REGISTRY_VERSION
        resolution = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        )
        resolved = resolution.to_dict()
        assert resolved["definition"]["clock"]["registry_version"] == CLOCK_REGISTRY_VERSION
        assignment = assign_research_day(
            lineage_registry, "EUR_DAILY_LINEAGE", "EURUSD", _utc("2026-03-03T19:05:00Z")
        )
        assert assignment.market_data_schema_version == MARKET_DATA_SCHEMA_VERSION
        assert assignment.clock_identity.registry_version == CLOCK_REGISTRY_VERSION


# ---------------------------------------------------------------------------
# T11 — Boundaries and security (N1–N8, O1–O8)
# ---------------------------------------------------------------------------


class TestT11Boundaries:
    def test_no_book1_authority_imports(self):
        banned = re.compile(
            r"(?:from|import)\s+(?:app\.forge\.|\.)(?:qa|retrieval|provenance|canonical)\b"
        )
        for name, source in _package_sources():
            assert not banned.search(source), name
        # III.1 emits data facts only: no claim/evidence/setup/model object.
        for name, source in _package_sources():
            assert not re.search(r"class\s+(Claim|Evidence|Setup|Model)\w*\s*\(", source), name

    def test_no_corpus_writes(self):
        for name, source in _package_sources():
            assert "write_text" not in source and "write_bytes" not in source, name
            assert not re.search(r"\bopen\s*\(", source), name
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", "corpus/"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
        except OSError:
            pytest.skip("git unavailable")
        if result.returncode != 0:
            pytest.skip("git status unavailable in this checkout")
        assert result.stdout.strip() == "", result.stdout

    def test_fixtures_labeled_historical(
        self, eur_slice, btc_slice, alpha_feed, beta_feed, btc_feed, sessions_fx
    ):
        for fixture in (eur_slice, btc_slice, alpha_feed, beta_feed, btc_feed, sessions_fx):
            assert "historical" in fixture
            assert "provenance" in fixture
        for fixture in (eur_slice, btc_slice, alpha_feed, beta_feed, btc_feed):
            assert fixture["historical"] is False
            assert _utc(fixture["observation_cutoff"])  # labeled data cutoff
        assert sessions_fx["historical"] is True
        # No serving surface exists in this package (III.6 owns serving).
        for name, source in _package_sources():
            assert not re.search(r"(fastapi|APIRouter|HTTPServer)", source), name

    def test_synthetic_fixture_labeled_at_creation(self, eur_slice):
        assert eur_slice["provenance"] == "SYNTHETIC_FIXTURE"
        assert "SYNTHETIC_FIXTURE" in eur_slice["data_classification"]
        base = dict(
            instrument_id="EURUSD",
            timeframe="M5",
            open_time=_utc("2026-03-03T00:00:00Z"),
            close_time=_utc("2026-03-03T00:05:00Z"),
            open=Decimal("1.08005"),
            high=Decimal("1.08030"),
            low=Decimal("1.08000"),
            close=Decimal("1.08020"),
            volume=Decimal("10"),
            provider="fake_alpha",
            finality=Finality.FINAL,
            source_timestamp=_utc("2026-03-03T00:05:03Z"),
            quality_flags=frozenset({QualityFlag.COMPLETE}),
        )
        synthetic = Bar(**base, provenance=ProvenanceKind.SYNTHETIC_FIXTURE, source_ref=None)
        assert synthetic.provenance is ProvenanceKind.SYNTHETIC_FIXTURE
        # A synthetic bar can never satisfy an evidence-reference check.
        with pytest.raises(Exception) as exc:
            Bar(
                **base,
                provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
                source_ref="corpus/canonical/evidence/SOME_CARD.md",
            )
        assert type(exc.value).__name__ == "ConventionViolationError"
        # Source-slice bars must cite their source (symmetric guard).
        with pytest.raises(Exception) as exc2:
            Bar(**base, provenance=ProvenanceKind.SOURCE_SLICE, source_ref=None)
        assert type(exc2.value).__name__ == "ConventionViolationError"

    def test_no_trading_or_game_concepts(self, session_registry):
        banned = re.compile(r"\b(game|setup|trigger|entry|win_?rate)\b", re.IGNORECASE)
        for name, source in _package_sources():
            assert not banned.search(source), name
        # Session names come from canonical session definitions only: the
        # package contains no hardcoded session instance names.
        for name, source in _package_sources():
            assert "EUR_DAILY.ASIAN_RANGE" not in source, name
            assert "BTC_TRACKER" not in source, name
        resolved = session_registry.resolve(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY.ASIAN_RANGE"
        )
        assert resolved.definition is not None

    def test_quarantined_sources_absent(self):
        plan = canonicalize_files(load_corpus_files(REPO_ROOT))
        catalog = QuarantineCatalog.from_report(plan.report)
        entries = list(catalog.entries)
        assert len(entries) == 9
        assert all(entry.reason for entry in entries), "reasons must be documented"
        fixture_texts = [
            path.read_text(encoding="utf-8") for path in sorted(FIXTURE_DIR.glob("*.json"))
        ]
        for entry in entries:
            for text in fixture_texts:
                assert entry.source_path not in text, entry.source_path

    def test_suite_makes_no_network_calls(self, monkeypatch, alpha_feed, registry, eur_ctx):
        for name, source in _package_sources():
            assert not re.search(
                r"^\s*(?:import|from)\s+(?:socket|requests|urllib|httpx|aiohttp)\b",
                source,
                re.MULTILINE,
            ), name

        def boom(*_args, **_kwargs):
            raise AssertionError("network call attempted inside Bloc III.1 suite")

        monkeypatch.setattr(socket, "socket", boom)
        monkeypatch.setattr(socket, "create_connection", boom)
        monkeypatch.setattr(socket, "getaddrinfo", boom)
        replay = replay_historical(alpha_feed["records"], "fake_alpha", eur_ctx)
        stream = stream_live(alpha_feed["records"], "fake_alpha", eur_ctx)
        assert compare_parity(replay, stream).overall

    def test_discover_migrations_unchanged(self):
        versions = [migration.version for migration in discover_migrations()]
        assert versions == [1, 2, 3, 4]
        assert not list(
            (REPO_ROOT / "app" / "forge" / "persistence" / "sql").glob("005_*.sql")
        )

    def test_market_data_readiness_seam_unchanged(self):
        container = ForgeServiceContainer(config=ForgeConfig(environment="test"))
        deps = container.as_readiness_dependencies()
        assert deps["market_data"] == {
            "status": "NOT_CONFIGURED",
            "required": False,
            "note": "market-data providers belong to Book III; not wired at II.1",
        }
        # This bloc never imports the composition root (no silent rewiring).
        for name, source in _package_sources():
            assert "container" not in source, name

    def test_frozen_manifests_unchanged(self):
        # Book II: all 50 frozen contract hashes still bind the worktree.
        text = BOOK_II_FREEZE_MANIFEST.read_text(encoding="utf-8")
        entries = re.findall(r"`([^`\s]+)`\s+—\s+`([0-9a-f]{64})`", text)
        assert len(entries) == 50, len(entries)
        for rel_path, expected in entries:
            target = REPO_ROOT / rel_path
            assert target.exists(), rel_path
            raw = target.read_bytes()
            normalized = raw.replace(b"\r\n", b"\n")
            candidates = {
                hashlib.sha256(raw).hexdigest(),
                hashlib.sha256(normalized).hexdigest(),
                hashlib.sha256(normalized.replace(b"\n", b"\r\n")).hexdigest(),
            }
            assert expected in candidates, rel_path
        # Book I freeze manifest: committed content unchanged in the worktree.
        try:
            shown = subprocess.run(
                [
                    "git",
                    "show",
                    "HEAD:implementation/forge/book_i/bloc_i_5/BOOK_I_FREEZE_MANIFEST_V1.md",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
            )
        except OSError:
            pytest.skip("git unavailable")
        if shown.returncode == 0:
            head_bytes = shown.stdout.replace(b"\r\n", b"\n")
            work_bytes = BOOK_I_FREEZE_MANIFEST.read_bytes().replace(b"\r\n", b"\n")
            assert head_bytes == work_bytes

    def test_planning_pins_unchanged(self):
        text = PLANNING_FREEZE_MANIFEST.read_text(encoding="utf-8")
        pins = re.findall(
            r"^-\s+(\S+)\s*\r?\n\s+commit\s+([0-9a-f]{40})\s*$", text, re.MULTILINE
        )
        assert len(pins) == 23, len(pins)
        for rel_path, _sha in pins:
            assert (REPO_ROOT / rel_path).exists(), rel_path

        def _git(*args):
            return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True)

        try:
            available = sum(
                1
                for _path, sha in pins
                if _git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
            )
        except OSError:
            pytest.skip("git unavailable")
        if available == 0:
            pytest.skip("planning-pin commit objects unavailable (shallow clone)")
        assert available == len(pins)
        for rel_path, sha in pins:
            shown = _git("show", f"{sha}:{rel_path}")
            assert shown.returncode == 0, rel_path
            head_content = shown.stdout.replace(b"\r\n", b"\n")
            work_content = (REPO_ROOT / rel_path).read_bytes().replace(b"\r\n", b"\n")
            assert head_content == work_content, rel_path

    def test_no_credentials_in_data_path(self):
        secret_pattern = re.compile(
            r"(api[_-]?key\s*[:=]|secret[_-]?key\s*[:=]|password\s*[:=]|passwd"
            r"|bearer\s+[A-Za-z0-9._-]{8,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{16,})",
            re.IGNORECASE,
        )
        for name, source in _package_sources():
            assert not secret_pattern.search(source), name
        for path in sorted(FIXTURE_DIR.glob("*.json")):
            assert not secret_pattern.search(
                path.read_text(encoding="utf-8")
            ), path.name

    def test_deterministic_repeat_runs(self, alpha_feed, beta_feed, eur_ctx):
        for provider, fixture in (
            ("fake_alpha", alpha_feed),
            ("fake_beta", beta_feed),
        ):
            first = replay_historical(fixture["records"], provider, eur_ctx)
            second = replay_historical(fixture["records"], provider, eur_ctx)
            assert first.digest() == second.digest(), provider
            assert json.dumps(first.to_dict(), sort_keys=True) == json.dumps(
                second.to_dict(), sort_keys=True
            ), provider
        wall_clock = re.compile(
            r"(datetime\.now|utcnow|time\.time\s*\(|import random|from random)"
        )
        for name, source in _package_sources():
            assert not wall_clock.search(source), name
