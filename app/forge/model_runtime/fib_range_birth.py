"""Fib / Range Birth runtime (Ch III.3.6).

Canonical chain: range-birth eligibility → active A/B range →
Alpha/Beta/Gamma/Delta sequence → coordinate/path → rekey/new range —
evaluated **behind the R15 gate**:

* the canonical Range Birth eligibility rule is not materialized
  (``ANCHOR_RULE_REGISTRY`` is empty; III.3-GAP-1).  Any
  eligibility-bearing claim under a ``NOT_MATERIALIZED`` rule refuses
  with ``RULE_NOT_MATERIALIZED``, including when coordinates are
  available — coordinate availability is never proof of structural
  eligibility;
* no anchor generator exists in this package: an absent anchor yields
  an explicit unresolved state and is never synthesized; the R11
  generic-pivot fallback is absent by construction, and an
  ``anchor_origin`` other than ``RANGE_BIRTH`` refuses;
* ``production_authorization`` stays ``RESEARCH_ONLY`` /
  ``NOT_AUTHORIZED`` for every output — production setup generation
  remains blocked and automation-ready claims are refused on input;
* rekey is a structural remapping (prior anchor → rekey event →
  successor mapping recorded), never "price touched 132";
* R11 over-generation negative evidence is referenced as the rationale
  and no R11 statistic ever enters an output.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from app.forge.measurements import (
    AnchorEligibility,
    AnchorStatus,
    CoordinateProjection,
    PathMeasurement,
    RangeMeasurement,
    RemainingState,
    RuleMaterialization,
)
from app.forge.measurements.anchors import AnchorRekey

from .contract import (
    AnchorStateRef,
    DirectionBias,
    ExplanationFact,
    LevelKind,
    ModelOutput,
    ModelRequest,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    TypedLevel,
    WarningCode,
    evidence_union,
    iter_measurements,
    make_fact,
    prior_ref,
    resolve_quality,
)
from .errors import (
    InputMeasurementMissingError,
    ModelContractError,
    RuleNotMaterializedError,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .registry import RegistryEntry

__all__ = ["FibRangeBirthInputs", "FibState", "evaluate"]


_CARD = "corpus/canonical/models/FIB_RANGE_BIRTH_MODEL_CARD_V1.md"

#: The only admissible anchor origin: an earned Range Birth.
_ALLOWED_ORIGIN = "RANGE_BIRTH"

#: Nested sequence/geometry families (card vocabulary).
_SEQUENCES: frozenset[str] = frozenset({"ALPHA", "BETA", "GAMMA", "DELTA"})

#: Negative evidence cited as the rationale for the gate (never stats).
_EV_R11 = "EV.FIB.R11.ANCHOR_OVERGEN.V1"

_EARNED: frozenset[AnchorStatus] = frozenset(
    {AnchorStatus.ELIGIBLE, AnchorStatus.ACTIVE}
)


class FibState(str, Enum):
    """Family-bounded model states (no free text)."""

    RANGE_BIRTH_UNRESOLVED = "RANGE_BIRTH_UNRESOLVED"
    RANGE_ACTIVE = "RANGE_ACTIVE"
    REKEY_REMAPPED = "REKEY_REMAPPED"
    ANCHOR_INVALIDATED = "ANCHOR_INVALIDATED"


@dataclass(frozen=True)
class FibRangeBirthInputs:
    """The family-typed measurement bundle (PLAN.md §7.3).

    Required at evaluation: ``anchor`` is the gate — when it is absent
    the state is explicit ``RANGE_BIRTH_UNRESOLVED`` (never
    synthesized); ``range``/``sequence``/``coordinates``/``path``/
    ``rekey`` are optional chain structure.
    """

    anchor: AnchorEligibility | None = None
    range: RangeMeasurement | None = None
    sequence: str | None = None
    coordinates: tuple[CoordinateProjection, ...] = ()
    path: PathMeasurement | None = None
    rekey: AnchorRekey | None = None
    anchor_origin: str = _ALLOWED_ORIGIN


def _evaluate(request: ModelRequest, entry: "RegistryEntry") -> ModelOutput:
    inputs = request.inputs
    if not isinstance(inputs, FibRangeBirthInputs):
        raise ModelContractError(
            f"{entry.model_key} evaluates FibRangeBirthInputs, got "
            f"{type(inputs).__name__}"
        )

    # --- G5: no arbitrary local pivot / generic anchor origin ---------------
    if inputs.anchor_origin != _ALLOWED_ORIGIN:
        raise ModelContractError(
            f"anchor origin {inputs.anchor_origin!r} is refused: only an "
            f"earned Range Birth may originate an anchor (R11 generic-pivot "
            f"fallback is forbidden)"
        )
    if inputs.sequence is not None and inputs.sequence not in _SEQUENCES:
        raise ModelContractError(
            f"sequence family {inputs.sequence!r} is outside the canonical "
            f"Alpha/Beta/Gamma/Delta vocabulary"
        )

    anchor = inputs.anchor
    if anchor is not None and anchor.automation_ready:
        raise ModelContractError(
            "an automation-ready claim is never a model-runtime input; "
            "automation approval belongs to III.5 governance"
        )

    # --- R15 gate: refuses any eligibility-bearing claim before anything ---
    unmaterialized = anchor is not None and (
        anchor.rule_materialization is RuleMaterialization.NOT_MATERIALIZED
        or anchor.refusal_code.value == "RULE_NOT_MATERIALIZED"
    )
    if unmaterialized:
        raise RuleNotMaterializedError(
            "the canonical R15 Range Birth eligibility rule is not "
            "materialized (III.3-GAP-1); eligibility-bearing evaluation "
            "refuses even with coordinates available"
        )

    warnings: list[WarningCode] = [WarningCode.GAP_UNRESOLVED]
    facts: list[ExplanationFact] = []

    # --- gate status travels on every output --------------------------------
    facts.append(
        make_fact(
            "FIB.R15_GATE",
            "FIB.RANGE_BIRTH_ELIGIBILITY",
            _CARD,
            {
                "rule_id": anchor.rule_id if anchor is not None else "R15.RANGE_BIRTH",
                "materialization": (
                    anchor.rule_materialization.value
                    if anchor is not None
                    else "NOT_MATERIALIZED"
                ),
                "production": "BLOCKED",
            },
        )
    )

    if anchor is not None:
        facts.append(
            make_fact(
                "FIB.RANGE_BIRTH",
                "FIB.ANCHOR_ELIGIBILITY",
                _CARD,
                {
                    "anchor_id": anchor.anchor_id,
                    "status": anchor.status.value,
                    "refusal_code": anchor.refusal_code.value,
                },
            )
        )

    # --- active A/B range ---------------------------------------------------
    if inputs.range is not None:
        facts.append(
            make_fact(
                "FIB.AB_RANGE",
                "FIB.ACTIVE_RANGE",
                _CARD,
                {
                    "high": inputs.range.high.value,
                    "low": inputs.range.low.value,
                    "size": inputs.range.size.value,
                    "window_digest": inputs.range.source_window.input_digest,
                },
            )
        )

    # --- sequence / geometry family -----------------------------------------
    if inputs.sequence is not None:
        facts.append(
            make_fact(
                "FIB.SEQUENCE",
                "FIB.SEQUENCE_FAMILY",
                _CARD,
                {"family": inputs.sequence},
            )
        )
    else:
        facts.append(
            make_fact(
                "FIB.SEQUENCE_UNRESOLVED",
                "FIB.SEQUENCE_FAMILY",
                _CARD,
                {"family": "UNRESOLVED"},
            )
        )

    # --- coordinates (projection authority stays in III.2) -------------------
    levels: list[TypedLevel] = []
    anchor_earned = anchor is not None and anchor.status in _EARNED
    for projection in inputs.coordinates:
        facts.append(
            make_fact(
                f"FIB.COORDINATE.{projection.family_id}",
                "FIB.COORDINATE_PATH",
                _CARD,
                {
                    "family_id": projection.family_id,
                    "level": projection.level,
                    "anchor_id": projection.anchor_id,
                },
            )
        )
        levels.append(
            TypedLevel(
                level_id=projection.coordinate_id,
                level_kind=LevelKind.COORDINATE,
                family=projection.family_id,
                level=projection.level,
                price=projection.projected_price.value,
                active=anchor_earned,
                source_ref=projection.family_source_ref,
            )
        )
    if inputs.coordinates and anchor is None:
        facts.append(
            make_fact(
                "FIB.COORDINATES_WITHOUT_ANCHOR",
                "FIB.COORDINATES_NEED_EARNED_RANGE",
                _CARD,
                {"eligibility": "UNRESOLVED"},
            )
        )

    # --- path ---------------------------------------------------------------
    conditioned: tuple[str, ...] = ()
    if inputs.path is not None:
        facts.append(
            make_fact(
                "FIB.PATH",
                "FIB.COORDINATE_PATH",
                _CARD,
                {
                    "levels_measured": len(inputs.path.levels),
                    "remaining_state": inputs.path.remaining_state.value,
                },
            )
        )
        conditioned = ("FIB.PATH",)

    # --- rekey: structural remapping, never a coordinate touch --------------
    if inputs.rekey is not None:
        mapping = ",".join(
            f"{source}={target}" for source, target in inputs.rekey.mapping
        )
        facts.append(
            make_fact(
                "FIB.REKEY_REMAPPING",
                "FIB.REKEY_REMAPPING",
                _CARD,
                {
                    "prior_anchor_id": inputs.rekey.anchor_id,
                    "successor_anchor_id": inputs.rekey.successor_anchor_id,
                    "mapping": mapping,
                },
            )
        )

    # --- R11 negative evidence: rationale only, never statistics ------------
    facts.append(
        make_fact(
            "FIB.R11_NEGATIVE_EVIDENCE",
            "FIB.R11_ANCHOR_OVERGENERATION",
            _CARD,
            {"evidence_id": _EV_R11, "stance": "NEGATIVE"},
        )
    )

    # --- range-left ----------------------------------------------------------
    remainder = (
        inputs.path.remaining_distribution
        if inputs.path is not None
        and inputs.path.remaining_state is RemainingState.MEASURED
        and inputs.path.remaining_distribution is not None
        else None
    )
    if remainder is not None:
        range_left = RangeLeftField(
            state=RemainingState.MEASURED,
            value=remainder,
            basis_fact_id="FIB.PATH",
            conditioned_on=conditioned,
        )
    else:
        range_left = RangeLeftField.unresolved(conditioned_on=conditioned)
    facts.append(
        make_fact(
            "FIB.DISTRIBUTION",
            "FIB_RANGE_LEFT",
            _CARD,
            {"range_left_state": range_left.state.value},
        )
    )

    # --- prior-state reference ----------------------------------------------
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

    # --- state / authorization -----------------------------------------------
    if inputs.rekey is not None:
        state = FibState.REKEY_REMAPPED
    elif anchor is None:
        state = FibState.RANGE_BIRTH_UNRESOLVED
    elif anchor.status is AnchorStatus.INVALIDATED:
        state = FibState.ANCHOR_INVALIDATED
    elif anchor.status in _EARNED:
        state = FibState.RANGE_ACTIVE
    else:
        state = FibState.RANGE_BIRTH_UNRESOLVED

    earned_chain = state in (FibState.RANGE_ACTIVE, FibState.REKEY_REMAPPED)
    authorization = (
        ProductionAuthorization.RESEARCH_ONLY
        if earned_chain
        else ProductionAuthorization.NOT_AUTHORIZED
    )
    no_go: tuple[NoGoReason, ...] = (
        () if earned_chain else (NoGoReason.RULE_NOT_MATERIALIZED,)
    )

    active_ranges: tuple[str, ...] = ()
    if inputs.range is not None:
        active_ranges = (inputs.range.source_window.input_digest,)
    elif anchor is not None and anchor.earned_range_reference:
        active_ranges = (anchor.earned_range_reference,)

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

    measurements = iter_measurements(inputs)
    evidence: list[str] = list(evidence_union(measurements))
    if _EV_R11 not in evidence:
        evidence.append(_EV_R11)

    return ModelOutput(
        model_id=request.model_id,
        model_version=request.model_version,
        model_runtime_version=entry.runtime_version,
        output_hash="",
        model_state=state.value,
        layer=entry.layer,
        direction_bias=DirectionBias.none(),
        active_ranges=active_ranges,
        active_anchor_states=anchor_states,
        levels=tuple(levels),
        range_left=range_left,
        no_go=no_go,
        warnings=tuple(warnings),
        claim_refs=(),
        evidence_refs=tuple(evidence),
        quality_state=resolve_quality(measurements),
        production_authorization=authorization,
        explanation_facts=tuple(facts),
        sub_states=(),
        identity=request.identity(prior_ref(request)),
    )


def evaluate(request: ModelRequest) -> ModelOutput:
    """Evaluate one Fib Range Birth request through the replay pipeline."""
    from .replay import run_model

    return run_model(request)
