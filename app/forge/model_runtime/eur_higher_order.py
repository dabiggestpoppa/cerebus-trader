"""EUR Higher Order runtime (Ch III.3.3).

Canonical chain: quarter seed → D3 prior → M1 scale → M2 shaping →
M3 resolution → weekly/local handoff.  Frozen protections:

* L3 destination authority — the typed direction prior populates only
  from the L3 D3 input with its basis fact and evidence ref; weekly or
  daily facts can never populate it (they enter only as routing
  context);
* D3 agreement/completion statistics never appear as fields — the
  evidence ids travel, no percentage, win-rate or probability field
  exists anywhere on the output;
* M1 correlation is a typed magnitude fact with its evidence ref, not
  a probability;
* unfinished-side completion is an explicit conditional destination
  state (never a guarantee field);
* layer conflicts pass through as ``LayerConflict`` facts — the output
  structure is incapable of a confluence score;
* an evidence-bound parameter with no materialized definition yields an
  explicit ``UNRESOLVED`` state — never an invented constant
  (III.3-GAP-5).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from app.forge.measurements import (
    D1D3State,
    HigherOrderCheckpoint,
    HigherOrderState,
    LayerConflict,
    M1Scale,
    M2Shaping,
    SeedRange,
    SeedRangeKind,
    UnfinishedSide,
    UnfinishedSideState,
    WeeklyPath,
)

from .contract import (
    DirectionBias,
    DirectionSide,
    ExplanationFact,
    Layer,
    ModelOutput,
    ModelRequest,
    ProductionAuthorization,
    RangeLeftField,
    SubState,
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

__all__ = ["EurHigherOrderInputs", "EurHigherOrderState", "evaluate"]


_CARD = "corpus/canonical/models/EUR_HIGHER_ORDER_MODEL_CARD_V1.md"

#: Family-bound canonical evidence ids (read-only citations, PLAN §5.2).
_EV_D3 = "EV.EUR.HO.D3_DIRECTION.V1"
_EV_M1 = "EV.EUR.HO.M1_RANGE_CORR.V1"
_EV_UNFINISHED = "EV.EUR.HO.UNFINISHED_M3.V1"


class EurHigherOrderState(str, Enum):
    """Family-bounded model states (no free text)."""

    UNRESOLVED = "UNRESOLVED"
    PRIOR_DECLARED = "PRIOR_DECLARED"
    COMPLETION_CONDITIONAL = "COMPLETION_CONDITIONAL"
    M3_RESOLVED = "M3_RESOLVED"


@dataclass(frozen=True)
class EurHigherOrderInputs:
    """The family-typed measurement bundle (PLAN.md §7.3).

    Required at evaluation: ``quarter_seed`` (QUARTER) and ``d1d3``.
    ``m1``/``m2``/``d3_direction`` are evidence-bound chain parameters —
    when one is missing the state is explicit ``UNRESOLVED``, never an
    invented value.  ``unfinished`` is an optional conditional input.
    """

    quarter_seed: SeedRange | None = None
    d1d3: D1D3State | None = None
    m1: M1Scale | None = None
    m2: M2Shaping | None = None
    unfinished: UnfinishedSide | None = None
    checkpoints: tuple[HigherOrderCheckpoint, ...] = ()
    weekly_path: WeeklyPath | None = None
    conflicts: LayerConflict | None = None
    d3_direction: DirectionSide | None = None


def _evaluate(request: ModelRequest, entry: "RegistryEntry") -> ModelOutput:
    inputs = request.inputs
    if not isinstance(inputs, EurHigherOrderInputs):
        raise ModelContractError(
            f"{entry.model_key} evaluates EurHigherOrderInputs, got "
            f"{type(inputs).__name__}"
        )

    quarter_seed = inputs.quarter_seed
    if quarter_seed is None:
        raise InputMeasurementMissingError(
            "EUR Higher Order requires the quarter seed measurement"
        )
    if quarter_seed.seed_kind is not SeedRangeKind.QUARTER:
        raise ModelContractError(
            f"EUR Higher Order requires a QUARTER seed, got "
            f"{quarter_seed.seed_kind.value}"
        )
    d1d3 = inputs.d1d3
    if d1d3 is None:
        raise InputMeasurementMissingError(
            "EUR Higher Order requires the D1-D3 seed state measurement"
        )

    warnings: list[WarningCode] = []
    facts: list[ExplanationFact] = []
    cited: list[str] = []

    # --- chain: quarter seed ----------------------------------------------
    facts.append(
        make_fact(
            "EUR_HO.QUARTER_SEED",
            "EUR_HO.QUARTER_SEED",
            _CARD,
            {
                "size": quarter_seed.size.value,
                "unit": quarter_seed.size.unit.value,
                "window_digest": quarter_seed.source_window.input_digest,
            },
        )
    )

    # --- D3 prior (typed direction + basis + evidence; never a statistic) --
    direction_declared = inputs.d3_direction is not None
    facts.append(
        make_fact(
            "EUR_HO.D3_PRIOR",
            "EUR_HO.D3_DIRECTION_PRIOR",
            _CARD,
            {
                "direction": (
                    inputs.d3_direction.value
                    if direction_declared
                    else "UNDECLARED"
                ),
                "d1d3_state": d1d3.state.value,
                "evidence_id": _EV_D3 if direction_declared else "NONE",
            },
        )
    )
    if direction_declared:
        cited.append(_EV_D3)
    else:
        warnings.append(WarningCode.EVIDENCE_BOUND_PARAMETER)

    # --- M1 scale / M2 shaping (structure, never probability) --------------
    unresolved_parameters: list[str] = []
    if inputs.m1 is not None:
        facts.append(
            make_fact(
                "EUR_HO.M1_SCALE",
                "EUR_HO.M1_SCALE",
                _CARD,
                {
                    "state": inputs.m1.state.value,
                    "scale": (
                        inputs.m1.scale.value
                        if inputs.m1.scale is not None
                        else "UNRESOLVED"
                    ),
                    "evidence_id": _EV_M1,
                },
            )
        )
        cited.append(_EV_M1)
    else:
        unresolved_parameters.append("M1_SCALE")
    if inputs.m2 is not None:
        facts.append(
            make_fact(
                "EUR_HO.M2_SHAPING",
                "EUR_HO.M2_SHAPING",
                _CARD,
                {"state": inputs.m2.state.value},
            )
        )
    else:
        unresolved_parameters.append("M2_SHAPING")
    for parameter in unresolved_parameters:
        warnings.append(WarningCode.EVIDENCE_BOUND_PARAMETER)
        facts.append(
            make_fact(
                f"EUR_HO.PARAM_{parameter}",
                "EUR_HO_MISSING_PARAMETER",
                _CARD,
                {"parameter": parameter, "state": "UNRESOLVED"},
            )
        )

    # --- unfinished side: conditional destination evidence ------------------
    unfinished_conditional = (
        inputs.unfinished is not None
        and inputs.unfinished.side is not UnfinishedSideState.UNRESOLVED
    )
    if inputs.unfinished is not None:
        if unfinished_conditional:
            warnings.append(WarningCode.CONDITIONAL_DESTINATION)
            cited.append(_EV_UNFINISHED)
        facts.append(
            make_fact(
                "EUR_HO.UNFINISHED_SIDE",
                "EUR_HO_UNFINISHED_COMPLETION",
                _CARD,
                {
                    "side": inputs.unfinished.side.value,
                    "state": inputs.unfinished.state.value,
                    "evidence_id": (
                        _EV_UNFINISHED if unfinished_conditional else "NONE"
                    ),
                },
            )
        )

    # --- M3 resolution checkpoints -----------------------------------------
    all_reached = bool(inputs.checkpoints) and all(
        checkpoint.reached for checkpoint in inputs.checkpoints
    )
    for checkpoint in inputs.checkpoints:
        facts.append(
            make_fact(
                "EUR_HO.M3_CHECKPOINT",
                "EUR_HO_M3_RESOLUTION",
                checkpoint.source_ref,
                {
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "reached": checkpoint.reached,
                },
            )
        )

    # --- weekly handoff: routing context, layer ownership preserved --------
    sub_states: list[SubState] = []
    if inputs.weekly_path is not None:
        path = inputs.weekly_path
        facts.append(
            make_fact(
                "EUR_HO.WEEKLY_HANDOFF",
                "EUR_HO_WEEKLY_HANDOFF",
                _CARD,
                {"state": path.state.value, "context": "ROUTING"},
            )
        )
        sub_states.append(
            SubState(
                label="WEEKLY_HANDOFF",
                layer=Layer.L2,
                state=path.state.value,
                fact_ids=("EUR_HO.WEEKLY_HANDOFF",),
            )
        )

    # --- layer conflicts: facts only, no score field exists -----------------
    if inputs.conflicts is not None:
        for conflict in inputs.conflicts.conflicts:
            facts.append(
                make_fact(
                    "EUR_HO.LAYER_CONFLICT",
                    "EUR_HO_LAYER_CONFLICT",
                    _CARD,
                    {
                        "layer_a": conflict.layer_a.value,
                        "layer_b": conflict.layer_b.value,
                        "kind": conflict.kind.value,
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

    # --- state precedence ---------------------------------------------------
    upstream_unresolved = d1d3.state is HigherOrderState.UNRESOLVED
    if upstream_unresolved or not direction_declared or unresolved_parameters:
        if upstream_unresolved:
            warnings.append(WarningCode.EVIDENCE_BOUND_PARAMETER)
        state = EurHigherOrderState.UNRESOLVED
    elif all_reached:
        state = EurHigherOrderState.M3_RESOLVED
    elif unfinished_conditional:
        state = EurHigherOrderState.COMPLETION_CONDITIONAL
    else:
        state = EurHigherOrderState.PRIOR_DECLARED

    # --- evidence: read-only ids, deduplicated, deterministic order ---------
    evidence: list[str] = list(evidence_union(iter_measurements(inputs)))
    for ref in cited:
        if ref not in evidence:
            evidence.append(ref)

    direction = (
        DirectionBias(
            side=inputs.d3_direction,
            basis_fact_id="EUR_HO.D3_PRIOR",
            evidence_refs=(_EV_D3,) if direction_declared else (),
        )
        if direction_declared
        else DirectionBias.none()
    )

    return ModelOutput(
        model_id=request.model_id,
        model_version=request.model_version,
        model_runtime_version=entry.runtime_version,
        output_hash="",
        model_state=state.value,
        layer=entry.layer,
        direction_bias=direction,
        active_ranges=(quarter_seed.source_window.input_digest,),
        active_anchor_states=(),
        levels=(),
        range_left=RangeLeftField.unresolved(),
        no_go=(),
        warnings=tuple(warnings),
        claim_refs=(),
        evidence_refs=tuple(evidence),
        quality_state=resolve_quality(iter_measurements(inputs)),
        production_authorization=ProductionAuthorization.RESEARCH_ONLY,
        explanation_facts=tuple(facts),
        sub_states=tuple(sub_states),
        identity=request.identity(prior_ref(request)),
    )


def evaluate(request: ModelRequest) -> ModelOutput:
    """Evaluate one EUR Higher Order request through the replay pipeline."""
    from .replay import run_model

    return run_model(request)
