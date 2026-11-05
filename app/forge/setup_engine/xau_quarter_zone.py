"""XAU Quarter-Zone operator (Ch III.5.6) — ``MANUAL_OPERATOR``.

The canonical card's doctrine, encoded without inventing a single number
beyond the card's own text:

* after-03:00 NY context is required;
* entry requires an **excursion into** the quarter zone, then a push or
  rejection back — a 5-minute close outside the zone or a valid S/R flip
  may confirm; a blind touch never may;
* next-quarter doctrine is the primary target and comes first;
* ``$5``/``$10`` moves are confirmation/evidence states, not doctrine;
* the ladder invalidation and the quarter mapping are **not** canonically
  materialised (III.5-GAP-1 / III.5-GAP-3), so a fully-armed evaluation
  is capped at ``WATCH`` until they are;
* an automatic ``132→168`` promotion is refused;
* no automation approval is ever emitted.

Because the mapping is unmaterialised, this module declares *no* zone
prices.  It exposes only the card's offset vocabulary and target order.
"""

from __future__ import annotations

from decimal import Decimal

from .contracts import EvidenceReference, SetupTarget
from .eligibility import SetupEvaluation, SetupEvaluationRequest, evaluate_setup
from .errors import SetupContractError, SetupRefusalCode, TargetPromotionRefused
from .registry import CanonicalSetupCard, SetupRegistry

__all__ = [
    "CONFIRMATION_TARGET_IDS",
    "LADDER_PARAMETER",
    "PRIMARY_TARGET_ID",
    "SETUP_ID",
    "ZONE_OFFSETS",
    "ZONE_PARAMETER",
    "assert_no_forbidden_promotion",
    "card",
    "confirmation_targets",
    "evaluate_xau",
    "evidence_refs",
    "primary_target",
]

SETUP_ID = "SETUP.XAU.QUARTER_ZONE.V1"

#: The two parameters the card requires before a verdict may exceed WATCH.
ZONE_PARAMETER = "QUARTER_ZONE_MAPPING"
LADDER_PARAMETER = "LADDER_INVALIDATION"

#: The card's declared offset vocabulary — *offsets*, never prices.
ZONE_OFFSETS: tuple[Decimal, ...] = (Decimal("10"), Decimal("15"))

PRIMARY_TARGET_ID = "SETUP.XAU.TARGET.NEXT_QUARTER"

CONFIRMATION_TARGET_IDS: tuple[str, ...] = (
    "SETUP.XAU.TARGET.CONFIRM_5",
    "SETUP.XAU.TARGET.CONFIRM_10",
)

#: A promotion between these coordinates is refused, never auto-applied.
FORBIDDEN_PROMOTION_COORDINATES: tuple[tuple[Decimal, Decimal], ...] = (
    (Decimal("132"), Decimal("168")),
)


def card(registry: SetupRegistry | None = None) -> CanonicalSetupCard:
    return (SetupRegistry() if registry is None else registry).card(SETUP_ID)


def evidence_refs(registry: SetupRegistry | None = None) -> tuple[EvidenceReference, ...]:
    return card(registry).evidence_refs


def primary_target(registry: SetupRegistry | None = None) -> SetupTarget:
    for target in card(registry).targets:
        if target.target_id == PRIMARY_TARGET_ID:
            return target
    raise SetupContractError("the XAU card must declare its next-quarter target")


def confirmation_targets(
    registry: SetupRegistry | None = None,
) -> tuple[SetupTarget, ...]:
    declared = card(registry).targets
    return tuple(
        target for target in declared if target.target_id in CONFIRMATION_TARGET_IDS
    )


def assert_no_forbidden_promotion(
    source_coordinate: Decimal, destination_coordinate: Decimal
) -> None:
    """Refuse the shorthand ``132→168`` promotion the doctrine forbids."""

    pair = (source_coordinate, destination_coordinate)
    if pair in FORBIDDEN_PROMOTION_COORDINATES:
        raise TargetPromotionRefused(
            "an automatic 132->168 promotion is forbidden "
            f"({SetupRefusalCode.FORBIDDEN_PROMOTION.value})"
        )


def evaluate_xau(
    request: SetupEvaluationRequest, *, registry: SetupRegistry | None = None
) -> SetupEvaluation:
    """Evaluate the XAU operator on an operator-facing surface."""

    if request.setup_id != SETUP_ID:
        raise SetupContractError(
            f"the XAU operator evaluates {SETUP_ID}, not {request.setup_id}"
        )
    return evaluate_setup(request, registry=registry)
