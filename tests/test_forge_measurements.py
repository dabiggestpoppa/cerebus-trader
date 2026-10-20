"""Focused Bloc III.2 suite: Measurement & Feature Engine.

Binding specification: ``implementation/forge/book_iii/bloc_iii_2/
ACCEPTANCE.md`` — every frozen clause in §A–§P maps to a named test in
this file (the mapping may gain tests at implementation time, it may
never lose or weaken one).  Groups T1–T12 follow ``PLAN.md`` §8.

Discipline: deterministic, offline, network-free.  Inputs come only
from the committed fixtures under ``implementation/forge/book_iii/
bloc_iii_2/fixtures/`` (bar slices labeled ``SYNTHETIC_FIXTURE``,
canonical constant tables quoted as ``CANONICAL_SOURCE_SLICE``) and the
frozen III.1 market-data contracts.  No wall clock, no credentials, no
provider SDK, no corpus write, no migration.

Passing these fixture contract tests is **not** empirical
strategy-performance validation: every synthetic fixture is labeled at
creation and can never satisfy an evidence-reference check.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
import pkgutil
import re
import socket
import subprocess
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path

import pytest

import app.forge.measurements as measurements_pkg
from app.forge.market_data import (
    CLOCK_REGISTRY_VERSION,
    MARKET_DATA_SCHEMA_VERSION,
    SESSION_REGISTRY_VERSION,
    AssetClass,
    Bar,
    DataOutcome,
    Finality,
    Instrument,
    NativePrice,
    NativeUnit,
    ProvenanceKind,
    QualityFlag,
    QualityPolicy,
    ResearchDayLineage,
    ResearchDayRegistry,
    SessionRegistry,
    build_default_registry,
    content_digest,
    definitions_from_records,
    named_clock,
)
from app.forge.measurements import (
    ANCHOR_RULE_REGISTRY,
    CANONICAL_FAMILY_LEVELS,
    COORDINATE_SETS,
    DEFINITION_REGISTRY,
    EVENT_BUDGET_SOURCE,
    MEASUREMENT_ENGINE_VERSION,
    RATIO_QUANTUM,
    AcceptanceState,
    AnchorEligibility,
    AnchorRecord,
    AnchorRefusalCode,
    AnchorRule,
    AnchorStatus,
    AuScale,
    BreakoutReturnState,
    CalibrationKey,
    CalibrationStatus,
    CloseBeyondState,
    CoordinateFamily,
    CoordinateSet,
    DensityZone,
    D1D3State,
    ElapsedSinceEvent,
    EventBudget,
    EventFamily,
    EventFeatures,
    HigherOrderCheckpoint,
    HigherOrderLayer,
    HigherOrderState,
    LayerConflict,
    LayerConflictFact,
    LayerConflictKind,
    LevelOutcome,
    LevelSide,
    M1Scale,
    M2Shaping,
    Measurement,
    NativeMagnitude,
    NormalizedEvent,
    PathLevel,
    PathMeasurement,
    PeriodKind,
    Provenance,
    RangeDirection,
    RangeEdge,
    RangeMeasurement,
    ReEntryState,
    RejectionState,
    RemainingState,
    RuleMaterialization,
    SeedRange,
    SeedRangeKind,
    SessionPhaseState,
    SpatialBandState,
    TierBand,
    TierTable,
    TouchState,
    UnfinishedSideState,
    WeeklyOuterNode,
    WeeklyPath,
    add_magnitude,
    checkpoint_reached,
    classify_spatial_band,
    classify_tier,
    duration_seconds,
    elapsed_since,
    encode_value,
    evaluate_anchor,
    failure_age,
    measure_acceptance_duration,
    measure_au_scale,
    measure_density_zones,
    measure_d1d3_state,
    measure_event_budget,
    measure_event_features,
    measure_higher_order_checkpoint,
    measure_layer_conflict,
    measure_m1_scale,
    measure_m2_shaping,
    measure_path,
    measure_period_phase,
    measure_range,
    measure_seed_range,
    measure_session_phase,
    measure_threshold_levels,
    measure_unfinished_side,
    measure_weekly_path,
    project_coordinates,
    quantize_ratio,
    rekey_anchor,
    require_definition,
    source_window_from_bars,
    subtract_magnitude,
    time_to_delivery,
)
from app.forge.measurements.anchors import EARNED_STATES, PROJECTION_BLOCKING_STATES
from app.forge.measurements.contracts import decode_value, native_count, native_span
from app.forge.persistence.sql.migrations import discover_migrations
from app.forge.service.container import ForgeServiceContainer
from app.forge.config import ForgeConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = (
    REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_2" / "fixtures"
)
III1_FIXTURE_DIR = (
    REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_1" / "fixtures"
)
PACKAGE_DIR = REPO_ROOT / "app" / "forge" / "measurements"
III1_PACKAGE_DIR = REPO_ROOT / "app" / "forge" / "market_data"
BOOK_II_FREEZE_MANIFEST = (
    REPO_ROOT / "implementation" / "forge" / "book_ii" / "ratification"
    / "CONTRACT_FREEZE_MANIFEST_V1.md"
)
PLANNING_FREEZE_MANIFEST = REPO_ROOT / "planning" / "forge" / "PLANNING_FREEZE_MANIFEST_V1.md"
BOOK_I_FREEZE_MANIFEST = (
    REPO_ROOT / "implementation" / "forge" / "book_i" / "bloc_i_5"
    / "BOOK_I_FREEZE_MANIFEST_V1.md"
)
III2_PLAN = REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_2" / "PLAN.md"

#: Injected calculation timestamp — never a wall clock (I5/P7).
CALC_TS = "2026-03-03T09:00:00Z"

#: The frozen provenance-envelope field set (I1–I7).
ENV_FIELDS = frozenset(
    {
        "definition_id",
        "definition_version",
        "instrument_id",
        "source_window",
        "clock_id",
        "clock_registry_version",
        "session_id",
        "session_registry_version",
        "calculation_timestamp",
        "quality_state",
        "native_unit",
        "market_data_schema_version",
        "measurement_engine_version",
        "evidence_refs",
    }
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def _load(directory: Path, name: str) -> dict:
    return json.loads((directory / name).read_text(encoding="utf-8"))


def _load_iii2(name: str) -> dict:
    return _load(FIXTURE_DIR, name)


def _bar(
    instrument_id: str,
    o: str,
    h: str,
    l: str,
    c: str,
    *,
    start: datetime,
    minutes: int = 5,
    timeframe: str = "M5",
    flags: frozenset[QualityFlag] | None = None,
    finality: Finality = Finality.FINAL,
    provenance: ProvenanceKind = ProvenanceKind.SYNTHETIC_FIXTURE,
    source_ref: str | None = None,
) -> Bar:
    close_time = start + timedelta(minutes=minutes)
    return Bar(
        instrument_id=instrument_id,
        timeframe=timeframe,
        open_time=start,
        close_time=close_time,
        open=Decimal(o),
        high=Decimal(h),
        low=Decimal(l),
        close=Decimal(c),
        volume=Decimal(100),
        provider="synthetic",
        finality=finality,
        source_timestamp=close_time + timedelta(seconds=3),
        quality_flags=frozenset(flags or (QualityFlag.COMPLETE,)),
        provenance=provenance,
        source_ref=source_ref,
    )


def _ohlc_bars(
    instrument_id: str,
    rows: list[tuple[str, str, str, str]],
    start_iso: str,
    *,
    minutes: int = 5,
) -> list[Bar]:
    start = _utc(start_iso)
    return [
        _bar(
            instrument_id,
            o,
            h,
            l,
            c,
            start=start + timedelta(minutes=minutes * index),
            minutes=minutes,
        )
        for index, (o, h, l, c) in enumerate(rows)
    ]


def _bars_from_rows(rows: list[dict], instrument_id: str, timeframe: str = "M5") -> list[Bar]:
    """Build III.1 bars from committed fixture rows (synthetic, labeled)."""
    out: list[Bar] = []
    for row in rows:
        out.append(
            Bar(
                instrument_id=instrument_id,
                timeframe=timeframe,
                open_time=_utc(row["open_time"]),
                close_time=_utc(row["close_time"]),
                open=Decimal(row["o"]),
                high=Decimal(row["h"]),
                low=Decimal(row["l"]),
                close=Decimal(row["c"]),
                volume=Decimal(row["volume"]),
                provider="synthetic",
                finality=Finality.FINAL,
                source_timestamp=_utc(row["source_timestamp"]),
                quality_flags=frozenset({QualityFlag.COMPLETE}),
                provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
                source_ref=None,
            )
        )
    return out


def _prov(
    instrument_id: str = "EURUSD",
    session_id: str = "EUR_DAILY.ASIAN_RANGE",
    clock_id: str = "America/New_York",
    calc_ts: str = CALC_TS,
) -> Provenance:
    return Provenance(
        instrument_id=instrument_id,
        clock_id=clock_id,
        session_id=session_id,
        calculation_timestamp=_utc(calc_ts),
    )


def _policy() -> QualityPolicy:
    return QualityPolicy.from_strings(
        "EUR.DAILY.NEWS_REKEY.V1",
        "PHASE1",
        blocking=["GAP", "STALE", "OUTLIER_SOURCE", "UNSUPPORTED_CLOCK"],
        warning=["DUPLICATE", "REVISED", "NONFINAL"],
    )


def _session_registry() -> SessionRegistry:
    fixture = _load(III1_FIXTURE_DIR, "sessions_canonical.json")
    clocks = {"America/New_York": named_clock("America/New_York")}
    registry = SessionRegistry()
    registry.add_all(definitions_from_records(fixture["definitions"], clocks))
    return registry


def _lineage_registry() -> ResearchDayRegistry:
    fixture = _load(III1_FIXTURE_DIR, "sessions_canonical.json")
    clock = named_clock("America/New_York")
    registry = ResearchDayRegistry()
    for record in fixture["research_day_lineages"]:
        boundary = record.get("evening_shift_boundary")
        registry.register(
            ResearchDayLineage(
                lineage_id=record["lineage_id"],
                model_id=record["model_id"],
                model_version=record["model_version"],
                clock=clock,
                evening_shift_boundary=(
                    time.fromisoformat(boundary) if boundary else None
                ),
                source_ref=record["source_ref"],
            )
        )
    return registry


def _package_sources() -> list[tuple[str, str]]:
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in sorted(PACKAGE_DIR.glob("*.py"))
    ]


def _package_modules() -> list:
    modules = [measurements_pkg]
    for info in pkgutil.iter_modules(measurements_pkg.__path__):
        modules.append(
            importlib.import_module(f"app.forge.measurements.{info.name}")
        )
    return modules


def _tokens(identifier: str) -> set[str]:
    """Word tokens of an identifier (snake and camel case aware)."""
    camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", identifier)
    return {part.lower() for part in re.split(r"[_\W]+", camel) if part}


def _dataclass_field_names(obj) -> set[str]:
    return {item.name for item in fields(obj)}


def _usdjpy() -> Instrument:
    """A JPY-declared instrument (the default registry holds no JPY pair)."""
    return Instrument(
        instrument_id="USDJPY",
        symbol="USD/JPY",
        asset_class=AssetClass.FX,
        base_currency="USD",
        quote_currency="JPY",
        native_unit=NativeUnit.PIP,
        price_precision=3,
        supported_timeframes=frozenset({"M5", "M15", "H1", "D1"}),
        supported_clocks=frozenset({"America/New_York"}),
        pip_size=Decimal("0.01"),
    )


@pytest.fixture(scope="module")
def env() -> dict:
    """Module-scope environment: registries, policy and committed fixtures."""
    return {
        "registry": build_default_registry(),
        "policy": _policy(),
        "sessions": _session_registry(),
        "lineages": _lineage_registry(),
        "eur": _load_iii2("eur_daily_tier_seeds.json"),
        "ladder": _load_iii2("eur_rekey_ladder.json"),
        "events": _load_iii2("eur_event_budget.json"),
        "weekly": _load_iii2("eur_weekly_outer_nodes.json"),
        "ho": _load_iii2("eur_higher_order.json"),
        "xau": _load_iii2("xau_spatial_bands.json"),
        "btc": _load_iii2("btc_tier_seeds.json"),
        "jpy": _load_iii2("jpy_dt_structures.json"),
        "fib": _load_iii2("fib_anchor_cases.json"),
    }


def _seed(env: dict, fixture: str, case_id: str) -> dict:
    for seed in env[fixture]["seeds"]:
        if seed["case_id"] == case_id:
            return seed
    raise AssertionError(f"fixture case {case_id} not found")


def _measure_seed_range(env: dict, fixture: str, case_id: str) -> RangeMeasurement:
    data = env[fixture]
    seed = _seed(env, fixture, case_id)
    bars = _bars_from_rows(seed["rows"], data["instrument_id"], data["timeframe"])
    return measure_range(
        bars,
        instrument=env["registry"].get(data["instrument_id"]),
        provenance=_prov(
            data["instrument_id"], data["session_id"], data["clock"]
        ),
        observation_cutoff=_utc(data["observation_cutoff"]),
        quality_policy=env["policy"],
    )


def _active_anchor(env: dict, range_measurement: RangeMeasurement) -> AnchorRecord:
    rule = AnchorRule(
        rule_id="R15.RANGE_BIRTH",
        rule_version="DECLARED",
        materialization=RuleMaterialization.DECLARED,
        source_ref=env["fib"]["source_ref"],
    )
    return AnchorRecord(
        anchor_id="FIB.ANCHOR.ACTIVE.01",
        model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
        model_version="R15",
        status=AnchorStatus.ACTIVE,
        rule=rule,
        earned_range=range_measurement,
    )


def _path_fixture_bars() -> list[Bar]:
    """A four-bar path used by the T6 path-distinction tests."""
    return _ohlc_bars(
        "EURUSD",
        [
            ("1.08000", "1.08100", "1.07950", "1.08050"),
            ("1.08050", "1.08250", "1.08000", "1.08200"),
            ("1.08200", "1.08300", "1.07980", "1.08000"),
            ("1.08000", "1.08400", "1.07990", "1.08350"),
        ],
        "2026-03-03T01:00:00Z",
    )


def _level(price: str, level_id: str, side: LevelSide) -> PathLevel:
    return PathLevel(
        level_id=level_id,
        price=NativePrice("EURUSD", NativeUnit.PIP, Decimal(price)),
        side=side,
    )


def _measure_path(env: dict, bars: list[Bar], levels, **kwargs) -> PathMeasurement:
    return measure_path(
        bars,
        instrument=env["registry"].get("EURUSD"),
        provenance=_prov("EURUSD", "EUR_DAILY.ASIAN_RANGE"),
        observation_cutoff=_utc("2026-03-03T09:00:00Z"),
        quality_policy=env["policy"],
        levels=levels,
        **kwargs,
    )


def _event_from_fixture(env: dict, index: int) -> NormalizedEvent:
    record = env["events"]["events"][index]
    instrument_id = env["events"]["instrument_id"]
    unit = NativeUnit(env["events"]["unit"].upper())
    lower = upper = size = None
    if record["historical_band_lower"] is not None:
        lower = NativeMagnitude(
            instrument_id, unit, Decimal(record["historical_band_lower"])
        )
        upper = NativeMagnitude(
            instrument_id, unit, Decimal(record["historical_band_upper"])
        )
    if record["historical_size"] is not None:
        size = NativeMagnitude(instrument_id, unit, Decimal(record["historical_size"]))
    return NormalizedEvent(
        event_id=record["event_id"],
        family=EventFamily(record["family"]),
        relevance_currencies=frozenset(record["relevance_currencies"]),
        relevance_assets=frozenset(record["relevance_assets"]),
        scheduled_time=_utc(record["scheduled_time"]),
        actual_time=(
            _utc(record["actual_time"]) if record["actual_time"] else None
        ),
        source_ref=record["source_ref"],
        provenance_label=record["provenance_label"],
        historical_band_lower=lower,
        historical_band_upper=upper,
        historical_size=size,
    )


def _weekly_nodes_from_registry(env: dict) -> list[WeeklyOuterNode]:
    key = CalibrationKey(**env["weekly"]["calibration_key"])
    table = measurements_pkg.CALIBRATION_REGISTRY.weekly_outer_nodes(key)
    nodes: list[WeeklyOuterNode] = []
    for index, (tier_id, magnitude, sample_n) in enumerate(table.outer_nodes):
        nodes.append(
            WeeklyOuterNode(
                node_id=f"EUR_WEEKLY_{tier_id}",
                order_index=index,
                magnitude=NativeMagnitude(table.instrument_id, table.unit, magnitude),
                sample_n=sample_n,
                source_ref=table.source_ref,
                calibration_status=table.status,
            )
        )
    return nodes


def _golden_samples(env: dict) -> dict[str, object]:
    """One representative measurement per emitted definition family (T9/T11/P7)."""
    registry = env["registry"]
    policy = env["policy"]
    samples: dict[str, object] = {}

    prov_eur = _prov("EURUSD", "EUR_DAILY.ASIAN_RANGE")
    calib = measurements_pkg.CALIBRATION_REGISTRY
    rng_t2 = _measure_seed_range(env, "eur", "EUR_SEED_T2")
    samples["range"] = rng_t2
    samples["tier"] = classify_tier(
        calib,
        CalibrationKey(**env["eur"]["calibration_key"]),
        rng_t2.size,
        provenance=prov_eur,
        source_window=rng_t2.source_window,
    )

    # Coordinates + anchors (FIB model, declared R15 rule).
    fib_anchor = _active_anchor(env, rng_t2)
    samples["coordinate"] = project_coordinates(
        fib_anchor, "FIB_132", provenance=prov_eur
    )
    samples["anchor_eligibility"] = evaluate_anchor(fib_anchor, provenance=prov_eur)
    samples["anchor_rekey"] = rekey_anchor(
        fib_anchor,
        "FIB.ANCHOR.REKEYED.02",
        mapping={"FIB_132": "EUR_DAILY_132"},
        provenance=prov_eur,
    )

    # Clock / state age.
    samples["elapsed"] = elapsed_since(
        _utc("2026-03-03T08:00:00Z"),
        _utc("2026-03-03T08:02:30Z"),
        provenance=prov_eur,
    )
    samples["checkpoint"] = checkpoint_reached(
        _utc("2026-03-03T12:00:00Z"),
        _utc("2026-03-03T12:05:00Z"),
        provenance=prov_eur,
    )
    samples["acceptance_duration"] = measure_acceptance_duration(
        _utc("2026-03-03T08:00:00Z"),
        _utc("2026-03-03T08:00:45Z"),
        provenance=prov_eur,
    )
    samples["failure_age"] = failure_age(
        _utc("2026-03-03T07:00:00Z"),
        _utc("2026-03-03T07:03:20Z"),
        provenance=prov_eur,
    )
    samples["time_to_delivery"] = time_to_delivery(
        _utc("2026-03-03T17:00:00Z"),
        _utc("2026-03-03T16:30:00Z"),
        provenance=prov_eur,
    )
    samples["session_phase"] = measure_session_phase(
        env["sessions"],
        "EUR.DAILY.NEWS_REKEY.V1",
        "PHASE1",
        "EUR_DAILY.ASIAN_RANGE",
        _utc("2026-03-03T02:00:00Z"),
        provenance=prov_eur,
    )
    samples["period_phase"] = measure_period_phase(
        env["lineages"],
        "EUR_DAILY_LINEAGE",
        "EURUSD",
        _utc("2026-03-03T20:00:00Z"),
        PeriodKind.WEEK,
        provenance=prov_eur,
    )

    # Path.
    path_bars = _path_fixture_bars()
    samples["path"] = _measure_path(
        env,
        path_bars,
        [_level("1.08100", "TARGET", LevelSide.ABOVE)],
    )

    # Calibration outputs (BTC native + XAU spatial).
    prov_btc = _prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW")
    btc_key = CalibrationKey(**env["btc"]["calibration_key"])
    samples["au"] = measure_au_scale(
        calib, btc_key, "T2", provenance=prov_btc, source_window=rng_t2.source_window
    )
    samples["thresholds"] = measure_threshold_levels(
        calib, btc_key, provenance=prov_btc, source_window=rng_t2.source_window
    )
    samples["density"] = measure_density_zones(
        calib, btc_key, provenance=prov_btc, source_window=rng_t2.source_window
    )
    prov_xau = _prov("XAUUSD", "XAU_GAME.ASIAN_RANGE")
    samples["spatial"] = classify_spatial_band(
        calib,
        CalibrationKey(**env["xau"]["calibration_key"]),
        NativeMagnitude("XAUUSD", NativeUnit.POINT, Decimal("30")),
        provenance=prov_xau,
        source_window=rng_t2.source_window,
    )

    # Higher order.
    quarter = _ho_seed(env, "QUARTER")
    samples["seed"] = quarter
    samples["d1d3"] = measure_d1d3_state(
        quarter_seed=quarter,
        d1=_ho_seed(env, "D1"),
        d2=None,
        d3=None,
        provenance=prov_eur,
        source_window=quarter.source_window,
    )
    samples["m1"] = measure_m1_scale(
        m1_seed=_ho_seed(env, "M1"),
        provenance=prov_eur,
        source_window=quarter.source_window,
    )
    samples["m2"] = measure_m2_shaping(
        m2_seed=None,
        provenance=prov_eur,
        source_window=quarter.source_window,
    )
    samples["unfinished"] = measure_unfinished_side(
        side=UnfinishedSideState.UPPER,
        provenance=prov_eur,
        source_window=quarter.source_window,
    )
    samples["weekly_path"] = measure_weekly_path(
        weekly_seed=None,
        nodes=_weekly_nodes_from_registry(env),
        provenance=prov_eur,
        source_window=quarter.source_window,
    )
    samples["ho_checkpoint"] = measure_higher_order_checkpoint(
        checkpoint_id="HO.M3.RESOLUTION",
        scheduled_instant=_utc("2026-01-08T00:00:00Z"),
        observed_instant=_utc("2026-01-08T00:10:00Z"),
        source_ref=env["ho"]["source_ref"],
        provenance=prov_eur,
    )
    samples["layer_conflict"] = measure_layer_conflict(
        conflicts=[
            LayerConflictFact(
                layer_a=HigherOrderLayer.MONTH_1,
                layer_b=HigherOrderLayer.WEEK,
                kind=LayerConflictKind.DIRECTION_DISAGREEMENT,
            )
        ],
        provenance=prov_eur,
        source_window=quarter.source_window,
    )

    # Events.
    event = _event_from_fixture(env, 0)
    samples["event_features"] = measure_event_features(
        event, provenance=prov_eur, source_window=None
    )
    samples["event_budget"] = measure_event_budget(
        event,
        NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("6")),
        provenance=prov_eur,
    )
    return samples


def _ho_seed(env: dict, seed_id: str) -> SeedRange:
    data = env["ho"]
    for seed in data["seeds"]:
        if seed["seed_id"] == seed_id:
            bars = _bars_from_rows(seed["rows"], data["instrument_id"])
            kind = SeedRangeKind(seed["seed_kind"])
            return measure_seed_range(
                bars,
                seed_kind=kind,
                instrument=env["registry"].get(data["instrument_id"]),
                provenance=_prov(
                    data["instrument_id"], data["session_id"], data["clock"]
                ),
                observation_cutoff=_utc(seed["observation_cutoff"]),
                quality_policy=env["policy"],
            )
    raise AssertionError(f"higher-order seed {seed_id} not found")


def _golden_pipeline(env: dict) -> str:
    """A full deterministic measurement pass used for replay comparison (P7)."""
    samples = _golden_samples(env)
    payload = {name: encode_value(sample) for name, sample in sorted(samples.items())}
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# T1 — Range engine (A1–A7, M1, N9)
# ---------------------------------------------------------------------------


class TestT1RangeEngine:
    def test_range_measurement_frozen_fields(self, env):
        """A1: exactly the frozen field set plus the provenance envelope."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        frozen = {
            "high",
            "low",
            "size",
            "midpoint",
            "direction",
            "close_location",
            "consumed_fraction",
            "range_left",
            "breakout_return_state",
        }
        assert {item.name for item in fields(RangeMeasurement)} == ENV_FIELDS | frozen
        assert RangeMeasurement.__dataclass_params__.frozen is True
        # Every frozen field is populated with the declared type.
        assert isinstance(measured.direction, RangeDirection)
        assert isinstance(measured.breakout_return_state, BreakoutReturnState)
        assert measured.high.instrument_id == "EURUSD"
        assert measured.low.value <= measured.high.value

    def test_range_size_midpoint_native_units(self, env):
        """A2: Decimal asset-native arithmetic; cross-unit math refuses."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        assert isinstance(measured.size, NativeMagnitude)
        assert measured.size.unit is NativeUnit.PIP
        assert measured.size.instrument_id == "EURUSD"
        assert measured.size.value == Decimal("25.0")
        assert isinstance(measured.midpoint, NativePrice)
        assert measured.midpoint.value == (measured.high.value + measured.low.value) / 2
        for value in (
            measured.high.value,
            measured.low.value,
            measured.midpoint.value,
            measured.close_location,
            measured.consumed_fraction,
            measured.size.value,
            measured.range_left.value,
        ):
            assert isinstance(value, Decimal)
        # A pip count and a dollar count are different domains (III.1
        # convert_native is the only cross-unit authority; none exists here).
        eur_pips = NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("25"))
        btc_dollars = NativeMagnitude("BTCUSD", NativeUnit.DOLLAR, Decimal("25"))
        with pytest.raises(Exception) as excinfo:
            add_magnitude(eur_pips, btc_dollars)
        assert getattr(excinfo.value, "code", None) == "UNIT_DOMAIN"

    def test_close_location_and_direction(self, env):
        """A3: direction and close location are typed facts from the bars."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        bars = _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        origin = bars[0].open
        last_close = bars[-1].close
        expected = (
            RangeDirection.UP
            if last_close > origin
            else RangeDirection.DOWN
            if last_close < origin
            else RangeDirection.FLAT
        )
        assert measured.direction is expected
        span = measured.high.value - measured.low.value
        assert measured.close_location == quantize_ratio(
            (last_close - measured.low.value) / span
        )
        assert Decimal(0) <= measured.close_location <= Decimal(1)
        # Down and flat ranges are measured the same way.
        down_bars = _ohlc_bars(
            "EURUSD",
            [
                ("1.08000", "1.08010", "1.07950", "1.07970"),
                ("1.07970", "1.07980", "1.07900", "1.07920"),
            ],
            "2026-03-03T02:00:00Z",
        )
        down = measure_range(
            down_bars,
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(),
            observation_cutoff=_utc("2026-03-03T09:00:00Z"),
            quality_policy=env["policy"],
        )
        assert down.direction is RangeDirection.DOWN
        flat_bars = _ohlc_bars(
            "EURUSD",
            [("1.08000", "1.08010", "1.07990", "1.08000")],
            "2026-03-03T02:00:00Z",
        )
        flat = measure_range(
            flat_bars,
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(),
            observation_cutoff=_utc("2026-03-03T09:00:00Z"),
            quality_policy=env["policy"],
        )
        assert flat.direction is RangeDirection.FLAT
        assert flat.consumed_fraction == Decimal(0)

    def test_consumed_fraction_bounds(self, env):
        """A4: bounded and explicit; an unresolvable range refuses."""
        for fixture, case_ids in (
            ("eur", ["EUR_SEED_T1", "EUR_SEED_T2", "EUR_SEED_T3", "EUR_SEED_NO_GO"]),
            ("btc", ["BTC_SEED_T1", "BTC_SEED_T2", "BTC_SEED_T3", "BTC_SEED_NO_GO"]),
        ):
            for case_id in case_ids:
                measured = _measure_seed_range(env, fixture, case_id)
                assert Decimal(0) <= measured.consumed_fraction <= Decimal(1), case_id
                assert measured.range_left.value >= 0, case_id
        # A zero-size window is unresolvable — explicit refusal, no default.
        degenerate = _ohlc_bars(
            "EURUSD",
            [("1.08000", "1.08000", "1.08000", "1.08000")],
            "2026-03-03T02:00:00Z",
        )
        with pytest.raises(Exception) as excinfo:
            measure_range(
                degenerate,
                instrument=env["registry"].get("EURUSD"),
                provenance=_prov(),
                observation_cutoff=_utc("2026-03-03T09:00:00Z"),
                quality_policy=env["policy"],
            )
        assert getattr(excinfo.value, "code", None) == "RANGE_NOT_RESOLVABLE"

    def test_range_left_remaining_never_invented(self, env):
        """A5: range-left is measured from the window, never synthesized."""
        for fixture, case_ids in (
            ("eur", ["EUR_SEED_T1", "EUR_SEED_T2", "EUR_SEED_T3", "EUR_SEED_NO_GO"]),
            ("btc", ["BTC_SEED_T1", "BTC_SEED_T2", "BTC_SEED_T3", "BTC_SEED_NO_GO"]),
        ):
            for case_id in case_ids:
                measured = _measure_seed_range(env, fixture, case_id)
                seed = _seed(env, fixture, case_id)
                bars = _bars_from_rows(
                    seed["rows"], env[fixture]["instrument_id"], env[fixture]["timeframe"]
                )
                origin = bars[0].open
                last_close = bars[-1].close
                span = measured.high.value - measured.low.value
                consumed = min(
                    max(abs(last_close - origin), Decimal(0)), span
                )
                expected_consumed = native_span(
                    env[fixture]["instrument_id"],
                    measured.size.unit,
                    env["registry"].get(env[fixture]["instrument_id"]).native_step,
                    Decimal(0),
                    consumed,
                )
                # size == consumed + remaining, exactly and in native units.
                assert (
                    measured.size.value
                    == expected_consumed.value + measured.range_left.value
                ), case_id
                assert measured.range_left.value <= measured.size.value, case_id
        # The fixture expectation is reproduced, not defaulted.
        assert (
            _measure_seed_range(env, "eur", "EUR_SEED_T2").range_left.value
            == Decimal(_seed(env, "eur", "EUR_SEED_T2")["expected"]["range_left_native"])
        )

    def test_range_left_updates_after_consumption(self, env):
        """A5/N9: remaining movement updates explicitly as states consume."""
        # Both windows share identical extremes (high/low); only the last
        # close advances, so range-left can only fall through consumption.
        rows = [
            ("1.07900", "1.07960", "1.07900", "1.07950"),
            ("1.07950", "1.07990", "1.07940", "1.07950"),
            ("1.07950", "1.07975", "1.07945", "1.07970"),
            ("1.07970", "1.07990", "1.07960", "1.07990"),
        ]
        bars = _ohlc_bars("EURUSD", rows, "2026-03-03T03:00:00Z")

        def measure(window):
            return measure_range(
                window,
                instrument=env["registry"].get("EURUSD"),
                provenance=_prov(),
                observation_cutoff=_utc("2026-03-03T09:00:00Z"),
                quality_policy=env["policy"],
            )

        early = measure(bars[:2])
        late = measure(bars)
        # Identical extremes: the range itself did not move.
        assert early.high == late.high and early.low == late.low
        assert early.size == late.size
        # Consumption advanced, so the remaining movement shrank.
        assert late.consumed_fraction > early.consumed_fraction
        assert late.range_left.value < early.range_left.value
        # And the fixture golden value is what the engine reports.
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T1")
        assert measured.range_left.value == Decimal(
            _seed(env, "eur", "EUR_SEED_T1")["expected"]["range_left_native"]
        )

    def test_breakout_return_state_explicit(self, env):
        """A6: an explicit enum value; no silent or default state."""
        establishing = [
            ("1.07900", "1.07980", "1.07890", "1.07950"),
            ("1.07950", "1.08000", "1.07940", "1.07990"),
        ]
        establish_until = (
            _utc("2026-03-03T03:10:00Z")
        )  # close of the second establishing bar
        cases = {
            "INSIDE_RANGE": [("1.07990", "1.08000", "1.07970", "1.07980")],
            "BREAKOUT_ABOVE": [("1.07990", "1.08060", "1.07985", "1.08050")],
            "BREAKOUT_BELOW": [("1.07960", "1.07970", "1.07840", "1.07850")],
            "RETURNED_INSIDE": [
                ("1.07990", "1.08060", "1.07985", "1.08050"),
                ("1.08050", "1.08060", "1.07950", "1.07970"),
            ],
        }
        for expected, following in cases.items():
            bars = _ohlc_bars(
                "EURUSD",
                establishing + following,
                "2026-03-03T03:00:00Z",
            )
            measured = measure_range(
                bars,
                instrument=env["registry"].get("EURUSD"),
                provenance=_prov(),
                observation_cutoff=_utc("2026-03-03T09:00:00Z"),
                quality_policy=env["policy"],
                establish_until=establish_until,
            )
            assert measured.breakout_return_state.value == expected
            assert isinstance(measured.breakout_return_state, BreakoutReturnState)
        # With no establishment split a breakout cannot be measured.
        bars = _ohlc_bars("EURUSD", establishing, "2026-03-03T03:00:00Z")
        measured = measure_range(
            bars,
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(),
            observation_cutoff=_utc("2026-03-03T09:00:00Z"),
            quality_policy=env["policy"],
        )
        assert measured.breakout_return_state is BreakoutReturnState.INSIDE_RANGE

    def test_range_input_quality_blocked(self, env):
        """A7/M1: incomplete input blocks or degrades via III.1 policy."""
        good = _ohlc_bars(
            "EURUSD",
            [("1.07900", "1.07980", "1.07890", "1.07950")],
            "2026-03-03T03:00:00Z",
        )
        # A blocking flag (STALE) refuses with DATA_QUALITY_BLOCKED.
        stale = [
            _bar(
                "EURUSD",
                "1.07900",
                "1.07980",
                "1.07890",
                "1.07950",
                start=_utc("2026-03-03T03:00:00Z"),
                flags=frozenset({QualityFlag.STALE}),
            )
        ]
        with pytest.raises(Exception) as excinfo:
            measure_range(
                stale,
                instrument=env["registry"].get("EURUSD"),
                provenance=_prov(),
                observation_cutoff=_utc("2026-03-03T09:00:00Z"),
                quality_policy=env["policy"],
            )
        assert getattr(excinfo.value, "code", None) == "DATA_QUALITY_BLOCKED"
        # A missing expected open (GAP) blocks the same way.
        with pytest.raises(Exception) as excinfo:
            measure_range(
                good,
                instrument=env["registry"].get("EURUSD"),
                provenance=_prov(),
                observation_cutoff=_utc("2026-03-03T09:00:00Z"),
                quality_policy=env["policy"],
                expected_opens=(
                    _utc("2026-03-03T02:55:00Z"),
                    _utc("2026-03-03T03:00:00Z"),
                ),
            )
        assert getattr(excinfo.value, "code", None) == "DATA_QUALITY_BLOCKED"
        # No finalized bar at the cutoff blocks — never a fabricated range.
        future = _ohlc_bars(
            "EURUSD",
            [("1.07900", "1.07980", "1.07890", "1.07950")],
            "2026-03-03T23:00:00Z",
        )
        with pytest.raises(Exception) as excinfo:
            measure_range(
                future,
                instrument=env["registry"].get("EURUSD"),
                provenance=_prov(),
                observation_cutoff=_utc("2026-03-03T09:00:00Z"),
                quality_policy=env["policy"],
            )
        assert getattr(excinfo.value, "code", None) == "DATA_QUALITY_BLOCKED"
        # A model-declared warning flag degrades (disclosed), never fabricates.
        revised = [
            _bar(
                "EURUSD",
                "1.07900",
                "1.07980",
                "1.07890",
                "1.07950",
                start=_utc("2026-03-03T03:00:00Z"),
                flags=frozenset({QualityFlag.REVISED}),
            )
        ]
        degraded = measure_range(
            revised,
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(),
            observation_cutoff=_utc("2026-03-03T09:00:00Z"),
            quality_policy=env["policy"],
        )
        assert degraded.quality_state is DataOutcome.DEGRADED


