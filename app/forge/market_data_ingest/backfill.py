"""Deterministic offline backfill (WP-3B).

Pagination is caller-driven and bounded: one page per ``fetch``, no hidden
retries, no sleeping, no network.  The run merges pages by canonical key,
prefers the later ``source_timestamp`` and refuses to loop when a provider
cannot advance its cursor.

Idempotence is a property of the merge, not of the provider: re-ingesting the
same observations yields the same ordered candles and the same window digest.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Sequence

from app.forge.market_data.bars import TIMEFRAME_MINUTES
from app.forge.market_data.errors import ConventionViolationError

from .capture import source_window_digest
from .contract import CandleRequest, MarketDataProvider, RawCandle, as_utc


class BackfillStalledError(ConventionViolationError):
    """The provider returned no progress for an unexhausted window."""

    code = "BACKFILL_STALLED"


class BackfillBudgetError(ConventionViolationError):
    """The page budget was exhausted before the window completed."""

    code = "BACKFILL_BUDGET_EXHAUSTED"


@dataclass(frozen=True)
class BackfillCursor:
    """Resume point: the next unread open time."""

    next_start: datetime
    pages_completed: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "next_start", as_utc(self.next_start, "next_start"))
        if self.pages_completed < 0:
            raise ConventionViolationError("pages_completed must be >= 0")


@dataclass(frozen=True)
class BackfillRun:
    """Terminal result of one bounded backfill."""

    candles: tuple[RawCandle, ...]
    pages: int
    complete: bool
    cursor: BackfillCursor
    digest: str
    overlapping: int = 0

    @property
    def count(self) -> int:
        return len(self.candles)


def _merge(existing: dict[tuple, RawCandle], candle: RawCandle) -> bool:
    """Insert by key; later source timestamp wins. Returns True if inserted."""
    previous = existing.get(candle.key)
    if previous is None:
        existing[candle.key] = candle
        return True
    if candle.source_timestamp > previous.source_timestamp:
        existing[candle.key] = candle
        return True
    if candle.source_timestamp == previous.source_timestamp:
        # Deterministic tie-break: keep the lexicographically later digest.
        existing[candle.key] = max(previous, candle, key=lambda item: item.digest())
    return False


def run_backfill(
    provider: MarketDataProvider,
    request: CandleRequest,
    *,
    cursor: BackfillCursor | None = None,
    max_pages: int = 100,
) -> BackfillRun:
    """Fetch a window page by page with overlap-safe merging."""
    if max_pages < 1:
        raise ConventionViolationError("max_pages must be >= 1")
    step = timedelta(minutes=TIMEFRAME_MINUTES[request.timeframe])
    start = cursor.next_start if cursor is not None else request.start
    merged: dict[tuple, RawCandle] = {}
    pages = 0
    overlapping = 0
    complete = False
    while pages < max_pages:
        page_request = CandleRequest(
            instrument_id=request.instrument_id,
            timeframe=request.timeframe,
            start=start,
            end=request.end,
            limit=request.limit,
        )
        page = provider.fetch(page_request)
        pages += 1
        for candle in page.candles:
            if not _merge(merged, candle):
                overlapping += 1
        if page.candles:
            last_open = max(candle.open_time for candle in page.candles)
            next_start = last_open + step
        else:
            next_start = None
        if page.exhausted:
            complete = True
            start = next_start or start
            break
        if next_start is None or next_start <= start:
            raise BackfillStalledError(
                f"{provider.provider_id} did not advance the backfill window"
            )
        if next_start >= request.end:
            complete = True
            start = next_start
            break
        start = next_start
    if not complete:
        raise BackfillBudgetError("page budget exhausted before window completion")
    candles = tuple(sorted(merged.values(), key=lambda item: item.open_time.timestamp()))
    step_cursor = start
    return BackfillRun(
        candles=candles,
        pages=pages,
        complete=complete,
        cursor=BackfillCursor(next_start=step_cursor, pages_completed=pages),
        digest=source_window_digest(candles),
        overlapping=overlapping,
    )


def merge_runs(*runs: BackfillRun) -> tuple[RawCandle, ...]:
    """Idempotent merge of repeated runs over the same source events."""
    merged: dict[tuple, RawCandle] = {}
    for run in runs:
        for candle in run.candles:
            _merge(merged, candle)
    return tuple(sorted(merged.values(), key=lambda item: item.open_time.timestamp()))


def replay_identity(runs: Sequence[BackfillRun]) -> str:
    """Stable identity for a set of equivalent backfill runs."""
    if not runs:
        raise ConventionViolationError("at least one run is required")
    if len({run.digest for run in runs}) != 1:
        raise ConventionViolationError("runs are not equivalent")
    return runs[0].digest


__all__ = [
    "BackfillBudgetError",
    "BackfillCursor",
    "BackfillRun",
    "BackfillStalledError",
    "merge_runs",
    "replay_identity",
    "run_backfill",
]
