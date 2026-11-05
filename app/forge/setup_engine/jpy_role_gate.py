"""JPY Carry Role-Gated operator (Ch III.5.8) — ``MANUAL_OPERATOR``.

The role map is consumed **verbatim** from
``app.forge.model_runtime.jpy_carry.ROLE_MAP``: USDJPY carries the
``CARRY_MASTER`` role, AUDJPY the ``RISK_EXPRESSION`` role, EURJPY the
``CONFIRMATION_VETO`` role.

Consequences enforced structurally rather than by convention:

* primary agreement is USDJPY + AUDJPY; EURJPY strengthens or vetoes and
  is never an entry trigger;
* equal-vote aggregation is impossible — there is no aggregate, score or
  basket-confidence field anywhere;
* the executed pair must carry its own native tier and its own no-go
  state; the local setup comes from that pair's L1 geometry;
* historical 12-4 DT geometry is not imported automatically;
* basket role agreement (115/168, 103/115) is a *state relationship* with
  its evidence id, never a win rate;
* no automation approval while parity is unapproved.
"""

from __future__ import annotations

from app.forge.model_runtime.jpy_carry import ROLE_MAP

from .contracts import EvidenceReference
from .eligibility import SetupEvaluation, SetupEvaluationRequest, evaluate_setup
from .errors import SetupContractError
from .registry import CanonicalSetupCard, SetupRegistry

__all__ = [
    "AGGREGATE_FIELDS",
    "AUTOMATION_PERMITTED",
    "CONFIRMATION_PAIR",
    "HISTORICAL_DT_IMPORTED",
    "PAIR_ROLES",
    "PRIMARY_AGREEMENT",
    "SETUP_ID",
    "card",
    "equal_vote_supported",
    "evaluate_jpy",
    "evidence_refs",
    "local_geometry",
    "role_for",
]

SETUP_ID = "SETUP.JPY.CARRY_ROLE_GATE.V1"

#: The canonical role map, verbatim from III.3 (never reassigned).
PAIR_ROLES: dict[str, str] = dict(ROLE_MAP)

PRIMARY_AGREEMENT: tuple[str, str] = ("USDJPY", "AUDJPY")
CONFIRMATION_PAIR = "EURJPY"

#: There is no aggregate/score field, so equal-vote aggregation cannot exist.
AGGREGATE_FIELDS: tuple[str, ...] = ()

#: Historical DT geometry is not auto-imported; automation is not approved.
HISTORICAL_DT_IMPORTED = False
AUTOMATION_PERMITTED = False


def role_for(pair: str) -> str:
    try:
        return PAIR_ROLES[pair]
    except KeyError:
        raise SetupContractError(
            f"pair is not in the canonical role map: {pair!r}"
        ) from None


def equal_vote_supported() -> bool:
    """Equal-vote aggregation is impossible by construction."""

    return False


def card(registry: SetupRegistry | None = None) -> CanonicalSetupCard:
    return (SetupRegistry() if registry is None else registry).card(SETUP_ID)


def evidence_refs(registry: SetupRegistry | None = None) -> tuple[EvidenceReference, ...]:
    return card(registry).evidence_refs


def local_geometry(request: SetupEvaluationRequest, pair: str):
    """The selected pair's L1 geometry, taken from its own parent output."""

    role_for(pair)
    for parent in request.parents:
        instrument = parent.identity.instrument_id.upper()
        if instrument == pair.upper():
            for level in parent.levels:
                if level.active:
                    return level
    return None


def evaluate_jpy(
    request: SetupEvaluationRequest, *, registry: SetupRegistry | None = None
) -> SetupEvaluation:
    """Evaluate the JPY role-gated operator (operator surface)."""

    if request.setup_id != SETUP_ID:
        raise SetupContractError(
            f"the JPY operator evaluates {SETUP_ID}, not {request.setup_id}"
        )
    return evaluate_setup(request, registry=registry)
