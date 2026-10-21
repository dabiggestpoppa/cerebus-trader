"""JPY Carry Game runtime (Ch III.3.7).

Basket-role ownership, preserved as **separately returned role states**
(PLAN.md §7.1):

* USDJPY — carry master (``CARRY_MASTER``);
* AUDJPY — risk/execution expression (``RISK_EXPRESSION``);
* EURJPY — confirmation/veto (``CONFIRMATION_VETO``).

Frozen protections:

* no equal-vote majority: the output structure contains no
  aggregate/score/majority field at all — roles are separate sub-state
  entries by construction — and a request that asks for any
  aggregation refuses with ``MODEL_CONTRACT``;
* confirmation ≠ entry: the confirmation state affects only the
  basket-level state and its own sub-state, never another pair's local
  state or levels;
* confirm absent ⇒ explicit ``ABSENT`` (basket
  ``BASKET_CONFIRM_ABSENT``) — never a silent pass; disagreement or
  missing directions are explicit ``VETO``/``UNRESOLVED`` states;
* pair-native tier/no-go is honored per executed pair: a no-go pair
  cannot express local state and its measurements are scope-checked
  per pair (cross-pair transfer refuses with
  ``INSTRUMENT_SCOPE_MISMATCH``);
* the historical 12–4 PM DT geometry is never merged: DT coordinates
  appear only when the request explicitly references the DT family,
  and never as active levels (no earned range ⇒ no activation);
* ``production_authorization`` stays ``MANUAL_OPERATOR`` under every
  state until parity is approved (III.3-GAP-2).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from app.forge.measurements import (
    COORDINATE_SETS,
    PathMeasurement,
    RemainingState,
    SessionPhase,
)

from .contract import (
    DirectionBias,
    DirectionSide,
    ExplanationFact,
    Layer,
    LevelKind,
    ModelOutput,
    ModelRequest,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    SubState,
    TypedLevel,
    evidence_union,
    iter_measurements,
    make_fact,
    prior_ref,
    resolve_quality,
)
from .errors import (
    InputMeasurementMissingError,
    ModelContractError,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .registry import RegistryEntry

__all__ = [
    "JpyBasketState",
    "JpyCarryInputs",
    "JpyPairInput",
    "JpyRole",
    "ROLE_MAP",
    "evaluate",
]


_CARD = "corpus/canonical/models/JPY_CARRY_GAME_MODEL_CARD_V1.md"

#: The canonical role map — roles cannot be reassigned (card quote).
ROLE_MAP: dict[str, str] = {
    "USDJPY": "CARRY_MASTER",
    "AUDJPY": "RISK_EXPRESSION",
    "EURJPY": "CONFIRMATION_VETO",
}


class JpyRole(str, Enum):
    """The three canonical basket roles (no equal third vote)."""

    CARRY_MASTER = "CARRY_MASTER"
    RISK_EXPRESSION = "RISK_EXPRESSION"
    CONFIRMATION_VETO = "CONFIRMATION_VETO"


class JpyBasketState(str, Enum):
    """Family-bounded basket model states (no free text)."""

    BASKET_AGREE_CONFIRM = "BASKET_AGREE_CONFIRM"
    BASKET_CONFIRM_ABSENT = "BASKET_CONFIRM_ABSENT"
    BASKET_VETO = "BASKET_VETO"
    BASKET_CONFLICT = "BASKET_CONFLICT"
    BASKET_UNRESOLVED = "BASKET_UNRESOLVED"


@dataclass(frozen=True)
class JpyPairInput:
    """One pair's local facts — validated against the canonical role map."""

    instrument_id: str
    role: JpyRole
    local_direction: DirectionSide | None = None
    native_no_go: bool = False
    path: PathMeasurement | None = None
    session_phase: SessionPhase | None = None


@dataclass(frozen=True)
class JpyCarryInputs:
    """The family-typed basket bundle (PLAN.md §7.3).

    ``aggregation_request`` exists only to refuse: any explicit
    aggregation/equal-vote request raises ``MODEL_CONTRACT`` — no
    majority or score construction is ever performed.
    """

    pairs: tuple[JpyPairInput, ...] = ()
    dt_referenced: bool = False
    aggregation_request: str | None = None


