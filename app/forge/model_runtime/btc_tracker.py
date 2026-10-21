"""BTC Daily/Weekly/Monthly **Tracker** runtime (Ch III.3.5).

Daily lineage: 19:00–03:00 NY source frame → native tiers/AU →
03:00–19:00 slot × tier range-left.  Frozen protections:

* **BTC Tracker ≠ BTC Game** — only ``BTC.TRACKER.DWM.V1`` is
  registered; a Game-like request fails ``MODEL_VERSION_UNAVAILABLE``,
  this module statically excludes the XAU/JPY family modules, and the
  output structure contains no Game or setup object;
* the >$3,000 Asian-range no-go of the recovered native calibration
  refuses with ``ASIAN_RANGE_NO_GO`` (boundary edges classify per the
  frozen table: T3 is inclusive through $3,000);
* slot × tier range-left is conditioned on consumed states and only
  measured with an active slot (invariant #10);
* weekly/monthly anchor semantics are not materialized
  (III.3-GAP-8): those horizons are explicit ``UNRESOLVED`` sub-states
  with no invented anchors — never an invitation to import a BTC Game;
* no Gold Game setup vocabulary is reachable from this module.

Native AU/trigger/density constants enter only as canonical
calibration facts measured by III.2 — this runtime re-derives nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from app.forge.measurements import (
    AnchorEligibility,
    AnchorStatus,
    AuScaleMeasurement,
    DensityZoneMeasurement,
    PathMeasurement,
    RangeMeasurement,
    RemainingState,
    RuleMaterialization,
    SessionPhase,
    SessionPhaseState,
    ThresholdLevelsMeasurement,
    TierClassification,
)

from .contract import (
    AnchorStateRef,
    DirectionBias,
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

__all__ = ["BtcTrackerInputs", "BtcTrackerState", "evaluate"]


_CARD = "corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md"

_TIER_IDS: frozenset[str] = frozenset({"T1", "T2", "T3", "NO_GO"})

_ACTIVE_SLOTS: frozenset[SessionPhaseState] = frozenset(
    {SessionPhaseState.INSIDE_WINDOW, SessionPhaseState.CHECKPOINT_MATCHED}
)

_EARNED: frozenset[AnchorStatus] = frozenset(
    {AnchorStatus.ELIGIBLE, AnchorStatus.ACTIVE}
)


class BtcTrackerState(str, Enum):
    """Family-bounded daily model states (no free text)."""

    SEED_T1 = "SEED_T1"
    SEED_T2 = "SEED_T2"
    SEED_T3 = "SEED_T3"
    ASIAN_RANGE_NO_GO = "ASIAN_RANGE_NO_GO"


@dataclass(frozen=True)
class BtcTrackerInputs:
    """The family-typed measurement bundle (PLAN.md §7.3).

    Required at evaluation: ``seed`` (19:00–03:00 NY source frame) and
    ``tier`` (native BTC tier classification).  Weekly/monthly anchors
    are optional and only ever reflected, never synthesized.
    """

    seed: RangeMeasurement | None = None
    tier: TierClassification | None = None
    au: AuScaleMeasurement | None = None
    thresholds: ThresholdLevelsMeasurement | None = None
    density: DensityZoneMeasurement | None = None
    path: PathMeasurement | None = None
    slot_phase: SessionPhase | None = None
    weekly_anchor: AnchorEligibility | None = None
    monthly_anchor: AnchorEligibility | None = None


def _horizon_state(anchor: AnchorEligibility | None) -> str:
    """A horizon anchor is unresolved until a canonical rule exists."""
    if (
        anchor is not None
        and anchor.rule_materialization is RuleMaterialization.CANONICAL
        and anchor.status in _EARNED
    ):
        return anchor.status.value
    return "UNRESOLVED"


def _evaluate(request: ModelRequest, entry: "RegistryEntry") -> ModelOutput:
    inputs = request.inputs
    if not isinstance(inputs, BtcTrackerInputs):
        raise ModelContractError(
            f"{entry.model_key} evaluates BtcTrackerInputs, got "
            f"{type(inputs).__name__}"
        )

    seed = inputs.seed
    if seed is None:
        raise InputMeasurementMissingError(
            "BTC Tracker requires the 19:00-03:00 NY source-frame range"
        )
    tier = inputs.tier
    if tier is None:
        raise InputMeasurementMissingError(
            "BTC Tracker requires the native tier classification"
        )
    if tier.tier_id not in _TIER_IDS:
        raise ModelContractError(
            f"tier {tier.tier_id!r} is not part of the native BTC vocabulary"
        )

    warnings: list[WarningCode] = [WarningCode.GAP_UNRESOLVED]
    facts: list[ExplanationFact] = []

    # --- daily chain: seed → tier → AU --------------------------------------
    facts.append(
        make_fact(
            "BTC.SEED",
            "BTC.ASIAN_SOURCE_FRAME",
            _CARD,
            {
                "size": seed.size.value,
                "unit": seed.size.unit.value,
                "window_digest": seed.source_window.input_digest,
            },
        )
    )
    facts.append(
        make_fact(
            "BTC.TIER",
            "BTC.NATIVE_TIER_CLASSIFICATION",
            tier.source_ref,
            {
                "tier_id": tier.tier_id,
                "no_go": tier.no_go,
                "calibration_status": tier.calibration_status.value,
            },
        )
    )
    if inputs.au is not None:
        facts.append(
            make_fact(
                "BTC.AU_SCALE",
                "BTC.NATIVE_AU_SCALE",
                inputs.au.source_ref,
                {
                    "tier_id": inputs.au.tier_id,
                    "au": inputs.au.au.value,
                    "unit": inputs.au.au.unit.value,
                },
            )
        )

    # --- native threshold + density constants (measured by III.2) ----------
    levels: list[TypedLevel] = []
    if inputs.thresholds is not None:
        for index, magnitude in enumerate(inputs.thresholds.levels, start=1):
            levels.append(
                TypedLevel(
                    level_id=f"BTC_THRESHOLD_{index}",
                    level_kind=LevelKind.THRESHOLD,
                    family=inputs.thresholds.calibration_key.calibration_id,
                    level=magnitude.value,
                    price=None,
                    active=True,
                    source_ref=inputs.thresholds.source_ref,
                )
            )
    if inputs.density is not None:
        for zone in inputs.density.zones:
            facts.append(
                make_fact(
                    "BTC.DENSITY_ZONE",
                    "BTC.NATIVE_DENSITY_ZONES",
                    inputs.density.source_ref,
                    {
                        "zone_id": zone.zone_id,
                        "lower": zone.lower,
                        "upper": zone.upper,
                    },
                )
            )

    # --- slot × tier (03:00–19:00 window) -----------------------------------
    slot_active = (
        inputs.slot_phase is not None
        and inputs.slot_phase.state in _ACTIVE_SLOTS
    )
    facts.append(
        make_fact(
            "BTC.SLOT",
            "BTC.SLOT_TIER_SURFACE",
            _CARD,
            {
                "phase": (
                    inputs.slot_phase.state.value
                    if inputs.slot_phase is not None
                    else "UNRESOLVED"
                ),
                "tier_id": tier.tier_id,
                "slot_active": slot_active,
            },
        )
    )

    # --- consumed delivery states (path) -------------------------------------
    if inputs.path is not None:
        facts.append(
            make_fact(
                "BTC.PATH",
                "BTC.CONSUMED_STATES",
                _CARD,
                {
                    "levels_measured": len(inputs.path.levels),
                    "first_delivery": inputs.path.first_delivery is not None,
                    "remaining_state": inputs.path.remaining_state.value,
                },
            )
        )

    # --- weekly / monthly horizons: explicit, never invented ----------------
    anchor_states: list[AnchorStateRef] = []
    weekly_state = _horizon_state(inputs.weekly_anchor)
    monthly_state = _horizon_state(inputs.monthly_anchor)
    for fact_id, horizon, anchor, state in (
        ("BTC.WEEKLY_ANCHOR", "WEEKLY", inputs.weekly_anchor, weekly_state),
        ("BTC.MONTHLY_ANCHOR", "MONTHLY", inputs.monthly_anchor, monthly_state),
    ):
        payload: dict[str, object] = {
            "horizon": horizon,
            "state": state,
            "reason": "NOT_MATERIALIZED",
        }
        if anchor is not None:
            payload["anchor_id"] = anchor.anchor_id
            payload["refusal_code"] = anchor.refusal_code.value
            anchor_states.append(
                AnchorStateRef(
                    anchor_id=anchor.anchor_id,
                    status=anchor.status,
                    refusal_code=anchor.refusal_code,
                )
            )
        facts.append(make_fact(fact_id, "BTC.HORIZON_ANCHOR", _CARD, payload))

    # --- range-left: conditioned, active slot required ----------------------
    conditioned: tuple[str, ...] = (("BTC.PATH",) if inputs.path is not None else ())
    remainder = (
        inputs.path.remaining_distribution
        if inputs.path is not None
        and inputs.path.remaining_state is RemainingState.MEASURED
        and inputs.path.remaining_distribution is not None
        else None
    )
    if remainder is not None and slot_active:
        range_left = RangeLeftField(
            state=RemainingState.MEASURED,
            value=remainder,
            basis_fact_id="BTC.SLOT",
            conditioned_on=conditioned,
        )
    else:
        range_left = RangeLeftField.unresolved(conditioned_on=conditioned)
    facts.append(
        make_fact(
            "BTC.DISTRIBUTION",
            "BTC_SLOT_RANGE_LEFT",
            _CARD,
            {
                "range_left_state": range_left.state.value,
                "conditioned_on": "CONSUMED_STATES_AND_SLOT",
            },
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

    # --- state: native tier (no-go precedence) ------------------------------
    if tier.no_go or tier.tier_id == "NO_GO":
        state = BtcTrackerState.ASIAN_RANGE_NO_GO
        no_go: tuple[NoGoReason, ...] = (NoGoReason.ASIAN_RANGE_NO_GO,)
    else:
        state = BtcTrackerState(f"SEED_{tier.tier_id}")
        no_go = ()

    sub_states = (
        SubState(
            label="DAILY",
            layer=Layer.CROSS_LAYER,
            state=state.value,
            fact_ids=("BTC.SEED", "BTC.TIER", "BTC.SLOT"),
        ),
        SubState(
            label="WEEKLY",
            layer=Layer.CROSS_LAYER,
            state=weekly_state,
            fact_ids=("BTC.WEEKLY_ANCHOR",),
        ),
        SubState(
            label="MONTHLY",
            layer=Layer.CROSS_LAYER,
            state=monthly_state,
            fact_ids=("BTC.MONTHLY_ANCHOR",),
        ),
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
        active_ranges=(seed.source_window.input_digest,),
        active_anchor_states=tuple(anchor_states),
        levels=tuple(levels),
        range_left=range_left,
        no_go=no_go,
        warnings=tuple(warnings),
        claim_refs=(),
        evidence_refs=evidence_union(measurements),
        quality_state=resolve_quality(measurements),
        production_authorization=ProductionAuthorization.RESEARCH_ONLY,
        explanation_facts=tuple(facts),
        sub_states=sub_states,
        identity=request.identity(prior_ref(request)),
    )


def evaluate(request: ModelRequest) -> ModelOutput:
    """Evaluate one BTC Tracker request through the full replay pipeline."""
    from .replay import run_model

    return run_model(request)
