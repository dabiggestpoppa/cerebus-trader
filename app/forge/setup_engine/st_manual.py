"""Historical / manual ST representation (Ch III.5.9).

ST / Tier→AU→Tier is a valid **manual historical framework**, not a
canonical Setup Card: no ``SETUP.*`` identity exists for it (III.5-GAP-2),
and this module deliberately defines no setup-id constant.

It is explainable as bounded facts — inputs, the tier→AU→tier chain and
its evidence gate — while ``automation_permitted`` is ``False`` by
construction and the automation/perception gap stays ``UNRESOLVED`` and
disclosed.  A manual framework may coexist with failed automation parity;
it may never be requested as automation.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.canonical import EvidenceStatus

from .contracts import SetupEligibility
from .errors import SetupRefusalCode

__all__ = [
    "FRAMEWORK_ID",
    "ManualHistoricalFramework",
    "PERCEPTION_GAP",
    "TIER_CHAIN",
    "automation_request_refused",
    "explain",
    "framework",
]

FRAMEWORK_ID = "ST.TIER_TO_AU_TO_TIER"
TIER_CHAIN: tuple[str, ...] = ("TIER", "AU", "TIER")
PERCEPTION_GAP = "UNRESOLVED"

_SOURCE = "corpus/canonical/doctrine"


@dataclass(frozen=True)
class ManualHistoricalFramework:
    """A manual operator framework: inputs, chain, disclosure — no identity."""

    framework_id: str = FRAMEWORK_ID
    tier_chain: tuple[str, ...] = TIER_CHAIN
    inputs: tuple[str, ...] = ("TIER", "AU", "SESSION")
    automation_permitted: bool = False
    perception_gap: str = PERCEPTION_GAP
    setup_identity: None = None
    source_ref: str = _SOURCE

    def __post_init__(self) -> None:
        if self.automation_permitted:
            raise ValueError("the ST framework is manual and never automated")
        if self.setup_identity is not None:
            raise ValueError("no canonical SETUP identity exists for ST")
        if self.perception_gap != "UNRESOLVED":
            raise ValueError("the ST perception gap is unresolved and disclosed")


def framework() -> ManualHistoricalFramework:
    return ManualHistoricalFramework()


def explain():
    """The framework as bounded facts (tier → AU → tier, gap disclosed)."""

    from app.forge.model_runtime.contract import make_fact

    return (
        make_fact(
            "SETUP.ST.CHAIN",
            "SETUP.ST.TIER_TO_AU",
            FRAMEWORK_ID,
            (
                ("chain", "TIER_TO_AU_TO_TIER"),
                ("identity", "NONE"),
            ),
        ),
        make_fact(
            "SETUP.ST.AUTOMATION",
            "SETUP.ST.MANUAL.ONLY",
            FRAMEWORK_ID,
            (
                ("automation_permitted", "NO"),
                ("perception_gap", PERCEPTION_GAP),
                ("evidence_status", EvidenceStatus.HISTORICAL.value),
            ),
        ),
    )


def automation_request_refused() -> tuple[SetupEligibility, SetupRefusalCode]:
    """An ST automation request is a recorded refusal, never a capability."""

    return (SetupEligibility.BLOCKED, SetupRefusalCode.AUTOMATION_NOT_APPROVED)
