"""Deterministic fixture generator for Bloc III.1.

Run from this directory:  ``python generate_fixtures.py``

Every emitted file is a function of the fixed literals below — no wall
clock, no randomness, no network — so regeneration is byte-identical and
the recorded hashes in ``FIXTURE_MANIFEST.json`` verify.

Provenance honesty (PLAN §10 G1 / ACCEPTANCE I1, N3, N4):

* Bar values are ``SYNTHETIC_FIXTURE`` — deterministic generated
  numbers, *not* empirical market evidence and never citable for
  performance claims.
* ``sessions_canonical.json`` is a ``CANONICAL_SOURCE_SLICE``: session
  bounds, checkpoint times and research-day lineage rules are quoted
  from frozen corpus sources (each record carries its ``source_ref``).
* Raw provider feeds are scripted offline encodings of the same
  synthetic rows in two provider-specific conventions; no real provider,
  credential or network input exists anywhere in this directory.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

NY = "America/New_York"

EUR_CUTOFF = "2026-03-03T08:03:00Z"
BTC_CUTOFF = "2026-03-03T17:00:30Z"

# ---------------------------------------------------------------------------
# Synthetic row source-of-truth (fixed literals; deterministic by construction)
# ---------------------------------------------------------------------------

def _stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_eur_rows():
    """Contiguous M5 session slice with one deliberate hole.

    Every M5 open from 23:55 (context bar before the 19:00 NY boundary)
    through 07:55 (the canonical 02:55 final bar) is present except the
    00:15 slot, which is deliberately absent so the GAP state is real
    and visible.  Fixed-value rows mark the duplicate pair (00:20), the
    revision pair (00:30) and the in-progress NONFINAL bar (08:00).
    """
    from decimal import Decimal as _Decimal

    start = datetime(2026, 3, 2, 23, 55, tzinfo=timezone.utc)
    hole = datetime(2026, 3, 3, 0, 15, tzinfo=timezone.utc)
    duplicate_open = datetime(2026, 3, 3, 0, 20, tzinfo=timezone.utc)
    revision_open = datetime(2026, 3, 3, 0, 30, tzinfo=timezone.utc)
    specials = {
        duplicate_open: [
            ("2026-03-03T00:20:00Z", "2026-03-03T00:25:00Z", "1.08050", "1.08070", "1.08045", "1.08065", "642.0", "2026-03-03T00:20:03Z"),
            # duplicate feed row: identical OHLC/volume, later source ts
            ("2026-03-03T00:20:00Z", "2026-03-03T00:25:00Z", "1.08050", "1.08070", "1.08045", "1.08065", "642.0", "2026-03-03T00:20:05Z"),
        ],
        revision_open: [
            # original then explicit revision (different prices, later ts)
            ("2026-03-03T00:30:00Z", "2026-03-03T00:35:00Z", "1.08065", "1.08090", "1.08060", "1.08085", "590.0", "2026-03-03T00:30:03Z"),
            ("2026-03-03T00:30:00Z", "2026-03-03T00:35:00Z", "1.08065", "1.08095", "1.08060", "1.08088", "604.0", "2026-03-03T00:35:12Z"),
        ],
    }
    rows = []
    for k in range(97):  # opens 23:55 .. 07:55 (session end 08:00 exclusive)
        open_dt = start + timedelta(minutes=5 * k)
        if open_dt == hole:
            continue  # deliberate GAP: never synthesized
        if open_dt in specials:
            rows.extend(specials[open_dt])
            continue
        close_dt = open_dt + timedelta(minutes=5)
        base = _Decimal("1.07980") + _Decimal(k) * _Decimal("0.00002")
        rows.append(
            (
                _stamp(open_dt),
                _stamp(close_dt),
                f"{base:.5f}",
                f"{base + _Decimal('0.00020'):.5f}",
                f"{base - _Decimal('0.00005'):.5f}",
                f"{base + _Decimal('0.00015'):.5f}",
                str(500 + k * 7),
                _stamp(close_dt + timedelta(seconds=3)),
            )
        )
    # in-progress bar beyond the observation cutoff -> NONFINAL
    rows.append(
        (
            "2026-03-03T08:00:00Z",
            "2026-03-03T08:05:00Z",
            "1.08140",
            "1.08160",
            "1.08135",
            "1.08150",
            "388.0",
            "2026-03-03T08:02:58Z",
        )
    )
    return rows


EUR_ROWS = _build_eur_rows()

BTC_ROWS = [
    # evening bar -> following research day
    ("2026-03-03T00:00:00Z", "2026-03-03T00:05:00Z", "68410.00", "68455.00", "68402.00", "68441.00", "18.4", "2026-03-03T00:00:03Z"),
    # mid-day bar inside no registered session
    ("2026-03-03T16:50:00Z", "2026-03-03T16:55:00Z", "68500.00", "68520.00", "68490.00", "68512.00", "9.7", "2026-03-03T16:50:03Z"),
    # closes exactly at the 12:00 NY checkpoint
    ("2026-03-03T16:55:00Z", "2026-03-03T17:00:00Z", "68512.00", "68531.00", "68505.00", "68524.00", "11.2", "2026-03-03T17:00:03Z"),
    # in-progress beyond cutoff -> NONFINAL
    ("2026-03-03T17:00:00Z", "2026-03-03T17:05:00Z", "68524.00", "68540.00", "68518.00", "68533.00", "8.8", "2026-03-03T17:00:20Z"),
]

ROW_KEYS = ("open_time", "close_time", "o", "h", "l", "c", "volume", "source_timestamp")


def _epoch(iso_stamp: str) -> int:
    return int(datetime.fromisoformat(iso_stamp.replace("Z", "+00:00")).timestamp())


def _iso_offset(iso_stamp: str) -> str:
    parsed = datetime.fromisoformat(iso_stamp.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "+00:00")


def _rows_as_dicts(rows):
    return [dict(zip(ROW_KEYS, row)) for row in rows]


def _alpha_record(row: dict, symbol: str) -> dict:
    return {
        "pair": symbol,
        "tf": "M5",
        "epoch_open": _epoch(row["open_time"]),
        "epoch_close": _epoch(row["close_time"]),
        "o": row["o"],
        "h": row["h"],
        "l": row["l"],
        "c": row["c"],
        "vol": row["volume"],
        "feed_ts": _epoch(row["source_timestamp"]),
        "zone": NY,
    }


def _beta_record(row: dict, symbol: str) -> dict:
    return {
        "sym": symbol,
        "int": "M5",
        "t0": _iso_offset(row["open_time"]),
        "t1": _iso_offset(row["close_time"]),
        "px_o": row["o"],
        "px_h": row["h"],
        "px_l": row["l"],
        "px_c": row["c"],
        "qty": row["volume"],
        "src_t": _iso_offset(row["source_timestamp"]),
        "tz": NY,
    }


def _write(name: str, payload: dict) -> None:
    path = HERE / name
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _eur_slice() -> dict:
    return {
        "fixture_id": "BLOC_III_1.EURUSD_M5_ASIAN_SLICE.V1",
        "provenance": "SYNTHETIC_FIXTURE",
        "historical": False,
        "data_classification": (
            "SYNTHETIC_FIXTURE - deterministic generated values; not empirical "
            "market evidence and never citable for performance claims"
        ),
        "observation_cutoff": EUR_CUTOFF,
        "instrument_id": "EURUSD",
        "timeframe": "M5",
        "clock": NY,
        "session_context": {
            "session_id": "EUR_DAILY.ASIAN_RANGE",
            "day": "2026-03-02",
            "session_start_utc": "2026-03-03T00:00:00Z",
            "session_end_utc": "2026-03-03T08:00:00Z",
        },
        "expected_open_gap": "2026-03-03T00:15:00Z",
        "rows": _rows_as_dicts(EUR_ROWS),
    }


def _btc_slice() -> dict:
    return {
        "fixture_id": "BLOC_III_1.BTCUSD_M5_CHECKPOINT_SLICE.V1",
        "provenance": "SYNTHETIC_FIXTURE",
        "historical": False,
        "data_classification": (
            "SYNTHETIC_FIXTURE - deterministic generated values; not empirical "
            "market evidence and never citable for performance claims"
        ),
        "observation_cutoff": BTC_CUTOFF,
        "instrument_id": "BTCUSD",
        "timeframe": "M5",
        "clock": NY,
        "rows": _rows_as_dicts(BTC_ROWS),
    }


def _sessions_slice() -> dict:
    return {
        "fixture_id": "BLOC_III_1.SESSIONS_CANONICAL.V1",
        "provenance": "CANONICAL_SOURCE_SLICE",
        "historical": True,
        "description": (
            "Session definitions, documented family gaps and research-day "
            "lineage rules quoted from frozen canonical corpus sources. "
            "No timing definition exists here that a canonical source does "
            "not establish."
        ),
        "cited_evidence_ids": ["EV.EUR.DAILY.PHASE1_TIERS.V1"],
        "definitions": [
            {
                "session_id": "EUR_DAILY.ASIAN_RANGE",
                "family": "ASIAN_RANGE",
                "model_id": "EUR.DAILY.NEWS_REKEY.V1",
                "model_version": "PHASE1",
                "kind": "WINDOW",
                "start_local": "19:00:00",
                "end_local": "03:00:00",
                "end_inclusive": False,
                "instant_local": None,
                "clock": NY,
                "source_ref": (
                    "corpus/canonical/evidence/EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md "
                    "(Session 19:00-03:00 NY/research-day ownership and final-bar "
                    "convention are part of this claim); "
                    "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md; "
                    "final-bar convention: implementation/forge/book_iii/"
                    "bloc_iii_1/PLAN.md Ch III.1.6"
                ),
            },
            {
                "session_id": "BTC_TRACKER.ASIAN_WINDOW",
                "family": "ASIAN_RANGE",
                "model_id": "BTC.TRACKER.DWM.V1",
                "model_version": "V1",
                "kind": "WINDOW",
                "start_local": "19:00:00",
                "end_local": "03:00:00",
                "end_inclusive": False,
                "instant_local": None,
                "clock": NY,
                "source_ref": (
                    "corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md "
                    "(Asian window 19:00-03:00 NY research frame)"
                ),
            },
            {
                "session_id": "BTC_TRACKER.DAILY_CHECKPOINT_12PM",
                "family": "DAILY_CHECKPOINT",
                "model_id": "BTC.TRACKER.DWM.V1",
                "model_version": "V1",
                "kind": "CHECKPOINT",
                "start_local": None,
                "end_local": None,
                "end_inclusive": False,
                "instant_local": "12:00:00",
                "clock": NY,
                "source_ref": (
                    "corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md "
                    "(daily checkpoint 12PM NY)"
                ),
            },
        ],
        "documented_gaps": {
            "LONDON_MLR": (
                "no canonical London/MLR session bounds exist in the frozen "
                "corpus; disclosed as GAP-2, never invented"
            ),
            "WEEKLY_SEED": (
                "weekly seed windows are defined at day granularity only "
                "(Monday anchor); no canonical intraday window exists to "
                "register - GAP-2"
            ),
            "DT_WINDOW": (
                "a JPY DT research window (12-4PM) is named in "
                "JPY_CARRY_GAME_MODEL_CARD_V1.md but that card forbids "
                "automatic DT->Carry binding without a crosswalk ruling; "
                "binding unresolved - GAP-2 / stop condition 3"
            ),
            "MONTH_BOUNDARY": (
                "EUR.HIGHER_ORDER month hierarchy is canonical but no "
                "boundary clock/frame is stated in the corpus - GAP-2"
            ),
            "QUARTER_BOUNDARY": (
                "quarter hierarchy is canonical but the boundary clock/frame "
                "is unspecified in the corpus - GAP-2"
            ),
        },
        "research_day_lineages": [
            {
                "lineage_id": "EUR_DAILY_LINEAGE",
                "model_id": "EUR.DAILY.NEWS_REKEY.V1",
                "model_version": "PHASE1",
                "clock": NY,
                "evening_shift_boundary": "19:00:00",
                "source_ref": (
                    "corpus/canonical/evidence/EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md "
                    "(Session 19:00-03:00 NY/research-day ownership ... part of "
                    "this claim)"
                ),
            },
            {
                "lineage_id": "BTC_TRACKER_LINEAGE",
                "model_id": "BTC.TRACKER.DWM.V1",
                "model_version": "V1",
                "clock": NY,
                "evening_shift_boundary": "19:00:00",
                "source_ref": (
                    "corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md "
                    "(Asian window 19:00-03:00 NY; weekend/weekly transition "
                    "definitions require exact research-day ownership)"
                ),
            },
        ],
        "model_bindings": [
            {
                "instrument_id": "EURUSD",
                "model_id": "EUR.DAILY.NEWS_REKEY.V1",
                "model_version": "PHASE1",
                "lineage_id": "EUR_DAILY_LINEAGE",
            },
            {
                "instrument_id": "BTCUSD",
                "model_id": "BTC.TRACKER.DWM.V1",
                "model_version": "V1",
                "lineage_id": "BTC_TRACKER_LINEAGE",
            },
        ],
    }


def _manifest(files: dict[str, str]) -> dict:
    return {
        "algorithm": "sha256",
        "generator": "generate_fixtures.py",
        "description": (
            "Deterministic committed fixtures for Bloc III.1. Hashes cover "
            "every JSON fixture in this directory except this manifest."
        ),
        "provenance": {
            "bar_slices": "SYNTHETIC_FIXTURE",
            "sessions_slice": "CANONICAL_SOURCE_SLICE",
            "raw_feeds": "SYNTHETIC_FIXTURE (scripted provider encodings)",
        },
        "files": files,
    }


def main() -> None:
    _write("eurusd_m5_slice.json", _eur_slice())
    _write("btcusd_m5_slice.json", _btc_slice())
    _write("sessions_canonical.json", _sessions_slice())
    _write(
        "raw_feed_fake_alpha.json",
        {
            "fixture_id": "BLOC_III_1.RAW_FEED.FAKE_ALPHA.V1",
            "provenance": "SYNTHETIC_FIXTURE",
            "historical": False,
            "provider": "fake_alpha",
            "observation_cutoff": EUR_CUTOFF,
            "data_classification": "SYNTHETIC_FIXTURE scripted offline encoding",
            "records": [_alpha_record(row, "EUR/USD") for row in _rows_as_dicts(EUR_ROWS)],
        },
    )
    # provider beta: same slice, different conventions AND different arrival
    # order (rotation) so parity must come from normalization, not ordering.
    eur_rows = _rows_as_dicts(EUR_ROWS)
    rotated = eur_rows[3:] + eur_rows[:3]
    _write(
        "raw_feed_fake_beta.json",
        {
            "fixture_id": "BLOC_III_1.RAW_FEED.FAKE_BETA.V1",
            "provenance": "SYNTHETIC_FIXTURE",
            "historical": False,
            "provider": "fake_beta",
            "observation_cutoff": EUR_CUTOFF,
            "data_classification": "SYNTHETIC_FIXTURE scripted offline encoding",
            "records": [_beta_record(row, "EUR-USD") for row in rotated],
        },
    )
    _write(
        "raw_feed_btcusd_fake_alpha.json",
        {
            "fixture_id": "BLOC_III_1.RAW_FEED.FAKE_ALPHA_BTC.V1",
            "provenance": "SYNTHETIC_FIXTURE",
            "historical": False,
            "provider": "fake_alpha",
            "observation_cutoff": BTC_CUTOFF,
            "data_classification": "SYNTHETIC_FIXTURE scripted offline encoding",
            "records": [
                _alpha_record(row, "BTC/USD") for row in _rows_as_dicts(BTC_ROWS)
            ],
        },
    )

    hashes: dict[str, str] = {}
    for path in sorted(HERE.glob("*.json")):
        if path.name == "FIXTURE_MANIFEST.json":
            continue
        # EOL-independent hash: the record is always the LF-normalized
        # content, so the manifest verifies identically on Windows (CRLF
        # worktrees) and Linux CI (LF checkouts).
        content = path.read_bytes().replace(b"\r\n", b"\n")
        hashes[path.name] = hashlib.sha256(content).hexdigest()
    _write("FIXTURE_MANIFEST.json", _manifest(hashes))
    print("wrote fixtures:", ", ".join(sorted(hashes)))


if __name__ == "__main__":
    main()
