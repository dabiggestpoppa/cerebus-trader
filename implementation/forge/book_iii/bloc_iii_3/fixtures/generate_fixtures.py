"""Deterministic golden-fixture generator for Bloc III.3.

Run from this directory:  ``python generate_fixtures.py`` (regeneration)
or ``python generate_fixtures.py --check`` (byte-identical reproduction
plus replay-hash reproduction — the EVIDENCE golden check).

Every emitted file is a function of the fixed literals below plus the
committed III.1/III.2 fixture slices read **read-only** — no wall
clock, no randomness, no network — so regeneration is byte-identical
and the hashes recorded in ``FIXTURE_MANIFEST.json`` verify.

Provenance honesty (PLAN.md §10 GAP-4/5/6; ACCEPTANCE O3/O4):

* Bar rows are ``SYNTHETIC_FIXTURE`` — deterministic generated values
  or reused committed III.2 synthetic slices, *not* empirical market
  evidence; they can never support a performance claim.
* Canonical constants (tier tables, spatial bands, promotion sample
  sizes, outer nodes, evidence ids) enter only through the ratified
  III.2 registries and are ``CANONICAL_SOURCE_SLICE`` where quoted.
* ``replay_hashes.json`` entries are golden **contract** hashes over
  these fixtures — reproduction is determinism evidence, never
  empirical performance evidence.

This module is also the single source of truth for turning a fixture
case back into a ``ModelRequest``: the focused suite imports
:func:`build_request` from here so the generator and the tests can
never drift apart.  Regeneration requires ``app.forge.model_runtime``
to be present (it is, from the model-runtime commit onward).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import fields as dc_fields, is_dataclass, replace
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from app.forge.market_data import (  # noqa: E402
    Bar,
    DataOutcome,
    Finality,
    NativePrice,
    NativeUnit,
    ProvenanceKind,
    QualityFlag,
    QualityPolicy,
    ResearchDayLineage,
    ResearchDayRegistry,
    SessionRegistry,
    build_default_registry,
    definitions_from_records,
    named_clock,
)
from app.forge.measurements import (  # noqa: E402
    CALIBRATION_REGISTRY,
    COORDINATE_SETS,
    AnchorRecord,
    AnchorRule,
    AnchorStatus,
    CalibrationKey,
    CheckpointState,
    DensityZone,
    ElapsedSinceEvent,
    EventFamily,
    HigherOrderCheckpoint,
    LayerConflictFact,
    LayerConflictKind,
    LevelSide,
    NativeMagnitude,
    NormalizedEvent,
    PathLevel,
    PeriodKind,
    Provenance,
    RangeMeasurement,
    RuleMaterialization,
    SeedRangeKind,
    TimeToDelivery,
    UnfinishedSideState,
    WeeklyOuterNode,
    add_magnitude,
    checkpoint_reached,
    classify_spatial_band,
    classify_tier,
    duration_seconds,
    elapsed_since,
    encode_value,
    evaluate_anchor,
    measure_au_scale,
    measure_d1d3_state,
    measure_density_zones,
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
    time_to_delivery,
)
from app.forge.measurements.anchors import EARNED_STATES  # noqa: E402
from app.forge.measurements.contracts import envelope  # noqa: E402

from app.forge.model_runtime import (  # noqa: E402
    BtcTrackerInputs,
    DirectionSide,
    EurDailyInputs,
    EurHigherOrderInputs,
    EurWeeklyInputs,
    FibRangeBirthInputs,
    JpyCarryInputs,
    JpyPairInput,
    JpyRole,
    ModelRequest,
    XauGameInputs,
)

# ---------------------------------------------------------------------------
# Constants (all deterministic)
# ---------------------------------------------------------------------------

SYNTHETIC = "SYNTHETIC_FIXTURE"
CANONICAL = "CANONICAL_SOURCE_SLICE"

SYNTHETIC_CLASSIFICATION = (
    "SYNTHETIC_FIXTURE - deterministic generated or reused committed slices; "
    "contract-test inputs only, never empirical market evidence and never "
    "citable for performance claims"
)

CALC_TS = "2026-03-03T09:00:00Z"
CUTOFF = "2026-03-03T00:30:00Z"
#: six 5-minute bars ending 00:25, all finalized before CUTOFF
RAMP_START = "2026-03-02T23:55:00Z"

IDENTITY = {
    "market_data_schema_version": "MARKET_DATA_SCHEMA_V1",
    "clock_registry_version": "CLOCK_REGISTRY_V1",
    "session_registry_version": "SESSION_REGISTRY_V1",
    "measurement_engine_version": "MEASUREMENT_ENGINE_V1",
}

CARD_DAILY = "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
CARD_WEEKLY = "corpus/canonical/models/EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md"
CARD_HO = "corpus/canonical/models/EUR_HIGHER_ORDER_MODEL_CARD_V1.md"
CARD_XAU = "corpus/canonical/models/XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md"
CARD_BTC = "corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md"
CARD_FIB = "corpus/canonical/models/FIB_RANGE_BIRTH_MODEL_CARD_V1.md"
CARD_JPY = "corpus/canonical/models/JPY_CARRY_GAME_MODEL_CARD_V1.md"
EV_WEEKLY = "EV.EUR.WEEKLY.TIER_RANGE.V1"
EV_D3 = "EV.EUR.HO.D3_DIRECTION.V1"
EV_M1 = "EV.EUR.HO.M1_RANGE_CORR.V1"
EV_UNFIN = "EV.EUR.HO.UNFINISHED_M3.V1"
EV_XAU_68 = "EV.XAU.PROMOTION.68_80.V1"
EV_XAU_120 = "EV.XAU.PROMOTION.120_132.V1"
EV_R11 = "EV.FIB.R11.ANCHOR_OVERGEN.V1"
EV_EUR_TIER = "EV.EUR.DAILY.PHASE1_TIERS.V1"

KEY_EUR = CalibrationKey("EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY_PHASE1_TIERS", "V1")
KEY_WEEKLY = CalibrationKey("EUR.WEEKLY.V1_1", "V1_1", "EUR_WEEKLY_TIER_RANGE", "V1")
KEY_XAU = CalibrationKey("XAU.GAME.L1_L2_L3.V1", "V1", "XAU_SPATIAL_BANDS", "V1")
KEY_BTC = CalibrationKey("BTC.TRACKER.DWM.V1", "V1", "BTC_TRACKER_DWM_TIERS", "V1")

FAMILY_INPUTS = {
    "EUR.DAILY.NEWS_REKEY.V1": EurDailyInputs,
    "EUR.WEEKLY.V1_1": EurWeeklyInputs,
    "EUR.HIGHER_ORDER.V1": EurHigherOrderInputs,
    "XAU.GAME.L1_L2_L3.V1": XauGameInputs,
    "BTC.TRACKER.DWM.V1": BtcTrackerInputs,
    # adversarial alias: the registry must refuse this model id; the
    # tracker inputs stand in only so the request can reach the gate.
    "BTC.GAME.L1_V1": BtcTrackerInputs,
    "CROSSASSET.FIB.RANGE_BIRTH.V1": FibRangeBirthInputs,
    "JPY.CARRY_GAME.L1_L3.V1": JpyCarryInputs,
}

#: request-level defaults: (calibration, clock, session) per model.
_REQUEST_DEFAULTS = {
    "EUR.DAILY.NEWS_REKEY.V1": (KEY_EUR, "America/New_York", "EUR_DAILY.ASIAN_RANGE"),
    "EUR.WEEKLY.V1_1": (KEY_WEEKLY, None, None),
    "EUR.HIGHER_ORDER.V1": (None, None, None),
    "XAU.GAME.L1_L2_L3.V1": (KEY_XAU, "America/New_York", None),
    "BTC.TRACKER.DWM.V1": (KEY_BTC, "America/New_York", None),
    "BTC.GAME.L1_V1": (KEY_BTC, "America/New_York", None),
    "CROSSASSET.FIB.RANGE_BIRTH.V1": (None, None, None),
    "JPY.CARRY_GAME.L1_L3.V1": (None, None, None),
}


def _utc(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Bars (synthetic ramps + reused committed III.2 slices)
# ---------------------------------------------------------------------------


def _ramp_rows(
    base: Decimal, unit: Decimal, size_units: Decimal, *, start_iso: str, n: int = 6
) -> list[dict]:
    """``n`` contiguous M5 bars whose extremes are exactly ``0 .. size``.

    First bar is flat at ``base`` (the low), the last bar closes one
    unit below the high which carries the high — so the measured range
    spans ``size`` native units and ``range_left`` is exactly one unit
    after the last close (direction UP, consumed = size - 1).
    All arithmetic is exact Decimal integer-unit math.
    """
    start = _utc(start_iso)
    step_minutes = 5
    close_units = [((size_units - 1) / (n - 1)) * k for k in range(n)]
    rows: list[dict] = []
    previous = Decimal(0)
    for index in range(n):
        open_u = previous
        close_u = close_units[index]
        high_u = max(open_u, close_u) + (Decimal(1) if index == n - 1 else Decimal(0))
        low_u = min(open_u, close_u) - (Decimal(1) if index == 0 and open_u > 0 else Decimal(0))
        if index == 0:
            low_u = open_u  # the low is the first open (base)
        open_time = start + timedelta(minutes=step_minutes * index)
        close_time = open_time + timedelta(minutes=step_minutes)
        rows.append(
            {
                "open_time": open_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "close_time": close_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "o": str(base + unit * open_u),
                "h": str(base + unit * high_u),
                "l": str(base + unit * low_u),
                "c": str(base + unit * close_u),
                "volume": str(300 + index),
                "source_timestamp": (close_time).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
        previous = close_u
    return rows


def _bars(rows: list[dict], instrument_id: str, timeframe: str = "M5") -> list[Bar]:
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


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


def _env() -> dict:
    iii2 = json.loads(
        (REPO / "implementation/forge/book_iii/bloc_iii_2/fixtures").joinpath(
            "eur_daily_tier_seeds.json"
        ).read_text(encoding="utf-8")
    )
    xau_fx = json.loads(
        (REPO / "implementation/forge/book_iii/bloc_iii_2/fixtures").joinpath(
            "xau_spatial_bands.json"
        ).read_text(encoding="utf-8")
    )
    sessions_fx = json.loads(
        (REPO / "implementation/forge/book_iii/bloc_iii_1/fixtures").joinpath(
            "sessions_canonical.json"
        ).read_text(encoding="utf-8")
    )
    clocks = {"America/New_York": named_clock("America/New_York")}
    sessions = SessionRegistry()
    sessions.add_all(definitions_from_records(sessions_fx["definitions"], clocks))
    lineages = ResearchDayRegistry()
    for record in sessions_fx["research_day_lineages"]:
        boundary = record.get("evening_shift_boundary")
        lineages.register(
            ResearchDayLineage(
                lineage_id=record["lineage_id"],
                model_id=record["model_id"],
                model_version=record["model_version"],
                clock=clocks["America/New_York"],
                evening_shift_boundary=(
                    time.fromisoformat(boundary) if boundary else None
                ),
                source_ref=record["source_ref"],
            )
        )
    return {
        "registry": build_default_registry(),
        "sessions": sessions,
        "lineages": lineages,
        "eur_seeds": {s["case_id"]: s["rows"] for s in iii2["seeds"]},
        "xau_blind_rows": xau_fx["quarter_zone"]["blind_touch_case"]["rows"],
        "xau_zone_price": xau_fx["quarter_zone"]["zone_level"],
    }


_ENV: dict | None = None


def env() -> dict:
    global _ENV
    if _ENV is None:
        _ENV = _env()
    return _ENV


def _policy(model_id: str, model_version: str) -> QualityPolicy:
    return QualityPolicy.from_strings(
        model_id,
        model_version,
        blocking=["GAP", "STALE", "OUTLIER_SOURCE", "UNSUPPORTED_CLOCK"],
        warning=["DUPLICATE", "REVISED", "NONFINAL"],
    )


def _prov(
    instrument_id: str,
    session_id: str | None = None,
    clock_id: str | None = "America/New_York",
) -> Provenance:
    return Provenance(
        instrument_id=instrument_id,
        clock_id=clock_id or "America/New_York",
        session_id=session_id or "NONE",
        calculation_timestamp=_utc(CALC_TS),
    )


# --- measurement builders ---------------------------------------------------


def eur_range(rows: list[dict]) -> RangeMeasurement:
    e = env()
    return measure_range(
        _bars(rows, "EURUSD"),
        instrument=e["registry"].get("EURUSD"),
        provenance=_prov("EURUSD", "EUR_DAILY.ASIAN_RANGE"),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy("EUR.DAILY.NEWS_REKEY.V1", "PHASE1"),
    )


def ramp_range(
    base: str, unit: str, size: str, instrument_id: str, *, model: tuple[str, str]
) -> RangeMeasurement:
    e = env()
    rows = _ramp_rows(Decimal(base), Decimal(unit), Decimal(size), start_iso=RAMP_START)
    return measure_range(
        _bars(rows, instrument_id),
        instrument=e["registry"].get(instrument_id),
        provenance=_prov(instrument_id),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy(*model),
    )


def tier_of(rng: RangeMeasurement, key: CalibrationKey):
    return classify_tier(
        CALIBRATION_REGISTRY,
        key,
        rng.size,
        provenance=_prov(rng.instrument_id),
        source_window=rng.source_window,
    )


def path_of(
    rng: RangeMeasurement, *, rows: list[dict], level: tuple[str, str, str] | None
):
    e = env()
    levels = []
    if level is not None:
        level_id, price, side = level
        levels.append(
            PathLevel(
                level_id=level_id,
                price=NativePrice(rng.instrument_id, rng.native_unit, Decimal(price)),
                side=LevelSide(side),
            )
        )
    return measure_path(
        _bars(rows, rng.instrument_id),
        instrument=e["registry"].get(rng.instrument_id),
        provenance=_prov(rng.instrument_id),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy(
            "EUR.DAILY.NEWS_REKEY.V1"
            if rng.instrument_id == "EURUSD"
            else "BTC.TRACKER.DWM.V1",
            "PHASE1" if rng.instrument_id == "EURUSD" else "V1",
        ),
        levels=levels,
        measured_range=rng,
    )


def eur_phase(instant: str, *, outside: bool = False):
    return measure_session_phase(
        env()["sessions"],
        "EUR.DAILY.NEWS_REKEY.V1",
        "PHASE1",
        "EUR_DAILY.ASIAN_RANGE",
        _utc(instant),
        provenance=_prov("EURUSD", "EUR_DAILY.ASIAN_RANGE"),
    )


def btc_phase(session_id: str, instant: str):
    return measure_session_phase(
        env()["sessions"],
        "BTC.TRACKER.DWM.V1",
        "V1",
        session_id,
        _utc(instant),
        provenance=_prov("BTCUSD"),
    )


def weekly_seed() -> Any:
    e = env()
    rows = e["eur_seeds"]["EUR_SEED_T2"]
    return measure_seed_range(
        _bars(rows, "EURUSD"),
        seed_kind=SeedRangeKind.WEEK,
        instrument=e["registry"].get("EURUSD"),
        provenance=_prov("EURUSD"),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy("EUR.WEEKLY.V1_1", "V1_1"),
    )


def weekly_tier(seed) -> Any:
    """The weekly tier is an INPUT (III.2-GAP note): constructed as a
    labeled fixture fact bound to the registered weekly calibration."""
    payload = envelope(
        _prov("EURUSD").context(seed.source_window),
        "TIER_CLASSIFICATION",
        evidence_refs=(EV_WEEKLY,),
    )
    from app.forge.measurements import TierClassification

    return TierClassification(
        **payload,
        tier_id="T2",
        no_go=False,
        magnitude=NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("133.5")),
        calibration_key=KEY_WEEKLY,
        calibration_status=__import__(
            "app.forge.measurements", fromlist=["CalibrationStatus"]
        ).CalibrationStatus.RESEARCH,
        source_ref="corpus/canonical/evidence/EUR_WEEKLY_TIER_RANGE_EVIDENCE_V1.md",
    )


def weekly_nodes() -> list[WeeklyOuterNode]:
    table = CALIBRATION_REGISTRY.weekly_outer_nodes(KEY_WEEKLY)
    return [
        WeeklyOuterNode(
            node_id=f"EUR_WEEKLY_{tier_id}",
            order_index=index,
            magnitude=NativeMagnitude(table.instrument_id, table.unit, magnitude),
            sample_n=sample_n,
            source_ref=table.source_ref,
            calibration_status=table.status,
        )
        for index, (tier_id, magnitude, sample_n) in enumerate(table.outer_nodes)
    ]


def weekly_path(seed):
    return measure_weekly_path(
        weekly_seed=seed,
        nodes=weekly_nodes(),
        provenance=_prov("EURUSD"),
        source_window=seed.source_window,
    )


def weekly_period(close_iso: str):
    return measure_period_phase(
        env()["lineages"],
        "EUR_DAILY_LINEAGE",
        "EURUSD",
        _utc(close_iso),
        PeriodKind.WEEK,
        provenance=_prov("EURUSD"),
    )


def quarter_seed() -> Any:
    e = env()
    rows = e["eur_seeds"]["EUR_SEED_T2"]
    return measure_seed_range(
        _bars(rows, "EURUSD"),
        seed_kind=SeedRangeKind.QUARTER,
        instrument=e["registry"].get("EURUSD"),
        provenance=_prov("EURUSD"),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy("EUR.HIGHER_ORDER.V1", "V1"),
    )


def sub_seed(kind: SeedRangeKind) -> Any:
    e = env()
    rows = e["eur_seeds"]["EUR_SEED_T2"]
    return measure_seed_range(
        _bars(rows, "EURUSD"),
        seed_kind=kind,
        instrument=e["registry"].get("EURUSD"),
        provenance=_prov("EURUSD"),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy("EUR.HIGHER_ORDER.V1", "V1"),
    )


def d1d3(quarter, d1, d2, d3):
    return measure_d1d3_state(
        quarter_seed=quarter,
        d1=d1,
        d2=d2,
        d3=d3,
        provenance=_prov("EURUSD"),
        source_window=quarter.source_window,
    )


def m1_of(seed):
    return measure_m1_scale(
        m1_seed=seed, provenance=_prov("EURUSD"), source_window=seed.source_window
    )


def m2_of(seed):
    return measure_m2_shaping(
        m2_seed=seed, provenance=_prov("EURUSD"), source_window=seed.source_window
    )


def unfinished(side: UnfinishedSideState):
    seed = quarter_seed()
    return measure_unfinished_side(
        side=side, provenance=_prov("EURUSD"), source_window=seed.source_window
    )


def m3_checkpoint(checkpoint_id: str, scheduled: str, observed: str, reached: bool):
    return measure_higher_order_checkpoint(
        checkpoint_id=checkpoint_id,
        scheduled_instant=_utc(scheduled),
        observed_instant=_utc(observed),
        source_ref=CARD_HO,
        provenance=_prov("EURUSD"),
    )


def layer_conflicts(*facts: tuple[str, str, str]):
    seed = quarter_seed()
    return measure_layer_conflict(
        conflicts=tuple(
            LayerConflictFact(
                layer_a=__import__(
                    "app.forge.measurements", fromlist=["HigherOrderLayer"]
                ).HigherOrderLayer(a),
                layer_b=__import__(
                    "app.forge.measurements", fromlist=["HigherOrderLayer"]
                ).HigherOrderLayer(b),
                kind=LayerConflictKind(k),
            )
            for a, b, k in facts
        ),
        provenance=_prov("EURUSD"),
        source_window=seed.source_window,
    )


def xau_range(size: str) -> RangeMeasurement:
    return ramp_range("2340", "1", size, "XAUUSD", model=("XAU.GAME.L1_L2_L3.V1", "V1"))


def xau_band(size: str, rng: RangeMeasurement):
    return classify_spatial_band(
        CALIBRATION_REGISTRY,
        KEY_XAU,
        NativeMagnitude("XAUUSD", NativeUnit.POINT, Decimal(size)),
        provenance=_prov("XAUUSD"),
        source_window=rng.source_window,
    )


def hours_elapsed(hours: str) -> ElapsedSinceEvent:
    observed = _utc(CALC_TS)
    event_instant = observed - timedelta(hours=float(hours))
    return elapsed_since(
        event_instant, observed, provenance=_prov("XAUUSD")
    )


def delivery_clock(boundary: str, observed: str) -> TimeToDelivery:
    return time_to_delivery(
        _utc(boundary), _utc(observed), provenance=_prov("XAUUSD")
    )


def xau_anchor(rng: RangeMeasurement) -> AnchorRecord:
    return AnchorRecord(
        anchor_id="XAU.ANCHOR.ACTIVE.01",
        model_id="XAU.GAME.L1_L2_L3.V1",
        model_version="V1",
        status=AnchorStatus.ACTIVE,
        rule=AnchorRule("XAU.QUARTER_RANGE", "DECLARED", RuleMaterialization.DECLARED, CARD_XAU),
        earned_range=rng,
    )


def xau_coords(rng: RangeMeasurement, families: tuple[str, ...]):
    record = xau_anchor(rng)
    return tuple(
        project_coordinates(record, family, provenance=_prov("XAUUSD"))
        for family in families
    )


def xau_blind_route() -> Any:
    e = env()
    rows = e["xau_blind_rows"]
    level = PathLevel(
        level_id="XAU_QUARTER_ZONE",
        price=NativePrice("XAUUSD", NativeUnit.POINT, Decimal(e["xau_zone_price"])),
        side=LevelSide.ABOVE,
    )
    rng = measure_range(
        _bars(rows, "XAUUSD"),
        instrument=e["registry"].get("XAUUSD"),
        provenance=_prov("XAUUSD"),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy("XAU.GAME.L1_L2_L3.V1", "V1"),
    )
    return measure_path(
        _bars(rows, "XAUUSD"),
        instrument=e["registry"].get("XAUUSD"),
        provenance=_prov("XAUUSD"),
        observation_cutoff=_utc(CUTOFF),
        quality_policy=_policy("XAU.GAME.L1_L2_L3.V1", "V1"),
        levels=[level],
    )


def btc_range(size: str) -> RangeMeasurement:
    return ramp_range("60000", "1", size, "BTCUSD", model=("BTC.TRACKER.DWM.V1", "V1"))


def btc_au(tier_id: str, rng: RangeMeasurement):
    return measure_au_scale(
        CALIBRATION_REGISTRY,
        KEY_BTC,
        tier_id,
        provenance=_prov("BTCUSD"),
        source_window=rng.source_window,
    )


def btc_thresholds(rng: RangeMeasurement):
    return measure_threshold_levels(
        CALIBRATION_REGISTRY,
        KEY_BTC,
        provenance=_prov("BTCUSD"),
        source_window=rng.source_window,
    )


def btc_density(rng: RangeMeasurement):
    return measure_density_zones(
        CALIBRATION_REGISTRY,
        KEY_BTC,
        provenance=_prov("BTCUSD"),
        source_window=rng.source_window,
    )


def btc_anchor() -> Any:
    rng = btc_range("750")
    record = AnchorRecord(
        anchor_id="BTC.WEEKLY.ANCHOR.01",
        model_id="BTC.TRACKER.DWM.V1",
        model_version="V1",
        status=AnchorStatus.UNRESOLVED,
        rule=AnchorRule(
            "BTC_WEEKLY_ANCHOR", "NOT_MATERIALIZED", RuleMaterialization.NOT_MATERIALIZED, CARD_BTC
        ),
    )
    return evaluate_anchor(
        record, provenance=_prov("BTCUSD"), source_window=rng.source_window
    )


def fib_range() -> RangeMeasurement:
    return eur_range(env()["eur_seeds"]["EUR_SEED_T2"])


def fib_anchor(status: AnchorStatus, materialization: RuleMaterialization, rng):
    return AnchorRecord(
        anchor_id=f"FIB.ANCHOR.{status.value}.01",
        model_id="CROSSASSET.FIB.RANGE_BIRTH.V1",
        model_version="R15",
        status=status,
        rule=AnchorRule("R15.RANGE_BIRTH", "R15", materialization, CARD_FIB),
        earned_range=rng if status in EARNED_STATES else None,
    )


def fib_eligibility(status: AnchorStatus, materialization: RuleMaterialization, rng):
    return evaluate_anchor(
        fib_anchor(status, materialization, rng),
        provenance=_prov("EURUSD"),
        source_window=rng.source_window,
    )


def fib_coords(status: AnchorStatus, rng, families: tuple[str, ...]):
    record = fib_anchor(status, RuleMaterialization.DECLARED, rng)
    return tuple(
        project_coordinates(record, family, provenance=_prov("EURUSD"))
        for family in families
    )


def fib_rekey(rng):
    prior = fib_anchor(AnchorStatus.ACTIVE, RuleMaterialization.DECLARED, rng)
    return rekey_anchor(
        prior,
        "FIB.ANCHOR.REKEYED.02",
        mapping={"FIB_132": "FIB_168"},
        provenance=_prov("EURUSD"),
    )


def jpy_path(instrument_id: str) -> Any:
    """A directly constructed pair path (the registry holds no JPY pair)."""
    from app.forge.measurements import PathMeasurement, RemainingState

    digest = hashlib.sha256(f"{instrument_id}-jpy-path-fixture".encode()).hexdigest()
    sw = __import__("app.forge.measurements", fromlist=["SourceWindow"]).SourceWindow(
        window_open_utc=_utc("2026-03-03T00:00:00Z"),
        window_close_utc=_utc("2026-03-03T00:30:00Z"),
        input_digest=digest,
        bar_count=6,
    )
    payload = envelope(_prov(instrument_id).context(sw), "PATH_MEASUREMENT")
    return PathMeasurement(
        **payload,
        reference_price=NativePrice(instrument_id, NativeUnit.PIP, Decimal("150.100")),
        mae=NativeMagnitude(instrument_id, NativeUnit.PIP, Decimal("12")),
        mfe=NativeMagnitude(instrument_id, NativeUnit.PIP, Decimal("24")),
        levels=(),
        first_delivery=None,
        delivery_order=(),
        remaining_state=RemainingState.UNRESOLVED,
        remaining_distribution=None,
        bar_count=6,
    )


def synthetic_event():
    return NormalizedEvent(
        event_id="EUR_EVENT.FIXTURE_01",
        family=EventFamily.MACRO_RELEASE,
        relevance_currencies=frozenset({"EUR"}),
        relevance_assets=frozenset({"EURUSD"}),
        scheduled_time=_utc("2026-03-03T13:30:00Z"),
        actual_time=_utc("2026-03-03T13:30:00Z"),
        source_ref="implementation/forge/book_iii/bloc_iii_3/fixtures/generate_fixtures.py",
        provenance_label=SYNTHETIC,
        historical_band_lower=NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("8")),
        historical_band_upper=NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("30")),
        historical_size=NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal("22")),
    )


def event_features(rng: RangeMeasurement):
    return measure_event_features(
        synthetic_event(),
        provenance=_prov("EURUSD", "EUR_DAILY.ASIAN_RANGE"),
        source_window=rng.source_window,
    )


def event_budget(rng: RangeMeasurement, consumed: str):
    return measure_event_budget(
        synthetic_event(),
        NativeMagnitude("EURUSD", NativeUnit.PIP, Decimal(consumed)),
        provenance=_prov("EURUSD", "EUR_DAILY.ASIAN_RANGE"),
        source_window=rng.source_window,
    )


# ---------------------------------------------------------------------------
# Case assembly
# ---------------------------------------------------------------------------

CASES: dict[str, list[dict]] = {}


def add_case(
    group: str,
    case_id: str,
    model_id: str,
    inputs: dict[str, Any],
    *,
    expected: dict | None = None,
    refusal: str | None = None,
    instrument_id: str | None = None,
    model_version: str | None = None,
    calibration: CalibrationKey | str | None = "__default__",
    clock_id: str | None = "__default__",
    session_id: str | None = "__default__",
    prior_case: str | None = None,
) -> None:
    default_cal, default_clock, default_session = _REQUEST_DEFAULTS[model_id]
    version = model_version
    if version is None:
        version = {
            "EUR.DAILY.NEWS_REKEY.V1": "PHASE1",
            "EUR.WEEKLY.V1_1": "V1_1",
            "EUR.HIGHER_ORDER.V1": "V1",
            "XAU.GAME.L1_L2_L3.V1": "V1",
            "BTC.TRACKER.DWM.V1": "V1",
            "BTC.GAME.L1_V1": "V1",
            "CROSSASSET.FIB.RANGE_BIRTH.V1": "R15",
            "JPY.CARRY_GAME.L1_L3.V1": "V1",
        }[model_id]
    instrument = instrument_id
    if instrument is None:
        instrument = {
            "EUR.DAILY.NEWS_REKEY.V1": "EURUSD",
            "EUR.WEEKLY.V1_1": "EURUSD",
            "EUR.HIGHER_ORDER.V1": "EURUSD",
            "XAU.GAME.L1_L2_L3.V1": "XAUUSD",
            "BTC.TRACKER.DWM.V1": "BTCUSD",
            "BTC.GAME.L1_V1": "BTCUSD",
            "CROSSASSET.FIB.RANGE_BIRTH.V1": "EURUSD",
            "JPY.CARRY_GAME.L1_L3.V1": "USDJPY",
        }[model_id]
    cal = default_cal if calibration == "__default__" else calibration
    clock = default_clock if clock_id == "__default__" else clock_id
    session = default_session if session_id == "__default__" else session_id
    case = {
        "case_id": case_id,
        "model_id": model_id,
        "model_version": version,
        "instrument_id": instrument,
        "calibration_key": encode_value(cal) if cal is not None else None,
        "calculation_timestamp": CALC_TS,
        "clock_id": clock,
        "session_id": session,
        "prior_case": prior_case,
        "inputs": {name: encode_value(value) for name, value in inputs.items()},
        "expected": expected,
        "expected_refusal": refusal,
    }
    CASES.setdefault(group, []).append(case)


def exp(
    model_state: str,
    layer: str,
    auth: str,
    *,
    quality: str = "OK",
    no_go: list[str] | None = None,
    warnings: list[str] | None = None,
    range_left: str = "UNRESOLVED",
    range_value: str | None = None,
    direction: str | dict | None = "NONE_DECLARED",
    sub_states: list[dict] | None = None,
    facts: list[str],
    evidence: list[str],
    levels: list[dict] | None = None,
) -> dict:
    payload = {
        "model_state": model_state,
        "layer": layer,
        "production_authorization": auth,
        "quality_state": quality,
        "no_go": no_go or [],
        "warnings": warnings or [],
        "range_left_state": range_left,
        "range_left_value": range_value,
        "direction_bias": direction,
        "sub_states": sub_states or [],
        "fact_ids": facts,
        "evidence_refs": evidence,
        "levels": levels or [],
    }
    return payload


# ---------------------------------------------------------------------------
# Group: EUR Daily
# ---------------------------------------------------------------------------

_E = "eur_daily_states"
_EUR_T1 = env()["eur_seeds"]["EUR_SEED_T1"]
_EUR_T2 = env()["eur_seeds"]["EUR_SEED_T2"]
_EUR_T3 = env()["eur_seeds"]["EUR_SEED_T3"]
_EUR_NOGO = env()["eur_seeds"]["EUR_SEED_NO_GO"]

_R_T1 = eur_range(_EUR_T1)
_R_T2 = eur_range(_EUR_T2)
_R_T3 = eur_range(_EUR_T3)
_R_NOGO = eur_range(_EUR_NOGO)
_R_45 = ramp_range("1.07900", "0.0001", "45", "EURUSD", model=("EUR.DAILY.NEWS_REKEY.V1", "PHASE1"))
_R_46 = ramp_range("1.07900", "0.0001", "46", "EURUSD", model=("EUR.DAILY.NEWS_REKEY.V1", "PHASE1"))

_DAILY_FACTS_BASE = ["EUR_DAILY.SEED", "EUR_DAILY.TIER", "EUR_DAILY.DISTANCE_ASYMMETRY"]
_DAILY_PRIOR_ABSENT = ["EUR_DAILY.DISTRIBUTION", "PRIOR_STATE.ABSENT"]
_EV_DAILY = [EV_EUR_TIER]

add_case(
    _E, "EUR_DAILY_SEED_T1", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T1, "tier": tier_of(_R_T1, KEY_EUR)},
    expected=exp(
        "SEED_T1", "L1", "RESEARCH_ONLY", facts=_DAILY_FACTS_BASE + _DAILY_PRIOR_ABSENT,
        evidence=_EV_DAILY,
    ),
)

_P_T2_PATH = path_of(_R_T2, rows=_EUR_T2, level=("EUR_DAILY_10810", "1.08100", "ABOVE"))
add_case(
    _E, "EUR_DAILY_SEED_T2_SLOT_PATH", "EUR.DAILY.NEWS_REKEY.V1",
    {
        "seed": _R_T2,
        "tier": tier_of(_R_T2, KEY_EUR),
        "path": _P_T2_PATH,
        "session_phase": eur_phase("2026-03-03T02:00:00Z"),
    },
    expected=exp(
        "SEED_T2", "L1", "RESEARCH_ONLY",
        range_left="MEASURED", range_value="10.0",
        facts=_DAILY_FACTS_BASE + [
            "EUR_DAILY.CONSUMED_STATES", "EUR_DAILY.SLOT",
            "EUR_DAILY.DISTRIBUTION", "PRIOR_STATE.ABSENT",
        ],
        evidence=_EV_DAILY,
    ),
)

add_case(
    _E, "EUR_DAILY_SEED_T3", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T3, "tier": tier_of(_R_T3, KEY_EUR)},
    expected=exp(
        "SEED_T3", "L1", "RESEARCH_ONLY", facts=_DAILY_FACTS_BASE + _DAILY_PRIOR_ABSENT,
        evidence=_EV_DAILY,
    ),
)

add_case(
    _E, "EUR_DAILY_TIER_45_BOUNDARY", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_45, "tier": tier_of(_R_45, KEY_EUR)},
    expected=exp(
        "SEED_T3", "L1", "RESEARCH_ONLY", facts=_DAILY_FACTS_BASE + _DAILY_PRIOR_ABSENT,
        evidence=_EV_DAILY,
    ),
)

add_case(
    _E, "EUR_DAILY_NO_GO_46", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_46, "tier": tier_of(_R_46, KEY_EUR)},
    expected=exp(
        "SOURCE_NO_GO", "L1", "RESEARCH_ONLY", no_go=["AR_SOURCE_NO_GO"],
        facts=_DAILY_FACTS_BASE + _DAILY_PRIOR_ABSENT, evidence=_EV_DAILY,
    ),
)

add_case(
    _E, "EUR_DAILY_NO_GO_52", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_NOGO, "tier": tier_of(_R_NOGO, KEY_EUR)},
    expected=exp(
        "SOURCE_NO_GO", "L1", "RESEARCH_ONLY", no_go=["AR_SOURCE_NO_GO"],
        facts=_DAILY_FACTS_BASE + _DAILY_PRIOR_ABSENT, evidence=_EV_DAILY,
    ),
)


def _rekey_eligibility(rng: RangeMeasurement, ladder: str | None):
    record = AnchorRecord(
        anchor_id="EUR_DAILY.ANCHOR.REKEYED.01",
        model_id="EUR.DAILY.NEWS_REKEY.V1",
        model_version="PHASE1",
        status=AnchorStatus.REKEYED,
        rule=AnchorRule("R15.RANGE_BIRTH", "R15", RuleMaterialization.DECLARED, CARD_FIB),
        earned_range=rng,
        rekey_source_anchor_id="EUR_DAILY.ANCHOR.PRIOR.01",
        rekey_mapping={"EUR_DAILY_100": "EUR_DAILY_132"},
    )
    return evaluate_anchor(
        record, provenance=_prov("EURUSD"), source_window=rng.source_window
    )


for _ladder in ("100", "125", "132", "168", "185"):
    add_case(
        _E, f"EUR_DAILY_REKEY_{_ladder}", "EUR.DAILY.NEWS_REKEY.V1",
        {
            "seed": _R_T2,
            "tier": tier_of(_R_T2, KEY_EUR),
            "anchor": _rekey_eligibility(_R_T2, _ladder),
            "ladder_state": _ladder,
        },
        expected=exp(
            f"REKEY_{_ladder}", "L1", "RESEARCH_ONLY",
            facts=_DAILY_FACTS_BASE + ["EUR_DAILY.REKEY_ANCHOR"] + _DAILY_PRIOR_ABSENT,
            evidence=_EV_DAILY,
        ),
    )

add_case(
    _E, "EUR_DAILY_REKEY_UNMAPPED", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T2, "tier": tier_of(_R_T2, KEY_EUR), "anchor": _rekey_eligibility(_R_T2, None)},
    expected=exp(
        "REKEYED", "L1", "RESEARCH_ONLY",
        facts=_DAILY_FACTS_BASE + ["EUR_DAILY.REKEY_ANCHOR"] + _DAILY_PRIOR_ABSENT,
        evidence=_EV_DAILY,
    ),
)

# Touch-only anchor: ladder claim without a REKEYED anchor refuses.
_TOUCH_ANCHOR = evaluate_anchor(
    AnchorRecord(
        anchor_id="EUR_DAILY.ANCHOR.ELIGIBLE.01",
        model_id="EUR.DAILY.NEWS_REKEY.V1",
        model_version="PHASE1",
        status=AnchorStatus.ELIGIBLE,
        rule=AnchorRule("R15.RANGE_BIRTH", "R15", RuleMaterialization.DECLARED, CARD_FIB),
        earned_range=_R_T2,
    ),
    provenance=_prov("EURUSD"),
    source_window=_R_T2.source_window,
)
add_case(
    _E, "EUR_DAILY_TOUCH_NO_REKEY", "EUR.DAILY.NEWS_REKEY.V1",
    {
        "seed": _R_T2,
        "tier": tier_of(_R_T2, KEY_EUR),
        "anchor": _TOUCH_ANCHOR,
        "ladder_state": "132",
    },
    refusal="MODEL_CONTRACT",
)

_EVENT_FEATURES = event_features(_R_T2)
_EVENT_BUDGET = event_budget(_R_T2, "10")
add_case(
    _E, "EUR_DAILY_EVENT_CONDITIONED", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T2, "tier": tier_of(_R_T2, KEY_EUR),
     "event_features": _EVENT_FEATURES, "event_budget": _EVENT_BUDGET},
    expected=exp(
        "SEED_T2", "L1", "RESEARCH_ONLY",
        facts=_DAILY_FACTS_BASE + [
            "EUR_DAILY.EVENT_CONDITIONING", "EUR_DAILY.EVENT_BUDGET",
            "EUR_DAILY.DISTRIBUTION", "PRIOR_STATE.ABSENT",
        ],
        evidence=_EV_DAILY,
    ),
)
add_case(
    _E, "EUR_DAILY_NO_EVENT", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T2, "tier": tier_of(_R_T2, KEY_EUR)},
    expected=exp(
        "SEED_T2", "L1", "RESEARCH_ONLY",
        facts=_DAILY_FACTS_BASE + _DAILY_PRIOR_ABSENT, evidence=_EV_DAILY,
    ),
)
add_case(
    _E, "EUR_DAILY_SLOT_OUTSIDE", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T2, "tier": tier_of(_R_T2, KEY_EUR), "path": _P_T2_PATH,
     "session_phase": eur_phase("2026-03-03T12:00:00Z")},
    expected=exp(
        "SEED_T2", "L1", "RESEARCH_ONLY", range_left="UNRESOLVED",
        facts=_DAILY_FACTS_BASE + [
            "EUR_DAILY.CONSUMED_STATES", "EUR_DAILY.SLOT",
            "EUR_DAILY.DISTRIBUTION", "PRIOR_STATE.ABSENT",
        ],
        evidence=_EV_DAILY,
    ),
)
add_case(
    _E, "EUR_DAILY_CLOCK_MISSING", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T2, "tier": tier_of(_R_T2, KEY_EUR)},
    clock_id=None,
    refusal="NO_CALCULATION",
)
add_case(
    _E, "EUR_DAILY_TIER_MISSING", "EUR.DAILY.NEWS_REKEY.V1",
    {"seed": _R_T2},
    refusal="INPUT_MEASUREMENT_MISSING",
)

# ---------------------------------------------------------------------------
# Group: EUR Weekly
# ---------------------------------------------------------------------------

_W = "eur_weekly_states"
_W_SEED = weekly_seed()
_W_TIER = weekly_tier(_W_SEED)
_W_PATH = weekly_path(_W_SEED)
_W_PERIOD = weekly_period("2026-03-02T21:00:00Z")

_W_TIMING = "EUR_WEEKLY.HOUR_TIER_TIMING"
_W_FACTS_OPEN = [
    "EUR_WEEKLY.SEED", "EUR_WEEKLY.TIER", "EUR_WEEKLY.ROUTE", _W_TIMING,
    "EUR_WEEKLY.CALIBRATION_STATUS", "EUR_WEEKLY.DESTINATION_BOUNDARY",
    "EUR_WEEKLY.DISTRIBUTION", "PRIOR_STATE.ABSENT",
]
_W_EV = [EV_WEEKLY]

add_case(
    _W, "EUR_WEEKLY_ROUTE", "EUR.WEEKLY.V1_1",
    {"seed": _W_SEED, "tier": _W_TIER, "path": _W_PATH, "period_phase": _W_PERIOD},
    expected=exp(
        "ROUTE_OPEN", "L2", "RESEARCH_ONLY", warnings=["RESEARCH_CALIBRATION"],
        facts=_W_FACTS_OPEN, evidence=_W_EV,
    ),
)
add_case(
    _W, "EUR_WEEKLY_PROMOTED", "EUR.WEEKLY.V1_1",
    {"seed": _W_SEED, "tier": _W_TIER, "path": _W_PATH, "period_phase": _W_PERIOD,
     "reached_node_id": "EUR_WEEKLY_T2"},
    expected=exp(
        "NODE_PROMOTED", "L2", "RESEARCH_ONLY", warnings=["RESEARCH_CALIBRATION"],
        facts=[
            "EUR_WEEKLY.SEED", "EUR_WEEKLY.TIER", "EUR_WEEKLY.ROUTE",
            "EUR_WEEKLY.NODE", _W_TIMING, "EUR_WEEKLY.CALIBRATION_STATUS",
            "EUR_WEEKLY.DESTINATION_BOUNDARY", "EUR_WEEKLY.DISTRIBUTION",
            "PRIOR_STATE.ABSENT",
        ],
        evidence=_W_EV,
    ),
)
add_case(
    _W, "EUR_WEEKLY_INNER_NODE", "EUR.WEEKLY.V1_1",
    {"seed": _W_SEED, "tier": _W_TIER, "path": _W_PATH, "period_phase": _W_PERIOD,
     "reached_node_id": "EUR_WEEKLY_INNER"},
    expected=exp(
        "ROUTE_OPEN", "L2", "RESEARCH_ONLY", warnings=["RESEARCH_CALIBRATION"],
        facts=[
            "EUR_WEEKLY.SEED", "EUR_WEEKLY.TIER", "EUR_WEEKLY.ROUTE",
            "EUR_WEEKLY.NODE_NOT_OUTER", _W_TIMING, "EUR_WEEKLY.CALIBRATION_STATUS",
            "EUR_WEEKLY.DESTINATION_BOUNDARY", "EUR_WEEKLY.DISTRIBUTION",
            "PRIOR_STATE.ABSENT",
        ],
        evidence=_W_EV,
    ),
)
add_case(
    _W, "EUR_WEEKLY_FROZEN", "EUR.WEEKLY.V1_1",
    {"seed": _W_SEED, "tier": _W_TIER, "path": _W_PATH, "period_phase": _W_PERIOD,
     "reached_node_id": "EUR_WEEKLY_T2", "occ_frozen": True},
    expected=exp(
        "FROZEN", "L2", "RESEARCH_ONLY", warnings=["RESEARCH_CALIBRATION"],
        facts=[
            "EUR_WEEKLY.SEED", "EUR_WEEKLY.TIER", "EUR_WEEKLY.ROUTE",
            "EUR_WEEKLY.NODE", "EUR_WEEKLY.OCC_FROZEN", _W_TIMING,
            "EUR_WEEKLY.CALIBRATION_STATUS", "EUR_WEEKLY.DESTINATION_BOUNDARY",
            "EUR_WEEKLY.DISTRIBUTION", "PRIOR_STATE.ABSENT",
        ],
        evidence=_W_EV,
    ),
)
add_case(
    _W, "EUR_WEEKLY_FROZEN_VIA_PRIOR", "EUR.WEEKLY.V1_1",
    {"seed": _W_SEED, "tier": _W_TIER, "path": _W_PATH, "period_phase": _W_PERIOD,
     "reached_node_id": "EUR_WEEKLY_T2"},
    prior_case="EUR_WEEKLY_FROZEN",
    expected=exp(
        "FROZEN", "L2", "RESEARCH_ONLY", warnings=["RESEARCH_CALIBRATION"],
        facts=[
            "EUR_WEEKLY.SEED", "EUR_WEEKLY.TIER", "EUR_WEEKLY.ROUTE",
            "EUR_WEEKLY.NODE", "EUR_WEEKLY.OCC_FROZEN", _W_TIMING,
            "EUR_WEEKLY.CALIBRATION_STATUS", "EUR_WEEKLY.DESTINATION_BOUNDARY",
            "EUR_WEEKLY.DISTRIBUTION", "PRIOR_STATE.LINKED",
        ],
        evidence=_W_EV,
    ),
)
add_case(
    _W, "EUR_WEEKLY_TIMING_UNRESOLVED", "EUR.WEEKLY.V1_1",
    {"seed": _W_SEED, "tier": _W_TIER, "path": _W_PATH},
    expected=exp(
        "ROUTE_OPEN", "L2", "RESEARCH_ONLY",
        warnings=["RESEARCH_CALIBRATION", "TIMING_UNRESOLVED"],
        facts=[
            "EUR_WEEKLY.SEED", "EUR_WEEKLY.TIER", "EUR_WEEKLY.ROUTE",
            "EUR_WEEKLY.HOUR_TIER_TIMING_UNRESOLVED", "EUR_WEEKLY.CALIBRATION_STATUS",
            "EUR_WEEKLY.DESTINATION_BOUNDARY", "EUR_WEEKLY.DISTRIBUTION",
            "PRIOR_STATE.ABSENT",
        ],
        evidence=_W_EV,
    ),
)

# ---------------------------------------------------------------------------
# Group: EUR Higher Order
# ---------------------------------------------------------------------------

_H = "eur_higher_order_states"
_Q = quarter_seed()
_D1 = sub_seed(SeedRangeKind.QUARTER_DAY)
_D2 = sub_seed(SeedRangeKind.QUARTER_DAY)
_D3 = sub_seed(SeedRangeKind.QUARTER_DAY)
_D1D3 = d1d3(_Q, _D1, _D2, _D3)
_M1 = m1_of(_D1)
_M2 = m2_of(_D2)

_H_CORE = ["EUR_HO.QUARTER_SEED", "EUR_HO.D3_PRIOR"]
_H_TAIL = ["PRIOR_STATE.ABSENT"]
_EV_HO_FULL = [EV_D3, EV_M1]

add_case(
    _H, "HO_PRIOR_DECLARED", "EUR.HIGHER_ORDER.V1",
    {"quarter_seed": _Q, "d1d3": _D1D3, "m1": _M1, "m2": _M2,
     "d3_direction": DirectionSide.UP},
    expected=exp(
        "PRIOR_DECLARED", "L3", "RESEARCH_ONLY",
        direction={"side": "UP", "basis_fact_id": "EUR_HO.D3_PRIOR"},
        facts=_H_CORE + ["EUR_HO.M1_SCALE", "EUR_HO.M2_SHAPING"] + _H_TAIL,
        evidence=_EV_HO_FULL,
    ),
)
add_case(
    _H, "HO_NO_DIRECTION", "EUR.HIGHER_ORDER.V1",
    {"quarter_seed": _Q, "d1d3": _D1D3, "m1": _M1, "m2": _M2},
    expected=exp(
        "UNRESOLVED", "L3", "RESEARCH_ONLY",
        warnings=["EVIDENCE_BOUND_PARAMETER"],
        direction="NONE_DECLARED",
        facts=_H_CORE + ["EUR_HO.M1_SCALE", "EUR_HO.M2_SHAPING"] + _H_TAIL,
        evidence=[EV_M1],
    ),
)
add_case(
    _H, "HO_MISSING_M1", "EUR.HIGHER_ORDER.V1",
    {"quarter_seed": _Q, "d1d3": _D1D3, "m2": _M2, "d3_direction": DirectionSide.UP},
    expected=exp(
        "UNRESOLVED", "L3", "RESEARCH_ONLY",
        warnings=["EVIDENCE_BOUND_PARAMETER"],
        direction={"side": "UP", "basis_fact_id": "EUR_HO.D3_PRIOR"},
        facts=_H_CORE + ["EUR_HO.M2_SHAPING", "EUR_HO.PARAM_M1_SCALE"] + _H_TAIL,
        evidence=[EV_D3],
    ),
)
add_case(
    _H, "HO_UNFINISHED_CONDITIONAL", "EUR.HIGHER_ORDER.V1",
    {"quarter_seed": _Q, "d1d3": _D1D3, "m1": _M1, "m2": _M2,
     "d3_direction": DirectionSide.UP,
     "unfinished": unfinished(UnfinishedSideState.UPPER)},
    expected=exp(
        "COMPLETION_CONDITIONAL", "L3", "RESEARCH_ONLY",
        warnings=["CONDITIONAL_DESTINATION"],
        direction={"side": "UP", "basis_fact_id": "EUR_HO.D3_PRIOR"},
        facts=_H_CORE + ["EUR_HO.M1_SCALE", "EUR_HO.M2_SHAPING",
                         "EUR_HO.UNFINISHED_SIDE"] + _H_TAIL,
        evidence=[EV_D3, EV_M1, EV_UNFIN],
    ),
)
add_case(
    _H, "HO_M3_RESOLVED", "EUR.HIGHER_ORDER.V1",
    {"quarter_seed": _Q, "d1d3": _D1D3, "m1": _M1, "m2": _M2,
     "d3_direction": DirectionSide.UP,
     "checkpoints": (
         m3_checkpoint("HO.M3.W1", "2026-02-02T00:00:00Z", "2026-02-02T01:00:00Z", True),
         m3_checkpoint("HO.M3.W4", "2026-02-23T00:00:00Z", "2026-02-23T01:00:00Z", True),
     )},
    expected=exp(
        "M3_RESOLVED", "L3", "RESEARCH_ONLY",
        direction={"side": "UP", "basis_fact_id": "EUR_HO.D3_PRIOR"},
        facts=_H_CORE + ["EUR_HO.M1_SCALE", "EUR_HO.M2_SHAPING",
                         "EUR_HO.M3_CHECKPOINT", "EUR_HO.M3_CHECKPOINT"] + _H_TAIL,
        evidence=_EV_HO_FULL,
    ),
)
add_case(
    _H, "HO_CONFLICT_NO_SCORE", "EUR.HIGHER_ORDER.V1",
    {"quarter_seed": _Q, "d1d3": _D1D3, "m1": _M1, "m2": _M2,
     "d3_direction": DirectionSide.UP,
     "conflicts": layer_conflicts(("QUARTER", "WEEK", "DIRECTION_DISAGREEMENT"))},
    expected=exp(
        "PRIOR_DECLARED", "L3", "RESEARCH_ONLY",
        direction={"side": "UP", "basis_fact_id": "EUR_HO.D3_PRIOR"},
        facts=_H_CORE + ["EUR_HO.M1_SCALE", "EUR_HO.M2_SHAPING",
                         "EUR_HO.LAYER_CONFLICT"] + _H_TAIL,
        evidence=_EV_HO_FULL,
    ),
)
add_case(
    _H, "HO_DEGRADED_INPUT", "EUR.HIGHER_ORDER.V1",
    {"quarter_seed": _Q, "d1d3": replace(_D1D3, quality_state=DataOutcome.DEGRADED),
     "m1": _M1, "m2": _M2, "d3_direction": DirectionSide.UP},
    expected=exp(
        "PRIOR_DECLARED", "L3", "RESEARCH_ONLY", quality="DEGRADED",
        warnings=["DEGRADED_INPUT"],
        direction={"side": "UP", "basis_fact_id": "EUR_HO.D3_PRIOR"},
        facts=_H_CORE + ["EUR_HO.M1_SCALE", "EUR_HO.M2_SHAPING"] + _H_TAIL,
        evidence=_EV_HO_FULL,
    ),
)

# ---------------------------------------------------------------------------
# Group: XAU
# ---------------------------------------------------------------------------

_X = "xau_promotion_states"
_X30 = xau_range("30")
_X68 = xau_range("68")

add_case(
    _X, "XAU_NORMAL_NODE50", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X30, "band": xau_band("30", _X30), "state_node": Decimal("50")},
    expected=exp(
        "NODE_DECLARED", "CROSS_LAYER", "MANUAL_OPERATOR",
        warnings=["RESEARCH_CALIBRATION"],
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "NODE_50"},
            {"label": "L1", "layer": "L1", "state": "BAND_NORMAL"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.BAND", "XAU.L3_DESTINATION",
               "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=["XAU.GAME.L1_L2_L3.V1"],
    ),
)
add_case(
    _X, "XAU_68_8H", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X68, "band": xau_band("68", _X68), "state_node": Decimal("68"),
     "elapsed": hours_elapsed("8"),
     "delivery_clocks": (delivery_clock("2026-03-03T17:00:00Z", "2026-03-03T16:00:00Z"),)},
    expected=exp(
        "PROMOTION_ELIGIBLE", "CROSS_LAYER", "MANUAL_OPERATOR",
        warnings=["RESEARCH_CALIBRATION"],
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "ELIGIBLE_80"},
            {"label": "L1", "layer": "L1", "state": "BAND_REPAIR"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.BAND", "XAU.DELIVERY_CLOCKS", "XAU.L3_DESTINATION",
               "XAU.PROMOTION_68_80", "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=["XAU.GAME.L1_L2_L3.V1", EV_XAU_68],
    ),
)
add_case(
    _X, "XAU_68_7H", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X68, "band": xau_band("68", _X68), "state_node": Decimal("68"),
     "elapsed": hours_elapsed("7")},
    expected=exp(
        "PROMOTION_PENDING", "CROSS_LAYER", "MANUAL_OPERATOR",
        warnings=["RESEARCH_CALIBRATION"],
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "PROMOTION_PENDING"},
            {"label": "L1", "layer": "L1", "state": "BAND_REPAIR"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.BAND", "XAU.L3_DESTINATION", "XAU.PROMOTION_PENDING",
               "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=["XAU.GAME.L1_L2_L3.V1"],
    ),
)
add_case(
    _X, "XAU_120_8H", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X30, "state_node": Decimal("120"), "elapsed": hours_elapsed("8")},
    expected=exp(
        "PROMOTION_RESEARCH", "CROSS_LAYER", "MANUAL_OPERATOR",
        warnings=["SMALL_N_RESEARCH_FLAG"],
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "RESEARCH_PROMOTED_132"},
            {"label": "L1", "layer": "L1", "state": "ASIAN_SEED"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.L3_DESTINATION", "XAU.PROMOTION_120_132",
               "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=[EV_XAU_120],
    ),
)
add_case(
    _X, "XAU_132_NO_168", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X30, "state_node": Decimal("132"), "elapsed": hours_elapsed("100")},
    expected=exp(
        "NODE_DECLARED", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "NODE_132"},
            {"label": "L1", "layer": "L1", "state": "ASIAN_SEED"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.L3_DESTINATION", "XAU.NODE_132_BOUNDARY",
               "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=[],
    ),
)
add_case(
    _X, "XAU_PARKED_68_8H", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X68, "band": xau_band("68", _X68), "state_node": Decimal("68"),
     "elapsed": hours_elapsed("8"), "parked": True,
     "confirmation_state": "CONFIRMED",
     "coordinates": xau_coords(_X68, ("XAU_50",))},
    expected=exp(
        "PARKED", "CROSS_LAYER", "MANUAL_OPERATOR",
        no_go=["PROMOTION_PARKED"], warnings=["RESEARCH_CALIBRATION"],
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "PARKED"},
            {"label": "L1", "layer": "L1", "state": "BAND_REPAIR"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "CONFIRMED"},
        ],
        facts=["XAU.SEED", "XAU.BAND", "XAU.L3_DESTINATION", "XAU.PARKED",
               "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=["XAU.GAME.L1_L2_L3.V1"],
        levels=[{"level_id": "XAU.ANCHOR.ACTIVE.01:XAU_50", "active": False}],
    ),
)
add_case(
    _X, "XAU_BLIND_TOUCH", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X30, "route": xau_blind_route()},
    expected=exp(
        "ROUTE_OPEN", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "ROUTE_OPEN"},
            {"label": "L1", "layer": "L1", "state": "ASIAN_SEED"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.ROUTE", "XAU.L3_DESTINATION",
               "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=[],
    ),
)
add_case(
    _X, "XAU_L3_UNRESOLVED_WITH_RICH_L1", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X68, "band": xau_band("68", _X68), "route": xau_blind_route()},
    expected=exp(
        "ROUTE_OPEN", "CROSS_LAYER", "MANUAL_OPERATOR",
        warnings=["RESEARCH_CALIBRATION"],
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "ROUTE_OPEN"},
            {"label": "L1", "layer": "L1", "state": "BAND_REPAIR"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.BAND", "XAU.ROUTE", "XAU.L3_DESTINATION",
               "XAU.CONFIRMATION_CONTEXT", "PRIOR_STATE.ABSENT"],
        evidence=["XAU.GAME.L1_L2_L3.V1"],
    ),
)
add_case(
    _X, "XAU_COORDINATES_ACTIVE", "XAU.GAME.L1_L2_L3.V1",
    {"seed": _X30, "coordinates": xau_coords(_X30, ("XAU_50", "XAU_68"))},
    expected=exp(
        "UNRESOLVED", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "L3", "layer": "L3", "state": "UNRESOLVED"},
            {"label": "L2", "layer": "L2", "state": "UNRESOLVED"},
            {"label": "L1", "layer": "L1", "state": "ASIAN_SEED"},
            {"label": "CONFIRMATION", "layer": "L1", "state": "ABSENT"},
        ],
        facts=["XAU.SEED", "XAU.L3_DESTINATION", "XAU.CONFIRMATION_CONTEXT",
               "PRIOR_STATE.ABSENT"],
        evidence=[],
        levels=[{"level_id": "XAU.ANCHOR.ACTIVE.01:XAU_50", "active": True},
                {"level_id": "XAU.ANCHOR.ACTIVE.01:XAU_68", "active": True}],
    ),
)

# ---------------------------------------------------------------------------
# Group: BTC Tracker
# ---------------------------------------------------------------------------

_B = "btc_tracker_states"
_B749 = btc_range("749")
_B750 = btc_range("750")
_B3000 = btc_range("3000")
_B3001 = btc_range("3001")

_BTC_FACTS_BASE = [
    "BTC.SEED", "BTC.TIER", "BTC.SLOT", "BTC.WEEKLY_ANCHOR", "BTC.MONTHLY_ANCHOR",
    "BTC.DISTRIBUTION", "PRIOR_STATE.ABSENT",
]
_BTC_SUBS_UNRESOLVED = [
    {"label": "WEEKLY", "layer": "CROSS_LAYER", "state": "UNRESOLVED"},
    {"label": "MONTHLY", "layer": "CROSS_LAYER", "state": "UNRESOLVED"},
]
_EV_BTC = ["BTC.TRACKER.DWM.V1"]


def _btc_daily(state: str, rng: RangeMeasurement, facts: list[str],
               *, no_go: list[str] | None = None, extra_subs: list[dict] | None = None,
               evidence: list[str] | None = None) -> dict:
    return exp(
        state, "CROSS_LAYER", "RESEARCH_ONLY",
        no_go=no_go,
        warnings=["GAP_UNRESOLVED"],
        sub_states=([{"label": "DAILY", "layer": "CROSS_LAYER", "state": state}]
                    + (extra_subs or []) + _BTC_SUBS_UNRESOLVED),
        facts=facts,
        evidence=evidence or _EV_BTC,
    )


add_case(
    _B, "BTC_TIER_T1_749", "BTC.TRACKER.DWM.V1",
    {"seed": _B749, "tier": tier_of(_B749, KEY_BTC)},
    expected=_btc_daily("SEED_T1", _B749, _BTC_FACTS_BASE),
)
add_case(
    _B, "BTC_TIER_T2_750", "BTC.TRACKER.DWM.V1",
    {"seed": _B750, "tier": tier_of(_B750, KEY_BTC)},
    expected=_btc_daily("SEED_T2", _B750, _BTC_FACTS_BASE),
)
add_case(
    _B, "BTC_TIER_T3_3000", "BTC.TRACKER.DWM.V1",
    {"seed": _B3000, "tier": tier_of(_B3000, KEY_BTC)},
    expected=_btc_daily("SEED_T3", _B3000, _BTC_FACTS_BASE),
)
add_case(
    _B, "BTC_NO_GO_3001", "BTC.TRACKER.DWM.V1",
    {"seed": _B3001, "tier": tier_of(_B3001, KEY_BTC)},
    expected=_btc_daily("ASIAN_RANGE_NO_GO", _B3001, _BTC_FACTS_BASE,
                        no_go=["ASIAN_RANGE_NO_GO"]),
)
_B5_PATH = path_of(_B750, rows=_ramp_rows(Decimal("60000"), Decimal("1"), Decimal("750"),
                                           start_iso=RAMP_START),
                   level=None)
add_case(
    _B, "BTC_SLOT_RANGE_LEFT", "BTC.TRACKER.DWM.V1",
    {"seed": _B750, "tier": tier_of(_B750, KEY_BTC), "path": _B5_PATH,
     "slot_phase": btc_phase("BTC_TRACKER.DAILY_CHECKPOINT_12PM", "2026-03-03T17:00:00Z")},
    expected=exp(
        "SEED_T2", "CROSS_LAYER", "RESEARCH_ONLY",
        range_left="MEASURED", range_value=_B5_PATH.remaining_distribution and str(_B5_PATH.remaining_distribution.value),
        warnings=["GAP_UNRESOLVED"],
        sub_states=([{"label": "DAILY", "layer": "CROSS_LAYER", "state": "SEED_T2"}]
                    + _BTC_SUBS_UNRESOLVED),
        facts=["BTC.SEED", "BTC.TIER", "BTC.SLOT", "BTC.PATH",
               "BTC.WEEKLY_ANCHOR", "BTC.MONTHLY_ANCHOR", "BTC.DISTRIBUTION",
               "PRIOR_STATE.ABSENT"],
        evidence=_EV_BTC,
    ),
)
add_case(
    _B, "BTC_SLOT_OUTSIDE", "BTC.TRACKER.DWM.V1",
    {"seed": _B750, "tier": tier_of(_B750, KEY_BTC), "path": _B5_PATH,
     "slot_phase": btc_phase("BTC_TRACKER.ASIAN_WINDOW", "2026-03-03T20:00:00Z")},
    expected=exp(
        "SEED_T2", "CROSS_LAYER", "RESEARCH_ONLY",
        range_left="UNRESOLVED", warnings=["GAP_UNRESOLVED"],
        sub_states=([{"label": "DAILY", "layer": "CROSS_LAYER", "state": "SEED_T2"}]
                    + _BTC_SUBS_UNRESOLVED),
        facts=["BTC.SEED", "BTC.TIER", "BTC.SLOT", "BTC.PATH",
               "BTC.WEEKLY_ANCHOR", "BTC.MONTHLY_ANCHOR", "BTC.DISTRIBUTION",
               "PRIOR_STATE.ABSENT"],
        evidence=_EV_BTC,
    ),
)
_B_ANCHOR = btc_anchor()
add_case(
    _B, "BTC_HORIZON_UNRESOLVED", "BTC.TRACKER.DWM.V1",
    {"seed": _B750, "tier": tier_of(_B750, KEY_BTC), "weekly_anchor": _B_ANCHOR},
    expected=_btc_daily("SEED_T2", _B750, _BTC_FACTS_BASE),
)
add_case(
    _B, "BTC_AU_THRESHOLDS", "BTC.TRACKER.DWM.V1",
    {"seed": _B750, "tier": tier_of(_B750, KEY_BTC), "au": btc_au("T2", _B750),
     "thresholds": btc_thresholds(_B750), "density": btc_density(_B750)},
    expected=exp(
        "SEED_T2", "CROSS_LAYER", "RESEARCH_ONLY",
        warnings=["GAP_UNRESOLVED"],
        sub_states=([{"label": "DAILY", "layer": "CROSS_LAYER", "state": "SEED_T2"}]
                    + _BTC_SUBS_UNRESOLVED),
        facts=["BTC.SEED", "BTC.TIER", "BTC.AU_SCALE", "BTC.DENSITY_ZONE",
               "BTC.DENSITY_ZONE", "BTC.DENSITY_ZONE", "BTC.SLOT",
               "BTC.WEEKLY_ANCHOR", "BTC.MONTHLY_ANCHOR", "BTC.DISTRIBUTION",
               "PRIOR_STATE.ABSENT"],
        evidence=_EV_BTC,
        levels=[{"level_id": "BTC_THRESHOLD_1", "active": True},
                {"level_id": "BTC_THRESHOLD_2", "active": True},
                {"level_id": "BTC_THRESHOLD_3", "active": True}],
    ),
)
add_case(
    _B, "BTC_GAME_REQUEST", "BTC.GAME.L1_V1",
    {},
    refusal="MODEL_VERSION_UNAVAILABLE",
)
add_case(
    _B, "BTC_FOREIGN_INSTRUMENT", "BTC.TRACKER.DWM.V1",
    {"seed": _B750, "tier": tier_of(_B750, KEY_BTC)},
    instrument_id="EURUSD",
    refusal="INSTRUMENT_SCOPE_MISMATCH",
)
add_case(
    _B, "BTC_FOREIGN_CALIBRATION", "BTC.TRACKER.DWM.V1",
    {"seed": _B750, "tier": tier_of(_B750, KEY_BTC)},
    calibration=KEY_EUR,
    refusal="INSTRUMENT_SCOPE_MISMATCH",
)

# ---------------------------------------------------------------------------
# Group: Fib Range Birth
# ---------------------------------------------------------------------------

_F = "fib_range_birth_states"
_F_RANGE = fib_range()
_F_ANCHOR_ACTIVE = fib_eligibility(AnchorStatus.ACTIVE, RuleMaterialization.DECLARED, _F_RANGE)
_F_ANCHOR_ELIGIBLE = fib_eligibility(AnchorStatus.ELIGIBLE, RuleMaterialization.DECLARED, _F_RANGE)
_F_ANCHOR_UNRESOLVED = fib_eligibility(
    AnchorStatus.UNRESOLVED, RuleMaterialization.NOT_MATERIALIZED, _F_RANGE
)
_F_COORDS = fib_coords(AnchorStatus.ACTIVE, _F_RANGE, ("FIB_50", "FIB_132"))
_F_PATH = path_of(_F_RANGE, rows=_EUR_T2, level=("FIB_10810", "1.08100", "ABOVE"))

_F_EV = [EV_R11]

add_case(
    _F, "FIB_CHAIN_ACTIVE", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"anchor": _F_ANCHOR_ACTIVE, "range": _F_RANGE, "sequence": "ALPHA",
     "coordinates": _F_COORDS, "path": _F_PATH},
    expected=exp(
        "RANGE_ACTIVE", "CROSS_LAYER", "RESEARCH_ONLY",
        warnings=["GAP_UNRESOLVED"], range_left="MEASURED", range_value="10.0",
        facts=["FIB.R15_GATE", "FIB.RANGE_BIRTH", "FIB.AB_RANGE", "FIB.SEQUENCE",
               "FIB.COORDINATE.FIB_50", "FIB.COORDINATE.FIB_132", "FIB.PATH",
               "FIB.R11_NEGATIVE_EVIDENCE", "FIB.DISTRIBUTION", "PRIOR_STATE.ABSENT"],
        evidence=_F_EV,
        levels=[{"level_id": "FIB.ANCHOR.ACTIVE.01:FIB_50", "active": True},
                {"level_id": "FIB.ANCHOR.ACTIVE.01:FIB_132", "active": True}],
    ),
)
add_case(
    _F, "FIB_CHAIN_ELIGIBLE", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"anchor": _F_ANCHOR_ELIGIBLE, "range": _F_RANGE, "sequence": "BETA"},
    expected=exp(
        "RANGE_ACTIVE", "CROSS_LAYER", "RESEARCH_ONLY",
        warnings=["GAP_UNRESOLVED"],
        facts=["FIB.R15_GATE", "FIB.RANGE_BIRTH", "FIB.AB_RANGE", "FIB.SEQUENCE",
               "FIB.R11_NEGATIVE_EVIDENCE", "FIB.DISTRIBUTION", "PRIOR_STATE.ABSENT"],
        evidence=_F_EV,
    ),
)
add_case(
    _F, "FIB_R15_UNRESOLVED_REFUSES", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"anchor": _F_ANCHOR_UNRESOLVED, "range": _F_RANGE},
    refusal="RULE_NOT_MATERIALIZED",
)
add_case(
    _F, "FIB_COORDS_WITHOUT_RULE", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"anchor": _F_ANCHOR_UNRESOLVED, "range": _F_RANGE, "coordinates": _F_COORDS},
    refusal="RULE_NOT_MATERIALIZED",
)
add_case(
    _F, "FIB_NO_ANCHOR", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"range": _F_RANGE},
    expected=exp(
        "RANGE_BIRTH_UNRESOLVED", "CROSS_LAYER", "NOT_AUTHORIZED",
        no_go=["RULE_NOT_MATERIALIZED"], warnings=["GAP_UNRESOLVED"],
        facts=["FIB.R15_GATE", "FIB.AB_RANGE", "FIB.SEQUENCE_UNRESOLVED",
               "FIB.R11_NEGATIVE_EVIDENCE", "FIB.DISTRIBUTION", "PRIOR_STATE.ABSENT"],
        evidence=_F_EV,
    ),
)
add_case(
    _F, "FIB_COORDINATES_NEED_ANCHOR", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"range": _F_RANGE, "coordinates": _F_COORDS},
    expected=exp(
        "RANGE_BIRTH_UNRESOLVED", "CROSS_LAYER", "NOT_AUTHORIZED",
        no_go=["RULE_NOT_MATERIALIZED"], warnings=["GAP_UNRESOLVED"],
        facts=["FIB.R15_GATE", "FIB.AB_RANGE", "FIB.SEQUENCE_UNRESOLVED",
               "FIB.COORDINATE.FIB_50", "FIB.COORDINATE.FIB_132",
               "FIB.COORDINATES_WITHOUT_ANCHOR",
               "FIB.R11_NEGATIVE_EVIDENCE", "FIB.DISTRIBUTION", "PRIOR_STATE.ABSENT"],
        evidence=_F_EV,
        levels=[{"level_id": "FIB.ANCHOR.ACTIVE.01:FIB_50", "active": False},
                {"level_id": "FIB.ANCHOR.ACTIVE.01:FIB_132", "active": False}],
    ),
)
add_case(
    _F, "FIB_REKEY_REMAPPED", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"anchor": _F_ANCHOR_ACTIVE, "range": _F_RANGE, "sequence": "GAMMA",
     "rekey": fib_rekey(_F_RANGE)},
    expected=exp(
        "REKEY_REMAPPED", "CROSS_LAYER", "RESEARCH_ONLY",
        warnings=["GAP_UNRESOLVED"],
        facts=["FIB.R15_GATE", "FIB.RANGE_BIRTH", "FIB.AB_RANGE", "FIB.SEQUENCE",
               "FIB.REKEY_REMAPPING", "FIB.R11_NEGATIVE_EVIDENCE",
               "FIB.DISTRIBUTION", "PRIOR_STATE.ABSENT"],
        evidence=_F_EV,
    ),
)
add_case(
    _F, "FIB_COORD_132_NOT_A_REKEY", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"anchor": _F_ANCHOR_ACTIVE, "range": _F_RANGE, "sequence": "DELTA",
     "coordinates": (fib_coords(AnchorStatus.ACTIVE, _F_RANGE, ("FIB_132",))[0],)},
    expected=exp(
        "RANGE_ACTIVE", "CROSS_LAYER", "RESEARCH_ONLY",
        warnings=["GAP_UNRESOLVED"],
        facts=["FIB.R15_GATE", "FIB.RANGE_BIRTH", "FIB.AB_RANGE", "FIB.SEQUENCE",
               "FIB.COORDINATE.FIB_132",
               "FIB.R11_NEGATIVE_EVIDENCE", "FIB.DISTRIBUTION", "PRIOR_STATE.ABSENT"],
        evidence=_F_EV,
        levels=[{"level_id": "FIB.ANCHOR.ACTIVE.01:FIB_132", "active": True}],
    ),
)
add_case(
    _F, "FIB_PIVOT_ORIGIN_REFUSED", "CROSSASSET.FIB.RANGE_BIRTH.V1",
    {"range": _F_RANGE, "anchor_origin": "LOCAL_PIVOT"},
    refusal="MODEL_CONTRACT",
)

# ---------------------------------------------------------------------------
# Group: JPY Carry
# ---------------------------------------------------------------------------

_J = "jpy_carry_states"


def _pair(instrument: str, direction: str | None = None, *, no_go: bool = False,
          path=None) -> JpyPairInput:
    return JpyPairInput(
        instrument_id=instrument,
        role=JpyRole(JPY_ROLE := {"USDJPY": "CARRY_MASTER", "AUDJPY": "RISK_EXPRESSION",
                                  "EURJPY": "CONFIRMATION_VETO"}[instrument]),
        local_direction=DirectionSide(direction) if direction else None,
        native_no_go=no_go,
        path=path,
    )


_J1_FACTS = ["JPY.PAIR.USDJPY", "JPY.PAIR.AUDJPY", "JPY.PAIR.EURJPY",
             "JPY.BASKET.AGREEMENT", "JPY.BASKET.CONFIRMATION"]

add_case(
    _J, "JPY_AGREE_CONFIRM", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP"), _pair("AUDJPY", "UP"), _pair("EURJPY", "UP"))},
    expected=exp(
        "BASKET_AGREE_CONFIRM", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "USDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "AUDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "EURJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "CONFIRMATION", "layer": "L2", "state": "CONFIRMED"},
        ],
        facts=_J1_FACTS, evidence=[],
    ),
)
add_case(
    _J, "JPY_CONFIRM_ABSENT", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP"), _pair("AUDJPY", "UP"))},
    expected=exp(
        "BASKET_CONFIRM_ABSENT", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "USDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "AUDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "CONFIRMATION", "layer": "L2", "state": "ABSENT"},
        ],
        facts=["JPY.PAIR.USDJPY", "JPY.PAIR.AUDJPY", "JPY.BASKET.AGREEMENT",
               "JPY.BASKET.CONFIRMATION"],
        evidence=[],
    ),
)
add_case(
    _J, "JPY_CONFIRM_VETO", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP"), _pair("AUDJPY", "UP"), _pair("EURJPY", "DOWN"))},
    expected=exp(
        "BASKET_VETO", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "USDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "AUDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "EURJPY", "layer": "L1", "state": "DIRECTION_DOWN"},
            {"label": "CONFIRMATION", "layer": "L2", "state": "VETO"},
        ],
        facts=_J1_FACTS, evidence=[],
    ),
)
add_case(
    _J, "JPY_MASTER_EXPRESSION_CONFLICT", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP"), _pair("AUDJPY", "DOWN"), _pair("EURJPY", "UP"))},
    expected=exp(
        "BASKET_CONFLICT", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "USDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "AUDJPY", "layer": "L1", "state": "DIRECTION_DOWN"},
            {"label": "EURJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "CONFIRMATION", "layer": "L2", "state": "VETO"},
        ],
        facts=_J1_FACTS, evidence=[],
    ),
)
add_case(
    _J, "JPY_NO_GO_MASTER", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP", no_go=True), _pair("AUDJPY", "UP"),
               _pair("EURJPY", "UP"))},
    expected=exp(
        "BASKET_UNRESOLVED", "CROSS_LAYER", "MANUAL_OPERATOR",
        no_go=["NATIVE_TIER_NO_GO"],
        sub_states=[
            {"label": "USDJPY", "layer": "L1", "state": "NO_GO"},
            {"label": "AUDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "EURJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "CONFIRMATION", "layer": "L2", "state": "UNRESOLVED"},
        ],
        facts=_J1_FACTS, evidence=[],
    ),
)
add_case(
    _J, "JPY_DT_REFERENCED", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP"), _pair("AUDJPY", "UP"), _pair("EURJPY", "UP")),
     "dt_referenced": True},
    expected=exp(
        "BASKET_AGREE_CONFIRM", "CROSS_LAYER", "MANUAL_OPERATOR",
        sub_states=[
            {"label": "USDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "AUDJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "EURJPY", "layer": "L1", "state": "DIRECTION_UP"},
            {"label": "CONFIRMATION", "layer": "L2", "state": "CONFIRMED"},
        ],
        facts=_J1_FACTS + ["JPY.DT.REFERENCED"], evidence=[],
        levels=[{"level_id": "JPY_132", "active": False},
                {"level_id": "JPY_168", "active": False},
                {"level_id": "JPY_187_5", "active": False}],
    ),
)
add_case(
    _J, "JPY_EQUAL_VOTE_REFUSED", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP"), _pair("AUDJPY", "UP"), _pair("EURJPY", "UP")),
     "aggregation_request": "EQUAL_VOTE"},
    refusal="MODEL_CONTRACT",
)
add_case(
    _J, "JPY_CROSS_PAIR_PATH", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (_pair("USDJPY", "UP", path=jpy_path("AUDJPY")), _pair("AUDJPY", "UP"))},
    refusal="INSTRUMENT_SCOPE_MISMATCH",
)
add_case(
    _J, "JPY_ROLE_MAP_REASSIGNED", "JPY.CARRY_GAME.L1_L3.V1",
    {"pairs": (JpyPairInput(instrument_id="USDJPY", role=JpyRole.CONFIRMATION_VETO),)},
    refusal="MODEL_CONTRACT",
)

# ---------------------------------------------------------------------------
# Registry dispatch expectations
# ---------------------------------------------------------------------------

REGISTRY_FIXTURE = {
    "fixture_id": "BLOC_III_3.REGISTRY_DISPATCH_CASES.V1",
    "historical": True,
    "provenance": SYNTHETIC,
    "data_classification": (
        "CANONICAL_SOURCE_SLICE for the registered model keys and calibration/"
        "coordinate bindings quoted from the frozen PLAN.md §5.2 matrix; "
        "resolution behavior is contract-test material"
    ),
    "observation_cutoff": CUTOFF,
    "calculation_timestamp": CALC_TS,
    "entries": [
        {
            "model_id": "EUR.DAILY.NEWS_REKEY.V1",
            "model_version": "PHASE1",
            "family": "EUR_DAILY",
            "layer": "L1",
            "stateful": True,
            "clock_bound": True,
            "market_scope": ["EURUSD"],
            "calibration_bindings": [["EUR.DAILY.NEWS_REKEY.V1", "PHASE1",
                                      "EUR_DAILY_PHASE1_TIERS", "V1"]],
            "coordinate_set_keys": [["EUR.DAILY.NEWS_REKEY.V1", "PHASE1"]],
        },
        {
            "model_id": "EUR.WEEKLY.V1_1",
            "model_version": "V1_1",
            "family": "EUR_WEEKLY",
            "layer": "L2",
            "stateful": True,
            "clock_bound": False,
            "market_scope": ["EURUSD"],
            "calibration_bindings": [["EUR.WEEKLY.V1_1", "V1_1",
                                      "EUR_WEEKLY_TIER_RANGE", "V1"]],
            "coordinate_set_keys": [],
        },
        {
            "model_id": "EUR.HIGHER_ORDER.V1",
            "model_version": "V1",
            "family": "EUR_HIGHER_ORDER",
            "layer": "L3",
            "stateful": True,
            "clock_bound": False,
            "market_scope": ["EURUSD"],
            "calibration_bindings": [],
            "coordinate_set_keys": [],
        },
        {
            "model_id": "XAU.GAME.L1_L2_L3.V1",
            "model_version": "V1",
            "family": "XAU",
            "layer": "CROSS_LAYER",
            "stateful": True,
            "clock_bound": False,
            "market_scope": ["XAUUSD"],
            "calibration_bindings": [["XAU.GAME.L1_L2_L3.V1", "V1",
                                      "XAU_SPATIAL_BANDS", "V1"]],
            "coordinate_set_keys": [["XAU.GAME.L1_L2_L3.V1", "V1"]],
        },
        {
            "model_id": "BTC.TRACKER.DWM.V1",
            "model_version": "V1",
            "family": "BTC_TRACKER",
            "layer": "CROSS_LAYER",
            "stateful": True,
            "clock_bound": False,
            "market_scope": ["BTCUSD"],
            "calibration_bindings": [["BTC.TRACKER.DWM.V1", "V1",
                                      "BTC_TRACKER_DWM_TIERS", "V1"]],
            "coordinate_set_keys": [],
        },
        {
            "model_id": "CROSSASSET.FIB.RANGE_BIRTH.V1",
            "model_version": "R15",
            "family": "FIB_RANGE_BIRTH",
            "layer": "CROSS_LAYER",
            "stateful": True,
            "clock_bound": False,
            "market_scope": [],
            "calibration_bindings": [],
            "coordinate_set_keys": [["CROSSASSET.FIB.RANGE_BIRTH.V1", "R15"]],
        },
        {
            "model_id": "JPY.CARRY_GAME.L1_L3.V1",
            "model_version": "V1",
            "family": "JPY_CARRY",
            "layer": "CROSS_LAYER",
            "stateful": False,
            "clock_bound": False,
            "market_scope": ["AUDJPY", "EURJPY", "USDJPY"],
            "calibration_bindings": [],
            "coordinate_set_keys": [["JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM"]],
        },
        {
            "model_id": "JPY.CARRY_GAME.L1_L3.V1",
            "model_version": "DT_12_4PM",
            "family": "JPY_DT_HISTORICAL",
            "layer": "CROSS_LAYER",
            "stateful": False,
            "clock_bound": False,
            "market_scope": ["AUDJPY", "EURJPY", "USDJPY"],
            "calibration_bindings": [],
            "coordinate_set_keys": [["JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM"]],
            "dispatch": "REFUSED_NO_AUTHORIZED_RUNTIME",
        },
    ],
    "refusals": [
        {"model_id": "EUR.DAILY.NEWS_REKEY.V1", "model_version": "V2",
         "expected_refusal": "MODEL_VERSION_UNAVAILABLE"},
        {"model_id": "BTC.GAME.L1_V1", "model_version": "V1",
         "expected_refusal": "MODEL_VERSION_UNAVAILABLE"},
        {"model_id": "", "model_version": "V1",
         "expected_refusal": "MODEL_VERSION_UNAVAILABLE"},
        {"model_id": "XAU.GAME.L1_L2_L3.V1", "model_version": "V2",
         "expected_refusal": "MODEL_VERSION_UNAVAILABLE"},
    ],
}


# ---------------------------------------------------------------------------
# Encoding / decoding / request building (single source of truth)
# ---------------------------------------------------------------------------

_HINT_CACHE: dict[type, dict[str, Any]] = {}


def _hints(cls: type) -> dict[str, Any]:
    if cls not in _HINT_CACHE:
        _HINT_CACHE[cls] = get_type_hints(cls)
    return _HINT_CACHE[cls]


def decode_as(hint: Any, data: Any) -> Any:
    """Type-driven rebuild of one input value from ``encode_value`` JSON."""
    if data is None:
        return None
    origin = get_origin(hint)
    if origin is Union or origin is UnionType:
        args = [arg for arg in get_args(hint) if arg is not type(None)]
        return decode_as(args[0], data)
    if origin is tuple:
        args = get_args(hint)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(decode_as(args[0], item) for item in data)
        return tuple(decode_as(arg, item) for arg, item in zip(args, data))
    if origin is list:
        (arg,) = get_args(hint) or (Any,)
        return [decode_as(arg, item) for item in data]
    if hint is Decimal:
        return Decimal(data)
    if hint is datetime:
        return _utc(data)
    if hint is bool:
        return data
    if hint is int:
        return int(data)
    if hint is str:
        return str(data)
    if isinstance(hint, type) and issubclass(hint, Enum):
        return hint(data)
    if isinstance(hint, type) and is_dataclass(hint):
        hints = _hints(hint)
        kwargs = {
            field.name: decode_as(hints[field.name], data[field.name])
            for field in dc_fields(hint)
            if field.name in data
        }
        return hint(**kwargs)
    return data


def build_request(case: dict, outputs: dict[str, Any] | None = None) -> ModelRequest:
    """Rebuild one fixture case into a ready ``ModelRequest``.

    ``outputs`` maps case_id → previously computed ``ModelOutput`` for
    ``prior_case`` chaining (the focused suite passes the same cache it
    uses for golden reproduction).
    """
    outputs = outputs if outputs is not None else {}
    inputs_cls = FAMILY_INPUTS[case["model_id"]]
    hints = _hints(inputs_cls)
    unknown = set(case["inputs"]) - set(hints)
    if unknown:
        raise AssertionError(f"{case['case_id']}: unknown input fields {sorted(unknown)}")
    decoded = {
        name: decode_as(hints[name], value) for name, value in case["inputs"].items()
    }
    inputs = inputs_cls(**decoded)
    prior = outputs.get(case["prior_case"]) if case.get("prior_case") else None
    if case.get("prior_case") and prior is None:
        raise AssertionError(
            f"{case['case_id']}: prior case {case['prior_case']} not computed yet"
        )
    calibration = (
        decode_as(CalibrationKey, case["calibration_key"])
        if case["calibration_key"] is not None
        else None
    )
    return ModelRequest(
        model_id=case["model_id"],
        model_version=case["model_version"],
        instrument_id=case["instrument_id"],
        inputs=inputs,
        calculation_timestamp=_utc(case["calculation_timestamp"]),
        calibration_key=calibration,
        market_data_schema_version=IDENTITY["market_data_schema_version"],
        clock_registry_version=IDENTITY["clock_registry_version"],
        session_registry_version=IDENTITY["session_registry_version"],
        measurement_engine_version=IDENTITY["measurement_engine_version"],
        prior_state=prior,
        clock_id=case["clock_id"],
        session_id=case["session_id"],
    )


def all_cases() -> list[tuple[str, dict]]:
    ordered: list[tuple[str, dict]] = []
    for group in sorted(CASES):
        for case in CASES[group]:
            ordered.append((group, case))
    return ordered


def run_cases() -> tuple[dict[str, Any], list[tuple[str, str]]]:
    """Run every case; return (outputs by id, [(case_id, refusal_code)])."""
    from app.forge.model_runtime import ModelRuntimeError, run_model

    outputs: dict[str, Any] = {}
    refusals: list[tuple[str, str]] = []
    # Dependency order: cases without priors first (all of them), then priors.
    pending = [case for _group, case in all_cases()]
    for _ in range(3):
        remaining = []
        for case in pending:
            if case.get("prior_case") and case["prior_case"] not in outputs:
                remaining.append(case)
                continue
            request = build_request(case, outputs)
            try:
                outputs[case["case_id"]] = run_model(request)
            except ModelRuntimeError as exc:
                code = str(exc).split(":", 1)[0]
                refusals.append((case["case_id"], code))
        pending = remaining
        if not pending:
            break
    if pending:
        raise AssertionError(f"unresolved prior dependencies: {[c['case_id'] for c in pending]}")
    return outputs, refusals


# ---------------------------------------------------------------------------
# Fixture documents
# ---------------------------------------------------------------------------

_GROUP_META = {
    "eur_daily_states": (
        "BLOC_III_3.EUR_DAILY_STATES.V1",
        "EUR.DAILY.NEWS_REKEY.V1",
        "Synthetic golden states for the EUR Daily News + Rekey chain: seed/tier "
        "states, the >45p no-go boundary, the 100/125/132/168/185 ladder, event "
        "conditioning over a synthetic labeled event and slot-conditioned range-left",
    ),
    "eur_weekly_states": (
        "BLOC_III_3.EUR_WEEKLY_STATES.V1",
        "EUR.WEEKLY.V1_1",
        "Synthetic golden states for the EUR Weekly Engine: outer-node promotion "
        "only, frozen-after-completion chaining, NOT_THIS_LAYER destination "
        "boundary and explicit unresolved timing",
    ),
    "eur_higher_order_states": (
        "BLOC_III_3.EUR_HIGHER_ORDER_STATES.V1",
        "EUR.HIGHER_ORDER.V1",
        "Synthetic golden states for the EUR Higher Order chain: typed D3 prior, "
        "evidence-bound parameters resolving to UNRESOLVED, unfinished-side "
        "conditional completion, M3 checkpoints and layer-conflict facts (no "
        "score field exists)",
    ),
    "xau_promotion_states": (
        "BLOC_III_3.XAU_PROMOTION_STATES.V1",
        "XAU.GAME.L1_L2_L3.V1",
        "Synthetic golden states for the XAU three-layer runtime: promotion rules "
        "68+8h->80 (VALIDATED_SMALL_N) and 120+8h->132 (RESEARCH_FLAG_SMALL_N), "
        "the 132 boundary with no automatic 168, parked-stays-parked, blind-touch "
        "never confirming and L3 authority isolation",
    ),
    "btc_tracker_states": (
        "BLOC_III_3.BTC_TRACKER_STATES.V1",
        "BTC.TRACKER.DWM.V1",
        "Synthetic golden states for the BTC Tracker: native tier boundary edges "
        "(749/750/3000/3001), the >$3,000 Asian-range no-go, slot-conditioned "
        "range-left, unresolved weekly/monthly horizons and cross-asset/cross-model "
        "refusals — BTC Tracker, never a BTC Game",
    ),
    "fib_range_birth_states": (
        "BLOC_III_3.FIB_RANGE_BIRTH_STATES.V1",
        "CROSSASSET.FIB.RANGE_BIRTH.V1",
        "Synthetic golden states for the Fib Range Birth chain behind the R15 "
        "gate: declared-rule research chains, RULE_NOT_MATERIALIZED refusals, "
        "structural rekey remapping and the absence of any pivot fallback",
    ),
    "jpy_carry_states": (
        "BLOC_III_3.JPY_CARRY_STATES.V1",
        "JPY.CARRY_GAME.L1_L3.V1",
        "Synthetic golden states for the JPY basket roles: agree+confirm, "
        "confirm-absent, veto/conflict, per-pair no-go, explicit DT reference "
        "only, equal-vote refusal and cross-pair contamination refusal",
    ),
}


def _project(output: Any) -> dict:
    """Project one ModelOutput onto the authored expectation shape."""
    direction = (
        "NONE_DECLARED"
        if not output.direction_bias.declared
        else {
            "side": output.direction_bias.side.value,
            "basis_fact_id": output.direction_bias.basis_fact_id,
        }
    )
    return {
        "model_state": output.model_state,
        "layer": output.layer.value,
        "production_authorization": output.production_authorization.value,
        "quality_state": output.quality_state.value,
        "no_go": [reason.value for reason in output.no_go],
        "warnings": [code.value for code in output.warnings],
        "range_left_state": output.range_left.state.value,
        "range_left_value": (
            str(output.range_left.value.value)
            if output.range_left.value is not None
            else None
        ),
        "direction_bias": direction,
        "sub_states": [
            {
                "label": sub.label,
                "layer": sub.layer.value,
                "state": sub.state,
            }
            for sub in output.sub_states
        ],
        "fact_ids": [fact.fact_id for fact in output.explanation_facts],
        "evidence_refs": list(output.evidence_refs),
        "levels": [
            {"level_id": level.level_id, "active": level.active}
            for level in output.levels
        ],
    }


def _group_document(group: str) -> dict:
    fixture_id, model_id, description = _GROUP_META[group]
    default_cal, default_clock, default_session = _REQUEST_DEFAULTS[model_id]
    return {
        "fixture_id": fixture_id,
        "description": description,
        "model_id": model_id,
        "historical": True,
        "provenance": SYNTHETIC,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "observation_cutoff": CUTOFF,
        "calculation_timestamp": CALC_TS,
        "clock": default_clock,
        "session_id": default_session,
        "cases": CASES[group],
    }


def _replay_document(outputs: dict[str, Any]) -> dict:
    return {
        "fixture_id": "BLOC_III_3.REPLAY_HASHES.V1",
        "algorithm": "sha256",
        "description": (
            "Canonical replay hashes per golden case: sha256 over the sorted-key "
            "compact JSON of the full ModelOutput payload (III.2 encode_value "
            "graph) including the input-identity envelope and prior-state "
            "reference. Reproduction is determinism evidence, never performance "
            "evidence."
        ),
        "historical": True,
        "provenance": SYNTHETIC,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "observation_cutoff": CUTOFF,
        "calculation_timestamp": CALC_TS,
        "hashes": {case_id: out.output_hash for case_id, out in sorted(outputs.items())},
    }


def _dumps(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def documents() -> dict[str, str]:
    """Every fixture file this generator owns, as exact file text."""
    outputs, refusals = run_cases()
    refusal_map = dict(refusals)
    # validate expected_refusal authorship against actual behavior
    for _group, case in all_cases():
        expected = case["expected_refusal"]
        actual = refusal_map.get(case["case_id"])
        if expected is not None and actual is None:
            raise AssertionError(
                f"{case['case_id']}: expected refusal {expected} but the case ran"
            )
        if expected is None and actual is not None:
            raise AssertionError(
                f"{case['case_id']}: unexpected refusal {actual}"
            )
        if expected is not None and actual != expected:
            raise AssertionError(
                f"{case['case_id']}: refusal {actual} != authored {expected}"
            )
        if expected is None and case["expected"] is not None:
            projected = _project(outputs[case["case_id"]])
            authored = case["expected"]
            for key in sorted(set(projected) | set(authored)):
                if projected.get(key) != authored.get(key):
                    raise AssertionError(
                        f"{case['case_id']}: expected {key}="
                        f"{authored.get(key)!r} but runtime produced "
                        f"{projected.get(key)!r}"
                    )
    files: dict[str, str] = {}
    for group in sorted(CASES):
        files[f"{group}.json"] = _dumps(_group_document(group))
    files["registry_dispatch_cases.json"] = _dumps(REGISTRY_FIXTURE)
    files["replay_hashes.json"] = _dumps(_replay_document(outputs))

    manifest = {
        "algorithm": "sha256",
        "description": (
            "Deterministic committed golden fixtures for Bloc III.3. Hashes "
            "cover every JSON fixture in this directory except this manifest. "
            "Hashes are recorded over the LF-normalized content, so the "
            "manifest verifies identically on Windows (CRLF worktrees) and "
            "Linux CI (LF checkouts)."
        ),
        "files": {},
        "generator": "generate_fixtures.py",
        "provenance": {
            "bar_slices": "SYNTHETIC_FIXTURE",
            "measurement_inputs": "SYNTHETIC_FIXTURE",
            "canonical_constants": "CANONICAL_SOURCE_SLICE",
            "replay_hashes": "SYNTHETIC_FIXTURE",
        },
    }
    for name in sorted(files):
        normalized = files[name].encode("utf-8")
        manifest["files"][name] = hashlib.sha256(normalized).hexdigest()
    files["FIXTURE_MANIFEST.json"] = _dumps(manifest)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify committed fixtures reproduce byte-identically")
    args = parser.parse_args(argv)
    produced = documents()
    if args.check:
        problems: list[str] = []
        for name, text in sorted(produced.items()):
            target = HERE / name
            if not target.exists():
                problems.append(f"missing {name}")
                continue
            committed = target.read_text(encoding="utf-8").replace("\r\n", "\n")
            if committed != text:
                problems.append(f"content differs: {name}")
        for name in sorted(p.name for p in HERE.glob("*.json")):
            if name not in produced:
                problems.append(f"unexpected file: {name}")
        if problems:
            for problem in problems:
                print(f"FAIL {problem}")
            return 1
        print(f"OK {len(produced)} fixture files reproduce byte-identically "
              f"(inputs, expectations and replay hashes)")
        return 0
    for name, text in sorted(produced.items()):
        (HERE / name).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
