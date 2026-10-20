"""Deterministic golden-fixture generator for Bloc III.2.

Run from this directory:  ``python generate_fixtures.py``

Every emitted file is a function of the fixed literals below — no wall
clock, no randomness, no network — so regeneration is byte-identical and
the hashes recorded in ``FIXTURE_MANIFEST.json`` verify.

Provenance honesty (PLAN.md §10 GAP-4/GAP-5; ACCEPTANCE O3/O4, J7):

* Bar rows and event records are ``SYNTHETIC_FIXTURE`` — deterministic
  generated values, *not* empirical market evidence.  They can never
  support a performance, expectancy or win-rate claim.
* Calibration constants, spatial bands, promotion sample sizes, weekly
  outer nodes, the D3/unfinished-side evidence ids and the JPY DT
  structures are ``CANONICAL_SOURCE_SLICE`` — quoted from frozen
  canonical corpus sources, each record carrying its ``source_ref`` and,
  where the corpus states one, the source sentence.
* Every expected value in these files is computed here with explicit
  ``Decimal`` arithmetic — independently of the engine under test — so
  the focused suite is a genuine cross-check and not a tautology.

Nothing in this directory performs a network call, reads a credential or
writes to the canonical corpus.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent

NY = "America/New_York"

EUR_CUTOFF = "2026-03-03T00:30:00Z"
XAU_CUTOFF = "2026-03-03T00:30:00Z"
BTC_CUTOFF = "2026-03-03T00:30:00Z"

SYNTHETIC = "SYNTHETIC_FIXTURE"
CANONICAL = "CANONICAL_SOURCE_SLICE"

SYNTHETIC_CLASSIFICATION = (
    "SYNTHETIC_FIXTURE - deterministic generated values; not empirical "
    "market evidence and never citable for performance claims"
)

ROW_KEYS = ("open_time", "close_time", "o", "h", "l", "c", "volume", "source_timestamp")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _ramp_rows(
    base: Decimal,
    unit: Decimal,
    *,
    first_open_u: int,
    low_u: int,
    high_u: int,
    step_u: int,
    n: int,
    start_iso: str,
    timeframe_minutes: int = 5,
) -> list[dict]:
    """Build ``n`` contiguous bars whose extremes are the declared ones.

    All arithmetic is in integer multiples of ``unit`` above ``base``:
    the first bar opens at ``first_open_u`` and carries the low, the last
    bar closes at ``first_open_u + step_u * (n - 1)`` and carries the
    high.  The result is exact — no rounding, no floating point.
    """
    start = _parse(start_iso)
    step = timedelta(minutes=timeframe_minutes)
    closes = [first_open_u + step_u * k for k in range(n)]
    rows: list[dict] = []
    previous_close = first_open_u
    for index in range(n):
        open_u = previous_close
        close_u = closes[index]
        high_u_bar = max(open_u, close_u) + 1
        low_u_bar = min(open_u, close_u) - 1
        if index == 0:
            low_u_bar = low_u
        if index == n - 1:
            high_u_bar = high_u
        open_time = start + step * index
        close_time = open_time + step
        rows.append(
            {
                "open_time": _stamp(open_time),
                "close_time": _stamp(close_time),
                "o": str(base + unit * open_u),
                "h": str(base + unit * high_u_bar),
                "l": str(base + unit * low_u_bar),
                "c": str(base + unit * close_u),
                "volume": str(100 + index),
                "source_timestamp": _stamp(close_time + timedelta(seconds=3)),
            }
        )
        previous_close = close_u
    return rows


def _explicit_rows(
    base: Decimal,
    unit: Decimal,
    offsets: list[tuple[int, int, int, int]],
    *,
    start_iso: str,
    timeframe_minutes: int = 5,
) -> list[dict]:
    """Build contiguous bars from explicit (open, high, low, close) unit offsets."""
    start = _parse(start_iso)
    step = timedelta(minutes=timeframe_minutes)
    rows: list[dict] = []
    for index, (open_u, high_u, low_u, close_u) in enumerate(offsets):
        open_u = Decimal(str(open_u))
        high_u = Decimal(str(high_u))
        low_u = Decimal(str(low_u))
        close_u = Decimal(str(close_u))
        open_time = start + step * index
        close_time = open_time + step
        rows.append(
            {
                "open_time": _stamp(open_time),
                "close_time": _stamp(close_time),
                "o": str(base + unit * open_u),
                "h": str(base + unit * high_u),
                "l": str(base + unit * low_u),
                "c": str(base + unit * close_u),
                "volume": str(200 + index),
                "source_timestamp": _stamp(close_time + timedelta(seconds=3)),
            }
        )
    return rows


def _expected_range(
    base: Decimal,
    unit: Decimal,
    *,
    first_open_u: int,
    low_u: int,
    high_u: int,
    step_u: int,
    n: int,
) -> dict:
    """Independently compute the golden range facts (plain Decimal math)."""
    first_open = base + unit * first_open_u
    low = base + unit * low_u
    high = base + unit * high_u
    last_close = base + unit * (first_open_u + step_u * (n - 1))
    size = high - low
    if last_close > first_open:
        direction = "UP"
        consumed = min(max(last_close - first_open, Decimal(0)), size)
    elif last_close < first_open:
        direction = "DOWN"
        consumed = min(max(first_open - last_close, Decimal(0)), size)
    else:
        direction = "FLAT"
        consumed = Decimal(0)
    midpoint = (high + low) / Decimal(2)
    return {
        "high": str(high),
        "low": str(low),
        "size_native": str(size / unit),
        "midpoint": str(midpoint),
        "direction": direction,
        "close_location": str(_ratio((last_close - low) / size)),
        "consumed_fraction": str(_ratio(consumed / size)),
        "range_left_native": str((size - consumed) / unit),
    }


def _ratio(value: Decimal) -> Decimal:
    """Quantize a ratio to 10 decimal places, half-even (engine quantum)."""
    return value.quantize(Decimal("0.0000000001"))


def _write(name: str, payload: dict) -> None:
    path = HERE / name
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# ---------------------------------------------------------------------------
# EUR daily tier seeds (T1 / T2 / T3 / no-go)
# ---------------------------------------------------------------------------

EUR_BASE = Decimal("1.07900")
EUR_UNIT = Decimal("0.0001")  # one EURUSD pip

EUR_SEED_SPECS = [
    ("EUR_SEED_T1", "T1", False, 6, 4, 16, 1, 6),
    ("EUR_SEED_T2", "T2", False, 3, 0, 25, 3, 6),
    ("EUR_SEED_T3", "T3", False, 3, 0, 38, 5, 6),
    ("EUR_SEED_NO_GO", "NO_GO", True, 3, 0, 52, 7, 6),
]


def _eur_tier_seeds() -> dict:
    seeds = []
    for (
        case_id,
        tier_id,
        no_go,
        first_open_u,
        low_u,
        high_u,
        step_u,
        n,
    ) in EUR_SEED_SPECS:
        rows = _ramp_rows(
            EUR_BASE,
            EUR_UNIT,
            first_open_u=first_open_u,
            low_u=low_u,
            high_u=high_u,
            step_u=step_u,
            n=n,
            start_iso="2026-03-03T00:00:00Z",
        )
        expected = _expected_range(
            EUR_BASE,
            EUR_UNIT,
            first_open_u=first_open_u,
            low_u=low_u,
            high_u=high_u,
            step_u=step_u,
            n=n,
        )
        expected["expected_tier_id"] = tier_id
        expected["expected_no_go"] = no_go
        seeds.append(
            {
                "case_id": case_id,
                "tier_id": tier_id,
                "expected_no_go": no_go,
                "rows": rows,
                "expected": expected,
            }
        )
    return {
        "fixture_id": "BLOC_III_2.EUR_DAILY_TIER_SEEDS.V1",
        "provenance": SYNTHETIC,
        "historical": True,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "observation_cutoff": EUR_CUTOFF,
        "instrument_id": "EURUSD",
        "timeframe": "M5",
        "clock": NY,
        "session_id": "EUR_DAILY.ASIAN_RANGE",
        "model_id": "EUR.DAILY.NEWS_REKEY.V1",
        "model_version": "PHASE1",
        "calibration_key": {
            "model_id": "EUR.DAILY.NEWS_REKEY.V1",
            "model_version": "PHASE1",
            "calibration_id": "EUR_DAILY_PHASE1_TIERS",
            "calibration_version": "V1",
        },
        "calibration_evidence_id": "EV.EUR.DAILY.PHASE1_TIERS.V1",
        "calibration_source_ref": (
            "corpus/canonical/evidence/EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md"
        ),
        "calibration_quote": "T1 <20p T2 20-30p T3 30-45p >45p excluded/no-go.",
        "seeds": seeds,
    }


# ---------------------------------------------------------------------------
# EUR rekey ladder (coordinate families named by the EUR Daily card)
# ---------------------------------------------------------------------------


def _eur_rekey_ladder() -> dict:
    # Projection arithmetic is in price units: offset = span * level/100
    # where span = high - low of the earned range (the T2 seed).  Native
    # unit counts (pips) are never added to a price.
    low = Decimal("1.07900")
    high = Decimal("1.08150")
    span = high - low
    ladder = []
    for family_id, level in (
        ("EUR_DAILY_100", "100"),
        ("EUR_DAILY_125", "125"),
        ("EUR_DAILY_132", "132"),
        ("EUR_DAILY_168", "168"),
        ("EUR_DAILY_185", "185"),
    ):
        offset = span * Decimal(level) / Decimal(100)
        ladder.append(
            {
                "family_id": family_id,
                "level": level,
                "expected_projected_price": str(low + offset),
            }
        )
    return {
        "fixture_id": "BLOC_III_2.EUR_REKEY_LADDER.V1",
        "provenance": SYNTHETIC,
        "historical": True,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "observation_cutoff": EUR_CUTOFF,
        "instrument_id": "EURUSD",
        "clock": NY,
        "session_id": "EUR_DAILY.ASIAN_RANGE",
        "model_id": "EUR.DAILY.NEWS_REKEY.V1",
        "model_version": "PHASE1",
        "source_ref": (
            "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
        ),
        "source_quote": (
            "100 /125 /132 /168 /185 appear in the modern Daily lineage."
        ),
        "earned_range_case_id": "EUR_SEED_T2",
        "earned_range_low": "1.07900",
        "earned_range_high": "1.08150",
        "ladder": ladder,
        "note": (
            "The coordinate family is a level projection over the earned "
            "range.  A projected coordinate carries no acceptance, rekey, "
            "promotion or setup meaning (invariant: a coordinate touch "
            "implies nothing)."
        ),
    }


# ---------------------------------------------------------------------------
# EUR event budget (subtractive residual)
# ---------------------------------------------------------------------------


def _eur_event_budget() -> dict:
    return {
        "fixture_id": "BLOC_III_2.EUR_EVENT_BUDGET.V1",
        "provenance": SYNTHETIC,
        "historical": True,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "instrument_id": "EURUSD",
        "clock": NY,
        "session_id": "EUR_DAILY.ASIAN_RANGE",
        "source_ref": (
            "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
        ),
        "source_quote": (
            "Residual event budget is subtractive: already-consumed "
            "movement changes what remains available."
        ),
        "unit": "PIP",
        "events": [
            {
                "event_id": "EVT.SYNTH.EUR.EMPLOYMENT_01",
                "family": "EMPLOYMENT_RELEASE",
                "relevance_currencies": ["EUR"],
                "relevance_assets": ["EURUSD"],
                "scheduled_time": "2026-03-03T13:30:00Z",
                "actual_time": "2026-03-03T13:30:02Z",
                "source_ref": (
                    "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
                ),
                "provenance_label": SYNTHETIC,
                "historical_band_lower": "8",
                "historical_band_upper": "25",
                "historical_size": "17",
                "consumed": "6",
                "expected_residual": "11",
                "expected_band_declared": True,
                "expected_size_declared": True,
            },
            {
                "event_id": "EVT.SYNTH.EUR.NO_HISTORY_01",
                "family": "MACRO_RELEASE",
                "relevance_currencies": ["EUR"],
                "relevance_assets": ["EURUSD"],
                "scheduled_time": "2026-03-04T13:30:00Z",
                "actual_time": None,
                "source_ref": (
                    "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
                ),
                "provenance_label": SYNTHETIC,
                "historical_band_lower": None,
                "historical_band_upper": None,
                "historical_size": None,
                "consumed": None,
                "expected_residual": None,
                "expected_band_declared": False,
                "expected_size_declared": False,
                "expected_budget": "REFUSED",
            },
        ],
    }


# ---------------------------------------------------------------------------
# EUR weekly outer nodes (canonical research slice)
# ---------------------------------------------------------------------------


def _eur_weekly_outer_nodes() -> dict:
    return {
        "fixture_id": "BLOC_III_2.EUR_WEEKLY_OUTER_NODES.V1",
        "provenance": CANONICAL,
        "historical": True,
        "data_classification": (
            "CANONICAL_SOURCE_SLICE - weekly tier median ranges and sample "
            "sizes quoted from a frozen evidence card; research claims, not "
            "guaranteed ranges and not entry levels"
        ),
        "model_id": "EUR.WEEKLY.V1_1",
        "model_version": "V1_1",
        "calibration_key": {
            "model_id": "EUR.WEEKLY.V1_1",
            "model_version": "V1_1",
            "calibration_id": "EUR_WEEKLY_TIER_RANGE",
            "calibration_version": "V1",
        },
        "calibration_status": "RESEARCH",
        "evidence_id": "EV.EUR.WEEKLY.TIER_RANGE.V1",
        "source_ref": (
            "corpus/canonical/evidence/EUR_WEEKLY_TIER_RANGE_EVIDENCE_V1.md"
        ),
        "source_quote": "T1 N45 median126.8p. T2 N69 median133.5p. T3 N60 median168.95p.",
        "unit": "PIP",
        "outer_nodes": [
            {"tier_id": "T1", "median_range": "126.8", "sample_n": 45},
            {"tier_id": "T2", "median_range": "133.5", "sample_n": 69},
            {"tier_id": "T3", "median_range": "168.95", "sample_n": 60},
        ],
        "note": (
            "The weekly tier is an input to this table, never a "
            "classification produced by it: the evidence card publishes "
            "median ranges and sample sizes, not the tier boundaries."
        ),
    }


# ---------------------------------------------------------------------------
# EUR higher-order structural handoff
# ---------------------------------------------------------------------------


def _eur_higher_order() -> dict:
    pip = Decimal("0.0001")
    quarter_base = Decimal("1.07000")
    m1_base = Decimal("1.06000")
    m2_base = Decimal("1.05000")

    quarter_rows = _explicit_rows(
        quarter_base,
        pip,
        [(10, 40, 0, 20), (20, 45, 5, 30), (30, 50, 10, 35)],
        start_iso="2026-01-05T00:00:00Z",
    )
    d1_rows = _explicit_rows(
        quarter_base,
        pip,
        [(0, 12, 0, 8), (8, 14, 4, 10), (10, 15, 6, 12)],
        start_iso="2026-01-05T00:15:00Z",
    )
    d2_rows = _explicit_rows(
        quarter_base,
        pip,
        [(0, 10, 0, 6), (6, 13, 2, 9), (9, 14, 5, 11)],
        start_iso="2026-01-06T00:00:00Z",
    )
    d3_rows = _explicit_rows(
        quarter_base,
        pip,
        [(0, 11, 0, 7), (7, 12, 3, 9), (9, 13, 5, 10)],
        start_iso="2026-01-07T00:00:00Z",
    )
    m1_rows = _explicit_rows(
        m1_base,
        pip,
        [(0, 95, 0, 60), (60, 110, 40, 85), (85, 120, 70, 100)],
        start_iso="2026-01-08T00:00:00Z",
    )
    m2_rows = _explicit_rows(
        m2_base,
        pip,
        [(0, 80, 0, 50), (50, 95, 30, 70), (70, 100, 45, 85)],
        start_iso="2026-02-05T00:00:00Z",
    )

    def _seed_size(base: Decimal, rows: list[dict]) -> str:
        highs = [Decimal(row["h"]) for row in rows]
        lows = [Decimal(row["l"]) for row in rows]
        return str((max(highs) - min(lows)) / pip)

    return {
        "fixture_id": "BLOC_III_2.EUR_HIGHER_ORDER_HANDOFF.V1",
        "provenance": SYNTHETIC,
        "historical": True,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "instrument_id": "EURUSD",
        "clock": NY,
        "session_id": "EUR_HIGHER_ORDER.QUARTER",
        "model_id": "EUR.HIGHER_ORDER.V1",
        "model_version": "V1",
        "source_ref": "corpus/canonical/models/EUR_HIGHER_ORDER_MODEL_CARD_V1.md",
        "source_quote": (
            "Quarter seed -> M1 range seed -> M2 shaping -> M3 resolution "
            "-> Weekly local path -> Daily execution."
        ),
        "hierarchy": [
            "QUARTER_SEED",
            "M1_RANGE_SEED",
            "M2_SHAPING",
            "M3_RESOLUTION",
            "WEEKLY_LOCAL_PATH",
            "DAILY_EXECUTION",
        ],
        "evidence_refs": [
            "EV.EUR.HO.D3_DIRECTION.V1",
            "EV.EUR.HO.M1_RANGE_CORR.V1",
            "EV.EUR.HO.UNFINISHED_M3.V1",
        ],
        "unfinished_side": "UPPER",
        "seeds": [
            {
                "seed_id": "QUARTER",
                "seed_kind": "QUARTER",
                "rows": quarter_rows,
                "observation_cutoff": "2026-01-05T00:15:00Z",
                "expected_size_native": _seed_size(quarter_base, quarter_rows),
            },
            {
                "seed_id": "D1",
                "seed_kind": "QUARTER_DAY",
                "rows": d1_rows,
                "observation_cutoff": "2026-01-05T00:30:00Z",
                "expected_size_native": _seed_size(quarter_base, d1_rows),
            },
            {
                "seed_id": "D2",
                "seed_kind": "QUARTER_DAY",
                "rows": d2_rows,
                "observation_cutoff": "2026-01-06T00:15:00Z",
                "expected_size_native": _seed_size(quarter_base, d2_rows),
            },
            {
                "seed_id": "D3",
                "seed_kind": "QUARTER_DAY",
                "rows": d3_rows,
                "observation_cutoff": "2026-01-07T00:15:00Z",
                "expected_size_native": _seed_size(quarter_base, d3_rows),
            },
            {
                "seed_id": "M1",
                "seed_kind": "MONTH",
                "rows": m1_rows,
                "observation_cutoff": "2026-01-08T00:15:00Z",
                "expected_size_native": _seed_size(m1_base, m1_rows),
            },
            {
                "seed_id": "M2",
                "seed_kind": "MONTH",
                "rows": m2_rows,
                "observation_cutoff": "2026-02-05T00:15:00Z",
                "expected_size_native": _seed_size(m2_base, m2_rows),
            },
        ],
        "note": (
            "The D3 directional prior, the M1 range correlation and the "
            "unfinished-side completion rate are statistical parameters of "
            "their evidence cards.  They are referenced by evidence id and "
            "are deliberately absent from the measured output."
        ),
    }


# ---------------------------------------------------------------------------
# XAU spatial bands, promotions and quarter zone
# ---------------------------------------------------------------------------


def _xau_spatial_bands() -> dict:
    # Absolute price paths: base 0 with unit 1 keeps the exact decimals.
    blind_touch_rows = _explicit_rows(
        Decimal("0"),
        Decimal("1"),
        [
            (2350.00, 2352.00, 2349.00, 2351.00),
            (2351.00, 2355.00, 2350.50, 2354.00),
            (2354.00, 2362.00, 2353.00, 2360.00),
            (2360.00, 2361.00, 2357.00, 2358.00),
            (2358.00, 2359.00, 2356.00, 2357.50),
            (2357.50, 2358.50, 2355.00, 2356.00),
        ],
        start_iso="2026-03-03T00:00:00Z",
    )
    eligible_rows = _explicit_rows(
        Decimal("0"),
        Decimal("1"),
        [
            (2350.00, 2352.00, 2349.00, 2351.00),
            (2351.00, 2357.00, 2350.50, 2356.00),
            (2356.00, 2363.00, 2355.00, 2362.00),
            (2362.00, 2364.00, 2361.00, 2363.00),
            (2363.00, 2365.00, 2362.00, 2364.50),
            (2364.50, 2366.00, 2364.00, 2365.50),
        ],
        start_iso="2026-03-03T00:00:00Z",
    )

    earned_low = Decimal("2349.00")
    earned_high = Decimal("2366.00")
    size = earned_high - earned_low
    ladder = []
    for family_id, level in (
        ("XAU_50", "50"),
        ("XAU_61_8", "61.8"),
        ("XAU_68", "68"),
        ("XAU_72", "72"),
        ("XAU_80", "80"),
        ("XAU_82", "82"),
        ("XAU_132", "132"),
        ("XAU_NEG_50", "-50"),
    ):
        offset = size * Decimal(level) / Decimal(100)
        ladder.append(
            {
                "family_id": family_id,
                "level": level,
                "expected_projected_price": str(earned_low + offset),
            }
        )

    return {
        "fixture_id": "BLOC_III_2.XAU_SPATIAL_BANDS.V1",
        "provenance": CANONICAL,
        "historical": True,
        "data_classification": (
            "CANONICAL_SOURCE_SLICE for the band table and the promotion "
            "examples (quoted from frozen corpus sources); the two quarter-"
            "zone price paths are SYNTHETIC_FIXTURE"
        ),
        "observation_cutoff": XAU_CUTOFF,
        "instrument_id": "XAUUSD",
        "timeframe": "M5",
        "clock": NY,
        "session_id": "XAU_GAME.ASIAN_RANGE",
        "model_id": "XAU.GAME.L1_L2_L3.V1",
        "model_version": "V1",
        "calibration_key": {
            "model_id": "XAU.GAME.L1_L2_L3.V1",
            "model_version": "V1",
            "calibration_id": "XAU_SPATIAL_BANDS",
            "calibration_version": "V1",
        },
        "calibration_status": "RESEARCH",
        "source_ref": "corpus/canonical/models/XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md",
        "source_quote": "25-50 normal 50-68 failure 68+ repair 100-110 snap.",
        "unit": "POINT",
        "bands": [
            {"band_id": "XAU_NORMAL", "state": "NORMAL", "lower": "25", "upper": "50"},
            {"band_id": "XAU_FAILURE", "state": "FAILURE", "lower": "50", "upper": "68"},
            {"band_id": "XAU_REPAIR", "state": "REPAIR", "lower": "68", "upper": None},
            {"band_id": "XAU_SNAP", "state": "SNAP", "lower": "100", "upper": "110"},
        ],
        "band_probes": [
            {"magnitude": "30", "expected_band_id": "XAU_NORMAL", "expected_state": "NORMAL"},
            {"magnitude": "50", "expected_band_id": "XAU_FAILURE", "expected_state": "FAILURE"},
            {"magnitude": "68", "expected_band_id": "XAU_REPAIR", "expected_state": "REPAIR"},
            {"magnitude": "105", "expected_band_id": "XAU_SNAP", "expected_state": "SNAP"},
        ],
        "promotion_examples": [
            {
                "example_id": "XAU_68_8H_TO_80",
                "from_state": "68",
                "age_condition_hours": "8",
                "to_coordinate": "80",
                "evidence_id": "EV.XAU.PROMOTION.68_80.V1",
                "source_ref": (
                    "corpus/canonical/evidence/XAU_PROMOTION_68_TO_80_EVIDENCE_V1.md"
                ),
                "sample_n": 48,
                "completed": 42,
                "observed_rate": "0.875",
                "standing": "VALIDATED_SMALL_N",
                "routing": "L2 path, not L1 entry",
                "disclosure": (
                    "42/48 is a conditional path-completion rate in the "
                    "source sample.  It is not a trade win rate, not an "
                    "entry probability and not an executable expectancy."
                ),
            },
            {
                "example_id": "XAU_120_8H_TO_132",
                "from_state": "120",
                "age_condition_hours": "8",
                "to_coordinate": "132",
                "evidence_id": "EV.XAU.PROMOTION.120_132.V1",
                "source_ref": (
                    "corpus/canonical/evidence/XAU_PROMOTION_120_TO_132_EVIDENCE_V1.md"
                ),
                "sample_n": 25,
                "completed": 24,
                "observed_rate": "0.96",
                "standing": "RESEARCH_FLAG_SMALL_N",
                "routing": "L2 path, not L1 entry",
                "governance": (
                    "N=25 remains a small-N research flag; the frozen model "
                    "explicitly does NOT promote 132 -> 168 automatically."
                ),
                "disclosure": (
                    "24/25 is a conditional path-completion rate in the "
                    "source sample.  It is not a trade win rate and does "
                    "not license a 132 -> 168 continuation."
                ),
            },
        ],
        "quarter_zone": {
            "zone_level": "2360.50",
            "zone_side": "ABOVE",
            "source_ref": (
                "corpus/canonical/setups/XAU_QUARTER_ZONE_OPERATOR_CARD_V1.md"
            ),
            "source_quote": "No blind touch entry.",
            "blind_touch_case": {
                "case_id": "XAU_QUARTER.BLIND_TOUCH",
                "provenance": SYNTHETIC,
                "rows": blind_touch_rows,
                "expected_touch_state": "TOUCHED",
                "expected_acceptance_state": "NOT_ACCEPTED",
                "expected_close_beyond_state": "NOT_BEYOND",
                "expected_rejection_state": "REJECTED",
                "expected_re_entry_state": "NOT_REENTERED",
                "expected_mae_native": "1",
                "expected_mfe_native": "12",
            },
            "eligible_case": {
                "case_id": "XAU_QUARTER.ELIGIBLE",
                "provenance": SYNTHETIC,
                "rows": eligible_rows,
                "expected_touch_state": "TOUCHED",
                "expected_acceptance_state": "ACCEPTED",
                "expected_close_beyond_state": "BEYOND",
                "expected_rejection_state": "NOT_REJECTED",
                "expected_re_entry_state": "NOT_REENTERED",
                "expected_mae_native": "1",
                "expected_mfe_native": "16",
                "expected_first_delivery_bar_index": 2,
            },
            "earned_range": {
                "case_id": "XAU_QUARTER.ELIGIBLE",
                "low": "2349.00",
                "high": "2366.00",
                "size_native": "17",
            },
        },
        "coordinate_ladder": ladder,
        "coordinate_source_ref": (
            "corpus/canonical/models/XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md"
        ),
        "coordinate_source_quote": (
            "Quarter zones; -50 decision node;132 rekey;80 invalidation "
            "family;50-72 Asian-range entry family."
        ),
        "not_declared_families": [
            {
                "family_id": "XAU_168",
                "expected_refusal": "COORDINATE_FAMILY_NOT_EARNED",
                "reason": (
                    "The XAU card names 132 rekey and 168/185 belong to the "
                    "deeper Fib rekey sequence; the 132 state does not "
                    "promote to 168 automatically."
                ),
            }
        ],
    }


# ---------------------------------------------------------------------------
# BTC tier seeds and slot x tier range-left
# ---------------------------------------------------------------------------


def _btc_tier_seeds() -> dict:
    dollar = Decimal("1.00")
    base = Decimal("68000.00")
    specs = [
        ("BTC_SEED_T1", "T1", False, 100, 0, 600, 80, 6),
        ("BTC_SEED_T2", "T2", False, 200, 0, 1200, 160, 6),
        ("BTC_SEED_T3", "T3", False, 300, 0, 2400, 300, 6),
        ("BTC_SEED_NO_GO", "NO_GO", True, 400, 0, 3500, 450, 6),
    ]
    seeds = []
    for case_id, tier_id, no_go, first_open_u, low_u, high_u, step_u, n in specs:
        rows = _ramp_rows(
            base,
            dollar,
            first_open_u=first_open_u,
            low_u=low_u,
            high_u=high_u,
            step_u=step_u,
            n=n,
            start_iso="2026-03-03T00:00:00Z",
        )
        expected = _expected_range(
            base,
            dollar,
            first_open_u=first_open_u,
            low_u=low_u,
            high_u=high_u,
            step_u=step_u,
            n=n,
        )
        expected["expected_tier_id"] = tier_id
        expected["expected_no_go"] = no_go
        seeds.append(
            {
                "case_id": case_id,
                "tier_id": tier_id,
                "expected_no_go": no_go,
                "rows": rows,
                "expected": expected,
            }
        )
    return {
        "fixture_id": "BLOC_III_2.BTC_TIER_SEEDS.V1",
        "provenance": SYNTHETIC,
        "historical": True,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "observation_cutoff": BTC_CUTOFF,
        "instrument_id": "BTCUSD",
        "timeframe": "M5",
        "clock": NY,
        "session_id": "BTC_TRACKER.ASIAN_WINDOW",
        "model_id": "BTC.TRACKER.DWM.V1",
        "model_version": "V1",
        "calibration_key": {
            "model_id": "BTC.TRACKER.DWM.V1",
            "model_version": "V1",
            "calibration_id": "BTC_TRACKER_DWM_TIERS",
            "calibration_version": "V1",
        },
        "calibration_evidence_id": "BTC.TRACKER.DWM.V1",
        "calibration_source_ref": (
            "corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md"
        ),
        "calibration_quote": (
            "T1 < $750 T2 $750-$1,700 T3 $1,700-$3,000 > $3,000 NO-GO. "
            "AU205/545/1160. Triggers246/654/1392. Density zones164-246 "
            "/436-654 /928-1392."
        ),
        "au_values": [
            {"tier_id": "T1", "au": "205"},
            {"tier_id": "T2", "au": "545"},
            {"tier_id": "T3", "au": "1160"},
        ],
        "threshold_levels": ["246", "654", "1392"],
        "density_zones": [
            {"zone_id": "T1", "lower": "164", "upper": "246"},
            {"zone_id": "T2", "lower": "436", "upper": "654"},
            {"zone_id": "T3", "lower": "928", "upper": "1392"},
        ],
        "seeds": seeds,
        "slot_surface": {
            "source_ref": (
                "corpus/canonical/models/"
                "BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md"
            ),
            "source_quote": (
                "Modern research extends slot x tier / range-left context "
                "from03:00 through19:00 NY."
            ),
            "clock": NY,
            "slot_local_start": "03:00:00",
            "slot_local_end": "19:00:00",
            "expected_range_left_native": {"T1": "200", "T2": "400", "T3": "900"},
        },
        "separation_note": (
            "The BTC Daily Tracker and the BTC Game are distinct branches.  "
            "Tracker-side measurement output carries no Game or setup object."
        ),
    }


# ---------------------------------------------------------------------------
# JPY 12-4PM DT structures
# ---------------------------------------------------------------------------


def _jpy_dt_structures() -> dict:
    return {
        "fixture_id": "BLOC_III_2.JPY_DT_STRUCTURES.V1",
        "provenance": CANONICAL,
        "historical": True,
        "data_classification": (
            "CANONICAL_SOURCE_SLICE - DT structure levels, the research "
            "window and the asset role map quoted from the frozen JPY model "
            "card; no JPY price history exists in this repository"
        ),
        "model_id": "JPY.CARRY_GAME.L1_L3.V1",
        "model_version": "DT_12_4PM",
        "source_ref": "corpus/canonical/models/JPY_CARRY_GAME_MODEL_CARD_V1.md",
        "source_quote": (
            "JPY12-4PM DT research includes132/168/187.5 structures,"
            "no-132-touch continuation and132-touch+OCC recovery."
        ),
        "clock": NY,
        "research_window_local": {"start": "12:00:00", "end": "16:00:00"},
        "declared_families": [
            {"family_id": "JPY_132", "level": "132", "declared_extension": False},
            {"family_id": "JPY_168", "level": "168", "declared_extension": False},
            {"family_id": "JPY_187_5", "level": "187.5", "declared_extension": True},
        ],
        "asset_roles": [
            {"instrument_id": "USDJPY", "role": "CARRY_MASTER"},
            {"instrument_id": "AUDJPY", "role": "RISK_EXPRESSION"},
            {"instrument_id": "EURJPY", "role": "CONFIRMATION_VETO"},
        ],
        "role_quote": (
            "USDJPY = carry master / primary structural driver. AUDJPY = "
            "risk/execution expression. EURJPY = confirmation/veto. EURJPY "
            "is not an equal third vote unless a later validated model "
            "explicitly changes the role map."
        ),
        "native_tier_tables": "NOT_CANONICAL",
        "native_tier_note": (
            "The JPY card publishes no complete per-pair tier/AU table.  A "
            "JPY tier lookup therefore refuses with "
            "MODEL_VERSION_UNAVAILABLE; no table is invented here."
        ),
        "deferred_cases": [
            {
                "case_id": "JPY_BASKET.AGREE_AND_CONFIRM",
                "reason": (
                    "Basket-role aggregation is a model-runtime concern "
                    "(III.3); the measurement layer measures single-asset "
                    "facts only."
                ),
            },
            {
                "case_id": "JPY_BASKET.CONFIRM_ABSENT",
                "reason": (
                    "Basket-role aggregation is a model-runtime concern "
                    "(III.3); the measurement layer measures single-asset "
                    "facts only."
                ),
            },
            {
                "case_id": "JPY_BASKET.NO_EQUAL_VOTE",
                "reason": (
                    "The no-equal-vote rule is a role-map property of the "
                    "model runtime; the measurement layer carries the role "
                    "map as a declaration and no aggregation."
                ),
            },
        ],
    }


# ---------------------------------------------------------------------------
# Fib anchor cases
# ---------------------------------------------------------------------------


def _fib_anchor_cases() -> dict:
    return {
        "fixture_id": "BLOC_III_2.FIB_ANCHOR_CASES.V1",
        "provenance": SYNTHETIC,
        "historical": True,
        "data_classification": SYNTHETIC_CLASSIFICATION,
        "instrument_id": "EURUSD",
        "clock": NY,
        "session_id": "EUR_DAILY.ASIAN_RANGE",
        "model_id": "CROSSASSET.FIB.RANGE_BIRTH.V1",
        "model_version": "R15",
        "source_ref": "corpus/canonical/models/FIB_RANGE_BIRTH_MODEL_CARD_V1.md",
        "source_quote": (
            "Current canonical Range Birth eligibility must be materialized "
            "from R15 before autonomous signal generation."
        ),
        "earned_range_case_id": "EUR_SEED_T2",
        "earned_range_low": "1.07900",
        "earned_range_high": "1.08150",
        "rule": {
            "rule_id": "R15.RANGE_BIRTH",
            "rule_version": "DECLARED",
            "materialization": "DECLARED",
            "source_ref": (
                "corpus/canonical/models/FIB_RANGE_BIRTH_MODEL_CARD_V1.md"
            ),
        },
        "cases": [
            {
                "case_id": "FIB.VALID_BORN_RANGE",
                "anchor_id": "FIB.ANCHOR.ACTIVE.01",
                "status": "ACTIVE",
                "expected_refusal_code": "NONE",
                "expected_automation_ready": False,
                "expected_projection_allowed": True,
            },
            {
                "case_id": "FIB.UNRESOLVED_ANCHOR",
                "anchor_id": "FIB.ANCHOR.UNRESOLVED.01",
                "status": "UNRESOLVED",
                "expected_refusal_code": "ANCHOR_UNRESOLVED",
                "expected_automation_ready": False,
                "expected_projection_allowed": False,
            },
            {
                "case_id": "FIB.INVALIDATED_ANCHOR",
                "anchor_id": "FIB.ANCHOR.INVALIDATED.01",
                "status": "INVALIDATED",
                "invalidation_reason": "synthetic invalidation for the golden case",
                "expected_refusal_code": "ANCHOR_INVALIDATED",
                "expected_automation_ready": False,
                "expected_projection_allowed": False,
            },
            {
                "case_id": "FIB.REKEY_TRANSITION",
                "anchor_id": "FIB.ANCHOR.ACTIVE.01",
                "status": "ACTIVE",
                "successor_anchor_id": "FIB.ANCHOR.REKEYED.02",
                "mapping": {"FIB_132": "EUR_DAILY_132"},
                "expected_refusal_code": "NONE",
                "expected_automation_ready": False,
                "expected_projection_allowed": True,
            },
        ],
        "coordinate_ladder": [
            {
                "family_id": family_id,
                "level": level,
                "expected_projected_price": str(
                    Decimal("1.07900")
                    + (Decimal("1.08150") - Decimal("1.07900"))
                    * Decimal(level)
                    / Decimal(100)
                ),
            }
            for family_id, level in (
                ("FIB_50", "50"),
                ("FIB_61_8", "61.8"),
                ("FIB_68", "68"),
                ("FIB_72", "72"),
                ("FIB_80", "80"),
                ("FIB_82", "82"),
                ("FIB_132", "132"),
                ("FIB_168", "168"),
                ("FIB_185", "185"),
                ("FIB_NEG_25", "-25"),
                ("FIB_NEG_50", "-50"),
            )
        ],
        "rejected_cases": [
            {
                "case_id": "FIB.ARBITRARY_LOCAL_PIVOT",
                "expected_refusal": "ANCHOR_NOT_EARNED",
                "reason": (
                    "The R11 generic local-pivot generator is absent from the "
                    "package by construction: no API turns bars or pivots "
                    "into an anchor, so an arbitrary pivot can never reach a "
                    "coordinate projection."
                ),
            }
        ],
        "deferred_cases": [
            {
                "case_id": "FIB.R15.AUTOMATION_APPROVAL",
                "reason": (
                    "The canonical R15 Range Birth eligibility rule is not "
                    "materialized in the corpus (III.2-GAP-1).  Automation "
                    "approval is a III.5 governed concern."
                ),
            }
        ],
    }


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------


def _manifest(files: dict[str, str]) -> dict:
    return {
        "algorithm": "sha256",
        "generator": "generate_fixtures.py",
        "description": (
            "Deterministic committed golden fixtures for Bloc III.2. "
            "Hashes cover every JSON fixture in this directory except this "
            "manifest.  Hashes are recorded over the LF-normalized content, "
            "so the manifest verifies identically on Windows (CRLF "
            "worktrees) and Linux CI (LF checkouts)."
        ),
        "provenance": {
            "bar_slices": SYNTHETIC,
            "event_records": SYNTHETIC,
            "calibration_and_doctrine_slices": CANONICAL,
        },
        "files": files,
    }


def main() -> None:
    _write("eur_daily_tier_seeds.json", _eur_tier_seeds())
    _write("eur_rekey_ladder.json", _eur_rekey_ladder())
    _write("eur_event_budget.json", _eur_event_budget())
    _write("eur_weekly_outer_nodes.json", _eur_weekly_outer_nodes())
    _write("eur_higher_order.json", _eur_higher_order())
    _write("xau_spatial_bands.json", _xau_spatial_bands())
    _write("btc_tier_seeds.json", _btc_tier_seeds())
    _write("jpy_dt_structures.json", _jpy_dt_structures())
    _write("fib_anchor_cases.json", _fib_anchor_cases())

    hashes: dict[str, str] = {}
    for path in sorted(HERE.glob("*.json")):
        if path.name == "FIXTURE_MANIFEST.json":
            continue
        content = path.read_bytes().replace(b"\r\n", b"\n")
        hashes[path.name] = hashlib.sha256(content).hexdigest()
    _write("FIXTURE_MANIFEST.json", _manifest(hashes))
    print("wrote fixtures:", ", ".join(sorted(hashes)))


if __name__ == "__main__":
    main()
