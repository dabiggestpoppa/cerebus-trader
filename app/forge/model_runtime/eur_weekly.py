"""EUR Weekly Engine V1.1 runtime (Ch III.3.2).

Canonical chain: Monday/early-week seed → weekly tier → route/
range-left → hour × tier timing → outer-node state.  Frozen
protections:

* outer-node promotion only — a node that is not one of the registered
  outer nodes can never reach the promoted state;
* static/frozen after defined completion (OCC) — once frozen, every
  re-evaluation (including one keyed only on a matching prior state)
  returns the identical frozen state;
* the destination field is structurally ``NOT_THIS_LAYER`` — weekly
  path facts can never be laundered into higher-order destination
  evidence (the output carries no destination field at all; the
  boundary travels as a typed fact);
* recovered tier research is ``RESEARCH`` calibration status that
  travels on every output (warning + typed fact + evidence id) and is
  never emitted as a runtime statistic;
* hour × tier timing derives from III.1 session phases — unresolvable
  timing is an explicit unresolved fact, never an invented one;
* no win-rate, expectancy or any performance field exists.

Range-left has no source-supported weekly remainder measurement in
III.2, so it is explicit ``UNRESOLVED`` conditioned on the consumed
node — never a fabricated value.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from app.forge.measurements import (
    PeriodPhase,
    RangeMeasurement,  # noqa: F401  (documented sibling input type)
    RemainingState,
    SeedRange,
    SeedRangeKind,
    SessionPhase,
    SessionPhaseState,
    TierClassification,
    WeeklyPath,
)

from .contract import (
    DirectionBias,
    ExplanationFact,
    ModelOutput,
    ModelRequest,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
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

__all__ = ["EurWeeklyInputs", "EurWeeklyState", "evaluate"]


_CARD = "corpus/canonical/models/EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md"

_TIER_IDS: frozenset[str] = frozenset({"T1", "T2", "T3"})


class EurWeeklyState(str, Enum):
    """Family-bounded model states (no free text)."""

    ROUTE_OPEN = "ROUTE_OPEN"
    NODE_PROMOTED = "NODE_PROMOTED"
    FROZEN = "FROZEN"


@dataclass(frozen=True)
class EurWeeklyInputs:
    """The family-typed measurement bundle (PLAN.md §7.3).

    Required at evaluation: ``seed`` (WEEK) and ``tier``.
    """

    seed: SeedRange | None = None
    tier: TierClassification | None = None
    path: WeeklyPath | None = None
    session_phase: SessionPhase | None = None
    period_phase: PeriodPhase | None = None
    reached_node_id: str | None = None
    occ_frozen: bool = False


def _evaluate(request: ModelRequest, entry: "RegistryEntry") -> ModelOutput:
    inputs = request.inputs
    if not isinstance(inputs, EurWeeklyInputs):
        raise ModelContractError(
            f"{entry.model_key} evaluates EurWeeklyInputs, got "
            f"{type(inputs).__name__}"
        )

    seed = inputs.seed
    if seed is None:
        raise InputMeasurementMissingError(
            "EUR Weekly requires the early-week seed range measurement"
        )
    if seed.seed_kind is not SeedRangeKind.WEEK:
        raise ModelContractError(
            f"EUR Weekly requires a WEEK seed, got {seed.seed_kind.value}"
        )
    tier = inputs.tier
    if tier is None:
        raise InputMeasurementMissingError(
            "EUR Weekly requires the weekly tier classification"
        )
    if tier.tier_id not in _TIER_IDS or tier.no_go:
        raise ModelContractError(
            "the weekly tier input carries T1/T2/T3 only; no canonical weekly "
            "no-go rule exists to interpret another value"
        )

    warnings: list[WarningCode] = [WarningCode.RESEARCH_CALIBRATION]
    facts: list[ExplanationFact] = []

    # --- chain: seed → tier ------------------------------------------------
    facts.append(
        make_fact(
            "EUR_WEEKLY.SEED",
            "EUR_WEEKLY.SEED_RANGE",
            _CARD,
            {
                "size": seed.size.value,
                "unit": seed.size.unit.value,
                "bar_count": seed.bar_count,
                "window_digest": seed.source_window.input_digest,
            },
        )
    )
    status_fact_id = "EUR_WEEKLY.CALIBRATION_STATUS"
    evidence_id = (
        tier.evidence_refs[0] if tier.evidence_refs else "NONE"
    )
    facts.append(
        make_fact(
            "EUR_WEEKLY.TIER",
            "EUR_WEEKLY.TIER_CLASSIFICATION",
            tier.source_ref,
            {
                "tier_id": tier.tier_id,
                "calibration_status": tier.calibration_status.value,
                "evidence_id": evidence_id,
            },
        )
    )

    # --- route: outer nodes ------------------------------------------------
    node_ids: tuple[str, ...] = ()
    if inputs.path is not None:
        path = inputs.path
        node_ids = tuple(node.node_id for node in path.nodes)
        facts.append(
            make_fact(
                "EUR_WEEKLY.ROUTE",
                "EUR_WEEKLY.ROUTE_PATH",
                _CARD,
                {
                    "outer_nodes": len(path.nodes),
                    "state": path.state.value,
                    "calibration_status": (
                        path.calibration_status.value
                        if path.calibration_status is not None
                        else "UNRESOLVED"
                    ),
                },
            )
        )

    reached = inputs.reached_node_id
    promoted = reached is not None and reached in node_ids
    if reached is not None:
        if promoted:
            facts.append(
                make_fact(
                    "EUR_WEEKLY.NODE",
                    "EUR_WEEKLY.OUTER_NODE_PROMOTION",
                    _CARD,
                    {"node_id": reached, "promoted": True},
                )
            )
        else:
            facts.append(
                make_fact(
                    "EUR_WEEKLY.NODE_NOT_OUTER",
                    "EUR_WEEKLY.OUTER_NODE_PROMOTION",
                    _CARD,
                    {"node_id": reached, "promoted": False},
                )
            )

    frozen = bool(inputs.occ_frozen) or (
        request.prior_state is not None
        and request.prior_state.model_state == EurWeeklyState.FROZEN.value
    )
    if frozen:
        facts.append(
            make_fact(
                "EUR_WEEKLY.OCC_FROZEN",
                "EUR_WEEKLY.COMPLETION_FREEZE",
                _CARD,
                {"structure": "STATIC"},
            )
        )

    # --- hour × tier timing (from III.1 session/period phases only) ---------
    if inputs.session_phase is not None:
        facts.append(
            make_fact(
                "EUR_WEEKLY.HOUR_TIER_TIMING",
                "EUR_WEEKLY.HOUR_TIER_TIMING",
                _CARD,
                {
                    "source": "SESSION",
                    "phase": inputs.session_phase.state.value,
                    "tier_id": tier.tier_id,
                },
            )
        )
    elif inputs.period_phase is not None:
        facts.append(
            make_fact(
                "EUR_WEEKLY.HOUR_TIER_TIMING",
                "EUR_WEEKLY.HOUR_TIER_TIMING",
                _CARD,
                {
                    "source": "PERIOD",
                    "period": inputs.period_phase.period_kind.value,
                    "label": inputs.period_phase.period_label,
                    "tier_id": tier.tier_id,
                },
            )
        )
    else:
        warnings.append(WarningCode.TIMING_UNRESOLVED)
        facts.append(
            make_fact(
                "EUR_WEEKLY.HOUR_TIER_TIMING_UNRESOLVED",
                "EUR_WEEKLY.HOUR_TIER_TIMING",
                _CARD,
                {"source": "NONE", "phase": "UNRESOLVED", "tier_id": tier.tier_id},
            )
        )

    if inputs.period_phase is not None and inputs.session_phase is not None:
        # Both timing surfaces present: record the period identity as well.
        facts.append(
            make_fact(
                "EUR_WEEKLY.PERIOD_PHASE",
                "EUR_WEEKLY.PERIOD_PHASE",
                _CARD,
                {
                    "kind": inputs.period_phase.period_kind.value,
                    "label": inputs.period_phase.period_label,
                },
            )
        )
    elif inputs.period_phase is not None and inputs.session_phase is None:
        # Period identity already recorded inside the timing fact.
        pass

    # --- research status travels (C5) --------------------------------------
    facts.append(
        make_fact(
            status_fact_id,
            "EUR_WEEKLY.RESEARCH_STATUS",
            _CARD,
            {
                "status": tier.calibration_status.value,
                "evidence_id": evidence_id,
            },
        )
    )

    # --- destination boundary (C4: structurally NOT_THIS_LAYER) ------------
    facts.append(
        make_fact(
            "EUR_WEEKLY.DESTINATION_BOUNDARY",
            "EUR_WEEKLY_DESTINATION_BOUNDARY",
            _CARD,
            {"destination_evidence": "NOT_THIS_LAYER"},
        )
    )

    # --- range-left: explicit, never fabricated ----------------------------
    conditioned: tuple[str, ...] = (
        ("EUR_WEEKLY.NODE",) if promoted else ()
    )
    range_left = RangeLeftField.unresolved(conditioned_on=conditioned)
    facts.append(
        make_fact(
            "EUR_WEEKLY.DISTRIBUTION",
            "EUR_WEEKLY_REMAINING_DISTRIBUTION",
            _CARD,
            {
                "range_left_state": range_left.state.value,
                "reason": "NO_WEEKLY_REMAINING_MEASUREMENT",
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

    # --- state precedence: FROZEN > promoted > open ------------------------
    if frozen:
        state = EurWeeklyState.FROZEN
    elif promoted:
        state = EurWeeklyState.NODE_PROMOTED
    else:
        state = EurWeeklyState.ROUTE_OPEN

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
        active_anchor_states=(),
        levels=(),
        range_left=range_left,
        no_go=(),
        warnings=tuple(warnings),
        claim_refs=(),
        evidence_refs=evidence_union(measurements),
        quality_state=resolve_quality(measurements),
        production_authorization=ProductionAuthorization.RESEARCH_ONLY,
        explanation_facts=tuple(facts),
        sub_states=(),
        identity=request.identity(prior_ref(request)),
    )


def evaluate(request: ModelRequest) -> ModelOutput:
    """Evaluate one EUR Weekly request through the full replay pipeline."""
    from .replay import run_model

    return run_model(request)
