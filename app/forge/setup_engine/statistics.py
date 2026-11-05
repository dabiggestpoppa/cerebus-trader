"""Setup result vs setup statistics (Ch III.5.11).

A setup *result* is a state; a setup *statistic* is a claim about a
population.  This module exposes **no numeric result type** and no field
for win rate, expectancy, probability, confidence, confluence or
risk/reward — the absence is structural.

A performance statement may only be attached through a ``CL.*`` claim
reference whose population matches the evidence, and it is always a
reference with its frozen status — never a computed number.  A
relationship (for example JPY basket role agreement 115/168) is labelled
as a relationship, never as a setup win rate.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.canonical import ClaimIdentity, EvidenceStatus

from .contracts import EvidenceReference
from .errors import (
    ClaimPopulationMismatchError,
    SetupContractError,
    UnsupportedStatisticError,
    SetupRefusalCode,
)

__all__ = [
    "FORBIDDEN_FIELD_NAMES",
    "NUMERIC_RESULT_TYPES",
    "SetupStatisticClaim",
    "describe_relationship",
    "describe_statistic",
    "refuse_numeric_result",
]

#: Names that must never exist as a field in this package.
FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "win_rate",
        "expectancy",
        "probability",
        "confidence",
        "confluence",
        "risk_reward",
        "position_size",
        "order_intent",
    }
)

#: There is no numeric result type — deliberately an empty tuple.
NUMERIC_RESULT_TYPES: tuple[type, ...] = ()


@dataclass(frozen=True)
class SetupStatisticClaim:
    """A claim reference: identity + population + evidence with status."""

    claim_id: str
    population_key: str
    identity: ClaimIdentity
    evidence: EvidenceReference
    relationship: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, str) or not self.claim_id.startswith("CL."):
            raise UnsupportedStatisticError(
                "a setup statistic requires a CL.* claim reference "
                f"({SetupRefusalCode.UNSUPPORTED_STATISTIC.value})"
            )
        if not isinstance(self.identity, ClaimIdentity):
            raise SetupContractError("a statistic carries a claim identity")
        if not isinstance(self.evidence, EvidenceReference):
            raise SetupContractError("a statistic carries typed evidence")
        if self.evidence.claim_id != self.claim_id:
            raise ClaimPopulationMismatchError(
                "evidence claim does not match the quoted claim "
                f"({SetupRefusalCode.CLAIM_POPULATION_MISMATCH.value})"
            )
        if not self.population_key:
            raise SetupContractError("a statistic names its population")
        if (
            self.evidence.population_key is not None
            and self.evidence.population_key != self.population_key
        ):
            raise ClaimPopulationMismatchError(
                "evidence population does not match the described population "
                f"({SetupRefusalCode.CLAIM_POPULATION_MISMATCH.value})"
            )


def describe_statistic(
    *,
    claim_id: str | None,
    population_key: str,
    identity: ClaimIdentity,
    evidence: EvidenceReference,
) -> SetupStatisticClaim:
    """Attach a statistic reference, requiring its canonical claim identity."""

    if claim_id is None:
        raise UnsupportedStatisticError(
            "a statistic without a CL.* reference is refused "
            f"({SetupRefusalCode.UNSUPPORTED_STATISTIC.value})"
        )
    return SetupStatisticClaim(
        claim_id=claim_id,
        population_key=population_key,
        identity=identity,
        evidence=evidence,
    )


def describe_relationship(
    *,
    claim_id: str,
    population_key: str,
    identity: ClaimIdentity,
    evidence: EvidenceReference,
) -> SetupStatisticClaim:
    """Describe a state relationship — never a win rate."""

    if not evidence.relationship:
        raise UnsupportedStatisticError(
            "a relationship statement requires relationship evidence "
            f"({SetupRefusalCode.UNSUPPORTED_STATISTIC.value})"
        )
    if evidence.status is not EvidenceStatus.VALIDATED:
        raise UnsupportedStatisticError(
            "a relationship statement requires validated relationship evidence "
            f"({SetupRefusalCode.UNSUPPORTED_STATISTIC.value})"
        )
    return SetupStatisticClaim(
        claim_id=claim_id,
        population_key=population_key,
        identity=identity,
        evidence=evidence,
        relationship=True,
    )


def refuse_numeric_result(*_args: object, **_kwargs: object) -> None:
    """There is no numeric setup result: any request is refused."""

    raise UnsupportedStatisticError(
        "this surface exposes no numeric setup result "
        f"({SetupRefusalCode.UNSUPPORTED_STATISTIC.value})"
    )
