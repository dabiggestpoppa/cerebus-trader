"""XAU Game L1-L2-L3 runtime (Ch III.3.4).

Canonical three-layer runtime, typed separately on the output:

* ``L3`` — higher-order destination/scale (input-reflected only);
* ``L2`` — route, pace, location, distribution and delivery clocks,
  including the promoted-aging rules;
* ``L1`` — Asian seed band context and relative consumption;
* plus the bounded ``CONFIRMATION`` context flag carried verbatim
  (III.5 owns confirmation semantics; this runtime respects the flag
  and can never clear or create it — a blind touch can never confirm).

Frozen protections:

* band 68 + elapsed ≥ 8h ⇒ eligible promotion to 80 (evidence
  ``EV.XAU.PROMOTION.68_80.V1``; both conditions required);
* band/state 120 + elapsed ≥ 8h ⇒ research promotion to 132 with
  ``RESEARCH_FLAG_SMALL_N`` (N=25) preserved and a small-N warning —
  never silently upgraded (``EV.XAU.PROMOTION.120_132.V1``);
* from the 132 state no transition to 168 exists — the rules contain no
  such path (absence by construction);
* parked input ⇒ parked output under every promotion/aging path with
  ``PROMOTION_PARKED`` no-go, and level activation is suppressed;
* L2 never carries entry/execution vocabulary and never populates L3 —
  layer ownership is typed on separate sub-state entries;
* aging uses III.2 ``elapsed_since`` plus the injected clock: time
  weights state, it never manufactures it (invariant #5);
* no quarter-zone execution object exists anywhere in this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from app.forge.measurements import (
    CoordinateProjection,
    ElapsedSinceEvent,
    PathMeasurement,
    RangeMeasurement,
    RemainingState,
    SessionPhase,
    SpatialBandClassification,
    TimeToDelivery,
)

from .contract import (
    DirectionBias,
    ExplanationFact,
    Layer,
    LevelKind as OutputLevelKind,
    ModelOutput,
    ModelRequest,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    SubState,
    TypedLevel,
    WarningCode,
    evidence_union,
    iter_measurements,
    make_fact,
    prior_ref,
    resolve_quality,
)
from .errors import InputMeasurementMissingError, ModelContractError

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .registry import RegistryEntry

__all__ = ["XauGameInputs", "XauState", "evaluate"]


_CARD = "corpus/canonical/models/XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md"

_EV_68_80 = "EV.XAU.PROMOTION.68_80.V1"
_EV_120_132 = "EV.XAU.PROMOTION.120_132.V1"

#: The canonical state-node vocabulary (coordinate set + promotion
#: from-states quoted by the frozen evidence cards).
_STATE_NODES: tuple[Decimal, ...] = tuple(
    Decimal(value) for value in ("50", "61.8", "68", "72", "80", "82", "120", "132")
)

_PROMOTION_AGE_HOURS = Decimal(8)

_L3_STATES: frozenset[str] = frozenset({"OPEN", "RESOLVED", "UNRESOLVED"})
_CONFIRMATION_STATES: frozenset[str] = frozenset({"ABSENT", "CONFIRMED"})


class XauState(str, Enum):
    """Family-bounded headline model states (no free text)."""

    PARKED = "PARKED"
    PROMOTION_ELIGIBLE = "PROMOTION_ELIGIBLE"
    PROMOTION_RESEARCH = "PROMOTION_RESEARCH"
    PROMOTION_PENDING = "PROMOTION_PENDING"
    NODE_DECLARED = "NODE_DECLARED"
    ROUTE_OPEN = "ROUTE_OPEN"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class XauGameInputs:
    """The family-typed measurement bundle (PLAN.md §7.3).

    Required at evaluation: ``seed`` (the Asian range).  ``parked`` and
    ``confirmation_state`` are bounded III.5-owned context flags the
    runtime respects but never clears or creates.
    """

    seed: RangeMeasurement | None = None
    band: SpatialBandClassification | None = None
    route: PathMeasurement | None = None
    delivery_clocks: tuple[TimeToDelivery, ...] = ()
    session_phase: SessionPhase | None = None
    coordinates: tuple[CoordinateProjection, ...] = ()
    elapsed: ElapsedSinceEvent | None = None
    state_node: Decimal | None = None
    l3_destination_state: str | None = None
    confirmation_state: str = "ABSENT"
    parked: bool = False


def _evaluate(request: ModelRequest, entry: "RegistryEntry") -> ModelOutput:
    inputs = request.inputs
    if not isinstance(inputs, XauGameInputs):
        raise ModelContractError(
            f"{entry.model_key} evaluates XauGameInputs, got "
            f"{type(inputs).__name__}"
        )

    seed = inputs.seed
    if seed is None:
        raise InputMeasurementMissingError(
            "XAU requires the Asian seed range measurement"
        )
    if inputs.confirmation_state not in _CONFIRMATION_STATES:
        raise ModelContractError(
            f"confirmation flag {inputs.confirmation_state!r} is outside the "
            f"bounded context vocabulary"
        )
    if inputs.l3_destination_state is not None and (
        inputs.l3_destination_state not in _L3_STATES
    ):
        raise ModelContractError(
            f"L3 destination state {inputs.l3_destination_state!r} is outside "
            f"the bounded vocabulary"
        )
    if inputs.state_node is not None and inputs.state_node not in _STATE_NODES:
        raise ModelContractError(
            f"state node {inputs.state_node} is outside the canonical XAU "
            f"node vocabulary"
        )

    warnings: list[WarningCode] = []
    facts: list[ExplanationFact] = []
    cited: list[str] = []

    # --- L1: seed + spatial band -------------------------------------------
    facts.append(
        make_fact(
            "XAU.SEED",
            "XAU.ASIAN_SEED",
            _CARD,
            {
                "size": seed.size.value,
                "unit": seed.size.unit.value,
                "window_digest": seed.source_window.input_digest,
            },
        )
    )
    if inputs.band is not None:
        band = inputs.band
        facts.append(
            make_fact(
                "XAU.BAND",
                "XAU.SPATIAL_BAND",
                band.source_ref,
                {
                    "band_id": band.band_id,
                    "band_state": band.band_state.value,
                    "magnitude": band.magnitude.value,
                    "calibration_status": band.calibration_status.value,
                },
            )
        )
        if band.calibration_status.value == "RESEARCH":
            warnings.append(WarningCode.RESEARCH_CALIBRATION)
    if inputs.session_phase is not None:
        facts.append(
            make_fact(
                "XAU.SEED_SESSION",
                "XAU.SESSION_PHASE",
                _CARD,
                {"phase": inputs.session_phase.state.value},
            )
        )

    # --- L2: route, pace, delivery clocks -----------------------------------
    route = inputs.route
    if route is not None:
        facts.append(
            make_fact(
                "XAU.ROUTE",
                "XAU.L2_ROUTE",
                _CARD,
                {
                    "levels_measured": len(route.levels),
                    "first_delivery": route.first_delivery is not None,
                    "remaining_state": route.remaining_state.value,
                },
            )
        )
    if inputs.delivery_clocks:
        first = inputs.delivery_clocks[0]
        facts.append(
            make_fact(
                "XAU.DELIVERY_CLOCKS",
                "XAU.L2_DELIVERY_CLOCKS",
                _CARD,
                {
                    "clocks": len(inputs.delivery_clocks),
                    "next_boundary": first.scheduled_boundary.isoformat().replace(
                        "+00:00", "Z"
                    ),
                    "state": first.state.value,
                },
            )
        )

    # --- L3: destination (input-reflected; never derived from lower layers)
    l3_state = inputs.l3_destination_state or "UNRESOLVED"
    facts.append(
        make_fact(
            "XAU.L3_DESTINATION",
            "XAU.L3_DESTINATION_STATE",
            _CARD,
            {"state": l3_state, "authority": "L3_ONLY"},
        )
    )

    # --- L2 promotion rules (pure typed functions of node + elapsed) -------
    node = inputs.state_node
    promotion_evidence: str | None = None
    if inputs.parked:
        l2_state = "PARKED"
        headline = XauState.PARKED
        facts.append(
            make_fact(
                "XAU.PARKED",
                "XAU.PARKED_CONTEXT",
                _CARD,
                {"parked": True, "activation": "BLOCKED"},
            )
        )
    elif node is None:
        if route is not None:
            l2_state = "ROUTE_OPEN"
            headline = XauState.ROUTE_OPEN
        else:
            l2_state = "UNRESOLVED"
            headline = XauState.UNRESOLVED
    else:
        hours: Decimal | None = None
        if inputs.elapsed is not None:
            hours = inputs.elapsed.elapsed_seconds / Decimal(3600)
        age_met = hours is not None and hours >= _PROMOTION_AGE_HOURS
        if node == Decimal(68):
            if age_met:
                l2_state = "ELIGIBLE_80"
                headline = XauState.PROMOTION_ELIGIBLE
                promotion_evidence = _EV_68_80
                facts.append(
                    make_fact(
                        "XAU.PROMOTION_68_80",
                        "XAU.PROMOTION_68_TO_80",
                        _CARD,
                        {
                            "from_state": "68",
                            "to_state": "80",
                            "age_hours": _PROMOTION_AGE_HOURS,
                            "standing": "VALIDATED_SMALL_N",
                            "sample_n": 48,
                            "evidence_id": _EV_68_80,
                        },
                    )
                )
            else:
                l2_state = "PROMOTION_PENDING"
                headline = XauState.PROMOTION_PENDING
                facts.append(
                    make_fact(
                        "XAU.PROMOTION_PENDING",
                        "XAU.PROMOTION_AGEING",
                        _CARD,
                        {
                            "from_state": "68",
                            "required_age_hours": _PROMOTION_AGE_HOURS,
                            "elapsed_hours": hours if hours is not None else "UNAVAILABLE",
                        },
                    )
                )
        elif node == Decimal(120):
            if age_met:
                l2_state = "RESEARCH_PROMOTED_132"
                headline = XauState.PROMOTION_RESEARCH
                promotion_evidence = _EV_120_132
                warnings.append(WarningCode.SMALL_N_RESEARCH_FLAG)
                facts.append(
                    make_fact(
                        "XAU.PROMOTION_120_132",
                        "XAU.PROMOTION_120_TO_132",
                        _CARD,
                        {
                            "from_state": "120",
                            "to_state": "132",
                            "age_hours": _PROMOTION_AGE_HOURS,
                            "standing": "RESEARCH_FLAG_SMALL_N",
                            "sample_n": 25,
                            "evidence_id": _EV_120_132,
                        },
                    )
                )
            else:
                l2_state = "PROMOTION_PENDING"
                headline = XauState.PROMOTION_PENDING
                facts.append(
                    make_fact(
                        "XAU.PROMOTION_PENDING",
                        "XAU.PROMOTION_AGEING",
                        _CARD,
                        {
                            "from_state": "120",
                            "required_age_hours": _PROMOTION_AGE_HOURS,
                            "elapsed_hours": hours if hours is not None else "UNAVAILABLE",
                        },
                    )
                )
        else:
            l2_state = f"NODE_{node}"
            headline = XauState.NODE_DECLARED
            if node == Decimal(132):
                facts.append(
                    make_fact(
                        "XAU.NODE_132_BOUNDARY",
                        "XAU.NODE_BOUNDARY",
                        _CARD,
                        {"node": "132", "automatic_168": "NO"},
                    )
                )
    if promotion_evidence is not None:
        cited.append(promotion_evidence)

    # --- confirmation flag (carried verbatim; never created or cleared) ----
    facts.append(
        make_fact(
            "XAU.CONFIRMATION_CONTEXT",
            "XAU.CONFIRMATION_FLAG",
            _CARD,
            {"state": inputs.confirmation_state, "owned_by": "III.5"},
        )
    )

    # --- range-left from the L2 route --------------------------------------
    conditioned: tuple[str, ...] = (("XAU.ROUTE",) if route is not None else ())
    remainder = (
        route.remaining_distribution
        if route is not None
        and route.remaining_state is RemainingState.MEASURED
        and route.remaining_distribution is not None
        else None
    )
    if remainder is not None:
        range_left = RangeLeftField(
            state=RemainingState.MEASURED,
            value=remainder,
            basis_fact_id="XAU.ROUTE",
            conditioned_on=conditioned,
        )
    else:
        range_left = RangeLeftField.unresolved(conditioned_on=conditioned)

    # --- levels from projected coordinates (parked ⇒ inactive) -------------
    levels: list[TypedLevel] = []
    for projection in inputs.coordinates:
        levels.append(
            TypedLevel(
                level_id=projection.coordinate_id,
                level_kind=OutputLevelKind.COORDINATE,
                family=projection.family_id,
                level=projection.level,
                price=projection.projected_price.value,
                active=not inputs.parked,
                source_ref=projection.family_source_ref,
            )
        )

    # --- prior-state reference ---------------------------------------------
    if request.prior_state is None:
        facts.append(
            make_fact(
                "PRIOR_STATE.ABSENT", "COMMON.PRIOR_STATE", _CARD, {"linked": False}
            )
        )
    else:
        facts.append(
            make_fact(
                "PRIOR_STATE.LINKED",
                "COMMON.PRIOR_STATE",
                _CARD,
                {"linked": True, "prior_hash": prior_ref(request)},
            )
        )

    # --- sub-states: layers typed separately, never merged ------------------
    sub_states = (
        SubState(
            label="L3",
            layer=Layer.L3,
            state=l3_state,
            fact_ids=("XAU.L3_DESTINATION",),
        ),
        SubState(
            label="L2",
            layer=Layer.L2,
            state=l2_state,
            fact_ids=(
                tuple(
                    fact.fact_id
                    for fact in facts
                    if fact.fact_id.startswith(("XAU.PROMOTION", "XAU.NODE", "XAU.ROUTE", "XAU.DELIVERY", "XAU.PARKED"))
                )
            ),
        ),
        SubState(
            label="L1",
            layer=Layer.L1,
            state=(
                f"BAND_{inputs.band.band_state.value}"
                if inputs.band is not None
                else "ASIAN_SEED"
            ),
            fact_ids=(
                tuple(
                    fact.fact_id
                    for fact in facts
                    if fact.fact_id.startswith(("XAU.SEED", "XAU.BAND"))
                )
            ),
        ),
        SubState(
            label="CONFIRMATION",
            layer=Layer.L1,
            state=inputs.confirmation_state,
            fact_ids=("XAU.CONFIRMATION_CONTEXT",),
        ),
    )

    no_go: tuple[NoGoReason, ...] = (
        (NoGoReason.PROMOTION_PARKED,) if inputs.parked else ()
    )

    measurements = iter_measurements(inputs)
    evidence: list[str] = list(evidence_union(measurements))
    for ref in cited:
        if ref not in evidence:
            evidence.append(ref)

    return ModelOutput(
        model_id=request.model_id,
        model_version=request.model_version,
        model_runtime_version=entry.runtime_version,
        output_hash="",
        model_state=headline.value,
        layer=entry.layer,
        direction_bias=DirectionBias.none(),
        active_ranges=(seed.source_window.input_digest,),
        active_anchor_states=(),
        levels=tuple(levels),
        range_left=range_left,
        no_go=no_go,
        warnings=tuple(warnings),
        claim_refs=(),
        evidence_refs=tuple(evidence),
        quality_state=resolve_quality(measurements),
        production_authorization=ProductionAuthorization.MANUAL_OPERATOR,
        explanation_facts=tuple(facts),
        sub_states=sub_states,
        identity=request.identity(prior_ref(request)),
    )


def evaluate(request: ModelRequest) -> ModelOutput:
    """Evaluate one XAU request through the full replay pipeline."""
    from .replay import run_model

    return run_model(request)
