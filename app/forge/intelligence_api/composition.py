"""Deterministic composition over ratified III.1-III.5 facts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace as _replace
from decimal import Decimal
from typing import Any, Mapping, Sequence

from app.forge.canonical import EvidenceStatus
from app.forge.intelligence_api.contracts import (
    Classifications,
    CurrentStatePayload,
    EvidenceLink,
    LevelView,
    LineageFacts,
    PathPayload,
    Provenance,
    QualityFacts,
    SetupContextPayload,
    Snapshot,
    SnapshotKey,
    TimeFacts,
    UnavailableSection,
)
from app.forge.intelligence_api.errors import RefusalError, SchemaIncompatibleError
from app.forge.intelligence_api.freshness import (
    FreshnessFacts,
    provider_status,
    quality_payload,
    short_circuit_codes,
    stale_label,
)
from app.forge.intelligence_api.identity import component_hashes, finalize
from app.forge.intelligence_api.refusals import (
    card_schema_status,
    require_machine_card as _require_machine_card,
    unavailable,
)
from app.forge.intelligence_api.serialization import content_hash
from app.forge.intelligence_api.versions import VIEW_CURRENT, VIEW_UNAVAILABLE
from app.forge.market_data.quality import DataOutcome
from app.forge.model_runtime.contract import Layer, ModelOutput
from app.forge.state_engine.delivery import DeliveryPath
from app.forge.state_engine.snapshot import MeasurementRef, StateSnapshot
from app.forge.state_engine.stand_down import StandDownRecord
from app.forge.setup_engine.contracts import SetupEligibility
from app.forge.setup_engine.eligibility import SetupEvaluation, SetupEvaluationRequest
from app.forge.setup_engine.registry import CanonicalSetupCard


@dataclass(frozen=True)
class CompositionInputs:
    key: SnapshotKey
    outputs: tuple[ModelOutput, ...] = ()
    state_snapshots: tuple[StateSnapshot, ...] = ()
    measurements: tuple[MeasurementRef, ...] = ()
    path: DeliveryPath | None = None
    setup: SetupEvaluation | None = None
    evidence: tuple[EvidenceLink, ...] = ()
    freshness: FreshnessFacts = FreshnessFacts(provider_configured=True)
    stand_down: StandDownRecord | None = None
    lineage: LineageFacts = field(default_factory=LineageFacts)
    engine_versions: tuple[tuple[str, str], ...] = ()
    registry_versions: tuple[tuple[str, str], ...] = ()
    source_window_digest: str | None = None
    fixture_identity: str | None = None
    materialized_rule: bool = True
    require_machine_card: bool = False
    explanation_facts: tuple[Any, ...] = ()
    view: str = VIEW_CURRENT


def _dec_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


def _direction(output: ModelOutput) -> dict[str, Any] | None:
    bias = output.direction_bias
    if bias.side is None:
        return None
    side = getattr(bias.side, "value", str(bias.side))
    return {
        "side": side,
        "basis_fact_id": bias.basis_fact_id,
        "evidence_refs": tuple(bias.evidence_refs),
    }


def _resolve_outputs(inputs: CompositionInputs) -> tuple[ModelOutput, ...]:
    if inputs.outputs:
        outputs = inputs.outputs
    else:
        outputs = ()
    for output in outputs:
        if output.identity.instrument_id != inputs.key.instrument_id:
            raise RefusalError("MALFORMED_REQUEST", detail="instrument_mismatch")
        if output.model_id != inputs.key.model_id:
            raise RefusalError("VERSION_DRIFT", detail="model_mismatch")
        if output.model_version != inputs.key.model_version:
            raise RefusalError("VERSION_DRIFT", detail="model_version_mismatch")
        if output.layer is not inputs.key.layer:
            raise RefusalError("MALFORMED_REQUEST", detail="layer_mismatch")
    return outputs


def _state_snapshot(inputs: CompositionInputs) -> StateSnapshot | None:
    if inputs.state_snapshots:
        return inputs.state_snapshots[0]
    return None


def _state_payload(inputs: CompositionInputs) -> CurrentStatePayload | None:
    outputs = _resolve_outputs(inputs)
    snapshot = _state_snapshot(inputs)
    if snapshot is not None:
        output = outputs[0] if outputs else None
        quality = {
            "outcome": snapshot.quality_state.value,
            "flags": tuple(sorted(flag.value for flag in (output.warnings if output else ()))),
        }
        return CurrentStatePayload(
            state=snapshot.active_state,
            layer=snapshot.layer,
            direction=_direction(output) if output is not None else None,
            active_ranges=tuple(snapshot.active_ranges),
            active_anchor_states=(),
            clock={
                "clock_id": snapshot.clock_id,
                "session_id": snapshot.session_id,
                "clock_registry_version": snapshot.clock_registry_version,
                "session_registry_version": snapshot.session_registry_version,
            },
            quality=quality,
            no_go=tuple(reason.value for reason in snapshot.no_go),
            stand_down=(
                inputs.stand_down.to_payload() if inputs.stand_down is not None else None
            ),
            warnings=tuple(code.value for code in snapshot.warnings),
            production_authorization=snapshot.production_authorization.value,
        )
    if not outputs:
        raise RefusalError("UNKNOWN_MODEL", detail="no_state_materialized")
    output = outputs[0]
    return CurrentStatePayload(
        state=output.model_state,
        layer=output.layer,
        direction=_direction(output),
        active_ranges=tuple(output.active_ranges),
        active_anchor_states=tuple(
            {
                "anchor_id": anchor.anchor_id,
                "status": anchor.status.value,
                "refusal_code": anchor.refusal_code.value,
            }
            for anchor in output.active_anchor_states
        ),
        clock={
            "clock_id": output.identity.clock_id,
            "session_id": output.identity.session_id,
            "clock_registry_version": output.identity.clock_registry_version,
            "session_registry_version": output.identity.session_registry_version,
        },
        quality={"outcome": output.quality_state.value, "flags": ()},
        no_go=tuple(reason.value for reason in output.no_go),
        stand_down=inputs.stand_down.to_payload() if inputs.stand_down is not None else None,
        warnings=tuple(code.value for code in output.warnings),
        production_authorization=output.production_authorization.value,
    )


def _level_views(inputs: CompositionInputs) -> tuple[LevelView, ...]:
    outputs = _resolve_outputs(inputs)
    views: list[LevelView] = []
    for output in outputs:
        for level in output.levels:
            if not level.source_ref:
                raise RefusalError("INSUFFICIENT_EVIDENCE", detail="level_source_missing")
            views.append(
                LevelView.from_level(
                    level,
                    model_id=output.model_id,
                    model_version=output.model_version,
                    layer=output.layer,
                )
            )
    return tuple(views)


def _path_payload(inputs: CompositionInputs) -> PathPayload | None:
    path = inputs.path
    if path is None:
        return None
    layer = inputs.key.layer
    deliveries = tuple({**record.to_payload(), "layer": layer.value} for record in path.deliveries)
    return PathPayload(
        clock_id=path.clock_id,
        targets=tuple(
            {
                "target_id": target.target_id,
                "side": target.side.value,
                "declared_order_index": target.declared_order_index,
                "layer": layer.value,
            }
            for target in path.targets
        ),
        deliveries=deliveries,
        first_delivery=path.first_delivery.to_payload() if path.first_delivery else None,
        terminal_reach=path.terminal_reach.value,
        ambiguous=path.ambiguous,
        unresolved_ordering=path.ambiguous,
        range_left=(
            {
                "state": inputs.outputs[0].range_left.state.value
                if hasattr(inputs.outputs[0].range_left.state, "value")
                else str(inputs.outputs[0].range_left.state),
                "value": _dec_text(inputs.outputs[0].range_left.value),
                "conditioned_on": tuple(inputs.outputs[0].range_left.conditioned_on),
                "basis_fact_id": inputs.outputs[0].range_left.basis_fact_id,
            }
            if inputs.outputs
            else None
        ),
        transition_summary=tuple(
            {
                "target_id": record.target_id,
                "order_index": record.order_index,
                "layer": layer.value,
            }
            for record in path.deliveries
        ),
        layer=layer,
    )


def _card_payload(card: CanonicalSetupCard | None) -> dict[str, Any] | None:
    if card is None:
        return None
    return {
        "setup_id": card.setup_id,
        "version": card.version,
        "status": card.status.value,
        "execution_class": card.execution_class.value,
        "exposure": card.exposure.value,
        "parent_model_ids": tuple(card.parent_model_ids),
        "source_card_ref": card.source_card_ref,
        "market_scope": tuple(card.market_scope),
    }


def _evidence_links(
    links: Sequence[Any],
    *,
    view_label: str,
    exposure: str | None,
) -> tuple[EvidenceLink, ...]:
    out: list[EvidenceLink] = []
    for link in links:
        status = getattr(link, "status", None)
        if not isinstance(status, EvidenceStatus):
            continue
        out.append(
            EvidenceLink(
                claim_id=getattr(link, "claim_id", None),
                evidence_id=getattr(link, "evidence_id", ""),
                status=status,
                relationship=bool(getattr(link, "relationship", False)),
                population_key=getattr(link, "population_key", None),
                view_label=view_label,
                exposure=None,
            )
        )
    return tuple(out)


def _automation_permitted(card: Any) -> bool:
    """Read the registry-wide automation flag without calling a bool."""

    if card is None:
        return False
    value = getattr(card, "automation_permitted", False)
    return bool(value() if callable(value) else value)


def setup_payload(
    evaluation: SetupEvaluation,
    *,
    view_label: str = VIEW_CURRENT,
    machine_card_required: bool = False,
) -> SetupContextPayload:
    if machine_card_required:
        _require_machine_card(evaluation.card)
    card = evaluation.card
    record = evaluation.record
    evidence: tuple[EvidenceLink, ...] = ()
    if card is not None:
        evidence = _evidence_links(card.evidence_refs, view_label=view_label, exposure=card.exposure.value)
    if record is not None and record.evidence_refs:
        evidence = evidence + _evidence_links(
            record.evidence_refs,
            view_label=view_label,
            exposure=record.product_exposure.value,
        )
    eligibility = evaluation.eligibility
    execution_class = (
        record.execution_class.value
        if record is not None
        else (card.execution_class.value if card is not None else None)
    )
    surface = evaluation.surface.value
    if surface == "PRODUCTION" and execution_class == "RESEARCH_ONLY":
        raise RefusalError("EXPOSURE_FORBIDDEN", detail="research_only_surface")
    if surface == "AUTOMATION" and not _automation_permitted(card):
        raise RefusalError("EXPOSURE_FORBIDDEN", detail="automation_not_approved")
    return SetupContextPayload(
        setup_id=evaluation.setup_id,
        setup_version=evaluation.setup_version,
        surface=evaluation.surface.value,
        eligibility=eligibility.value,
        reasons=tuple(code.value for code in evaluation.reasons),
        gates=tuple(
            {
                "gate": gate.gate,
                "verdict": gate.verdict.value,
                "codes": tuple(code.value for code in gate.codes),
            }
            for gate in evaluation.gates
        ),
        record=record.to_payload() if record is not None else None,
        card=_card_payload(card),
        card_schema_status=card_schema_status(card),
        no_go_refs=tuple(reason.value for reason in (record.no_go_refs if record else ())),
        evidence=evidence,
        automation_permitted=False,
        execution_class=execution_class,
        exposure=(
            record.product_exposure.value
            if record is not None
            else (card.exposure.value if card is not None else None)
        ),
    )


def _classifications(
    inputs: CompositionInputs, payload: SetupContextPayload | None
) -> Classifications:
    if payload is not None:
        execution_class = payload.execution_class
        exposure = payload.exposure
        return Classifications(
            execution_class=execution_class,
            exposure=exposure,
            research_only=execution_class == "RESEARCH_ONLY",
            manual_only=execution_class == "MANUAL_OPERATOR",
            automation_permitted=False,
        )
    research_only = any(
        output.production_authorization.value == "RESEARCH_ONLY" for output in inputs.outputs
    )
    return Classifications(
        execution_class=None,
        exposure=None,
        research_only=research_only,
        manual_only=False,
        automation_permitted=False,
    )


def _engine_versions(inputs: CompositionInputs) -> tuple[tuple[str, str], ...]:
    versions: dict[str, str] = dict(inputs.engine_versions)
    snapshot = _state_snapshot(inputs)
    if snapshot is not None:
        versions.setdefault("market_data_schema_version", snapshot.market_data_schema_version)
        versions.setdefault("clock_registry_version", snapshot.clock_registry_version)
        versions.setdefault("session_registry_version", snapshot.session_registry_version)
        versions.setdefault("measurement_engine_version", snapshot.measurement_engine_version)
        versions.setdefault("model_runtime_version", snapshot.model_runtime_version)
        versions.setdefault("state_engine_version", snapshot.state_engine_version)
    if inputs.outputs:
        versions.setdefault("model_runtime_version", inputs.outputs[0].model_runtime_version)
    if inputs.setup is not None and inputs.setup.record is not None:
        versions.setdefault("setup_engine_version", inputs.setup.record.engine_version)
        versions.setdefault("setup_contract_version", inputs.setup.record.setup_contract_version)
    return tuple(sorted(versions.items()))


def _strip_view_labels(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_view_labels(item)
            for key, item in value.items()
            if key != "view_label"
        }
    if isinstance(value, list):
        return [_strip_view_labels(item) for item in value]
    return value


def _neutral_hash(value: Any) -> str:
    from app.forge.intelligence_api.serialization import to_primitive

    return content_hash(_strip_view_labels(to_primitive(value)))


def _blocking_codes(inputs: CompositionInputs) -> tuple[str, ...]:
    codes = list(short_circuit_codes(inputs.freshness))
    if not inputs.materialized_rule and "RULE_NOT_MATERIALIZED" not in codes:
        codes.append("RULE_NOT_MATERIALIZED")
    return tuple(codes)


def compose(inputs: CompositionInputs) -> Snapshot:
    """Pure composition. Deny/affirm decisions belong to the policy gate."""

    codes = _blocking_codes(inputs)
    blocking = tuple(code for code in codes if code != "RULE_NOT_MATERIALIZED")
    if blocking:
        raise RefusalError(blocking[0], detail="freshness_gate")

    key = inputs.key
    outputs = _resolve_outputs(inputs)
    state = _state_payload(inputs)
    levels = _level_views(inputs)
    path = _path_payload(inputs)
    setup = setup_payload(
        inputs.setup,
        view_label=inputs.view,
        machine_card_required=inputs.require_machine_card,
    ) if inputs.setup is not None else None
    evidence = (
        tuple(_replace(link, view_label=inputs.view) for link in inputs.evidence)
        if inputs.evidence
        else None
    )
    if evidence is None and setup is not None:
        evidence = setup.evidence or None

    unresolved: list[UnavailableSection] = []
    if path is None:
        unresolved.append(unavailable("path", "PATH_UNAVAILABLE"))
    if setup is None:
        unresolved.append(unavailable("setup", "NO_SETUP_CONTEXT"))
    if evidence is None:
        unresolved.append(unavailable("evidence", "NO_EVIDENCE_LINKS"))
    if levels == ():
        unresolved.append(unavailable("levels", "LEVELS_EMPTY"))
    if not inputs.materialized_rule:
        unresolved.append(unavailable("state", "RULE_NOT_MATERIALIZED"))

    classifications = _classifications(inputs, setup)
    quality = QualityFacts(
        outcome=inputs.freshness.quality_outcome,
        flags=tuple(sorted(inputs.freshness.quality_flags, key=lambda flag: flag.value)),
        source_window_digest=inputs.source_window_digest,
        stale_label=stale_label(inputs.freshness),
        provider_status=provider_status(inputs.freshness),
    )
    time_facts = TimeFacts(
        as_of=key.as_of,
        data_cutoff=key.data_cutoff,
        calculation_timestamp=_calculation_timestamp(outputs, inputs),
        source_cutoffs=tuple(sorted(set(inputs.freshness.cutoffs))) or (key.data_cutoff,),
    )

    component_map: dict[str, str] = {
        "quality": _neutral_hash(
            quality_payload(inputs.freshness, source_window_digest=inputs.source_window_digest)
        ),
        "identity": _neutral_hash(key.payload()),
    }
    if state is not None:
        component_map["state"] = _neutral_hash(state)
    if levels:
        component_map["levels"] = _neutral_hash(levels)
    if path is not None:
        component_map["path"] = _neutral_hash(path)
    if setup is not None:
        component_map["setup"] = _neutral_hash(setup)
    if evidence is not None:
        component_map["evidence"] = _neutral_hash(evidence)

    provenance = Provenance(
        engine_versions=_engine_versions(inputs),
        registry_versions=tuple(sorted(inputs.registry_versions)),
        component_hashes=component_hashes(component_map),
        fixture_identity=inputs.fixture_identity,
    )

    snapshot = Snapshot(
        key=key,
        time=time_facts,
        quality=quality,
        classifications=classifications,
        provenance=provenance,
        state=state,
        levels=levels if levels else (),
        path=path,
        setup=setup,
        evidence=evidence,
        lineage=inputs.lineage,
        explanation_facts=tuple(
            fact if isinstance(fact, dict) else _fact_payload(fact)
            for fact in (inputs.explanation_facts or _output_facts(outputs))
        ),
        warnings=tuple(code for code in codes if code == "RULE_NOT_MATERIALIZED"),
        unresolved=tuple(unresolved),
        refusals=(),
        view=inputs.view,
    )
    if classifications.automation_permitted:
        raise RefusalError("MALFORMED_REQUEST", detail="automation_authority")
    return finalize(snapshot)


def _fact_payload(fact: Any) -> dict[str, Any]:
    return {
        "fact_id": fact.fact_id,
        "rule_id": fact.rule_id,
        "rule_version": fact.rule_version,
        "source_ref": fact.source_ref,
        "payload": tuple(tuple(pair) for pair in fact.payload),
    }


def _output_facts(outputs: Sequence[ModelOutput]) -> tuple[dict[str, Any], ...]:
    facts: list[dict[str, Any]] = []
    for output in outputs:
        facts.extend(_fact_payload(fact) for fact in output.explanation_facts)
    return tuple(facts)


def _calculation_timestamp(outputs: Sequence[ModelOutput], inputs: CompositionInputs) -> str:
    if outputs:
        return outputs[0].identity.calculation_timestamp.isoformat().replace("+00:00", "Z")
    snapshot = _state_snapshot(inputs)
    if snapshot is not None:
        return snapshot.calculation_timestamp.isoformat().replace("+00:00", "Z")
    return inputs.key.as_of


def unavailable_view(reason: str) -> Snapshot:
    """A refusal-shaped, content-free envelope; never an empty success payload."""

    raise RefusalError(reason)


__all__ = [
    "CompositionInputs",
    "compose",
    "setup_payload",
    "unavailable_view",
]
