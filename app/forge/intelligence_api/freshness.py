"""Quality, freshness and version semantics. No invented thresholds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.forge.intelligence_api.versions import FRESH_LABEL, STALE_LABEL
from app.forge.market_data.quality import DataOutcome, QualityFlag


@dataclass(frozen=True)
class FreshnessFacts:
    provider_configured: bool = False
    final_bar: bool = True
    stale: bool = False
    quality_outcome: DataOutcome = DataOutcome.OK
    quality_flags: tuple[QualityFlag, ...] = ()
    clock_resolved: bool = True
    cutoffs: tuple[str, ...] = ()
    expected_cutoff: str | None = None
    request_model_version: str | None = None
    component_model_version: str | None = None
    staleness_policy_version: str | None = None
    stale_exceeds_policy: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.quality_outcome, DataOutcome):
            raise ValueError("quality outcome must be a DataOutcome")


def short_circuit_codes(facts: FreshnessFacts) -> tuple[str, ...]:
    """Blocking outcomes, in a fixed order. Unavailability is not a market fact."""

    codes: list[str] = []
    if not facts.provider_configured:
        codes.append("PROVIDER_NOT_CONFIGURED")
    if facts.quality_outcome is DataOutcome.DATA_QUALITY_BLOCKED:
        codes.append("DATA_QUALITY_BLOCKED")
    if facts.quality_outcome is DataOutcome.NO_CALCULATION:
        codes.append("CLOCK_UNRESOLVED")
    if not facts.final_bar:
        codes.append("NONFINAL_BAR")
    if not facts.clock_resolved:
        codes.append("CLOCK_UNRESOLVED")
    if len({cutoff for cutoff in facts.cutoffs}) > 1:
        codes.append("MIXED_CUTOFF")
    if (
        facts.request_model_version
        and facts.component_model_version
        and facts.request_model_version != facts.component_model_version
    ):
        codes.append("VERSION_DRIFT")
    if staleness_refusal(facts):
        codes.append("STALE_DATA")
    return tuple(codes)


def staleness_refusal(facts: FreshnessFacts) -> str | None:
    """A staleness *refusal* exists only when a versioned policy supplies one."""

    if not facts.stale:
        return None
    if facts.staleness_policy_version is None:
        return None
    if not facts.stale_exceeds_policy:
        return None
    return "STALE_DATA"


def stale_label(facts: FreshnessFacts) -> str:
    return STALE_LABEL if facts.stale else FRESH_LABEL


def provider_status(facts: FreshnessFacts) -> str:
    return "CONFIGURED" if facts.provider_configured else "NOT_CONFIGURED"


def is_live_claim_permitted(facts: FreshnessFacts) -> bool:
    """Live-served intelligence is prohibited while the provider seam is unset."""

    return facts.provider_configured and facts.final_bar


def quality_payload(facts: FreshnessFacts, *, source_window_digest: str | None) -> dict[str, object]:
    return {
        "outcome": facts.quality_outcome.value,
        "flags": tuple(sorted(flag.value for flag in facts.quality_flags)),
        "stale_label": stale_label(facts),
        "provider_status": provider_status(facts),
        "source_window_digest": source_window_digest,
    }


def unresolved_cutoffs(cutoffs: Iterable[str]) -> tuple[str, ...]:
    return tuple(cutoffs)


__all__ = [
    "FreshnessFacts",
    "short_circuit_codes",
    "staleness_refusal",
    "stale_label",
    "provider_status",
    "is_live_claim_permitted",
    "quality_payload",
    "unresolved_cutoffs",
]
