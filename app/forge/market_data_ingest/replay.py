"""Offline replay/stream parity over canonicalized provider observations.

The frozen III.1 runners (``replay_historical`` / ``stream_live``) resolve
providers through the frozen ``PROVIDER_SCHEMAS`` table, so they cannot accept a
real provider id without the blocked amendment.  This module assembles the same
``PipelineResult`` shape using the public kernel functions — ``canonicalize``,
``bar_ownership``, ``QualityPolicy.evaluate`` and ``compare_parity`` — so the
*comparison* logic remains III.1's, not a second implementation.

No claim of external parity is made here: both sides consume the same offline
observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from app.forge.market_data.bars import content_digest
from app.forge.market_data.clocks import CLOCK_REGISTRY_VERSION
from app.forge.market_data.instruments import InstrumentRegistry
from app.forge.market_data.parity import (
    ModelBinding,
    OwnershipResult,
    ParityReport,
    PipelinePath,
    PipelineResult,
    bar_ownership,
    compare_parity,
)
from app.forge.market_data.quality import DataOutcome, QualityFlag, QualityPolicy
from app.forge.market_data.research_day import ResearchDayRegistry
from app.forge.market_data.sessions import SessionRegistry
from app.forge.market_data.versions import MARKET_DATA_SCHEMA_VERSION

from .canonical import CanonicalOutcome, canonicalize
from .contract import RawCandle


@dataclass(frozen=True)
class OfflineRun:
    """Canonical facts produced by one offline ingestion path."""

    path: PipelinePath
    outcome: CanonicalOutcome
    ownership: tuple[tuple[str, OwnershipResult], ...]

    @property
    def bars(self):
        return self.outcome.bars

    @property
    def quality_flags(self) -> frozenset[QualityFlag]:
        return self.outcome.quality_flags

    @property
    def feed_outcome(self) -> DataOutcome:
        return self.outcome.outcome

    @property
    def missing(self) -> tuple[datetime, ...]:
        return self.outcome.missing

    @property
    def refused_count(self) -> int:
        return self.outcome.refusal_count

    @property
    def content_digest(self) -> str:
        return content_digest(self.bars)

    def ownership_map(self) -> dict[str, OwnershipResult]:
        return dict(self.ownership)

    def as_pipeline_result(self, path: PipelinePath | None = None) -> PipelineResult:
        return PipelineResult(
            path=path or self.path,
            bars=self.bars,
            ownership=self.ownership,
            quality_flags=self.quality_flags,
            feed_outcome=self.feed_outcome,
            refused_count=self.refused_count,
            missing=self.missing,
            market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
            session_registry_version="OFFLINE",
            clock_registry_version=CLOCK_REGISTRY_VERSION,
        )


def _ownership(
    outcome: CanonicalOutcome,
    bindings: Sequence[ModelBinding],
    sessions: SessionRegistry,
    lineages: ResearchDayRegistry,
) -> tuple[tuple[str, OwnershipResult], ...]:
    entries = []
    for bar in outcome.bars:
        key = f"{bar.instrument_id}/{bar.timeframe}/{bar.open_time.isoformat()}"
        entries.append(
            (key, bar_ownership(bar, bindings, sessions, lineages))
        )
    entries.sort(key=lambda item: item[0])
    return tuple(entries)


def run_offline(
    candles: Sequence[RawCandle],
    registry: InstrumentRegistry,
    policy: QualityPolicy,
    *,
    observation_cutoff: datetime,
    path: PipelinePath = PipelinePath.REPLAY,
    bindings: Sequence[ModelBinding] = (),
    sessions: SessionRegistry | None = None,
    lineages: ResearchDayRegistry | None = None,
    expected_opens: Sequence[datetime] | None = None,
) -> OfflineRun:
    outcome = canonicalize(
        candles,
        registry,
        policy,
        observation_cutoff=observation_cutoff,
        expected_opens=expected_opens,
    )
    ownership = _ownership(
        outcome,
        bindings,
        sessions if sessions is not None else SessionRegistry(),
        lineages if lineages is not None else ResearchDayRegistry(),
    )
    return OfflineRun(path=path, outcome=outcome, ownership=ownership)


def offline_parity(replay: OfflineRun, streaming: OfflineRun) -> ParityReport:
    """Compare two offline runs with the frozen parity routine."""
    return compare_parity(
        replay.as_pipeline_result(PipelinePath.REPLAY),
        streaming.as_pipeline_result(PipelinePath.STREAMING),
    )


__all__ = ["OfflineRun", "offline_parity", "run_offline"]
