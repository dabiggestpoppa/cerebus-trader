"""Historical replay / live-style streaming parity (Ch III.1.9).

Two runners consume the *same* scripted fixture records:

* ``replay_historical`` normalizes the batch as a whole;
* ``stream_live`` absorbs records one at a time as they arrive
  (provisional per-arrival state, terminal reconciliation).

Both terminate in identical normalized bars, session ownership and
quality state — asserted by ``compare_parity`` (I2/I3).  This is a
scripted streaming runner over committed fixtures, not a live provider
feed: true live-feed parity requires provider selection (PLAN gaps
GAP-4/GAP-5) and is never claimed here.

Session ownership pairs a bar with its registered session (by local
open membership for windows, exact local close for checkpoints) and its
explicit research-day assignment.  Anything unresolvable returns an
explicit ``NO_CALCULATION``/``UNRESOLVED`` state — never an empty
success.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Mapping, Sequence

from .bars import (
    TIMEFRAME_MINUTES,
    Bar,
    ProvenanceKind,
    canonical_key,
    content_digest,
    finalize_for_cutoff,
    missing_opens,
    reconcile,
)
from .clocks import CLOCK_REGISTRY_VERSION, local_wall
from .instruments import InstrumentRegistry
from .normalize import FeedResult, normalize_feed, provider_schema
from .quality import DataOutcome, QualityFlag, QualityPolicy, normalize_flags
from .research_day import ResearchDayRegistry, ResearchDayStatus, assign_research_day
from .sessions import (
    SessionKind,
    SessionRegistry,
    close_matches_checkpoint,
    local_open_in_session,
)
from .versions import MARKET_DATA_SCHEMA_VERSION


class OwnershipStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NO_CALCULATION = "NO_CALCULATION"
    UNRESOLVED = "UNRESOLVED"


class PipelinePath(str, Enum):
    REPLAY = "REPLAY"
    STREAMING = "STREAMING"


@dataclass(frozen=True)
class ModelBinding:
    """Instrument -> (model, calibration version, research-day lineage).

    Wiring is supplied by the caller (tests/fixtures), never invented
    inside the package from instrument naming.
    """

    instrument_id: str
    model_id: str
    model_version: str
    lineage_id: str


@dataclass(frozen=True)
class OwnershipResult:
    """Session + research-day ownership of one normalized bar."""

    status: OwnershipStatus
    reason_code: str
    session_id: str | None
    research_day: date | None
    model_id: str | None
    model_version: str | None
    clock_id: str | None
    session_registry_version: str
    market_data_schema_version: str

    @property
    def resolved(self) -> bool:
        return self.status is OwnershipStatus.RESOLVED

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "reason_code": self.reason_code,
            "session_id": self.session_id,
            "research_day": self.research_day.isoformat() if self.research_day else None,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "clock_id": self.clock_id,
            "session_registry_version": self.session_registry_version,
            "market_data_schema_version": self.market_data_schema_version,
        }


def bar_ownership(
    bar: Bar,
    bindings: Sequence[ModelBinding],
    sessions: SessionRegistry,
    lineages: ResearchDayRegistry,
) -> OwnershipResult:
    """Explicit (session, research-day) ownership for one bar — fail closed."""
    binding = next(
        (item for item in bindings if item.instrument_id == bar.instrument_id), None
    )
    if binding is None:
        return OwnershipResult(
            status=OwnershipStatus.NO_CALCULATION,
            reason_code="NO_BINDING",
            session_id=None,
            research_day=None,
            model_id=None,
            model_version=None,
            clock_id=None,
            session_registry_version=sessions.registry_version,
            market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        )

    matches = []
    for definition in sessions.definitions_for(
        binding.model_id, binding.model_version
    ):
        if definition.kind is SessionKind.WINDOW:
            if local_open_in_session(definition, local_wall(bar.open_time, definition.clock)):
                matches.append(definition)
        else:
            if close_matches_checkpoint(definition, local_wall(bar.close_time, definition.clock)):
                matches.append(definition)
    if not matches:
        return OwnershipResult(
            status=OwnershipStatus.NO_CALCULATION,
            reason_code="NO_SESSION",
            session_id=None,
            research_day=None,
            model_id=binding.model_id,
            model_version=binding.model_version,
            clock_id=None,
            session_registry_version=sessions.registry_version,
            market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        )
    if len(matches) > 1:
        return OwnershipResult(
            status=OwnershipStatus.NO_CALCULATION,
            reason_code="AMBIGUOUS_SESSION",
            session_id=None,
            research_day=None,
            model_id=binding.model_id,
            model_version=binding.model_version,
            clock_id=None,
            session_registry_version=sessions.registry_version,
            market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        )
    definition = matches[0]
    research = assign_research_day(
        lineages, binding.lineage_id, bar.instrument_id, bar.close_time
    )
    if research.status is not ResearchDayStatus.RESOLVED:
        return OwnershipResult(
            status=OwnershipStatus.UNRESOLVED,
            reason_code="LINEAGE_UNRESOLVED",
            session_id=None,
            research_day=None,
            model_id=binding.model_id,
            model_version=binding.model_version,
            clock_id=definition.clock.clock_id,
            session_registry_version=sessions.registry_version,
            market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        )
    return OwnershipResult(
        status=OwnershipStatus.RESOLVED,
        reason_code="RESOLVED",
        session_id=definition.session_id,
        research_day=research.research_day,
        model_id=binding.model_id,
        model_version=binding.model_version,
        clock_id=definition.clock.clock_id,
        session_registry_version=sessions.registry_version,
        market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
    )


@dataclass(frozen=True)
class PipelineContext:
    """Everything the runners need — all injected, nothing global."""

    registry: InstrumentRegistry
    sessions: SessionRegistry
    lineages: ResearchDayRegistry
    bindings: tuple[ModelBinding, ...]
    policy: QualityPolicy
    observation_cutoff: datetime
    provenance: ProvenanceKind
    source_ref: str | None = None
    expected_opens: tuple[datetime, ...] | None = None


@dataclass(frozen=True)
class PipelineResult:
    """Terminal result of one runner — normalized facts only."""

    path: PipelinePath
    bars: tuple[Bar, ...]
    ownership: tuple[tuple[str, OwnershipResult], ...]
    quality_flags: frozenset[QualityFlag]
    feed_outcome: DataOutcome
    refused_count: int
    missing: tuple[datetime, ...]
    market_data_schema_version: str
    session_registry_version: str
    clock_registry_version: str

    def ownership_map(self) -> dict[str, OwnershipResult]:
        return dict(self.ownership)

    @staticmethod
    def _bar_key(bar: Bar) -> str:
        return f"{bar.instrument_id}/{bar.timeframe}/{bar.open_time.isoformat()}"

    def to_dict(self) -> dict:
        return {
            "path": self.path.value,
            "bars": [bar.to_dict() for bar in self.bars],
            "ownership": [
                [key, result.to_dict()] for key, result in self.ownership
            ],
            "quality_flags": sorted(flag.value for flag in self.quality_flags),
            "feed_outcome": self.feed_outcome.value,
            "refused_count": self.refused_count,
            "missing": [
                stamp.isoformat().replace("+00:00", "Z") for stamp in self.missing
            ],
            "market_data_schema_version": self.market_data_schema_version,
            "session_registry_version": self.session_registry_version,
            "clock_registry_version": self.clock_registry_version,
        }

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _finalize_ownership(
    bars: Sequence[Bar], ctx: PipelineContext
) -> tuple[tuple[str, OwnershipResult], ...]:
    ownership = [
        (PipelineResult._bar_key(bar), bar_ownership(bar, ctx.bindings, ctx.sessions, ctx.lineages))
        for bar in bars
    ]
    ownership.sort(key=lambda item: item[0])
    return tuple(ownership)


def _finish(
    path: PipelinePath,
    bars: Sequence[Bar],
    feed: FeedResult,
    ctx: PipelineContext,
) -> PipelineResult:
    return PipelineResult(
        path=path,
        bars=tuple(bars),
        ownership=_finalize_ownership(bars, ctx),
        quality_flags=feed.quality_flags,
        feed_outcome=ctx.policy.evaluate(feed.quality_flags),
        refused_count=feed.refusal_count,
        missing=feed.missing,
        market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        session_registry_version=ctx.sessions.registry_version,
        clock_registry_version=CLOCK_REGISTRY_VERSION,
    )


def replay_historical(
    records: Sequence[Mapping[str, object]],
    provider: str,
    ctx: PipelineContext,
) -> PipelineResult:
    """Batch historical replay over a committed fixture slice."""
    feed = normalize_feed(
        records,
        provider,
        ctx.registry,
        observation_cutoff=ctx.observation_cutoff,
        provenance=ctx.provenance,
        source_ref=ctx.source_ref,
        expected_opens=ctx.expected_opens,
    )
    return _finish(PipelinePath.REPLAY, feed.bars, feed, ctx)


def stream_live(
    records: Sequence[Mapping[str, object]],
    provider: str,
    ctx: PipelineContext,
) -> PipelineResult:
    """Scripted live-style streaming runner over the same records.

    Records are absorbed one arrival at a time into a running journal;
    terminal reconciliation, finality, gap detection and ownership use
    the same rules as the batch path, so both runners must agree (I2/I3).
    The observation cutoff is a fixture label — a true advancing live
    cutoff belongs to the deferred provider work (GAP-4/GAP-5).
    """
    provider_schema(provider)  # fail closed for unknown providers, early
    journal: dict[tuple[str, str, float], list[Bar]] = {}
    refused_records = []
    for payload in records:
        feed_step = normalize_feed(
            (payload,),
            provider,
            ctx.registry,
            observation_cutoff=ctx.observation_cutoff,
            provenance=ctx.provenance,
            source_ref=ctx.source_ref,
        )
        refused_records.extend(feed_step.refused)
        for bar in feed_step.bars:
            journal.setdefault(canonical_key(bar), []).append(bar)
    grouped = [reconcile(tuple(journal[key])) for key in sorted(journal)]
    bars = sorted(
        (
            finalize_for_cutoff(bar, ctx.observation_cutoff)
            for group in grouped
            for bar in group
        ),
        key=lambda bar: (bar.open_time.timestamp(), bar.dumps()),
    )
    timeframe = bars[0].timeframe if bars else None
    if timeframe is None and records:
        candidate = str(records[0].get(provider_schema(provider).timeframe, ""))
        timeframe = candidate if candidate in TIMEFRAME_MINUTES else None
    missing = missing_opens(bars, ctx.expected_opens, timeframe=timeframe)
    # Terminal quality is recomputed from reconciled state, exactly as the
    # batch path does: terminal bar flags + refusal flags + GAP for absence.
    quality: set[QualityFlag] = set()
    for bar in bars:
        quality |= set(bar.quality_flags)
    for record in refused_records:
        quality |= set(record.flags)
    if missing:
        quality.add(QualityFlag.GAP)
    feed = FeedResult(
        bars=tuple(bars),
        refused=tuple(refused_records),
        missing=tuple(missing),
        quality_flags=normalize_flags(quality),
        timeframe=timeframe,
    )
    return _finish(PipelinePath.STREAMING, bars, feed, ctx)


@dataclass(frozen=True)
class ParityReport:
    """Comparison of two runner results (I2 session, I3 quality)."""

    session_parity: bool
    quality_parity: bool
    bar_parity: bool
    outcome_parity: bool
    differences: tuple[str, ...]

    @property
    def overall(self) -> bool:
        return (
            self.session_parity
            and self.quality_parity
            and self.bar_parity
            and self.outcome_parity
        )


def compare_parity(replay: PipelineResult, streaming: PipelineResult) -> ParityReport:
    """Assert replay == streaming on bars, ownership, quality and outcome."""
    differences: list[str] = []

    replay_own = replay.ownership_map()
    stream_own = streaming.ownership_map()
    if set(replay_own) != set(stream_own):
        differences.append("ownership_keys")
    else:
        for key in sorted(replay_own):
            left, right = replay_own[key], stream_own[key]
            if (
                left.status != right.status
                or left.session_id != right.session_id
                or left.research_day != right.research_day
                or left.reason_code != right.reason_code
            ):
                differences.append(f"ownership:{key}")
    session_parity = not any(item.startswith("ownership") for item in differences)

    quality_parity = replay.quality_flags == streaming.quality_flags
    if not quality_parity:
        differences.append("quality_flags")

    bar_parity = (
        content_digest(replay.bars) == content_digest(streaming.bars)
        and len(replay.bars) == len(streaming.bars)
        and replay.missing == streaming.missing
    )
    if not bar_parity:
        differences.append("bars")

    outcome_parity = (
        replay.feed_outcome == streaming.feed_outcome
        and replay.refused_count == streaming.refused_count
    )
    if not outcome_parity:
        differences.append("feed_outcome")

    return ParityReport(
        session_parity=session_parity,
        quality_parity=quality_parity,
        bar_parity=bar_parity,
        outcome_parity=outcome_parity,
        differences=tuple(differences),
    )