# ---------------------------------------------------------------------------
# T2 — Tier / AU calibration (B1–B9, M4, N1, N3)
# ---------------------------------------------------------------------------


class TestT2Calibration:
    def test_tier_table_keyed_by_model_and_version(self, env):
        """B1: any wrong or missing key part refuses."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        good = CalibrationKey(**env["eur"]["calibration_key"])
        assert calib.tier_table(good).instrument_id == "EURUSD"
        mutations = {
            "model_id": "OTHER.MODEL.V1",
            "model_version": "V99",
            "calibration_id": "OTHER_CALIBRATION",
            "calibration_version": "V99",
        }
        for field_name, wrong in mutations.items():
            data = good.to_dict()
            data[field_name] = wrong
            with pytest.raises(Exception) as excinfo:
                calib.tier_table(CalibrationKey(**data))
            assert getattr(excinfo.value, "code", None) == "MODEL_VERSION_UNAVAILABLE"

    def test_eur_daily_phase1_tiers_reproduce(self, env):
        """B2: T1 <20p, T2 20–30p, T3 30–45p, >45p no-go, each edge."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        key = CalibrationKey(**env["eur"]["calibration_key"])
        prov = _prov()
        window = source_window_from_bars(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        )
        edges = [
            ("0", "T1", False),
            ("19.999", "T1", False),
            ("20", "T2", False),
            ("29.999", "T2", False),
            ("30", "T3", False),
            ("44.999", "T3", False),
            ("45", "T3", False),
            ("45.001", "NO_GO", True),
            ("120", "NO_GO", True),
        ]
        for value, tier_id, no_go in edges:
            classification = classify_tier(
                calib,
                key,
                NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal(value)),
                provenance=prov,
                source_window=window,
            )
            assert classification.tier_id == tier_id, value
            assert classification.no_go is no_go, value
            assert classification.evidence_refs == (
                "EV.EUR.DAILY.PHASE1_TIERS.V1",
            ), value
        assert (
            classification.calibration_status is CalibrationStatus.FROZEN_LAUNCH
        )

    def test_btc_native_tiers_reproduce(self, env):
        """B3: BTC native boundaries, AU, thresholds and density zones."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        key = CalibrationKey(**env["btc"]["calibration_key"])
        prov = _prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW")
        window = source_window_from_bars(
            _bars_from_rows(_seed(env, "btc", "BTC_SEED_T1")["rows"], "BTCUSD")
        )
        edges = [
            ("0", "T1", False),
            ("749.99", "T1", False),
            ("750", "T2", False),
            ("1699.99", "T2", False),
            ("1700", "T3", False),
            ("3000", "T3", False),
            ("3000.01", "NO_GO", True),
        ]
        for value, tier_id, no_go in edges:
            classification = classify_tier(
                calib,
                key,
                NativeMagnitude("BTCUSD", NativeUnit.DOLLAR, Decimal(value)),
                provenance=prov,
                source_window=window,
            )
            assert classification.tier_id == tier_id, value
            assert classification.no_go is no_go, value
            assert classification.evidence_refs == ("BTC.TRACKER.DWM.V1",), value
        # AU 205/545/1160 as dollar counts.
        for tier_id, value in (("T1", "205"), ("T2", "545"), ("T3", "1160")):
            au = measure_au_scale(
                calib, key, tier_id, provenance=prov, source_window=window
            )
            assert au.au.value == Decimal(value)
            assert au.au.unit is NativeUnit.DOLLAR
        # trigger_levels 246/654/1392 — canonical name preserved as threshold.
        thresholds = measure_threshold_levels(
            calib, key, provenance=prov, source_window=window
        )
        assert [item.value for item in thresholds.levels] == [
            Decimal("246"),
            Decimal("654"),
            Decimal("1392"),
        ]
        # Density zones 164–246 / 436–654 / 928–1392.
        zones = measure_density_zones(calib, key, provenance=prov, source_window=window)
        assert [(z.lower, z.upper) for z in zones.zones] == [
            (Decimal("164"), Decimal("246")),
            (Decimal("436"), Decimal("654")),
            (Decimal("928"), Decimal("1392")),
        ]
        # The committed fixture agrees with the canonical registry.
        fixture_au = {row["tier_id"]: row["au"] for row in env["btc"]["au_values"]}
        assert fixture_au == {"T1": "205", "T2": "545", "T3": "1160"}

    def test_au_scale_native_atomic_distance(self, env):
        """B4: AU is the asset-native atomic distance of one calibration."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        key = CalibrationKey(**env["btc"]["calibration_key"])
        au = measure_au_scale(
            calib,
            key,
            "T3",
            provenance=_prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW"),
            source_window=source_window_from_bars(
                _bars_from_rows(_seed(env, "btc", "BTC_SEED_T1")["rows"], "BTCUSD")
            ),
        )
        # One BTC AU counts whole dollars: BTC's native step is 1 dollar.
        btc = env["registry"].get("BTCUSD")
        assert btc.native_step == Decimal("1")
        assert au.au.instrument_id == "BTCUSD"
        assert au.au.unit is NativeUnit.DOLLAR
        assert au.au.value == Decimal("1160")
        # No universal AU: the EUR calibration publishes no AU scale at all.
        eur_key = CalibrationKey(**env["eur"]["calibration_key"])
        with pytest.raises(Exception) as excinfo:
            calib.au_scale(eur_key)
        assert getattr(excinfo.value, "code", None) == "MODEL_VERSION_UNAVAILABLE"

    def test_no_global_tier_constant(self, env):
        """B5: no universal tier constant exists anywhere in the package."""
        banned = re.compile(
            r"(?i)\b(universal|global|shared|common|default)_tier\b"
            r"|\bTIER_UNIVERSAL\b|\bGLOBAL_TIERS\b"
        )
        for name, source in _package_sources():
            assert not banned.search(source), name
        # Every registered tier table binds exactly one instrument and unit.
        calib = measurements_pkg.CALIBRATION_REGISTRY
        seen: list[tuple[str, str, str]] = []
        for key in calib.keys():
            try:
                table = calib.tier_table(key)
            except Exception:
                continue
            seen.append((table.instrument_id, table.unit.value, table.source_ref))
            assert table.key.model_id and table.key.model_version
        assert len(seen) >= 2  # EUR and BTC tables, each asset-local
        instruments = {instrument for instrument, _unit, _ref in seen}
        assert instruments == {"EURUSD", "BTCUSD"}
        # Classification always requires an explicit four-part key.
        signature = inspect.signature(classify_tier)
        assert signature.parameters["key"].default is inspect.Parameter.empty
        assert signature.parameters["registry"].default is inspect.Parameter.empty

    def test_cross_asset_tier_transfer_refuses(self, env):
        """B5/N1: calibration is local unless transfer is validated."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        eur_key = CalibrationKey(**env["eur"]["calibration_key"])
        btc_key = CalibrationKey(**env["btc"]["calibration_key"])
        prov = _prov()
        window = source_window_from_bars(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        )
        with pytest.raises(Exception) as excinfo:
            classify_tier(
                calib,
                btc_key,
                NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("25")),
                provenance=prov,
                source_window=window,
            )
        assert getattr(excinfo.value, "code", None) == "CALIBRATION_TRANSFER_REFUSED"
        with pytest.raises(Exception) as excinfo:
            classify_tier(
                calib,
                eur_key,
                NativeMagnitude("BTCUSD", NativeUnit.DOLLAR, Decimal("25")),
                provenance=prov,
                source_window=window,
            )
        assert getattr(excinfo.value, "code", None) == "CALIBRATION_TRANSFER_REFUSED"
        # Same instrument id, foreign unit: also refused (unit is a domain).
        with pytest.raises(Exception) as excinfo:
            classify_tier(
                calib,
                eur_key,
                NativeMagnitude("EURUSD", NativeUnit.DOLLAR, Decimal("25")),
                provenance=prov,
                source_window=window,
            )
        assert getattr(excinfo.value, "code", None) == "CALIBRATION_TRANSFER_REFUSED"

    def test_research_calibration_status_labeled(self, env):
        """B6: RESEARCH travels with every output; FROZEN_LAUNCH stays fixed."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        prov = _prov()
        window = source_window_from_bars(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        )
        frozen = classify_tier(
            calib,
            CalibrationKey(**env["eur"]["calibration_key"]),
            NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("25")),
            provenance=prov,
            source_window=window,
        )
        assert frozen.calibration_status is CalibrationStatus.FROZEN_LAUNCH
        xau = classify_spatial_band(
            calib,
            CalibrationKey(**env["xau"]["calibration_key"]),
            NativeMagnitude("XAUUSD", NativeUnit.POINT, Decimal("30")),
            provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
            source_window=window,
        )
        assert xau.calibration_status is CalibrationStatus.RESEARCH
        weekly_key = CalibrationKey(**env["weekly"]["calibration_key"])
        table = calib.weekly_outer_nodes(weekly_key)
        assert table.status is CalibrationStatus.RESEARCH
        weekly_path = measure_weekly_path(
            weekly_seed=None,
            nodes=_weekly_nodes_from_registry(env),
            provenance=prov,
            source_window=window,
        )
        assert weekly_path.calibration_status is CalibrationStatus.RESEARCH
        # The vocabulary is bounded and no promotion API exists.
        assert {member.value for member in CalibrationStatus} == {
            "FROZEN_LAUNCH",
            "RESEARCH",
        }
        for attribute in ("promote", "set_status", "update_status", "reclassify"):
            assert not hasattr(calib, attribute)

    def test_tier_is_compression_not_force(self, env):
        """B7/N3: a tier compresses continuous behavior; no force field."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        classification = classify_tier(
            calib,
            CalibrationKey(**env["eur"]["calibration_key"]),
            NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("25")),
            provenance=_prov(),
            source_window=source_window_from_bars(
                _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
            ),
        )
        forbidden = {
            "direction",
            "force",
            "cause",
            "causal",
            "impact",
            "bias",
            "momentum",
            "conviction",
            "strength",
            "pressure",
        }
        names = {item.name for item in fields(classification)}
        assert not (names & forbidden)
        payload = json.loads(json.dumps(encode_value(classification), sort_keys=True))
        keys = set(payload)
        assert not (keys & forbidden)
        # The classification is a label plus its identity, nothing more.
        assert payload["tier_id"] == "T2"
        assert payload["no_go"] is False

    def test_unknown_tier_explicit_unclassified(self, env):
        """B8: out-of-band values refuse; never nearest-bucket guessing."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        prov = _prov()
        window = source_window_from_bars(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        )
        # XAU: 20 points is below every declared band.
        with pytest.raises(Exception) as excinfo:
            classify_spatial_band(
                calib,
                CalibrationKey(**env["xau"]["calibration_key"]),
                NativeMagnitude("XAUUSD", NativeUnit.POINT, Decimal("20")),
                provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
                source_window=window,
            )
        assert getattr(excinfo.value, "code", None) == "UNCLASSIFIED_VALUE"
        # A bounded table refuses a value outside its declared span.
        local = measurements_pkg.CalibrationRegistry()
        key = CalibrationKey(
            model_id="TEST.MODEL.V1",
            model_version="V1",
            calibration_id="BOUNDED_TIERS",
            calibration_version="V1",
        )
        local.add_tier_table(
            TierTable(
                key=key,
                instrument_id="EURUSD",
                unit=NativeUnit.PIP,
                status=CalibrationStatus.RESEARCH,
                bands=(
                    TierBand(
                        tier_id="T1",
                        lower=Decimal("10"),
                        upper=Decimal("30"),
                        upper_inclusive=False,
                    ),
                ),
                source_ref="tests/test_forge_measurements.py",
            )
        )
        assert local.tier_table(key).band_for(Decimal("10")) is not None
        assert local.tier_table(key).band_for(Decimal("9.999")) is None
        with pytest.raises(Exception) as excinfo:
            classify_tier(
                local,
                key,
                NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("5")),
                provenance=prov,
                source_window=window,
            )
        assert getattr(excinfo.value, "code", None) == "UNCLASSIFIED_VALUE"

    def test_missing_calibration_version_unavailable(self, env):
        """B9/M4: a missing model/calibration version refuses."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        prov = _prov()
        window = source_window_from_bars(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        )
        # III.2-GAP-2: no JPY pair-native tier table is canonical, so a JPY
        # tier lookup refuses instead of inventing a table.
        jpy_key = CalibrationKey(
            model_id=env["jpy"]["model_id"],
            model_version=env["jpy"]["model_version"],
            calibration_id="JPY_PAIR_TIERS",
            calibration_version="V1",
        )
        with pytest.raises(Exception) as excinfo:
            calib.tier_table(jpy_key)
        assert getattr(excinfo.value, "code", None) == "MODEL_VERSION_UNAVAILABLE"
        # Unknown model version for any other lookup refuses identically.
        with pytest.raises(Exception) as excinfo:
            calib.spatial_table(
                CalibrationKey(
                    model_id="XAU.GAME.L1_L2_L3.V1",
                    model_version="V2",
                    calibration_id="XAU_SPATIAL_BANDS",
                    calibration_version="V1",
                )
            )
        assert getattr(excinfo.value, "code", None) == "MODEL_VERSION_UNAVAILABLE"


# ---------------------------------------------------------------------------
# T3 — Coordinate engine (C1–C5, K-c, L1, L3, M3, N2)
# ---------------------------------------------------------------------------


class TestT3Coordinates:
    def test_coordinate_families_bounded(self, env):
        """C1: canonical bound + declared extensions, each with a source."""
        assert CANONICAL_FAMILY_LEVELS == (
            Decimal("50"),
            Decimal("61.8"),
            Decimal("68"),
            Decimal("72"),
            Decimal("80"),
            Decimal("82"),
            Decimal("100"),
            Decimal("120"),
            Decimal("125"),
            Decimal("132"),
            Decimal("168"),
            Decimal("185"),
        )
        for coordinate_set in COORDINATE_SETS.values():
            for family in coordinate_set.families:
                assert family.source_ref, family.family_id
                assert family.source_quote, family.family_id
                assert isinstance(family.level, Decimal)
                assert family.level != 0
        # An unknown family refuses; nothing is invented.
        anchor = self._anchor(env, "EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        for bogus in ("FIB_99", "GOLDEN_RATIO", "FIB_200", "MAGIC_LEVEL"):
            with pytest.raises(Exception) as excinfo:
                project_coordinates(anchor, bogus, provenance=_prov())
            assert getattr(excinfo.value, "code", None) in {
                "UNKNOWN_COORDINATE_FAMILY",
                "COORDINATE_FAMILY_NOT_EARNED",
            }

    def _anchor(self, env, model_id: str, model_version: str) -> AnchorRecord:
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        return AnchorRecord(
            anchor_id=f"TEST.ANCHOR.{model_version}",
            model_id=model_id,
            model_version=model_version,
            status=AnchorStatus.ACTIVE,
            rule=AnchorRule(
                rule_id="R15.RANGE_BIRTH",
                rule_version="DECLARED",
                materialization=RuleMaterialization.DECLARED,
                source_ref=env["fib"]["source_ref"],
            ),
            earned_range=measured,
        )

    def test_projection_requires_eligible_anchor(self, env):
        """C2/K-c: only ELIGIBLE or ACTIVE anchors project."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        rule = AnchorRule(
            rule_id="R15.RANGE_BIRTH",
            rule_version="DECLARED",
            materialization=RuleMaterialization.DECLARED,
            source_ref=env["fib"]["source_ref"],
        )
        for status in (AnchorStatus.UNRESOLVED, AnchorStatus.INVALIDATED):
            anchor = AnchorRecord(
                anchor_id=f"TEST.{status.value}",
                model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                model_version="R15",
                status=status,
                rule=rule,
                earned_range=None,
                invalidation_reason=(
                    "synthetic invalidation" if status is AnchorStatus.INVALIDATED else None
                ),
            )
            with pytest.raises(Exception) as excinfo:
                project_coordinates(anchor, "FIB_50", provenance=_prov())
            assert getattr(excinfo.value, "code", None) == "ANCHOR_NOT_EARNED"
        rekeyed = AnchorRecord(
            anchor_id="TEST.REKEYED",
            model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
            model_version="R15",
            status=AnchorStatus.REKEYED,
            rule=rule,
            earned_range=measured,
            rekey_source_anchor_id="TEST.PRIOR",
        )
        with pytest.raises(Exception) as excinfo:
            project_coordinates(rekeyed, "FIB_50", provenance=_prov())
        assert getattr(excinfo.value, "code", None) == "ANCHOR_NOT_EARNED"
        # Positive control: an ACTIVE anchor projects.
        active = self._anchor(env, "CROSSASSET.FIB.RANGE_BIRTH.V1", "R15")
        projection = project_coordinates(active, "FIB_50", provenance=_prov())
        assert projection.anchor_id == active.anchor_id

    def test_arbitrary_pivot_rejected(self, env):
        """C3: no anchor generator exists — arbitrary pivots cannot project."""
        defined_functions: set[str] = set()
        for path in sorted(PACKAGE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined_functions.add(node.name)
        # No pivot finder, no anchor synthesiser: bars never become anchors.
        pivot_tools = {
            name for name in defined_functions if re.search(r"(?i)pivot", name)
        }
        creation_verbs = re.compile(
            r"(?i)^(find|derive|make|create|generate|extract|detect|build|"
            r"compute|synthes\w*|invent)\w*anchor$"
        )
        anchor_tools = {
            name for name in defined_functions if creation_verbs.match(name)
        }
        assert not pivot_tools, sorted(pivot_tools)
        assert not anchor_tools, sorted(anchor_tools)
        # The documented R11 generic-pivot fallback is absent by construction:
        # ANCHOR_RULE_REGISTRY holds no registered rule to fall back to.
        assert dict(ANCHOR_RULE_REGISTRY) == {}
        # An anchor declared from nothing (no earned range) never projects.
        anchor = AnchorRecord(
            anchor_id="PIVOT.ANCHOR.01",
            model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
            model_version="R15",
            status=AnchorStatus.UNRESOLVED,
            rule=AnchorRule(
                rule_id="R11.GENERIC_PIVOT",
                rule_version="V1",
                materialization=RuleMaterialization.NOT_MATERIALIZED,
                source_ref=env["fib"]["source_ref"],
            ),
            earned_range=None,
        )
        with pytest.raises(Exception) as excinfo:
            project_coordinates(anchor, "FIB_50", provenance=_prov())
        assert getattr(excinfo.value, "code", None) == "ANCHOR_NOT_EARNED"

    def test_no_coordinate_without_earned_range(self, env):
        """C4/N2: an earned range must exist before a coordinate does."""
        rule = AnchorRule(
            rule_id="R15.RANGE_BIRTH",
            rule_version="DECLARED",
            materialization=RuleMaterialization.DECLARED,
            source_ref=env["fib"]["source_ref"],
        )
        # Construction itself refuses an earned state without a range.
        for status in (AnchorStatus.ELIGIBLE, AnchorStatus.ACTIVE):
            with pytest.raises(Exception):
                AnchorRecord(
                    anchor_id=f"TEST.{status.value}.RANGELESS",
                    model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                    model_version="R15",
                    status=status,
                    rule=rule,
                    earned_range=None,
                )
        # An eligible rule that is not materialized can never earn.
        with pytest.raises(Exception):
            AnchorRecord(
                anchor_id="TEST.NOT_MATERIALIZED",
                model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                model_version="R15",
                status=AnchorStatus.ELIGIBLE,
                rule=AnchorRule(
                    rule_id="R15.RANGE_BIRTH",
                    rule_version="V1",
                    materialization=RuleMaterialization.NOT_MATERIALIZED,
                    source_ref=env["fib"]["source_ref"],
                ),
                earned_range=_measure_seed_range(env, "eur", "EUR_SEED_T2"),
            )
        # The golden FIB rejected case refuses with the expected code.
        anchor = self._anchor(
            env, "CROSSASSET.FIB.RANGE_BIRTH.V1", "R15"
        )
        projection = project_coordinates(anchor, "FIB_50", provenance=_prov())
        assert projection.projected_price.instrument_id == "EURUSD"
        assert projection.range_size.value == anchor.earned_range.size.value

    def test_rekey_ladder_does_not_auto_extend(self, env):
        """C5: a deeper coordinate appears only when declared and earned."""
        eur_set = COORDINATE_SETS[("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")]
        assert eur_set.family_ids == (
            "EUR_DAILY_100",
            "EUR_DAILY_125",
            "EUR_DAILY_132",
            "EUR_DAILY_168",
            "EUR_DAILY_185",
        )
        anchor = AnchorRecord(
            anchor_id="TEST.EUR.ACTIVE",
            model_id="EUR.DAILY.NEWS_REKEY.V1",
            model_version="PHASE1",
            status=AnchorStatus.ACTIVE,
            rule=AnchorRule(
                rule_id="TEST.RULE",
                rule_version="V1",
                materialization=RuleMaterialization.CANONICAL,
                source_ref=env["ladder"]["source_ref"],
            ),
            earned_range=_measure_seed_range(env, "eur", "EUR_SEED_T2"),
        )
        # Projecting 132 yields exactly one coordinate — never 168 too.
        projection = project_coordinates(anchor, "EUR_DAILY_132", provenance=_prov())
        assert projection.family_id == "EUR_DAILY_132"
        assert "168" not in projection.coordinate_id
        encoded = encode_value(projection)
        assert "168" not in json.dumps(encoded)
        # A canonical level this model's card does not name refuses as
        # not-earned rather than guessing.
        with pytest.raises(Exception) as excinfo:
            project_coordinates(anchor, "EUR_DAILY_50", provenance=_prov())
        assert getattr(excinfo.value, "code", None) == "COORDINATE_FAMILY_NOT_EARNED"
        # XAU names 132 but not 168: the 132 state never yields 168.
        xau_set = COORDINATE_SETS[("XAU.GAME.L1_L2_L3.V1", "V1")]
        assert xau_set.family("XAU_168") is None
        with pytest.raises(Exception) as excinfo:
            project_coordinates(
                self._anchor(env, "XAU.GAME.L1_L2_L3.V1", "V1"),
                "XAU_168",
                provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
            )
        assert getattr(excinfo.value, "code", None) == "COORDINATE_FAMILY_NOT_EARNED"


def _module_source(module) -> str:
    path = Path(module.__file__)
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# T4 — Range Birth / anchor interface (D1–D5, K-c, L3, N8)
# ---------------------------------------------------------------------------


class TestT4Anchors:
    def _rule(self, env) -> AnchorRule:
        return AnchorRule(
            rule_id="R15.RANGE_BIRTH",
            rule_version="DECLARED",
            materialization=RuleMaterialization.DECLARED,
            source_ref=env["fib"]["source_ref"],
        )

    def test_anchor_status_vocabulary_exact(self, env):
        """D1: exactly the five frozen states; unknown states refuse."""
        assert [member.value for member in AnchorStatus] == [
            "UNRESOLVED",
            "ELIGIBLE",
            "ACTIVE",
            "INVALIDATED",
            "REKEYED",
        ]
        with pytest.raises(ValueError):
            AnchorStatus("BORROWED_STATE")
        # A plain string never satisfies the typed constructor.
        with pytest.raises(Exception) as excinfo:
            AnchorRecord(
                anchor_id="TEST.STRING_STATE",
                model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                model_version="R15",
                status="ACTIVE",  # type: ignore[arg-type]
                rule=self._rule(env),
                earned_range=_measure_seed_range(env, "eur", "EUR_SEED_T2"),
            )
        assert getattr(excinfo.value, "code", None) == "INVALID_ANCHOR_STATE"
        assert PROJECTION_BLOCKING_STATES == frozenset(
            {
                AnchorStatus.UNRESOLVED,
                AnchorStatus.INVALIDATED,
                AnchorStatus.REKEYED,
            }
        )
        assert EARNED_STATES == frozenset({AnchorStatus.ELIGIBLE, AnchorStatus.ACTIVE})

    def test_anchor_eligibility_first_class_output(self, env):
        """D2: status + earned-range reference + rule identity + refusal."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        active = AnchorRecord(
            anchor_id="FIB.ANCHOR.ACTIVE.01",
            model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
            model_version="R15",
            status=AnchorStatus.ACTIVE,
            rule=self._rule(env),
            earned_range=measured,
        )
        eligibility = evaluate_anchor(active, provenance=_prov())
        assert isinstance(eligibility, AnchorEligibility)
        assert eligibility.status is AnchorStatus.ACTIVE
        assert eligibility.earned_range_reference == measured.source_window.input_digest
        assert eligibility.rule_id == "R15.RANGE_BIRTH"
        assert eligibility.rule_version == "DECLARED"
        assert eligibility.rule_materialization is RuleMaterialization.DECLARED
        assert eligibility.refusal_code is AnchorRefusalCode.NONE
        assert eligibility.automation_ready is False
        assert ENV_FIELDS <= {item.name for item in fields(eligibility)}
        # Refusal codes are reported, not swallowed.
        for status, code in (
            (AnchorStatus.UNRESOLVED, AnchorRefusalCode.ANCHOR_UNRESOLVED),
            (
                AnchorStatus.INVALIDATED,
                AnchorRefusalCode.ANCHOR_INVALIDATED,
            ),
        ):
            anchor = AnchorRecord(
                anchor_id=f"TEST.{status.value}",
                model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                model_version="R15",
                status=status,
                rule=self._rule(env),
                earned_range=None,
                invalidation_reason=(
                    "synthetic invalidation" if status is AnchorStatus.INVALIDATED else None
                ),
            )
            report = evaluate_anchor(
                anchor,
                provenance=_prov(),
                source_window=measured.source_window,
            )
            assert report.refusal_code is code
            assert report.automation_ready is False

    def test_rekeyed_is_remapping_transition(self, env):
        """D3/N8: a remapping transition, never a destruction."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        prior = AnchorRecord(
            anchor_id="FIB.ANCHOR.ACTIVE.01",
            model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
            model_version="R15",
            status=AnchorStatus.ACTIVE,
            rule=self._rule(env),
            earned_range=measured,
        )
        before = prior.to_dict()
        transition = rekey_anchor(
            prior,
            "FIB.ANCHOR.REKEYED.02",
            mapping={"FIB_132": "EUR_DAILY_132"},
            provenance=_prov(),
        )
        assert transition.anchor_id == prior.anchor_id
        assert transition.successor_anchor_id == "FIB.ANCHOR.REKEYED.02"
        assert transition.prior_status is AnchorStatus.ACTIVE
        assert dict(transition.mapping) == {"FIB_132": "EUR_DAILY_132"}
        # The prior anchor is untouched — nothing was destroyed or replaced.
        assert prior.to_dict() == before
        # The REKEYED successor record names what it remaps.
        successor = AnchorRecord(
            anchor_id="FIB.ANCHOR.REKEYED.02",
            model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
            model_version="R15",
            status=AnchorStatus.REKEYED,
            rule=self._rule(env),
            earned_range=measured,
            rekey_source_anchor_id=prior.anchor_id,
        )
        assert successor.rekey_source_anchor_id == prior.anchor_id
        # Unresolved or invalidated anchors cannot be rekeyed at all.
        unresolved = AnchorRecord(
            anchor_id="TEST.UNRESOLVED",
            model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
            model_version="R15",
            status=AnchorStatus.UNRESOLVED,
            rule=self._rule(env),
            earned_range=None,
        )
        with pytest.raises(Exception):
            rekey_anchor(
                unresolved,
                "TEST.SUCC",
                mapping={"a": "b"},
                provenance=_prov(),
            )

    def test_invalidated_anchor_blocks_projection(self, env):
        """D4/M3: INVALIDATED/UNRESOLVED block projection explicitly."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        for status, code in (
            (AnchorStatus.INVALIDATED, "ANCHOR_INVALIDATED"),
            (AnchorStatus.UNRESOLVED, "ANCHOR_UNRESOLVED"),
        ):
            anchor = AnchorRecord(
                anchor_id=f"TEST.{status.value}",
                model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                model_version="R15",
                status=status,
                rule=self._rule(env),
                earned_range=None,
                invalidation_reason=(
                    "synthetic invalidation" if status is AnchorStatus.INVALIDATED else None
                ),
            )
            with pytest.raises(Exception) as excinfo:
                project_coordinates(anchor, "FIB_50", provenance=_prov())
            assert getattr(excinfo.value, "code", None) == "ANCHOR_NOT_EARNED"
            report = evaluate_anchor(
                anchor, provenance=_prov(), source_window=measured.source_window
            )
            assert report.refusal_code.value == code
            assert report.status is status

    def test_no_generic_pivot_fallback(self, env):
        """D5: no R11 generic-pivot fallback exists as callable API."""
        # The rule registry is empty: no production Range Birth rule and no
        # generic-pivot rule can be looked up, let alone applied.
        assert dict(ANCHOR_RULE_REGISTRY) == {}
        for name, source in _package_sources():
            assert not re.search(
                r"def\s+\w*pivot\w*\s*\(", source
            ), name
            assert "def derive_anchor" not in source, name
        # An anchor under a NOT_MATERIALIZED rule (the R15 situation) can
        # never become eligible — the engine refuses at construction.
        with pytest.raises(Exception):
            AnchorRecord(
                anchor_id="TEST.R15.NOT_MATERIALIZED",
                model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
                model_version="R15",
                status=AnchorStatus.ELIGIBLE,
                rule=AnchorRule(
                    rule_id="R15.RANGE_BIRTH",
                    rule_version="V1",
                    materialization=RuleMaterialization.NOT_MATERIALIZED,
                    source_ref=env["fib"]["source_ref"],
                ),
                earned_range=_measure_seed_range(env, "eur", "EUR_SEED_T2"),
            )
        # And the fixture discloses the automation gate (III.2-GAP-1).
        deferred = env["fib"]["deferred_cases"][0]
        assert deferred["case_id"] == "FIB.R15.AUTOMATION_APPROVAL"
        assert "not materialized" in deferred["reason"]


# ---------------------------------------------------------------------------
# T5 — Clock / state-age engine (E1–E8, M2, N4)
# ---------------------------------------------------------------------------


class TestT5StateAge:
    def test_state_age_elapsed_since_event(self, env):
        """E1: elapsed measured against injected instants."""
        elapsed = elapsed_since(
            _utc("2026-03-03T12:00:00Z"),
            _utc("2026-03-03T12:01:30Z"),
            provenance=_prov(),
        )
        assert isinstance(elapsed, ElapsedSinceEvent)
        assert elapsed.elapsed_seconds == Decimal("90.0")
        assert elapsed.event_instant == _utc("2026-03-03T12:00:00Z")
        # Refuses a negative span rather than signing it silently.
        with pytest.raises(Exception):
            elapsed_since(
                _utc("2026-03-03T12:00:00Z"),
                _utc("2026-03-03T11:59:00Z"),
                provenance=_prov(),
            )

    def test_checkpoint_reached(self, env):
        """E2: checkpoint reached is a typed fact."""
        reached = checkpoint_reached(
            _utc("2026-03-03T12:00:00Z"),
            _utc("2026-03-03T12:00:00Z"),
            provenance=_prov(),
        )
        pending = checkpoint_reached(
            _utc("2026-03-03T12:00:00Z"),
            _utc("2026-03-03T11:59:59Z"),
            provenance=_prov(),
        )
        assert reached.state.value == "REACHED"
        assert pending.state.value == "NOT_REACHED"
        assert {member.value for member in type(reached.state)} == {
            "REACHED",
            "NOT_REACHED",
        }

    def test_acceptance_duration(self, env):
        """E3: acceptance duration is measured exactly."""
        duration = measure_acceptance_duration(
            _utc("2026-03-03T08:00:00Z"),
            _utc("2026-03-03T08:00:45.500000Z"),
            provenance=_prov(),
        )
        assert duration.duration_seconds == Decimal("45.5")
        with pytest.raises(Exception):
            measure_acceptance_duration(
                _utc("2026-03-03T08:00:00Z"),
                _utc("2026-03-03T07:59:00Z"),
                provenance=_prov(),
            )

    def test_failure_age(self, env):
        """E4: failure age is measured exactly."""
        age = failure_age(
            _utc("2026-03-03T07:00:00Z"),
            _utc("2026-03-03T07:03:20Z"),
            provenance=_prov(),
        )
        assert age.age_seconds == Decimal("200.0")
        with pytest.raises(Exception):
            failure_age(
                _utc("2026-03-03T07:00:00Z"),
                _utc("2026-03-03T06:59:59Z"),
                provenance=_prov(),
            )

    def test_time_to_delivery_scheduled_elapsed_only(self, env):
        """E5: distance to a scheduled boundary; no price semantics."""
        pending = time_to_delivery(
            _utc("2026-03-03T17:00:00Z"),
            _utc("2026-03-03T16:30:00Z"),
            provenance=_prov(),
        )
        elapsed_state = time_to_delivery(
            _utc("2026-03-03T17:00:00Z"),
            _utc("2026-03-03T17:30:00Z"),
            provenance=_prov(),
        )
        assert pending.state.value == "PENDING"
        assert pending.remaining_seconds == Decimal("1800.0")
        assert elapsed_state.state.value == "ELAPSED"
        assert elapsed_state.remaining_seconds == Decimal("1800.0")
        # The record has no price, direction or forecast field.
        names = {item.name for item in fields(pending)}
        assert names == ENV_FIELDS | {
            "scheduled_boundary",
            "observed_instant",
            "remaining_seconds",
            "state",
        }
        forbidden = {"price", "target_price", "direction", "forecast", "delivery_time"}
        assert not (names & forbidden)

    def test_session_weekly_monthly_phase(self, env):
        """E6/L1: phase derives from the III.1 session and lineage rules."""
        # EUR Asian range window: 19:00–03:00 New York (crosses midnight).
        inside = measure_session_phase(
            env["sessions"],
            "EUR.DAILY.NEWS_REKEY.V1",
            "PHASE1",
            "EUR_DAILY.ASIAN_RANGE",
            _utc("2026-03-03T02:00:00Z"),  # 21:00 EST the previous evening
            provenance=_prov(),
        )
        outside = measure_session_phase(
            env["sessions"],
            "EUR.DAILY.NEWS_REKEY.V1",
            "PHASE1",
            "EUR_DAILY.ASIAN_RANGE",
            _utc("2026-03-03T17:00:00Z"),  # 12:00 EST
            provenance=_prov(),
        )
        assert inside.state is SessionPhaseState.INSIDE_WINDOW
        assert outside.state is SessionPhaseState.OUTSIDE_WINDOW
        # A checkpoint session matches exactly one wall time.
        checkpoint = measure_session_phase(
            env["sessions"],
            "BTC.TRACKER.DWM.V1",
            "V1",
            "BTC_TRACKER.DAILY_CHECKPOINT_12PM",
            _utc("2026-03-03T17:00:00Z"),  # 12:00 EST
            provenance=_prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW"),
        )
        assert checkpoint.state is SessionPhaseState.CHECKPOINT_MATCHED
        off_checkpoint = measure_session_phase(
            env["sessions"],
            "BTC.TRACKER.DWM.V1",
            "V1",
            "BTC_TRACKER.DAILY_CHECKPOINT_12PM",
            _utc("2026-03-03T17:05:00Z"),
            provenance=_prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW"),
        )
        assert off_checkpoint.state is SessionPhaseState.CHECKPOINT_NOT_MATCHED
        # Weekly and monthly phase follow the III.1 research-day lineage
        # (evening bars after 19:00 NY belong to the following research day).
        weekly = measure_period_phase(
            env["lineages"],
            "EUR_DAILY_LINEAGE",
            "EURUSD",
            _utc("2026-03-03T20:00:00Z"),  # 15:00 EST, same research day
            PeriodKind.WEEK,
            provenance=_prov(),
        )
        assert weekly.research_day == "2026-03-03"
        iso_year, iso_week, _ = datetime(2026, 3, 3).isocalendar()
        assert weekly.period_label == f"{iso_year}-W{iso_week:02d}"
        monthly = measure_period_phase(
            env["lineages"],
            "EUR_DAILY_LINEAGE",
            "EURUSD",
            _utc("2026-03-03T20:00:00Z"),
            PeriodKind.MONTH,
            provenance=_prov(),
        )
        assert monthly.period_label == "2026-03"
        shifted = measure_period_phase(
            env["lineages"],
            "EUR_DAILY_LINEAGE",
            "EURUSD",
            _utc("2026-03-04T01:00:00Z"),  # 20:00 EST → next research day
            PeriodKind.MONTH,
            provenance=_prov(),
        )
        assert shifted.research_day == "2026-03-04"

    def test_unresolvable_clock_no_calculation(self, env):
        """E7/M2: an unresolvable clock or session refuses."""
        with pytest.raises(Exception) as excinfo:
            measure_session_phase(
                env["sessions"],
                "EUR.DAILY.NEWS_REKEY.V1",
                "PHASE1",
                "EUR_DAILY.NO_SUCH_SESSION",
                _utc("2026-03-03T02:00:00Z"),
                provenance=_prov(),
            )
        assert getattr(excinfo.value, "code", None) == "NO_CALCULATION"
        # Wrong model version is also unresolvable — never remapped.
        with pytest.raises(Exception) as excinfo:
            measure_session_phase(
                env["sessions"],
                "EUR.DAILY.NEWS_REKEY.V1",
                "V99",
                "EUR_DAILY.ASIAN_RANGE",
                _utc("2026-03-03T02:00:00Z"),
                provenance=_prov(),
            )
        assert getattr(excinfo.value, "code", None) == "NO_CALCULATION"
        # Unknown research-day lineage refuses with NO_CALCULATION.
        with pytest.raises(Exception) as excinfo:
            measure_period_phase(
                env["lineages"],
                "UNKNOWN_LINEAGE",
                "EURUSD",
                _utc("2026-03-03T20:00:00Z"),
                PeriodKind.WEEK,
                provenance=_prov(),
            )
        assert getattr(excinfo.value, "code", None) == "NO_CALCULATION"
        # A naive (wall-clock-less) instant is a contract violation.
        with pytest.raises(Exception):
            elapsed_since(
                datetime(2026, 3, 3, 12, 0, 0),
                _utc("2026-03-03T12:01:00Z"),
                provenance=_prov(),
            )

    def test_time_weights_never_manufactures_state(self, env):
        """E8/N4: time measures elapsed facts; it never calls the play."""
        # The module consumes instants only — no bars, no prices.
        source = _module_source(
            importlib.import_module("app.forge.measurements.state_age")
        )
        assert "measure_range" not in source
        assert "measure_path" not in source
        assert not re.search(r"\bBar\b", source)
        forbidden_params = {"bars", "price", "level", "target", "signal"}
        for public in (
            elapsed_since,
            checkpoint_reached,
            measure_acceptance_duration,
            failure_age,
            time_to_delivery,
            measure_session_phase,
            measure_period_phase,
        ):
            for parameter in inspect.signature(public).parameters:
                assert parameter not in forbidden_params, public.__name__
        # Durations are Decimal facts derived from the injected pair alone.
        first = duration_seconds(
            _utc("2026-03-03T12:00:00Z"), _utc("2026-03-03T12:00:10Z")
        )
        second = duration_seconds(
            _utc("2026-03-03T12:00:00Z"), _utc("2026-03-03T12:00:10Z")
        )
        assert first == second == Decimal("10.0")


# ---------------------------------------------------------------------------
# T6 — Path measurements (F1–F9, K-d, L1, N5–N7)
# ---------------------------------------------------------------------------


class TestT6Path:
    def test_mae_mfe_from_path(self, env):
        """F1/L1: MAE and MFE computed from the typed path."""
        measured = _measure_path(env, _path_fixture_bars(), [])
        assert measured.reference_price.value == Decimal("1.08000")
        # Highest high 1.08400, lowest low 1.07950 around 1.08000.
        assert measured.mfe.value == Decimal("40.0")
        assert measured.mae.value == Decimal("5.0")
        assert measured.mae.unit is NativeUnit.PIP
        assert measured.bar_count == 4
        # A path that never goes below its reference has zero MAE.
        only_up = _ohlc_bars(
            "EURUSD",
            [
                ("1.08000", "1.08100", "1.08000", "1.08050"),
                ("1.08050", "1.08200", "1.08040", "1.08150"),
            ],
            "2026-03-03T04:00:00Z",
        )
        measured_up = _measure_path(env, only_up, [])
        assert measured_up.mae.value == Decimal(0)

    def test_first_delivery_order(self, env):
        """F2/N7: the first delivery is retained with its order."""
        bars = _path_fixture_bars()
        levels = [
            _level("1.08300", "DEEP", LevelSide.ABOVE),
            _level("1.08100", "NEAR", LevelSide.ABOVE),
        ]
        measured = _measure_path(env, bars, levels)
        # NEAR is accepted on bar 1, DEEP on bar 3.
        assert measured.first_delivery is not None
        assert measured.first_delivery.level_id == "NEAR"
        assert measured.first_delivery.bar_index == 1
        assert measured.first_delivery.order_index == 0
        deep = next(
            outcome for outcome in measured.levels if outcome.level_id == "DEEP"
        )
        assert deep.first_delivery is not None
        assert deep.first_delivery.bar_index == 3
        assert deep.first_delivery.order_index == 1
        # A path with no delivery keeps the fact explicitly absent.
        none_measured = _measure_path(
            env,
            _path_fixture_bars(),
            [_level("9.99900", "FAR", LevelSide.ABOVE)],
        )
        assert none_measured.first_delivery is None

    def test_target_order(self, env):
        """F3: the ordered sequence of realized deliveries is retained."""
        bars = _path_fixture_bars()
        # Names deliberately sort opposite to realization order: the deep
        # level is alphabetically first but delivers last.
        levels = [
            _level("1.08300", "A_DEEP", LevelSide.ABOVE),
            _level("1.08100", "Z_NEAR", LevelSide.ABOVE),
        ]
        measured = _measure_path(env, bars, levels)
        order = [(item.level_id, item.bar_index, item.order_index) for item in measured.delivery_order]
        assert order == [("Z_NEAR", 1, 0), ("A_DEEP", 3, 1)]
        # Deterministic: re-measuring produces the identical sequence.
        repeat = _measure_path(env, bars, levels)
        assert repeat.delivery_order == measured.delivery_order

    def test_touch_not_acceptance(self, env):
        """F4/N5: distinct typed states; touch never coerces to acceptance."""
        # Level 1.08360 is touched intrabar by the last bar's high (1.08400)
        # and is never closed at or beyond: a pure touch.
        bars = _path_fixture_bars()
        measured = _measure_path(env, bars, [_level("1.08360", "L", LevelSide.ABOVE)])
        outcome = measured.levels[0]
        assert outcome.touch_state is TouchState.TOUCHED
        assert outcome.acceptance_state is AcceptanceState.NOT_ACCEPTED
        # A touch that is later accepted keeps both facts distinct.
        accepted = _measure_path(
            env, bars, [_level("1.08100", "L", LevelSide.ABOVE)]
        )
        accepted_outcome = accepted.levels[0]
        assert accepted_outcome.touch_state is TouchState.TOUCHED
        assert accepted_outcome.acceptance_state is AcceptanceState.ACCEPTED
        # The two enums are separate types with separate vocabularies.
        assert {member.value for member in TouchState} == {"TOUCHED", "NOT_TOUCHED"}
        assert {member.value for member in AcceptanceState} == {
            "ACCEPTED",
            "NOT_ACCEPTED",
        }
        assert TouchState.TOUCHED not in tuple(AcceptanceState)

    def test_reach_not_target_before_stop(self, env):
        """F5: reaching both sides is not a target-before-stop claim."""
        # The stop-side level delivers first; the target side delivers later.
        bars = _ohlc_bars(
            "EURUSD",
            [
                ("1.08000", "1.08020", "1.07900", "1.07920"),
                ("1.07920", "1.07950", "1.07900", "1.07940"),
                ("1.07940", "1.08150", "1.07930", "1.08120"),
            ],
            "2026-03-03T05:00:00Z",
        )
        measured = _measure_path(
            env,
            bars,
            [
                _level("1.08100", "TARGET", LevelSide.ABOVE),
                _level("1.07950", "STOP", LevelSide.BELOW),
            ],
        )
        outcomes = {item.level_id: item for item in measured.levels}
        assert outcomes["TARGET"].acceptance_state is AcceptanceState.ACCEPTED
        assert outcomes["STOP"].acceptance_state is AcceptanceState.ACCEPTED
        # The actual order is retained: stop first, target second.
        assert [item.level_id for item in measured.delivery_order] == [
            "STOP",
            "TARGET",
        ]
        # There is no aggregate field claiming any ordering relation.
        names = {item.name for item in fields(measured)}
        assert "target_before_stop" not in names
        assert not any("won" in name or "loss" in name for name in names)
        # Terminal outcome does not erase the ordered path.
        assert measured.first_delivery.level_id == "STOP"
        assert measured.first_delivery.bar_index == 0

    def test_excursion_rejection_acceptance_typed(self, env):
        """F6: excursion, rejection, acceptance, close-beyond, re-entry."""
        bars = _path_fixture_bars()
        measured = _measure_path(env, bars, [_level("1.08100", "L", LevelSide.ABOVE)])
        outcome = measured.levels[0]
        assert isinstance(outcome, LevelOutcome)
        # max excursion past the level is measured in native units.
        assert outcome.max_excursion.value == Decimal("30.0")  # 1.08400 - 1.08100
        # Touched at bar 0 while closing below → rejected is typed, not implied.
        assert outcome.rejection_state is RejectionState.REJECTED
        # Accepted at bar 1, closes beyond, later returns inside at bar 2.
        assert outcome.acceptance_state is AcceptanceState.ACCEPTED
        assert outcome.close_beyond_state is CloseBeyondState.BEYOND
        assert outcome.re_entry_state is ReEntryState.REENTERED
        # A level untouched keeps every typed state negative.
        untouched = _measure_path(
            env, bars, [_level("9.99900", "FAR", LevelSide.ABOVE)]
        ).levels[0]
        assert untouched.touch_state is TouchState.NOT_TOUCHED
        assert untouched.acceptance_state is AcceptanceState.NOT_ACCEPTED
        assert untouched.close_beyond_state is CloseBeyondState.NOT_BEYOND
        assert untouched.re_entry_state is ReEntryState.NOT_REENTERED
        assert untouched.rejection_state is RejectionState.NOT_REJECTED
        assert untouched.max_excursion.value == Decimal(0)
        # Re-entry is a distinct enum from acceptance.
        assert {member.value for member in ReEntryState} == {
            "REENTERED",
            "NOT_REENTERED",
        }

    def test_remaining_distribution_never_synthesized(self, env):
        """F7: without a measured range the remainder is explicit absence."""
        bars = _path_fixture_bars()
        without = _measure_path(env, bars, [])
        assert without.remaining_state is RemainingState.UNRESOLVED
        assert without.remaining_distribution is None
        # With a measured range the remainder is the measured range-left.
        measured_range = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        with_range = _measure_path(env, bars, [], measured_range=measured_range)
        assert with_range.remaining_state is RemainingState.MEASURED
        assert with_range.remaining_distribution == measured_range.range_left
        assert {member.value for member in RemainingState} == {
            "MEASURED",
            "UNRESOLVED",
        }

    def test_path_distinctions_survive_serialization(self, env):
        """F8/K-d: the touch/acceptance/path distinctions survive a round trip."""
        bars = _path_fixture_bars()
        measured = _measure_path(
            env,
            bars,
            [
                _level("1.08100", "L", LevelSide.ABOVE),
                _level("1.08360", "DEEP", LevelSide.ABOVE),
            ],
        )
        encoded = encode_value(measured)
        text = json.dumps(encoded, sort_keys=True)
        restored = decode_value(measured, json.loads(text))
        assert restored == measured
        # The distinctions are separate keys with separate values in JSON.
        payload = json.loads(text)
        level_payloads = {item["level_id"]: item for item in payload["levels"]}
        near = level_payloads["L"]
        assert near["touch_state"] == "TOUCHED"
        assert near["acceptance_state"] == "ACCEPTED"
        assert near["close_beyond_state"] == "BEYOND"
        assert near["re_entry_state"] == "REENTERED"
        assert near["rejection_state"] == "REJECTED"
        deep = level_payloads["DEEP"]
        assert deep["touch_state"] == "TOUCHED"
        assert deep["acceptance_state"] == "NOT_ACCEPTED"
        # Encoding is deterministic.
        assert json.dumps(encode_value(measured), sort_keys=True) == text

    def test_reach_not_trade_win(self, env):
        """F9/N6: no win, expectancy or risk-reward field exists."""
        measured = _measure_path(
            env,
            _path_fixture_bars(),
            [_level("1.08100", "L", LevelSide.ABOVE)],
        )
        banned = {"win", "won", "wins", "loss", "expectancy", "rr", "reward", "profit"}
        for obj in (measured, *measured.levels):
            names = {item.name for item in fields(obj)}
            tokens = set()
            for name in names:
                tokens |= _tokens(name)
            assert not (tokens & banned), (obj, tokens & banned)
        payload = json.dumps(encode_value(measured), sort_keys=True).lower()
        for word in ("win_rate", "expectancy", '"reward"', '"profit"'):
            assert word not in payload


# ---------------------------------------------------------------------------
# T7 — Event / news features (G1–G5, N10)
# ---------------------------------------------------------------------------


class TestT7Events:
    def test_event_relevance_and_family(self, env):
        """G1: relevance currencies/assets and a declared family."""
        event = _event_from_fixture(env, 0)
        features = measure_event_features(
            event, provenance=_prov(), source_window=None
        )
        assert isinstance(features, EventFeatures)
        assert features.relevance_currencies == ("EUR",)
        assert features.relevance_assets == ("EURUSD",)
        assert features.family is EventFamily.EMPLOYMENT_RELEASE
        assert features.event_id == event.event_id
        assert features.provenance_label == "SYNTHETIC_FIXTURE"
        # The family vocabulary is bounded; no member means direction/impact.
        for member in EventFamily:
            tokens = _tokens(member.value)
            assert not (tokens & {"direction", "impact", "expectancy", "prediction"})

    def test_scheduled_and_actual_times_distinct(self, env):
        """G2: scheduled vs actual are distinct, explicitly nullable fields."""
        with_actual = _event_from_fixture(env, 0)
        without_actual = _event_from_fixture(env, 1)
        first = measure_event_features(
            with_actual, provenance=_prov(), source_window=None
        )
        second = measure_event_features(
            without_actual, provenance=_prov(), source_window=None
        )
        assert first.scheduled_time != first.actual_time
        assert first.scheduled_time == _utc("2026-03-03T13:30:00Z")
        assert first.actual_time == _utc("2026-03-03T13:30:02Z")
        assert first.actual_declared is True
        assert second.actual_time is None
        assert second.actual_declared is False
        assert second.scheduled_time is not None

    def test_band_size_fields_explicit_when_absent(self, env):
        """G3: absence is disclosed, never defaulted to zero."""
        declared = _event_from_fixture(env, 0)
        absent = _event_from_fixture(env, 1)
        assert declared.band_declared is True
        assert declared.size_declared is True
        assert absent.band_declared is False
        assert absent.size_declared is False
        assert absent.historical_band_lower is None
        assert absent.historical_band_upper is None
        assert absent.historical_size is None
        features = measure_event_features(
            absent, provenance=_prov(), source_window=None
        )
        assert features.band_declared is False
        assert features.size_declared is False
        # The fixture expectation records the refusal, not a zero budget.
        fixture = env["events"]["events"][1]
        assert fixture["expected_budget"] == "REFUSED"
        with pytest.raises(Exception) as excinfo:
            measure_event_budget(
                absent,
                NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("0")),
                provenance=_prov(),
            )
        assert getattr(excinfo.value, "code", None) == "EVENT_BUDGET"
        # A band needs both bounds — construction refuses a half band.
        with pytest.raises(Exception):
            NormalizedEvent(
                event_id="HALF.BAND",
                family=EventFamily.MACRO_RELEASE,
                relevance_currencies=frozenset({"EUR"}),
                relevance_assets=frozenset({"EURUSD"}),
                scheduled_time=_utc("2026-03-04T13:30:00Z"),
                actual_time=None,
                source_ref="corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md",
                provenance_label="SYNTHETIC_FIXTURE",
                historical_band_lower=NativeMagnitude(
                    "EURUSD", NativeUnit.PIP, Decimal("8")
                ),
            )

    def test_consumed_residual_budget_subtractive(self, env):
        """G4: canonical EUR doctrine — consumed reduces what remains."""
        event = _event_from_fixture(env, 0)
        consumed = NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("6"))
        budget = measure_event_budget(event, consumed, provenance=_prov())
        assert isinstance(budget, EventBudget)
        assert budget.total_size.value == Decimal("17")
        assert budget.consumed.value == Decimal("6")
        assert budget.residual.value == Decimal("11")
        assert budget.residual.value == budget.total_size.value - consumed.value
        assert budget.source_ref == EVENT_BUDGET_SOURCE
        fixture = env["events"]["events"][0]
        assert fixture["expected_residual"] == "11"
        # Consuming more than the total clamps at zero — never negative.
        over = measure_event_budget(
            event,
            NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("40")),
            provenance=_prov(),
        )
        assert over.residual.value == Decimal(0)
        # A band-only event uses the band width as its total.
        band_only = NormalizedEvent(
            event_id="BAND.ONLY",
            family=EventFamily.MACRO_RELEASE,
            relevance_currencies=frozenset({"EUR"}),
            relevance_assets=frozenset({"EURUSD"}),
            scheduled_time=_utc("2026-03-04T13:30:00Z"),
            actual_time=None,
            source_ref="corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md",
            provenance_label="SYNTHETIC_FIXTURE",
            historical_band_lower=NativeMagnitude(
                "EURUSD", NativeUnit.PIP, Decimal("8")
            ),
            historical_band_upper=NativeMagnitude(
                "EURUSD", NativeUnit.PIP, Decimal("25")
            ),
        )
        from_band = measure_event_budget(
            band_only,
            NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("6")),
            provenance=_prov(),
        )
        assert from_band.total_size.value == Decimal("17")
        assert from_band.residual.value == Decimal("11")
        # A consumed movement from another asset domain refuses.
        with pytest.raises(Exception) as excinfo:
            measure_event_budget(
                event,
                NativeMagnitude("BTCUSD", NativeUnit.DOLLAR, Decimal("6")),
                provenance=_prov(),
            )
        assert getattr(excinfo.value, "code", None) == "EVENT_BUDGET"

    def test_news_never_replaces_geometry(self, env):
        """G5/N10: no level, range, coordinate or direction is emitted."""
        event = _event_from_fixture(env, 0)
        features = measure_event_features(
            event, provenance=_prov(), source_window=None
        )
        budget = measure_event_budget(
            event,
            NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("6")),
            provenance=_prov(),
        )
        forbidden = {
            "level",
            "price",
            "range",
            "coordinate",
            "direction",
            "target",
            "anchor",
            "projection",
        }
        for measurement in (features, budget):
            names = {item.name for item in fields(measurement)}
            assert not (names & forbidden), measurement
            payload = json.dumps(encode_value(measurement), sort_keys=True)
            for word in ("projected_price", "midpoint", "close_location"):
                assert f'"{word}"' not in payload


# ---------------------------------------------------------------------------
# T8 — Higher-order measurements (H1–H5, M6)
# ---------------------------------------------------------------------------


class TestT8HigherOrder:
    def test_higher_order_seed_ranges(self, env):
        """H1: month/quarter seed ranges are measured."""
        expectations = {
            "QUARTER": ("QUARTER", "50.0"),
            "D1": ("QUARTER_DAY", "15.0"),
            "D2": ("QUARTER_DAY", "14.0"),
            "D3": ("QUARTER_DAY", "13.0"),
            "M1": ("MONTH", "120.0"),
            "M2": ("MONTH", "100.0"),
        }
        for seed_id, (kind, size) in expectations.items():
            measured = _ho_seed(env, seed_id)
            assert measured.seed_kind is SeedRangeKind(kind), seed_id
            assert measured.size.value == Decimal(size), seed_id
            assert measured.low.value <= measured.high.value, seed_id
            assert measured.bar_count == 3, seed_id
            assert measured.quality_state in tuple(DataOutcome)

    def test_d1d3_m1_m2_containers(self, env):
        """H2: D1–D3, M1 scale and M2 shaping are explicit containers."""
        quarter = _ho_seed(env, "QUARTER")
        d1d3 = measure_d1d3_state(
            quarter_seed=quarter,
            d1=_ho_seed(env, "D1"),
            d2=_ho_seed(env, "D2"),
            d3=_ho_seed(env, "D3"),
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert isinstance(d1d3, D1D3State)
        assert d1d3.state is HigherOrderState.MEASURED
        assert d1d3.quarter_seed.size.value == Decimal("50.0")
        assert d1d3.d3.size.value == Decimal("13.0")
        # Evidence-bound definitions are referenced by id, never hardcoded.
        assert require_definition(
            "HO_D1D3_STATE", "V1"
        ).evidence_refs == ("EV.EUR.HO.D3_DIRECTION.V1",)
        empty = measure_d1d3_state(
            quarter_seed=None,
            d1=None,
            d2=None,
            d3=None,
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert empty.state is HigherOrderState.UNRESOLVED
        # M1 scale is the measured month-1 seed magnitude.
        m1 = measure_m1_scale(
            m1_seed=_ho_seed(env, "M1"),
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert isinstance(m1, M1Scale)
        assert m1.state is HigherOrderState.MEASURED
        assert m1.scale == m1.m1_seed.size
        assert require_definition("HO_M1_SCALE", "V1").evidence_refs == (
            "EV.EUR.HO.M1_RANGE_CORR.V1",
        )
        unresolved_m1 = measure_m1_scale(
            m1_seed=None,
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert unresolved_m1.state is HigherOrderState.UNRESOLVED
        assert unresolved_m1.scale is None
        # M2 shaping reports the measured seed and an availability state.
        m2 = measure_m2_shaping(
            m2_seed=_ho_seed(env, "M2"),
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert isinstance(m2, M2Shaping)
        assert m2.state is HigherOrderState.MEASURED
        assert m2.m2_seed.size.value == Decimal("100.0")

    def test_unfinished_side_explicit(self, env):
        """H3: the unfinished side is explicit; absence is UNRESOLVED."""
        quarter = _ho_seed(env, "QUARTER")
        declared = measure_unfinished_side(
            side=UnfinishedSideState.UPPER,
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert declared.side is UnfinishedSideState.UPPER
        assert declared.state is HigherOrderState.MEASURED
        assert require_definition(
            "HO_UNFINISHED_SIDE", "V1"
        ).evidence_refs == ("EV.EUR.HO.UNFINISHED_M3.V1",)
        # The completion association stays in its evidence card: no
        # percentage or rate field exists on this container.
        names = {item.name for item in fields(declared)}
        assert not (names & {"completion_rate", "historical_rate", "probability"})
        unresolved = measure_unfinished_side(
            side=UnfinishedSideState.UNRESOLVED,
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert unresolved.state is HigherOrderState.UNRESOLVED
        assert {member.value for member in UnfinishedSideState} == {
            "UNRESOLVED",
            "UPPER",
            "LOWER",
        }
        # The fixture discloses UPPER as a declared structural fact.
        assert env["ho"]["unfinished_side"] == "UPPER"

    def test_weekly_seed_and_path(self, env):
        """H4: weekly seed measured; outer nodes ordered with standing."""
        weekly_seed = measure_seed_range(
            _bars_from_rows(
                _seed(env, "eur", "EUR_SEED_T1")["rows"], "EURUSD"
            ),
            seed_kind=SeedRangeKind.WEEK,
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(),
            observation_cutoff=_utc(env["eur"]["observation_cutoff"]),
            quality_policy=env["policy"],
        )
        assert weekly_seed.definition_id == "HO_WEEKLY_SEED"
        path = measure_weekly_path(
            weekly_seed=weekly_seed,
            nodes=_weekly_nodes_from_registry(env),
            provenance=_prov(),
            source_window=weekly_seed.source_window,
        )
        assert isinstance(path, WeeklyPath)
        assert path.state is HigherOrderState.MEASURED
        assert path.calibration_status is CalibrationStatus.RESEARCH
        assert [node.order_index for node in path.nodes] == [0, 1, 2]
        fixture_nodes = {
            row["tier_id"]: (row["median_range"], row["sample_n"])
            for row in env["weekly"]["outer_nodes"]
        }
        for node in path.nodes:
            tier = node.node_id.rsplit("_", 1)[-1]
            magnitude, sample_n = fixture_nodes[tier]
            assert node.magnitude.value == Decimal(magnitude)
            assert node.sample_n == sample_n
            assert node.calibration_status is CalibrationStatus.RESEARCH
        # No band boundaries are invented from the research medians.
        key = CalibrationKey(**env["weekly"]["calibration_key"])
        table = measurements_pkg.CALIBRATION_REGISTRY.weekly_outer_nodes(key)
        with pytest.raises(Exception):
            table.node_for("T4")  # an undeclared tier refuses, no guess

    def test_layer_conflict_no_confluence_score(self, env):
        """H5/M6: conflict facts only — structurally no score."""
        quarter = _ho_seed(env, "QUARTER")
        conflict = measure_layer_conflict(
            conflicts=[
                LayerConflictFact(
                    layer_a=HigherOrderLayer.QUARTER,
                    layer_b=HigherOrderLayer.WEEK,
                    kind=LayerConflictKind.DIRECTION_DISAGREEMENT,
                ),
                LayerConflictFact(
                    layer_a=HigherOrderLayer.MONTH_1,
                    layer_b=HigherOrderLayer.DAY,
                    kind=LayerConflictKind.TIMING_DISAGREEMENT,
                ),
            ],
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert isinstance(conflict, LayerConflict)
        assert conflict.state is HigherOrderState.MEASURED
        assert len(conflict.conflicts) == 2
        forbidden = {
            "score",
            "confluence",
            "weight",
            "confidence",
            "aggregate",
            "strength",
            "rating",
        }
        names = {item.name for item in fields(conflict)}
        assert not (names & forbidden)
        fact_names = {item.name for item in fields(conflict.conflicts[0])}
        assert fact_names == {"layer_a", "layer_b", "kind"}
        assert not (fact_names & forbidden)
        payload = json.dumps(encode_value(conflict), sort_keys=True).lower()
        for word in ("score", "confluence", "weight", "confidence"):
            assert f'"{word}"' not in payload
        # An empty conflict set reports explicit absence.
        none_conflict = measure_layer_conflict(
            conflicts=[],
            provenance=_prov(),
            source_window=quarter.source_window,
        )
        assert none_conflict.state is HigherOrderState.UNRESOLVED


# ---------------------------------------------------------------------------
# T9 — Measurement provenance (I1–I8, K-e, L2, M1, M5)
# ---------------------------------------------------------------------------


class TestT9Provenance:
    def test_definition_version_on_every_measurement(self, env):
        """I1: every emitted measurement cites its definition and version."""
        samples = _golden_samples(env)
        assert samples, "sample set must not be empty"
        for name, sample in samples.items():
            assert isinstance(sample, Measurement), name
            spec = require_definition(sample.definition_id, sample.definition_version)
            assert spec.definition_id == sample.definition_id
            assert spec.formula and spec.unit and spec.input_frame, name

    def test_source_window_present(self, env):
        """I2: UTC window bounds plus the input-bar content digest."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        window = measured.source_window
        assert window.window_open_utc.tzinfo is not None
        assert window.window_close_utc.tzinfo is not None
        assert window.window_close_utc >= window.window_open_utc
        assert window.input_digest == content_digest(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        )
        assert window.bar_count == 6
        # Temporal measurements bind the instants they consumed.
        samples = _golden_samples(env)
        temporal = samples["elapsed"]
        assert temporal.source_window.bar_count == 0
        assert temporal.source_window.input_digest

    def test_clock_session_id_present(self, env):
        """I3: clock/session ids and their III.1 registry versions."""
        samples = _golden_samples(env)
        for name, sample in samples.items():
            assert sample.clock_id, name
            assert sample.session_id, name
            assert sample.clock_registry_version == CLOCK_REGISTRY_VERSION, name
            assert sample.session_registry_version == SESSION_REGISTRY_VERSION, name

    def test_instrument_present(self, env):
        """I4: every measurement carries its instrument id."""
        samples = _golden_samples(env)
        for name, sample in samples.items():
            assert sample.instrument_id, name
        assert _measure_seed_range(env, "eur", "EUR_SEED_T2").instrument_id == "EURUSD"
        assert (
            measure_au_scale(
                measurements_pkg.CALIBRATION_REGISTRY,
                CalibrationKey(**env["btc"]["calibration_key"]),
                "T2",
                provenance=_prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW"),
                source_window=_measure_seed_range(
                    env, "eur", "EUR_SEED_T2"
                ).source_window,
            ).instrument_id
            == "BTCUSD"
        )

    def test_calculation_timestamp_injected(self, env):
        """I5: injected, never wall-clock."""
        early = measure_range(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD"),
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(calc_ts="2026-03-03T09:00:00Z"),
            observation_cutoff=_utc(env["eur"]["observation_cutoff"]),
            quality_policy=env["policy"],
        )
        late = measure_range(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD"),
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(calc_ts="2026-03-03T18:30:00Z"),
            observation_cutoff=_utc(env["eur"]["observation_cutoff"]),
            quality_policy=env["policy"],
        )
        assert early.calculation_timestamp == _utc("2026-03-03T09:00:00Z")
        assert late.calculation_timestamp == _utc("2026-03-03T18:30:00Z")
        # Identical inputs and identical injected clock → identical record.
        repeat = measure_range(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD"),
            instrument=env["registry"].get("EURUSD"),
            provenance=_prov(calc_ts="2026-03-03T09:00:00Z"),
            observation_cutoff=_utc(env["eur"]["observation_cutoff"]),
            quality_policy=env["policy"],
        )
        assert repeat.to_json() == early.to_json()
        # No wall clock exists anywhere in the package.
        wall_clock = re.compile(
            r"(datetime\.now|utcnow|time\.time\s*\(|import random|from random)"
        )
        for name, source in _package_sources():
            assert not wall_clock.search(source), name

    def test_quality_state_present(self, env):
        """I6: quality state in the frozen III.1 vocabulary."""
        samples = _golden_samples(env)
        for name, sample in samples.items():
            assert isinstance(sample.quality_state, DataOutcome), name
            assert sample.quality_state in (DataOutcome.OK, DataOutcome.DEGRADED), name
        assert {member.value for member in DataOutcome} == {
            "OK",
            "DEGRADED",
            "DATA_QUALITY_BLOCKED",
            "NO_CALCULATION",
        }
        # A blocked measurement is refused at construction, not emitted.
        with pytest.raises(Exception):
            Measurement(
                definition_id="RANGE_MEASUREMENT",
                definition_version="V1",
                instrument_id="EURUSD",
                source_window=_measure_seed_range(
                    env, "eur", "EUR_SEED_T2"
                ).source_window,
                clock_id="America/New_York",
                clock_registry_version=CLOCK_REGISTRY_VERSION,
                session_id="EUR_DAILY.ASIAN_RANGE",
                session_registry_version=SESSION_REGISTRY_VERSION,
                calculation_timestamp=_utc(CALC_TS),
                quality_state=DataOutcome.DATA_QUALITY_BLOCKED,
                native_unit=NativeUnit.PIP,
                market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
                measurement_engine_version=MEASUREMENT_ENGINE_VERSION,
                evidence_refs=(),
            )

    def test_measurement_engine_version_recorded(self, env):
        """I7: the Book III final-record engine version travels everywhere."""
        assert MEASUREMENT_ENGINE_VERSION == "MEASUREMENT_ENGINE_V1"
        samples = _golden_samples(env)
        for name, sample in samples.items():
            assert sample.measurement_engine_version == MEASUREMENT_ENGINE_VERSION, name
            assert sample.market_data_schema_version == MARKET_DATA_SCHEMA_VERSION, name
        # An unknown engine version is refused at construction.
        with pytest.raises(Exception):
            Provenance(
                instrument_id="EURUSD",
                clock_id="America/New_York",
                session_id="EUR_DAILY.ASIAN_RANGE",
                calculation_timestamp=_utc(CALC_TS),
                measurement_engine_version="MEASUREMENT_ENGINE_V0",
            )

    def test_no_unsupported_statistic_fields(self, env):
        """I8/M5: no statistical field without an explicit evidence ref."""
        banned = {
            "probability",
            "prob",
            "p_value",
            "pvalue",
            "confidence",
            "sigma",
            "percentile",
            "correlation",
            "likelihood",
            "expectancy",
            "variance",
            "z_score",
            "win_rate",
            "sharpe",
        }
        samples = _golden_samples(env)
        for name, sample in samples.items():
            for item in fields(sample):
                assert not (_tokens(item.name) & banned), (name, item.name)
        # Evidence-bound definitions carry their evidence references.
        for definition_id in (
            "HO_D1D3_STATE",
            "HO_M1_SCALE",
            "HO_UNFINISHED_SIDE",
        ):
            spec = require_definition(definition_id, "V1")
            assert spec.evidence_refs, definition_id
        # A tier classification travels with its canonical evidence id.
        classification = samples["tier"]
        assert classification.evidence_refs, "EUR tier classification needs evidence"
        # Conversely, a synthetic-fixture range carries no evidence ref at all
        # (a synthetic fixture can never satisfy an evidence check — J7).
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        assert measured.evidence_refs == ()