def _pair_state(pair: JpyPairInput) -> str:
    if pair.native_no_go:
        return "NO_GO"
    if pair.local_direction is DirectionSide.UP:
        return "DIRECTION_UP"
    if pair.local_direction is DirectionSide.DOWN:
        return "DIRECTION_DOWN"
    return "DIRECTION_UNDECLARED"


def _evaluate(request: ModelRequest, entry: "RegistryEntry") -> ModelOutput:
    inputs = request.inputs
    if not isinstance(inputs, JpyCarryInputs):
        raise ModelContractError(
            f"{entry.model_key} evaluates JpyCarryInputs, got "
            f"{type(inputs).__name__}"
        )

    # --- H5: aggregation/equal-vote requests refuse outright ----------------
    if inputs.aggregation_request is not None:
        raise ModelContractError(
            "basket aggregation is refused: roles are returned separately, "
            "no equal-vote majority or aggregate score exists in this model"
        )

    # --- canonical role map --------------------------------------------------
    seen: dict[str, JpyPairInput] = {}
    for pair in inputs.pairs:
        expected = ROLE_MAP.get(pair.instrument_id)
        if expected is None:
            raise ModelContractError(
                f"{pair.instrument_id} is not part of the JPY basket"
            )
        if pair.role.value != expected:
            raise ModelContractError(
                f"{pair.instrument_id} carries the canonical role {expected}; "
                f"roles cannot be reassigned"
            )
        if pair.instrument_id in seen:
            raise ModelContractError(
                f"duplicate pair {pair.instrument_id}: one entry per role"
            )
        seen[pair.instrument_id] = pair

    master = seen.get("USDJPY")
    if master is None:
        raise InputMeasurementMissingError(
            "JPY Carry requires the USDJPY carry master pair"
        )
    expression = seen.get("AUDJPY")
    referee = seen.get("EURJPY")

    facts: list[ExplanationFact] = []

    # --- per-pair local states (never merged) --------------------------------
    for pair in inputs.pairs:
        direction = (
            "SUPPRESSED"
            if pair.native_no_go
            else (pair.local_direction.value if pair.local_direction else "UNDECLARED")
        )
        facts.append(
            make_fact(
                f"JPY.PAIR.{pair.instrument_id}",
                "JPY.PAIR_LOCAL_STATE",
                _CARD,
                {
                    "pair": pair.instrument_id,
                    "role": pair.role.value,
                    "direction": direction,
                    "native_no_go": pair.native_no_go,
                },
            )
        )

    # --- agreement (typed facts only; no score field exists) -----------------
    def _direction(pair: JpyPairInput | None) -> DirectionSide | None:
        if pair is None or pair.native_no_go:
            return None
        return pair.local_direction

    master_direction = _direction(master)
    expression_direction = _direction(expression)
    agree: bool | None = None
    if master_direction is None or expression_direction is None:
        agree = None
    else:
        agree = master_direction is expression_direction
    facts.append(
        make_fact(
            "JPY.BASKET.AGREEMENT",
            "JPY.BASKET_ROLE_RELATIONSHIP",
            _CARD,
            {
                "master_direction": (
                    master_direction.value if master_direction else "UNRESOLVED"
                ),
                "expression_direction": (
                    expression_direction.value
                    if expression_direction
                    else "UNRESOLVED"
                ),
                "agree": (
                    "UNRESOLVED" if agree is None else ("YES" if agree else "NO")
                ),
            },
        )
    )

    # --- confirmation / veto (never an entry) --------------------------------
    if referee is None:
        confirmation = "ABSENT"
        state = JpyBasketState.BASKET_CONFIRM_ABSENT
    elif referee.native_no_go:
        # A no-go referee can never confirm — never a silent pass.
        confirmation = "VETO"
        state = JpyBasketState.BASKET_VETO
    elif agree is False:
        # Master and expression disagree: the basket conflicts.
        confirmation = "VETO"
        state = JpyBasketState.BASKET_CONFLICT
    elif agree is None:
        # Directions missing/suppressed: nothing may pass silently.
        confirmation = "UNRESOLVED"
        state = JpyBasketState.BASKET_UNRESOLVED
    else:  # agree is True
        referee_direction = referee.local_direction
        if referee_direction is None:
            confirmation = "UNRESOLVED"
            state = JpyBasketState.BASKET_UNRESOLVED
        elif referee_direction is master_direction:
            confirmation = "CONFIRMED"
            state = JpyBasketState.BASKET_AGREE_CONFIRM
        else:
            confirmation = "VETO"
            state = JpyBasketState.BASKET_VETO

    facts.append(
        make_fact(
            "JPY.BASKET.CONFIRMATION",
            "JPY.BASKET_CONFIRMATION",
            _CARD,
            {"state": confirmation, "effect": "NOT_AN_ENTRY"},
        )
    )

    # --- DT geometry: only on explicit reference, never active ---------------
    levels: list[TypedLevel] = []
    if inputs.dt_referenced:
        coordinate_set = COORDINATE_SETS[
            ("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM")
        ]
        for family in coordinate_set.families:
            levels.append(
                TypedLevel(
                    level_id=family.family_id,
                    level_kind=LevelKind.COORDINATE,
                    family=family.family_id,
                    level=family.level,
                    price=None,
                    active=False,  # no earned range ⇒ no activation (invariant #3)
                    source_ref=family.source_ref,
                )
            )
        facts.append(
            make_fact(
                "JPY.DT.REFERENCED",
                "JPY.DT_WINDOW_REFERENCE",
                _CARD,
                {"referenced": True, "consumed": "DECLARED_STRUCTURES_ONLY"},
            )
        )

    # --- range-left from the master pair (no-go suppresses) ------------------
    conditioned: tuple[str, ...] = ()
    remainder = None
    if master.path is not None and not master.native_no_go:
        conditioned = ("JPY.PAIR.USDJPY",)
        if (
            master.path.remaining_state is RemainingState.MEASURED
            and master.path.remaining_distribution is not None
        ):
            remainder = master.path.remaining_distribution
    if remainder is not None:
        range_left = RangeLeftField(
            state=RemainingState.MEASURED,
            value=remainder,
            basis_fact_id="JPY.PAIR.USDJPY",
            conditioned_on=conditioned,
        )
    else:
        range_left = RangeLeftField.unresolved(conditioned_on=conditioned)

    # --- levels of local pairs never come from confirmation ------------------
    # (levels are DT-only; pair paths contribute range-left and ranges only)

    # --- prior state (optional for this stateless family) --------------------
    if request.prior_state is not None:
        facts.append(
            make_fact(
                "PRIOR_STATE.LINKED",
                "COMMON.PRIOR_STATE",
                _CARD,
                {"linked": True, "prior_hash": prior_ref(request)},
            )
        )

    # --- sub-states: roles separate, never merged ----------------------------
    sub_states = tuple(
        SubState(
            label=pair.instrument_id,
            layer=Layer.L1,
            state=_pair_state(pair),
            fact_ids=(f"JPY.PAIR.{pair.instrument_id}",),
        )
        for pair in inputs.pairs
    ) + (
        SubState(
            label="CONFIRMATION",
            layer=Layer.L2,
            state=confirmation,
            fact_ids=("JPY.BASKET.CONFIRMATION",),
        ),
    )

    # --- no-go from native tier flags (per executed pair) --------------------
    no_go = (
        (NoGoReason.NATIVE_TIER_NO_GO,)
        if any(pair.native_no_go for pair in inputs.pairs)
        else ()
    )

    active_ranges = tuple(
        pair.path.source_window.input_digest
        for pair in inputs.pairs
        if pair.path is not None
    )

    measurements = iter_measurements(inputs)
    return ModelOutput(
        model_id=request.model_id,
        model_version=request.model_version,
        model_runtime_version=entry.runtime_version,
        output_hash="",
        model_state=state.value,
        layer=entry.layer,
        direction_bias=DirectionBias.none(),
        active_ranges=active_ranges,
        active_anchor_states=(),
        levels=tuple(levels),
        range_left=range_left,
        no_go=no_go,
        warnings=(),
        claim_refs=(),
        evidence_refs=evidence_union(measurements),
        quality_state=resolve_quality(measurements),
        production_authorization=ProductionAuthorization.MANUAL_OPERATOR,
        explanation_facts=tuple(facts),
        sub_states=sub_states,
        identity=request.identity(prior_ref(request)),
    )


def evaluate(request: ModelRequest) -> ModelOutput:
    """Evaluate one JPY basket request through the full replay pipeline."""
    from .replay import run_model

    return run_model(request)
