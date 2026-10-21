"""EUR Daily News + Rekey runtime (Ch III.3.1).

Canonical chain: Asian seed → tier → distance/asymmetry → consumed
states → event/news conditioning → rekey/extension → remaining
distribution.  Frozen protections:

* the Phase-1 source-generation no-go: >45p refuses with
  ``AR_SOURCE_NO_GO`` (45 exactly classifies as T3 per the frozen
  table);
* the rekey ladder states 100/125/132/168/185 are five distinct states,
  never collapsed or reordered, and a ladder state requires a REKEYED
  anchor — a coordinate touch never promotes (invariant #9);
* news conditions; it never replaces geometry — event facts attach to
  the conditioning surface only, geometry fields are untouched;
* slot × tier range-left is conditioned on consumed states
  (invariant #10) and is explicit ``UNRESOLVED`` without an active
  slot or a measured remainder;
* the family is not a direction oracle: direction is always the
  explicit ``NONE_DECLARED``.

The runtime consumes III.2 measurements as facts; it never re-measures,
never re-derives a canonical formula and attaches no statistic without
an evidence id (statistics are referenced by evidence id only).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from app.forge.measurements import (
    AnchorEligibility,
    AnchorStatus,
    EventBudget,
    EventFeatures,
    PathMeasurement,
    RangeMeasurement,
    RemainingState,
    SessionPhase,
    SessionPhaseState,
    TierClassification,
    quantize_ratio,
)

from .contract import (
    AnchorStateRef,
    DirectionBias,
    ExplanationFact,
    Layer,
    ModelOutput,
    ModelRequest,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    evidence_union,
    iter_measurements,
    make_fact,
    prior_ref,
    resolve_quality,
)
from .errors import InputMeasurementMissingError, ModelContractError

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .registry import RegistryEntry

__all__ = ["EurDailyInputs", "EurDailyState", "evaluate"]


_CARD = "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"

#: The five canonical rekey-ladder states of the modern Daily lineage.
LADDER_STATES: tuple[str, ...] = ("100", "125", "132", "168", "185")

#: The frozen Phase-1 tier vocabulary (calibration-defined).
_TIER_IDS: frozenset[str] = frozenset({"T1", "T2", "T3", "NO_GO"})

#: Slot states in which the daily slot window is active.
_ACTIVE_SLOTS: frozenset[SessionPhaseState] = frozenset(
    {SessionPhaseState.INSIDE_WINDOW, SessionPhaseState.CHECKPOINT_MATCHED}
)


class EurDailyState(str, Enum):
    """Family-bounded model states (no free text)."""

    SEED_T1 = "SEED_T1"
    SEED_T2 = "SEED_T2"
    SEED_T3 = "SEED_T3"
    SOURCE_NO_GO = "SOURCE_NO_GO"
    REKEY_100 = "REKEY_100"
    REKEY_125 = "REKEY_125"
    REKEY_132 = "REKEY_132"
    REKEY_168 = "REKEY_168"
    REKEY_185 = "REKEY_185"
    REKEYED = "REKEYED"


@dataclass(frozen=True)
class EurDailyInputs:
    """The family-typed measurement bundle (PLAN.md §7.3).

    Required at evaluation: ``seed`` and ``tier``.  Everything else is
    optional and its absence is explicit — a missing required
    measurement refuses with ``INPUT_MEASUREMENT_MISSING`` and is never
    synthesized.
    """

    seed: RangeMeasurement | None = None
    tier: TierClassification | None = None
    path: PathMeasurement | None = None
    event_features: EventFeatures | None = None
    event_budget: EventBudget | None = None
    anchor: AnchorEligibility | None = None
    ladder_state: str | None = None
    session_phase: SessionPhase | None = None


def _evaluate(request: ModelRequest, entry: "RegistryEntry") -> ModelOutput:
    inputs = request.inputs
    if not isinstance(inputs, EurDailyInputs):
        raise ModelContractError(
            f"{entry.model_key} evaluates EurDailyInputs, got "
            f"{type(inputs).__name__}"
        )

    seed = inputs.seed
    if seed is None:
        raise InputMeasurementMissingError(
            "EUR Daily requires the Asian seed range measurement"
        )
    tier = inputs.tier
    if tier is None:
        raise InputMeasurementMissingError(
            "EUR Daily requires the Phase-1 tier classification"
        )
    if tier.tier_id not in _TIER_IDS:
        raise ModelContractError(
            f"tier {tier.tier_id!r} is not part of the frozen Phase-1 vocabulary"
        )

    facts: list[ExplanationFact] = []

    # --- chain: seed → tier ------------------------------------------------
    facts.append(
        make_fact(
            "EUR_DAILY.SEED",
            "EUR_DAILY.SEED_RANGE",
            _CARD,
            {
                "size": seed.size.value,
                "unit": seed.size.unit.value,
                "direction": seed.direction.value,
                "window_digest": seed.source_window.input_digest,
            },
        )
    )
    facts.append(
        make_fact(
            "EUR_DAILY.TIER",
            "EUR_DAILY.TIER_CLASSIFICATION",
            tier.source_ref,
            {
                "tier_id": tier.tier_id,
                "no_go": tier.no_go,
                "calibration_status": tier.calibration_status.value,
            },
        )
    )

    # --- distance / asymmetry (declared rule; III.2 helper only) ----------
    asymmetry = quantize_ratio(abs(seed.close_location - Decimal("0.5")))
    facts.append(
        make_fact(
            "EUR_DAILY.DISTANCE_ASYMMETRY",
            "EUR_DAILY.DISTANCE_ASYMMETRY",
            _CARD,
            {
                "close_location": seed.close_location,
                "asymmetry": asymmetry,
            },
        )
    )

    # --- consumed delivery states -----------------------------------------
    if inputs.path is not None:
        path = inputs.path
        facts.append(
            make_fact(
                "EUR_DAILY.CONSUMED_STATES",
                "EUR_DAILY.CONSUMED_STATES",
                _CARD,
                {
                    "levels_measured": len(path.levels),
                    "first_delivery": path.first_delivery is not None,
                    "remaining_state": path.remaining_state.value,
                },
            )
        )

    # --- event conditioning (never geometry) -------------------------------
    if inputs.event_features is not None:
        features = inputs.event_features
        facts.append(
            make_fact(
                "EUR_DAILY.EVENT_CONDITIONING",
                "EUR_DAILY.EVENT_CONDITIONING",
                _CARD,
                {
                    "event_id": features.event_id,
                    "family": features.family.value,
                    "band_declared": features.band_declared,
                },
            )
        )
    if inputs.event_budget is not None:
        budget = inputs.event_budget
        facts.append(
            make_fact(
                "EUR_DAILY.EVENT_BUDGET",
                "EUR_DAILY.EVENT_BUDGET_SUBTRACTIVE",
                budget.source_ref,
                {
                    "event_id": budget.event_id,
                    "total_size": budget.total_size.value,
                    "consumed": budget.consumed.value,
                    "residual": budget.residual.value,
                },
            )
        )

    # --- anchor status / rekey ladder --------------------------------------
    anchor = inputs.anchor
    ladder = inputs.ladder_state
    if ladder is not None and ladder not in LADDER_STATES:
        raise ModelContractError(
            f"ladder state {ladder!r} is not one of the canonical ladder "
            f"states {', '.join(LADDER_STATES)}"
        )
    rekeyed = anchor is not None and anchor.status is AnchorStatus.REKEYED
    if ladder is not None and not rekeyed:
        raise ModelContractError(
            "a rekey ladder state requires a REKEYED anchor; a coordinate "
            "touch never promotes (invariant #9)"
        )

    # --- state precedence: source no-go > ladder > baseline ----------------
    if tier.no_go or tier.tier_id == "NO_GO":
        state = EurDailyState.SOURCE_NO_GO
        no_go: tuple[NoGoReason, ...] = (NoGoReason.AR_SOURCE_NO_GO,)
    elif ladder is not None:
        state = EurDailyState(f"REKEY_{ladder}")
        no_go = ()
    elif rekeyed:
        state = EurDailyState.REKEYED
        no_go = ()
    else:
        state = EurDailyState(f"SEED_{tier.tier_id}")
        no_go = ()

    if anchor is not None:
        if rekeyed:
            facts.append(
                make_fact(
                    "EUR_DAILY.REKEY_ANCHOR",
                    "EUR_DAILY.REKEY_EXTENSION",
                    _CARD,
                    {
                        "anchor_id": anchor.anchor_id,
                        "status": anchor.status.value,
                        "ladder": ladder if ladder is not None else "UNMAPPED",
                    },
                )
            )
        else:
            facts.append(
                make_fact(
                    "EUR_DAILY.ANCHOR_STATUS",
                    "EUR_DAILY.ANCHOR_STATUS",
                    _CARD,
                    {
                        "anchor_id": anchor.anchor_id,
                        "status": anchor.status.value,
                        "refusal_code": anchor.refusal_code.value,
                    },
                )
            )

    # --- slot × tier → remaining distribution ------------------------------
    slot_active = (
        inputs.session_phase is not None
        and inputs.session_phase.state in _ACTIVE_SLOTS
    )
    if inputs.session_phase is not None:
        facts.append(
            make_fact(
                "EUR_DAILY.SLOT",
                "EUR_DAILY.SLOT_STATE",
                _CARD,
                {"phase": inputs.session_phase.state.value},
            )
        )

    path = inputs.path
    conditioned: tuple[str, ...] = (
        ("EUR_DAILY.CONSUMED_STATES",) if path is not None else ()
    )
    remainder = (
        path.remaining_distribution
        if path is not None and path.remaining_state is RemainingState.MEASURED
        else None
    )
    if path is not None and remainder is not None and slot_active:
        range_left = RangeLeftField(
            state=RemainingState.MEASURED,
            value=remainder,
            basis_fact_id="EUR_DAILY.CONSUMED_STATES",
            conditioned_on=conditioned,
        )
    else:
        range_left = RangeLeftField.unresolved(conditioned_on=conditioned)

    facts.append(
        make_fact(
            "EUR_DAILY.DISTRIBUTION",
            "EUR_DAILY_REMAINING_DISTRIBUTION",
            _CARD,
            {
                "range_left_state": range_left.state.value,
                "slot_active": slot_active,
            },
        )
    )

    # --- prior-state reference (stateful family) ---------------------------
    if request.prior_state is None:
        facts.append(
            make_fact(
                "PRIOR_STATE.ABSENT",
                "COMMON.PRIOR_STATE",
                _CARD,
                {"linked": False},
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

    measurements = iter_measurements(inputs)
    anchor_states = (
        (
            AnchorStateRef(
                anchor_id=anchor.anchor_id,
                status=anchor.status,
                refusal_code=anchor.refusal_code,
            ),
        )
        if anchor is not None
        else ()
    )

    return ModelOutput(
        model_id=request.model_id,
        model_version=request.model_version,
        model_runtime_version=entry.runtime_version,
        output_hash="",
        model_state=state.value,
        layer=entry.layer,
        direction_bias=DirectionBias.none(),
        active_ranges=(seed.source_window.input_digest,),
        active_anchor_states=anchor_states,
        levels=(),
        range_left=range_left,
        no_go=no_go,
        warnings=(),
        claim_refs=(),
        evidence_refs=evidence_union(measurements),
        quality_state=resolve_quality(measurements),
        production_authorization=ProductionAuthorization.RESEARCH_ONLY,
        explanation_facts=tuple(facts),
        sub_states=(),
        identity=request.identity(prior_ref(request)),
    )


def evaluate(request: ModelRequest) -> ModelOutput:
    """Evaluate one EUR Daily request through the full replay pipeline."""
    from .replay import run_model

    return run_model(request)