# ---------------------------------------------------------------------------
# T10 — Golden measurement fixtures (J1–J7, K-a, L1, O4)
# ---------------------------------------------------------------------------


class TestT10GoldenFixtures:
    def test_golden_eur_fixtures_reproduce(self, env):
        """J1: EUR golden cases reproduce at the measurement layer."""
        # (a) T1/T2/T3/no-go daily seed tiers.
        calib = measurements_pkg.CALIBRATION_REGISTRY
        key = CalibrationKey(**env["eur"]["calibration_key"])
        for case_id in (
            "EUR_SEED_T1",
            "EUR_SEED_T2",
            "EUR_SEED_T3",
            "EUR_SEED_NO_GO",
        ):
            seed = _seed(env, "eur", case_id)
            measured = _measure_seed_range(env, "eur", case_id)
            expected = seed["expected"]
            assert str(measured.high.value) == expected["high"], case_id
            assert str(measured.low.value) == expected["low"], case_id
            assert measured.size.value == Decimal(expected["size_native"]), case_id
            assert measured.midpoint.value == Decimal(expected["midpoint"]), case_id
            assert measured.direction.value == expected["direction"], case_id
            assert (
                measured.close_location == Decimal(expected["close_location"])
            ), case_id
            assert (
                measured.consumed_fraction == Decimal(expected["consumed_fraction"])
            ), case_id
            assert (
                measured.range_left.value == Decimal(expected["range_left_native"])
            ), case_id
            classification = classify_tier(
                calib, key, measured.size, provenance=_prov(),
                source_window=measured.source_window,
            )
            assert classification.tier_id == expected["expected_tier_id"], case_id
            assert classification.no_go is expected["expected_no_go"], case_id
        # (b) The rekey-ladder coordinate families.
        ladder_anchor = AnchorRecord(
            anchor_id="EUR.LADDER.ANCHOR",
            model_id=env["ladder"]["model_id"],
            model_version=env["ladder"]["model_version"],
            status=AnchorStatus.ACTIVE,
            rule=AnchorRule(
                rule_id="TEST.RULE",
                rule_version="V1",
                materialization=RuleMaterialization.CANONICAL,
                source_ref=env["ladder"]["source_ref"],
            ),
            earned_range=_measure_seed_range(env, "eur", "EUR_SEED_T2"),
        )
        for row in env["ladder"]["ladder"]:
            projection = project_coordinates(
                ladder_anchor, row["family_id"], provenance=_prov()
            )
            assert (
                str(projection.projected_price.value)
                == row["expected_projected_price"]
            ), row["family_id"]
            assert projection.level == Decimal(row["level"])
            # A coordinate is a level and nothing more.
            names = {item.name for item in fields(projection)}
            assert not (
                names & {"acceptance", "rekey", "promotion", "setup", "touch"}
            )
        # (c) The event-conditioned residual budget.
        event = _event_from_fixture(env, 0)
        budget = measure_event_budget(
            event,
            NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("6")),
            provenance=_prov(),
        )
        assert budget.residual.value == Decimal(
            env["events"]["events"][0]["expected_residual"]
        )
        # (d) Weekly outer-node projections labeled RESEARCH.
        weekly_key = CalibrationKey(**env["weekly"]["calibration_key"])
        table = calib.weekly_outer_nodes(weekly_key)
        assert table.status is CalibrationStatus.RESEARCH
        assert env["weekly"]["calibration_status"] == "RESEARCH"
        for tier_id, magnitude, sample_n in table.outer_nodes:
            expected = next(
                row
                for row in env["weekly"]["outer_nodes"]
                if row["tier_id"] == tier_id
            )
            assert magnitude == Decimal(expected["median_range"])
            assert sample_n == expected["sample_n"]
        # (e) Higher-order D3/M1/M2/M3 structural handoff.
        assert env["ho"]["hierarchy"] == [
            "QUARTER_SEED",
            "M1_RANGE_SEED",
            "M2_SHAPING",
            "M3_RESOLUTION",
            "WEEKLY_LOCAL_PATH",
            "DAILY_EXECUTION",
        ]
        assert _ho_seed(env, "D3").size.value == Decimal("13.0")
        assert _ho_seed(env, "M1").size.value == Decimal("120.0")
        assert _ho_seed(env, "M2").size.value == Decimal("100.0")
        # Statistical parameters travel by evidence id only (III.2-GAP-6).
        assert set(env["ho"]["evidence_refs"]) == {
            "EV.EUR.HO.D3_DIRECTION.V1",
            "EV.EUR.HO.M1_RANGE_CORR.V1",
            "EV.EUR.HO.UNFINISHED_M3.V1",
        }

    def test_golden_xau_fixtures_reproduce(self, env):
        """J2: XAU golden cases reproduce; promotion stays non-executable."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        xau_key = CalibrationKey(**env["xau"]["calibration_key"])
        window = source_window_from_bars(
            _bars_from_rows(_seed(env, "eur", "EUR_SEED_T2")["rows"], "EURUSD")
        )
        # (a) Normal spatial-band state.
        for probe in env["xau"]["band_probes"]:
            classification = classify_spatial_band(
                calib,
                xau_key,
                NativeMagnitude("XAUUSD", NativeUnit.POINT, Decimal(probe["magnitude"])),
                provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
                source_window=window,
            )
            assert classification.band_id == probe["expected_band_id"], probe
            assert classification.band_state.value == probe["expected_state"]
            assert classification.calibration_status is CalibrationStatus.RESEARCH
        # (b) Promotion examples are disclosed sample statistics, not
        # executable rates: they are fixture disclosures only and no
        # calibration encodes them.
        for example in env["xau"]["promotion_examples"]:
            assert example["standing"] in {
                "VALIDATED_SMALL_N",
                "RESEARCH_FLAG_SMALL_N",
            }
            assert "small_n" in example["standing"].lower()
            assert "not a trade win rate" in example["disclosure"]
            assert example["sample_n"] in (48, 25)
        assert all(
            "PROMOTION" not in key.calibration_id for key in calib.keys()
        ), "promotion examples must never become a calibration"
        # (c) The 132 state proves no automatic 168.
        anchor = AnchorRecord(
            anchor_id="XAU.ANCHOR.ACTIVE.01",
            model_id="XAU.GAME.L1_L2_L3.V1",
            model_version="V1",
            status=AnchorStatus.ACTIVE,
            rule=AnchorRule(
                rule_id="TEST.RULE",
                rule_version="V1",
                materialization=RuleMaterialization.CANONICAL,
                source_ref=env["xau"]["source_ref"],
            ),
            earned_range=self._xau_range(env),
        )
        for row in env["xau"]["coordinate_ladder"]:
            projection = project_coordinates(
                anchor, row["family_id"],
                provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
            )
            assert (
                str(projection.projected_price.value)
                == row["expected_projected_price"]
            ), row["family_id"]
        assert env["xau"]["not_declared_families"][0]["family_id"] == "XAU_168"
        with pytest.raises(Exception) as excinfo:
            project_coordinates(
                anchor,
                "XAU_168",
                provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
            )
        assert (
            getattr(excinfo.value, "code", None)
            == env["xau"]["not_declared_families"][0]["expected_refusal"]
        )
        # (d) Quarter-zone eligible vs blind-touch paths.
        zone = env["xau"]["quarter_zone"]
        level = PathLevel(
            level_id="QUARTER_ZONE",
            price=NativePrice("XAUUSD", NativeUnit.POINT, Decimal(zone["zone_level"])),
            side=LevelSide(zone["zone_side"]),
        )
        for case_key, case in (
            ("eligible_case", zone["eligible_case"]),
            ("blind_touch_case", zone["blind_touch_case"]),
        ):
            bars = _bars_from_rows(case["rows"], "XAUUSD")
            measured = measure_path(
                bars,
                instrument=env["registry"].get("XAUUSD"),
                provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
                observation_cutoff=_utc(env["xau"]["observation_cutoff"]),
                quality_policy=env["policy"],
                levels=[level],
            )
            outcome = measured.levels[0]
            assert outcome.touch_state.value == case["expected_touch_state"], case_key
            assert (
                outcome.acceptance_state.value
                == case["expected_acceptance_state"]
            ), case_key
            assert (
                outcome.close_beyond_state.value
                == case["expected_close_beyond_state"]
            ), case_key
            assert (
                outcome.re_entry_state.value == case["expected_re_entry_state"]
            ), case_key
            assert (
                outcome.rejection_state.value == case["expected_rejection_state"]
            ), case_key
            assert measured.mae.value == Decimal(case["expected_mae_native"]), case_key
            assert measured.mfe.value == Decimal(case["expected_mfe_native"]), case_key
            if "expected_first_delivery_bar_index" in case:
                assert measured.first_delivery is not None
                assert (
                    measured.first_delivery.bar_index
                    == case["expected_first_delivery_bar_index"]
                )
        # "No blind touch entry" is the operator doctrine; the measurement
        # layer only reports the typed facts behind it.
        assert zone["source_quote"] == "No blind touch entry."
        # The earned-range geometry behind the zone.
        earned = zone["earned_range"]
        assert earned["size_native"] == "17"

    def _xau_range(self, env) -> RangeMeasurement:
        # Build the XAU earned range from the fixture's declared geometry.
        low = Decimal(env["xau"]["quarter_zone"]["earned_range"]["low"])
        high = Decimal(env["xau"]["quarter_zone"]["earned_range"]["high"])
        bars = _ohlc_bars(
            "XAUUSD",
            [
                (str(low + Decimal("1")), str(low + Decimal("8")), str(low), str(low + Decimal("6"))),
                (str(low + Decimal("6")), str(high), str(low + Decimal("5")), str(high - Decimal("1"))),
                (str(high - Decimal("1")), str(high), str(low + Decimal("4")), str(high - Decimal("3"))),
            ],
            "2026-03-03T00:00:00Z",
        )
        return measure_range(
            bars,
            instrument=env["registry"].get("XAUUSD"),
            provenance=_prov("XAUUSD", "XAU_GAME.ASIAN_RANGE"),
            observation_cutoff=_utc(env["xau"]["observation_cutoff"]),
            quality_policy=env["policy"],
        )

    def test_golden_btc_fixtures_reproduce(self, env):
        """J3: BTC native tiers, slot×tier range-left, no Game object."""
        calib = measurements_pkg.CALIBRATION_REGISTRY
        key = CalibrationKey(**env["btc"]["calibration_key"])
        slot_expected = env["btc"]["slot_surface"]["expected_range_left_native"]
        for case_id in (
            "BTC_SEED_T1",
            "BTC_SEED_T2",
            "BTC_SEED_T3",
            "BTC_SEED_NO_GO",
        ):
            seed = _seed(env, "btc", case_id)
            measured = _measure_seed_range(env, "btc", case_id)
            expected = seed["expected"]
            assert str(measured.high.value) == expected["high"], case_id
            assert str(measured.low.value) == expected["low"], case_id
            assert measured.size.value == Decimal(expected["size_native"]), case_id
            assert (
                measured.range_left.value == Decimal(expected["range_left_native"])
            ), case_id
            classification = classify_tier(
                calib,
                key,
                measured.size,
                provenance=_prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW"),
                source_window=measured.source_window,
            )
            assert classification.tier_id == expected["expected_tier_id"], case_id
            # Slot × tier range-left surface agrees with the measured seed.
            if classification.tier_id in slot_expected:
                assert (
                    measured.range_left.value
                    == Decimal(slot_expected[classification.tier_id])
                ), case_id
            # Tracker-side measurement output contains no Game/setup object.
            payload = json.dumps(encode_value(classification), sort_keys=True)
            assert "GAME" not in payload
            assert "setup" not in payload.lower()
            assert classification.instrument_id == "BTCUSD"
        # The >$3,000 no-go boundary is a canonical classification.
        no_go = classify_tier(
            calib,
            key,
            NativeMagnitude("BTCUSD", NativeUnit.DOLLAR, Decimal("3500")),
            provenance=_prov("BTCUSD", "BTC_TRACKER.ASIAN_WINDOW"),
            source_window=_measure_seed_range(env, "btc", "BTC_SEED_T1").source_window,
        )
        assert no_go.tier_id == "NO_GO" and no_go.no_go is True
        # AU, thresholds and density zones reproduce from the fixture.
        assert [row["au"] for row in env["btc"]["au_values"]] == [
            "205",
            "545",
            "1160",
        ]
        assert [str(row["lower"]) + "-" + str(row["upper"]) for row in env["btc"]["density_zones"]] == [
            "164-246",
            "436-654",
            "928-1392",
        ]

    def test_golden_jpy_fixtures_reproduce(self, env):
        """J4: JPY DT structures declared by the card; tiers refused."""
        jpy_set = COORDINATE_SETS[
            (env["jpy"]["model_id"], env["jpy"]["model_version"])
        ]
        fixture_families = {row["family_id"]: row for row in env["jpy"]["declared_families"]}
        assert set(jpy_set.family_ids) == set(fixture_families)
        for family in jpy_set.families:
            fixture = fixture_families[family.family_id]
            assert family.level == Decimal(fixture["level"])
            assert family.declared_extension is fixture["declared_extension"]
            assert env["jpy"]["source_ref"] in family.source_ref
            assert family.source_quote == env["jpy"]["source_quote"]
        # Projection works from a JPY-earned range in JPY native units.
        instrument = _usdjpy()
        bars = _ohlc_bars(
            "USDJPY",
            [
                ("150.000", "150.060", "149.990", "150.040"),
                ("150.040", "150.120", "150.030", "150.100"),
                ("150.100", "150.130", "150.080", "150.110"),
            ],
            "2026-03-03T01:00:00Z",
        )
        measured = measure_range(
            bars,
            instrument=instrument,
            provenance=_prov("USDJPY", "JPY_CARRY.ASIAN_RANGE"),
            observation_cutoff=_utc("2026-03-03T09:00:00Z"),
            quality_policy=env["policy"],
        )
        assert measured.size.unit is NativeUnit.PIP
        assert measured.size.value == Decimal("14.0")  # 0.140 / 0.01
        anchor = AnchorRecord(
            anchor_id="JPY.ANCHOR.ACTIVE.01",
            model_id=env["jpy"]["model_id"],
            model_version=env["jpy"]["model_version"],
            status=AnchorStatus.ACTIVE,
            rule=AnchorRule(
                rule_id="TEST.RULE",
                rule_version="V1",
                materialization=RuleMaterialization.CANONICAL,
                source_ref=env["jpy"]["source_ref"],
            ),
            earned_range=measured,
        )
        for row in env["jpy"]["declared_families"]:
            projection = project_coordinates(
                anchor,
                row["family_id"],
                provenance=_prov("USDJPY", "JPY_CARRY.ASIAN_RANGE"),
            )
            assert projection.level == Decimal(row["level"])
            assert projection.model_version == "DT_12_4PM"
            assert projection.projected_price.instrument_id == "USDJPY"
        # Native per-pair tier tables are not canonical (III.2-GAP-2):
        # the lookup refuses instead of inventing a JPY table.
        with pytest.raises(Exception) as excinfo:
            measurements_pkg.CALIBRATION_REGISTRY.tier_table(
                CalibrationKey(
                    model_id=env["jpy"]["model_id"],
                    model_version=env["jpy"]["model_version"],
                    calibration_id="JPY_PAIR_TIERS",
                    calibration_version="V1",
                )
            )
        assert getattr(excinfo.value, "code", None) == "MODEL_VERSION_UNAVAILABLE"
        assert env["jpy"]["native_tier_tables"] == "NOT_CANONICAL"
        # Basket-role cases are deferred and disclosed, never claimed here.
        deferred_ids = {row["case_id"] for row in env["jpy"]["deferred_cases"]}
        assert deferred_ids == {
            "JPY_BASKET.AGREE_AND_CONFIRM",
            "JPY_BASKET.CONFIRM_ABSENT",
            "JPY_BASKET.NO_EQUAL_VOTE",
        }
        for row in env["jpy"]["deferred_cases"]:
            reason = row["reason"]
            assert (
                "III.3" in reason
                or "no aggregation" in reason
                or "single-asset facts only" in reason
            ), row["case_id"]
        # The asset role map travels as a declaration, not an aggregation.
        assert {row["role"] for row in env["jpy"]["asset_roles"]} == {
            "CARRY_MASTER",
            "RISK_EXPRESSION",
            "CONFIRMATION_VETO",
        }

    def test_golden_fib_fixtures_reproduce(self, env):
        """J5: born range projects; unresolved refuses; rekey transitions."""
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T2")
        assert str(measured.low.value) == env["fib"]["earned_range_low"]
        assert str(measured.high.value) == env["fib"]["earned_range_high"]
        rule = AnchorRule(
            rule_id=env["fib"]["rule"]["rule_id"],
            rule_version=env["fib"]["rule"]["rule_version"],
            materialization=RuleMaterialization(
                env["fib"]["rule"]["materialization"]
            ),
            source_ref=env["fib"]["rule"]["source_ref"],
        )
        reports = {}
        for case in env["fib"]["cases"]:
            status = AnchorStatus(case["status"])
            anchor = AnchorRecord(
                anchor_id=case["anchor_id"],
                model_id=env["fib"]["model_id"],
                model_version=env["fib"]["model_version"],
                status=status,
                rule=rule,
                earned_range=measured,
                invalidation_reason=case.get("invalidation_reason"),
                rekey_source_anchor_id=(
                    case["anchor_id"]
                    if status is AnchorStatus.REKEYED
                    else None
                ),
            )
            report = evaluate_anchor(anchor, provenance=_prov())
            assert report.refusal_code.value == case["expected_refusal_code"], case
            assert report.automation_ready is case["expected_automation_ready"], case
            reports[case["case_id"]] = (anchor, report)
            if status in (AnchorStatus.ELIGIBLE, AnchorStatus.ACTIVE):
                assert report.status is status
        # Valid born range → the full coordinate ladder reproduces.
        active = reports["FIB.VALID_BORN_RANGE"][0]
        for row in env["fib"]["coordinate_ladder"]:
            projection = project_coordinates(
                active, row["family_id"], provenance=_prov()
            )
            assert (
                str(projection.projected_price.value)
                == row["expected_projected_price"]
            ), row["family_id"]
        # Unresolved and invalidated anchors refuse projection.
        for case_id in ("FIB.UNRESOLVED_ANCHOR", "FIB.INVALIDATED_ANCHOR"):
            anchor, _report = reports[case_id]
            with pytest.raises(Exception) as excinfo:
                project_coordinates(anchor, "FIB_50", provenance=_prov())
            assert getattr(excinfo.value, "code", None) == "ANCHOR_NOT_EARNED"
        # Rekey transition interface output.
        rekey_case = next(
            case for case in env["fib"]["cases"] if case["case_id"] == "FIB.REKEY_TRANSITION"
        )
        transition = rekey_anchor(
            active,
            rekey_case["successor_anchor_id"],
            mapping=rekey_case["mapping"],
            provenance=_prov(),
        )
        assert dict(transition.mapping) == rekey_case["mapping"]
        # The arbitrary local pivot case is rejected by construction.
        rejected = env["fib"]["rejected_cases"][0]
        assert rejected["expected_refusal"] == "ANCHOR_NOT_EARNED"
        pivot_anchor = AnchorRecord(
            anchor_id="FIB.PIVOT.ANCHOR",
            model_id=env["fib"]["model_id"],
            model_version=env["fib"]["model_version"],
            status=AnchorStatus.UNRESOLVED,
            rule=rule,
            earned_range=None,
        )
        with pytest.raises(Exception) as excinfo:
            project_coordinates(pivot_anchor, "FIB_50", provenance=_prov())
        assert getattr(excinfo.value, "code", None) == rejected["expected_refusal"]

    def test_fixture_manifest_hashes_recorded(self, env):
        """J6: LF-normalized content hashes, EOL-independent."""
        manifest = _load(FIXTURE_DIR, "FIXTURE_MANIFEST.json")
        assert manifest["algorithm"] == "sha256"
        assert manifest["generator"] == "generate_fixtures.py"
        recorded = manifest["files"]
        on_disk = sorted(
            path.name
            for path in FIXTURE_DIR.glob("*.json")
            if path.name != "FIXTURE_MANIFEST.json"
        )
        assert sorted(recorded) == on_disk
        for name, expected in recorded.items():
            raw = (FIXTURE_DIR / name).read_bytes()
            lf = raw.replace(b"\r\n", b"\n")
            # Hashes are recorded over LF-normalized content, so a CRLF
            # worktree and an LF checkout verify identically.
            assert hashlib.sha256(lf).hexdigest() == expected, name
            crlf = lf.replace(b"\n", b"\r\n")
            assert hashlib.sha256(crlf.replace(b"\r\n", b"\n")).hexdigest() == expected, name

    def test_synthetic_fixtures_labeled(self, env):
        """J7/O4: synthetic fixtures are labeled and never evidence."""
        synthetic_fixtures = []
        for path in sorted(FIXTURE_DIR.glob("*.json")):
            if path.name == "FIXTURE_MANIFEST.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data["provenance"] in {
                "SYNTHETIC_FIXTURE",
                "CANONICAL_SOURCE_SLICE",
            }, path.name
            if data["provenance"] == "SYNTHETIC_FIXTURE":
                synthetic_fixtures.append(path.name)
                assert data["data_classification"].startswith("SYNTHETIC_FIXTURE")
                assert "not empirical market evidence" in data["data_classification"]
        assert "eur_daily_tier_seeds.json" in synthetic_fixtures
        assert "fib_anchor_cases.json" in synthetic_fixtures
        # A synthetic bar can never carry an evidence reference (III.1 N4).
        with pytest.raises(Exception):
            _bar(
                "EURUSD",
                "1.07900",
                "1.07980",
                "1.07890",
                "1.07950",
                start=_utc("2026-03-03T03:00:00Z"),
                provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
                source_ref="EV.SYNTHETIC.NOT.ALLOWED",
            )
        # Measurements over synthetic bars carry no evidence reference.
        measured = _measure_seed_range(env, "eur", "EUR_SEED_T1")
        assert measured.evidence_refs == ()
        # The synthetic provenance label travels to the event output.
        event = _event_from_fixture(env, 0)
        features = measure_event_features(
            event, provenance=_prov(), source_window=None
        )
        assert features.provenance_label == "SYNTHETIC_FIXTURE"

    def test_deferred_golden_program_cases_disclosed(self, env):
        """J8: later-bloc golden-program cases are deferred, never claimed."""
        fib_deferred = env["fib"]["deferred_cases"][0]
        assert fib_deferred["case_id"] == "FIB.R15.AUTOMATION_APPROVAL"
        jpy_deferred = {row["case_id"] for row in env["jpy"]["deferred_cases"]}
        assert jpy_deferred == {
            "JPY_BASKET.AGREE_AND_CONFIRM",
            "JPY_BASKET.CONFIRM_ABSENT",
            "JPY_BASKET.NO_EQUAL_VOTE",
        }
        # Nothing in this package aggregates basket roles or approves
        # automation: those APIs do not exist here.
        for name, source in _package_sources():
            assert "agree_and_confirm" not in source, name
            assert "automation_approval" not in source, name
        samples = _golden_samples(env)
        assert samples["anchor_eligibility"].automation_ready is False


# ---------------------------------------------------------------------------
# T11 — Label / serialization discipline (K-b, K-d, N11, P5, P9)
# ---------------------------------------------------------------------------


BANNED_PREDICTION_TOKENS = {
    "prediction",
    "predictions",
    "predict",
    "forecast",
    "forecasts",
    "signal",
    "signals",
    "call",
    "calls",
    "expectancy",
    "winrate",
    "win",
    "wins",
    "wager",
}

BANNED_STATUS_TOKENS = {
    "guaranteed",
    "certain",
    "certainly",
    "surely",
    "victim",
    "kill",
    "slay",
    "destiny",
    "inevitable",
    "definitely",
    "always",
    "prophecy",
}


def _all_package_enums() -> list[type[Enum]]:
    found: list[type[Enum]] = []
    for module in _package_modules():
        for attribute in vars(module).values():
            if (
                isinstance(attribute, type)
                and issubclass(attribute, Enum)
                and attribute.__module__.startswith("app.forge.measurements")
                and attribute not in found
            ):
                found.append(attribute)
    assert found, "the package must define enums"
    return found


class TestT11LabelDiscipline:
    def test_no_prediction_or_signal_vocabulary(self, env):
        """K-b: no prediction/signal/call/expectancy/win-rate vocabulary."""
        # Enum members.
        for enum_class in _all_package_enums():
            for member in enum_class:
                tokens = _tokens(str(member.value))
                offenders = tokens & BANNED_PREDICTION_TOKENS
                assert not offenders, (enum_class.__name__, member, offenders)
        # Dataclass field names across every measurement the engine emits.
        samples = _golden_samples(env)
        for name, sample in samples.items():
            for item in fields(sample):
                offenders = _tokens(item.name) & BANNED_PREDICTION_TOKENS
                assert not offenders, (name, item.name, offenders)
            # Serialized payload keys and values.
            payload = json.loads(json.dumps(encode_value(sample), sort_keys=True))
            stack = [payload]
            while stack:
                current = stack.pop()
                if isinstance(current, dict):
                    for key, value in current.items():
                        offenders = _tokens(str(key)) & BANNED_PREDICTION_TOKENS
                        assert not offenders, (name, key, offenders)
                        stack.append(value)
                elif isinstance(current, list):
                    stack.extend(current)
                elif isinstance(current, str):
                    tokens = _tokens(current)
                    offenders = tokens & BANNED_PREDICTION_TOKENS
                    assert not offenders, (name, current, offenders)
        # Enum and field vocabulary of the package-wide definitions table.
        for spec in DEFINITION_REGISTRY.values():
            offenders = _tokens(spec.unit) & BANNED_PREDICTION_TOKENS
            assert not offenders, spec.definition_id

    def test_serialization_roundtrip_preserves_distinctions(self, env):
        """K-d: touch/acceptance/path distinctions survive a round trip."""
        samples = _golden_samples(env)
        for name, sample in samples.items():
            encoded = encode_value(sample)
            text = json.dumps(encoded, sort_keys=True)
            restored = decode_value(sample, json.loads(text))
            assert restored == sample, name
            # Re-encoding is byte-identical.
            assert json.dumps(encode_value(restored), sort_keys=True) == text, name
        # The path-specific distinctions are individually addressable.
        path = samples["path"]
        payload = json.loads(json.dumps(encode_value(path), sort_keys=True))
        level = payload["levels"][0]
        assert level["touch_state"] != level["acceptance_state"]
        assert level["close_beyond_state"] != level["re_entry_state"]
        # Rebuilding the enum from its value yields the same typed member.
        assert TouchState(level["touch_state"]) is TouchState.TOUCHED

    def test_status_labels_factual_enum_only(self, env):
        """N11: no deterministic rhetoric in runtime status labels."""
        for enum_class in _all_package_enums():
            for member in enum_class:
                tokens = _tokens(str(member.value))
                offenders = tokens & BANNED_STATUS_TOKENS
                assert not offenders, (enum_class.__name__, member, offenders)
                # Values are factual operational words, never prose.
                assert " " not in str(member.value), (enum_class.__name__, member)

    def test_bounded_enums_no_free_text(self, env):
        """P5: quality/measurement enums are bounded with no free text."""
        for enum_class in _all_package_enums():
            members = list(enum_class)
            assert len(members) <= 20, enum_class.__name__
            for member in members:
                assert re.fullmatch(
                    r"[A-Z][A-Z0-9_]*", str(member.value)
                ), (enum_class.__name__, member.value)

    def test_measurements_immutable(self, env):
        """P9: measurements are immutable; redefinition needs a new version."""
        samples = _golden_samples(env)
        for name, sample in samples.items():
            assert sample.__dataclass_params__.frozen is True, name
            with pytest.raises(FrozenInstanceError):
                setattr(sample, "definition_version", "V2")
        # A drifted definition version refuses rather than silently redefining.
        spec = require_definition("RANGE_MEASUREMENT", "V1")
        assert spec.definition_version == "V1"
        with pytest.raises(Exception) as excinfo:
            require_definition("RANGE_MEASUREMENT", "V2")
        assert getattr(excinfo.value, "code", None) == "UNKNOWN_DEFINITION"
        with pytest.raises(Exception):
            require_definition("NOT_A_REGISTERED_DEFINITION", "V1")


# ---------------------------------------------------------------------------
# T12 — Boundaries and security (O1–O6, P1–P8)
# ---------------------------------------------------------------------------


BANNED_TRADING_TOKENS = {
    "trade",
    "trading",
    "trades",
    "win",
    "wins",
    "won",
    "loss",
    "losses",
    "expectancy",
    "takeprofit",
    "stoploss",
    "position",
    "positions",
    "leverage",
    "portfolio",
    "profit",
    "profits",
    "pnl",
    "roi",
    "buy",
    "buys",
    "sell",
    "sells",
    "signal",
    "signals",
    "hedge",
    "margin",
    "drawdown",
    "sharpe",
    "game",
    "gamble",
    "casino",
    "bet",
}

SECRET_PATTERN = re.compile(
    r"(api[_-]?key\s*[:=]|secret[_-]?key\s*[:=]|password\s*[:=]|passwd"
    r"|bearer\s+[A-Za-z0-9._-]{8,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{16,})",
    re.IGNORECASE,
)


def _source_identifiers() -> set[str]:
    """All declared/referenced identifiers of the package (no prose)."""
    names: set[str] = set()
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
    return names


class TestT12Boundaries:
    def test_no_book1_authority_imports(self, env):
        """O1: measurements are not models, claims, evidence or setups."""
        forbidden_prefixes = (
            "app.forge.qa",
            "app.forge.retrieval",
            "app.forge.provenance",
            "app.forge.canonical",
            "app.forge.policy",
            "app.forge.service",
            "app.forge.providers",
            "app.forge.persistence",
            "app.forge.observability",
            "app.forge.backfill",
        )
        for path in sorted(PACKAGE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(
                            forbidden_prefixes
                        ), (path.name, alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.level and node.level > 0:
                        continue  # intra-package relative import
                    module = node.module or ""
                    assert not module.startswith(
                        forbidden_prefixes
                    ), (path.name, module)
                    # The only absolute app import is the III.1 contract.
                    if module.startswith("app."):
                        assert module.startswith(
                            "app.forge.market_data"
                        ), (path.name, module)
        # And the package never touches the composition root.
        for name, source in _package_sources():
            assert "ForgeServiceContainer" not in source, name

    def test_no_corpus_writes(self, env):
        """O2: III.2 never grants itself evidence authority."""
        # The package performs no file write at all.
        write_pattern = re.compile(
            r"""open\s*\([^)]*['"]w['"]|write_text\s*\(|write_bytes\s*\(|"""
            r"""os\.remove|os\.rename|\.unlink\s*\("""
        )
        for name, source in _package_sources():
            assert not write_pattern.search(source), name
        # The Book I freeze manifest is unchanged against HEAD.
        try:
            shown = subprocess.run(
                [
                    "git",
                    "show",
                    "HEAD:implementation/forge/book_i/bloc_i_5/BOOK_I_FREEZE_MANIFEST_V1.md",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        if shown.returncode == 0:
            head_bytes = shown.stdout.replace(b"\r\n", b"\n")
            work_bytes = BOOK_I_FREEZE_MANIFEST.read_bytes().replace(b"\r\n", b"\n")
            assert head_bytes == work_bytes
        # The corpus working tree is untouched by this suite.
        try:
            diff = subprocess.run(
                ["git", "status", "--porcelain", "--", "corpus/"],
                cwd=REPO_ROOT,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        assert diff.returncode == 0
        assert diff.stdout.strip() == b"", diff.stdout.decode(errors="replace")

    def test_fixtures_labeled_historical(self, env):
        """O3: historical observation is never served as current state."""
        for path in sorted(FIXTURE_DIR.glob("*.json")):
            if path.name == "FIXTURE_MANIFEST.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data["historical"] is True, path.name
            assert data["provenance"] in {
                "SYNTHETIC_FIXTURE",
                "CANONICAL_SOURCE_SLICE",
            }, path.name
        # Cutoffs are explicit wherever a bar window exists.
        for fixture in ("eur", "btc", "xau", "ladder"):
            data = env[fixture]
            assert data["observation_cutoff"], fixture
            assert data["observation_cutoff"].endswith("Z")
        for seed in env["ho"]["seeds"]:
            assert seed["observation_cutoff"].endswith("Z")

    def test_no_trading_or_game_concepts(self, env):
        """O6: no trading/game concepts as identifiers (canonical exception:
        the BTC ``trigger_levels`` field, preserved verbatim from
        ``BTC.TRACKER.DWM.V1`` per PLAN.md §6)."""
        identifiers = _source_identifiers()
        offenders: set[str] = set()
        for identifier in identifiers:
            tokens = _tokens(identifier)
            if tokens & BANNED_TRADING_TOKENS:
                offenders.add(identifier)
        assert not offenders, sorted(offenders)
        # Enum values and dataclass field names are checked too.
        for enum_class in _all_package_enums():
            for member in enum_class:
                assert not (_tokens(str(member.value)) & BANNED_TRADING_TOKENS), (
                    enum_class.__name__,
                    member.value,
                )
        samples = _golden_samples(env)
        for name, sample in samples.items():
            for item in fields(sample):
                assert not (_tokens(item.name) & BANNED_TRADING_TOKENS), (
                    name,
                    item.name,
                )
        # The disclosed exception exists only as canonical prose/fixture
        # vocabulary, never as a package identifier.
        assert "trigger_levels" not in identifiers

    def test_no_network_calls(self, env, monkeypatch):
        """P1: no network anywhere in the suite."""
        import_pattern = re.compile(
            r"^\s*(?:import|from)\s+(?:socket|requests|urllib|httpx|aiohttp|websockets|telnetlib)\b",
            re.MULTILINE,
        )
        for name, source in _package_sources():
            assert not import_pattern.search(source), name

        def boom(*_args, **_kwargs):
            raise AssertionError("network access is forbidden in Bloc III.2")

        monkeypatch.setattr(socket, "socket", boom)
        monkeypatch.setattr(socket, "create_connection", boom)
        monkeypatch.setattr(socket, "getaddrinfo", boom)
        # The full measurement pipeline runs offline under the guard.
        payload = _golden_pipeline(env)
        assert payload

    def test_discover_migrations_unchanged(self, env):
        """P2: no new persistence migration."""
        versions = [migration.version for migration in discover_migrations()]
        assert versions == [1, 2, 3, 4]
        assert not list(
            (REPO_ROOT / "app" / "forge" / "persistence" / "sql").glob("005_*.sql")
        )

    def test_market_data_readiness_seam_unchanged(self, env):
        """P3: the container readiness disclosure is identical."""
        container = ForgeServiceContainer(config=ForgeConfig(environment="test"))
        deps = container.as_readiness_dependencies()
        assert deps["market_data"] == {
            "status": "NOT_CONFIGURED",
            "required": False,
            "note": "market-data providers belong to Book III; not wired at II.1",
        }
        # This bloc never imports the composition root (no silent rewiring).
        for name, source in _package_sources():
            assert "ForgeServiceContainer" not in source, name
        for path in sorted(PACKAGE_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    assert not node.module.startswith(
                        "app.forge.service"
                    ), (path.name, node.module)

    def test_frozen_manifests_unchanged(self, env):
        """P4: Book II 50 hashes, 23 planning pins and Book I manifest."""
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
        planning_text = PLANNING_FREEZE_MANIFEST.read_text(encoding="utf-8")
        pins = re.findall(
            r"^-\s+(\S+)\s*\r?\n\s+commit\s+([0-9a-f]{40})\s*$",
            planning_text,
            re.MULTILINE,
        )
        assert len(pins) == 23, len(pins)
        for rel_path, _sha in pins:
            assert (REPO_ROOT / rel_path).exists(), rel_path
        try:
            def _git(*args: str):
                return subprocess.run(
                    ["git", *args], cwd=REPO_ROOT, capture_output=True, timeout=30
                )

            available = sum(
                1
                for _path, sha in pins
                if _git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0
            )
        except (OSError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        if available == len(pins):
            # Full verification when the pin objects exist: each pinned file
            # still matches the committed content at its planning pin.
            for rel_path, sha in pins:
                shown_pin = _git("show", f"{sha}:{rel_path}")
                assert shown_pin.returncode == 0, rel_path
                head_content = shown_pin.stdout.replace(b"\r\n", b"\n")
                work_content = (REPO_ROOT / rel_path).read_bytes().replace(
                    b"\r\n", b"\n"
                )
                assert head_content == work_content, rel_path
        try:
            shown = subprocess.run(
                [
                    "git",
                    "show",
                    "HEAD:implementation/forge/book_i/bloc_i_5/BOOK_I_FREEZE_MANIFEST_V1.md",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        if shown.returncode == 0:
            head_bytes = shown.stdout.replace(b"\r\n", b"\n")
            work_bytes = BOOK_I_FREEZE_MANIFEST.read_bytes().replace(b"\r\n", b"\n")
            assert head_bytes == work_bytes

    def test_iii1_interfaces_unchanged(self, env):
        """P4: the 11 ratified III.1 module hashes from PLAN.md §6."""
        text = III2_PLAN.read_text(encoding="utf-8")
        pairs = re.findall(
            r"`([A-Za-z_]+\.py) ([0-9a-f]{8})…([0-9a-f]{4,5})`", text
        )
        assert len(pairs) == 11, len(pairs)
        for name, prefix, suffix in pairs:
            target = III1_PACKAGE_DIR / name
            assert target.exists(), name
            raw = target.read_bytes()
            normalized = raw.replace(b"\r\n", b"\n")
            candidates = (
                raw,
                normalized,
                normalized.replace(b"\n", b"\r\n"),
            )
            matched = any(
                hashlib.sha256(candidate).hexdigest().startswith(prefix)
                and hashlib.sha256(candidate).hexdigest().endswith(suffix)
                for candidate in candidates
            )
            assert matched, name

    def test_no_credentials_in_data_path(self, env):
        """P5: no secrets/credentials/PII in the data path."""
        for name, source in _package_sources():
            assert not SECRET_PATTERN.search(source), name
        for path in sorted(FIXTURE_DIR.glob("*.json")):
            assert not SECRET_PATTERN.search(
                path.read_text(encoding="utf-8")
            ), path.name

    def test_deterministic_repeat_runs(self, env):
        """P7: injected clocks; two full runs produce identical results."""
        first = _golden_pipeline(env)
        second = _golden_pipeline(env)
        assert first == second
        # Every value in the payload is derived from fixtures and the
        # injected timestamp — never from wall time.
        assert _utc(CALC_TS).isoformat() in first or "2026-03-03" in first
        wall_clock = re.compile(
            r"(datetime\.now|utcnow|time\.time\s*\(|import random|from random)"
        )
        for name, source in _package_sources():
            assert not wall_clock.search(source), name
