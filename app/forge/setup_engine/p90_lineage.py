"""P90 automation lineage (Ch III.5.10).

A P90 lineage is a *recorded* implementation lineage, not an approved
automation card.  At this head every lineage is ``UNVERIFIED``:
implementation parity is not established (III.5-GAP-7), so
``automation_permitted`` is ``False`` everywhere.

Historical P90 statements stay ``HISTORICAL``; there is no API that
restates one as current verified performance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.forge.canonical import EvidenceStatus

from .errors import SetupContractError

__all__ = [
    "AUTOMATION_PERMITTED",
    "AutomationLineage",
    "LINEAGES",
    "LineageEvidence",
    "LineageStatus",
    "historical_claim",
    "lineage",
    "restate_as_current",
]


class LineageStatus(str, Enum):
    """How far a lineage's implementation parity is established."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    HISTORICAL_ONLY = "HISTORICAL_ONLY"


@dataclass(frozen=True)
class LineageEvidence:
    """A corpus artifact reference with its frozen evidence status."""

    artifact_ref: str
    status: EvidenceStatus
    claim_id: str | None = None

    def __post_init__(self) -> None:
        if not self.artifact_ref or " " in self.artifact_ref:
            raise SetupContractError("a lineage evidence ref is a corpus path")
        if not isinstance(self.status, EvidenceStatus):
            raise SetupContractError("lineage evidence carries its frozen status")
        if self.claim_id is not None and not self.claim_id.startswith("CL."):
            raise SetupContractError("a lineage claim reference is a CL.* id")


@dataclass(frozen=True)
class AutomationLineage:
    """Version + implementation reference + parity status + evidence."""

    lineage_id: str
    version: str
    implementation_ref: str
    parity_status: str
    evidence_refs: tuple[LineageEvidence, ...]
    status: LineageStatus = LineageStatus.UNVERIFIED

    def __post_init__(self) -> None:
        if not self.lineage_id or not self.version or not self.implementation_ref:
            raise SetupContractError(
                "a lineage requires an id, an explicit version and an implementation ref"
            )
        if not isinstance(self.status, LineageStatus):
            raise SetupContractError("a lineage status uses the bounded vocabulary")
        if not self.evidence_refs:
            raise SetupContractError("a lineage requires evidence references")
        for reference in self.evidence_refs:
            if not isinstance(reference, LineageEvidence):
                raise SetupContractError("lineage evidence refs are typed")

    @property
    def automation_permitted(self) -> bool:
        """Verified parity *and* verified status — otherwise never permitted."""

        return (
            self.status is LineageStatus.VERIFIED
            and self.parity_status == "PARITY_ESTABLISHED"
        )


_HISTORICAL = "corpus/canonical/evidence/EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md"

LINEAGES: tuple[AutomationLineage, ...] = (
    AutomationLineage(
        lineage_id="P90.EUR.DAILY.NEWS_REKEY",
        version="EUR.DAILY.NEWS_REKEY.V1@PHASE1",
        implementation_ref="app/forge/state_engine/failure_repair.py",
        parity_status="UNVERIFIED",
        evidence_refs=(
            LineageEvidence(
                artifact_ref=_HISTORICAL, status=EvidenceStatus.HISTORICAL
            ),
        ),
        status=LineageStatus.UNVERIFIED,
    ),
)

#: No lineage in this package may automate at this head.
AUTOMATION_PERMITTED = False


def lineage(lineage_id: str | None = None) -> AutomationLineage:
    if lineage_id is None:
        return LINEAGES[0]
    for item in LINEAGES:
        if item.lineage_id == lineage_id:
            return item
    raise SetupContractError(f"unknown lineage: {lineage_id!r}")


def historical_claim(item: AutomationLineage | None = None) -> LineageEvidence:
    """The historical statement, still labelled ``HISTORICAL``."""

    selected = lineage() if item is None else item
    for reference in selected.evidence_refs:
        if reference.status is EvidenceStatus.HISTORICAL:
            return reference
    raise SetupContractError("the lineage carries no historical statement")


def restate_as_current(reference: LineageEvidence) -> None:
    """Refuse: a historical statement is never restated as current."""

    raise SetupContractError(
        "a historical claim cannot be restated as current verified performance"
    )
