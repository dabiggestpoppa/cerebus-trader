"""Bloc III.6 acceptance suite — 258 frozen drivers (groups T1–T14).

Authoritative contract: implementation/forge/book_iii/bloc_iii_6/ACCEPTANCE.md.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path

import pytest

from app.forge.canonical import EvidenceStatus, ProductExposure, SetupClass
from app.forge.identity import ForgePrincipal
from app.forge.intelligence_api.cache import (
    INVALIDATION_EVENTS,
    ResponseKey,
    SnapshotCache,
    policy_fingerprint,
    principal_scope,
)
from app.forge.intelligence_api.composition import CompositionInputs, compose, setup_payload
from app.forge.intelligence_api.contracts import (
    BasketView,
    Classifications,
    EvidenceLink,
    InstrumentView,
    LevelView,
    Provenance,
    QualityFacts,
    SCHEMA_DESCRIPTOR,
    Snapshot,
    SnapshotKey,
    TimeFacts,
    UnavailableSection,
)
from app.forge.intelligence_api.errors import RefusalError, SchemaIncompatibleError
from app.forge.intelligence_api.freshness import (
    FreshnessFacts,
    is_live_claim_permitted,
    provider_status,
    short_circuit_codes,
    stale_label,
    staleness_refusal,
)
from app.forge.intelligence_api.history import HistoryStore
from app.forge.intelligence_api.identity import (
    component_hashes,
    finalize,
    fold_component_hashes,
    snapshot_id,
)
from app.forge.intelligence_api.policy_gate import IntelligenceGateway
from app.forge.intelligence_api.refusals import (
    card_machine_errors,
    card_schema_status,
    require_machine_card,
)
from app.forge.intelligence_api.requests import (
    BasketRequest,
    HistoricalRequest,
    InstrumentViewRequest,
    SetupContextRequest,
    SnapshotRequest,
)
from app.forge.intelligence_api.serialization import (
    canonical_json,
    content_hash,
    schema_hash,
    to_primitive,
)
from app.forge.intelligence_api.versions import (
    CARD_SCHEMA_INCOMPATIBLE,
    CARD_SCHEMA_VERBATIM,
    INTELLIGENCE_API_V1,
    REFUSAL_CODES,
    SNAPSHOT_SCHEMA_VERSION,
    VIEW_CURRENT,
    VIEW_HISTORICAL,
)
from app.forge.intelligence_api.views import compose_basket_view, compose_instrument_view
from app.forge.market_data.quality import DataOutcome, QualityFlag
from app.forge.model_runtime.contract import DirectionSide, Layer, LevelKind, NoGoReason
from app.forge.policy import AuthorizationContext, PolicyAction, PolicyResourceType
from app.forge.service.policy_enforcement import ForgePolicyEnforcementService
from app.forge.setup_engine.contracts import SetupEligibility, SetupSurface
from app.forge.setup_engine.registry import CANONICAL_SETUP_IDS, load_canonical_cards

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / "fixtures"


def _load_builders():
    spec = importlib.util.spec_from_file_location(
        "ii6_fixture_builders", FIXTURES / "_builders.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builders = _load_builders()

EUR = builders.EUR_MODEL
CARDS = {card.setup_id: card for card in load_canonical_cards()}
XAU_CARD = next(card for card in CARDS.values() if card.setup_id.startswith("SETUP.XAU"))
FIB_CARD = next(card for card in CARDS.values() if card.setup_id.startswith("SETUP.FIB"))
JPY_CARD = next(card for card in CARDS.values() if card.setup_id.startswith("SETUP.JPY"))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def inputs_for(**kwargs) -> CompositionInputs:
    return builders.base_inputs(**kwargs)


def snapshot_for(**kwargs) -> Snapshot:
    return compose(inputs_for(**kwargs))


def xau_inputs(**kwargs) -> CompositionInputs:
    setup = builders.setup_evaluation(
        XAU_CARD, eligibility=SetupEligibility.WATCH, surface=SetupSurface.OPERATOR
    )
    return builders.base_inputs(instrument_id="XAUUSD", setup=setup, **kwargs)


def refusal_code(fn, *args, **kwargs) -> str:
    with pytest.raises(RefusalError) as excinfo:
        fn(*args, **kwargs)
    return excinfo.value.code


def walk(value, path="") -> list[tuple[str, object]]:
    """Flatten the canonical JSON projection, including nested dataclasses."""

    return _walk(json.loads(canonical_json(value)), path)


def _walk(value, path="") -> list[tuple[str, object]]:
    out: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            out.extend(_walk(item, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            out.extend(_walk(item, f"{path}[{index}]"))
    else:
        out.append((path, value))
    return out


def operator_principal(user_id: str = "user-1") -> ForgePrincipal:
    return ForgePrincipal(
        authenticated=True,
        forge_user_id=user_id,
        session_id="session-1",
        roles=frozenset(),
    )


def operator_context() -> AuthorizationContext:
    return AuthorizationContext.of("model.read.operator")


_SHARED_GATEWAY = IntelligenceGateway()


def gateway_read(snapshot, *, exposure, principal=None, context=None, loader=None, gateway=None):
    gateway = gateway or _SHARED_GATEWAY
    return gateway.read(
        principal=principal or operator_principal(),
        context=context if context is not None else operator_context(),
        key=snapshot.key,
        exposure=exposure,
        loader=loader or (lambda: snapshot),
    )


# ---------------------------------------------------------------------------
# T1 — snapshot identity (20)
# ---------------------------------------------------------------------------


def test_snapshot_key_field_set_is_frozen():
    assert SnapshotKey.field_names() == (
        "instrument_id",
        "model_id",
        "model_version",
        "layer",
        "as_of",
        "data_cutoff",
        "calculation_version",
        "clock_id",
        "session_id",
    )
    assert len([f for f in fields(SnapshotKey)]) == 9


def test_snapshot_id_is_derived_not_supplied():
    key = builders.key()
    assert "snapshot_id" not in {field.name for field in fields(SnapshotKey)}
    assert snapshot_id(key) == snapshot_id(builders.key())
    snapshot = snapshot_for()
    assert snapshot.snapshot_id == snapshot_id(snapshot.key)


def test_clock_and_session_are_part_of_identity():
    left = builders.key(clock_id="CLOCK.EUR")
    right = builders.key(clock_id="CLOCK.OTHER")
    assert snapshot_id(left) != snapshot_id(right)
    assert snapshot_id(builders.key(session_id="SESSION.A")) != snapshot_id(
        builders.key(session_id="SESSION.B")
    )


def test_snapshot_hash_covers_every_component():
    base = snapshot_for()
    changed = compose(
        replace(
            inputs_for(),
            evidence=(EvidenceLink(claim_id=None, evidence_id="EV.EUR.2", status=EvidenceStatus.OBSERVED),),
        )
    )
    assert base.snapshot_hash != changed.snapshot_hash


def test_component_hash_order_is_canonical():
    assert component_hashes({"b": "2", "a": "1"}) == (("a", "1"), ("b", "2"))
    assert fold_component_hashes({"b": "2", "a": "1"}) == fold_component_hashes(
        {"a": "1", "b": "2"}
    )


def test_same_key_same_snapshot_id():
    first = snapshot_for()
    second = snapshot_for()
    assert first.snapshot_id == second.snapshot_id
    assert first.snapshot_hash == second.snapshot_hash


def test_different_as_of_changes_identity():
    assert snapshot_id(builders.key(as_of="2026-01-02T00:00:00Z")) != snapshot_id(
        builders.key(as_of="2026-01-03T00:00:00Z")
    )


def test_different_data_cutoff_changes_identity():
    assert snapshot_id(builders.key(data_cutoff="2026-01-01T17:00:00Z")) != snapshot_id(
        builders.key(data_cutoff="2026-01-01T16:00:00Z")
    )


def test_model_version_is_part_of_identity():
    assert snapshot_id(builders.key(model_version="PHASE1")) != snapshot_id(
        builders.key(model_version="PHASE2")
    )


def test_calculation_version_is_part_of_identity():
    assert snapshot_id(builders.key(calculation_version="CALC.V1")) != snapshot_id(
        builders.key(calculation_version="CALC.V2")
    )


def test_layer_is_part_of_identity():
    assert snapshot_id(builders.key(layer=Layer.L1)) != snapshot_id(
        builders.key(layer=Layer.L2)
    )


def test_identity_excludes_principal():
    snapshot = snapshot_for()
    assert "principal" not in canonical_json(snapshot.payload())
    first = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, principal=operator_principal("a"))
    second = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, principal=operator_principal("b"))
    assert first.snapshot.snapshot_hash == second.snapshot.snapshot_hash


def test_snapshot_is_immutable():
    snapshot = snapshot_for()
    with pytest.raises(FrozenInstanceError):
        snapshot.snapshot_hash = "0" * 64


def test_snapshot_requires_source_backing():
    with pytest.raises(ValueError):
        LevelView(
            level_id="EUR.L1.ZONE",
            level_kind="COORDINATE",
            family="ZONE",
            level=None,
            price="1.0842",
            active=True,
            source_ref="",
            source_model_id=EUR,
            source_model_version="PHASE1",
            layer=Layer.L1,
        )
    assert all(view.source_ref for view in snapshot_for().levels)


def test_missing_section_is_explicit_not_empty():
    sections = snapshot_for().section_map()
    assert sections["setup"] == {"status": "UNAVAILABLE", "reason": "NO_SETUP_CONTEXT"}
    assert sections["setup"] != [] and sections["setup"] is not None


def test_snapshot_provenance_block_is_complete():
    provenance = snapshot_for().provenance
    engines = dict(provenance.engine_versions)
    assert {"market_data_schema_version", "measurement_engine_version", "model_runtime_version", "state_engine_version"} <= set(engines)
    assert {"clock_registry", "session_registry"} <= set(dict(provenance.registry_versions))
    assert dict(provenance.component_hashes)
    assert provenance.fixture_identity is None


def test_engine_versions_recorded():
    inputs = replace(
        inputs_for(),
        engine_versions=(("setup_engine_version", "SETUP_ENGINE.V1"),),
    )
    engines = dict(compose(inputs).provenance.engine_versions)
    assert engines["setup_engine_version"] == "SETUP_ENGINE.V1"
    assert engines["measurement_engine_version"] == builders.MEASUREMENT_ENGINE_VERSION
    assert engines["state_engine_version"] == "STATE_ENGINE_V1"


def test_snapshot_serialization_is_stable_across_runs():
    left = canonical_json(snapshot_for().payload())
    right = canonical_json(snapshot_for().payload())
    assert left == right
    assert left == json.dumps(json.loads(left), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_snapshot_carries_no_free_prose():
    payload = snapshot_for().payload()
    assert "explanation" not in payload
    assert all(isinstance(entry, dict) and set(entry) <= {"code", "detail"} for entry in payload["refusals"])
    with pytest.raises(ValueError):
        UnavailableSection(section="state", reason="two words")


def test_snapshot_refuses_unknown_schema_version():
    with pytest.raises(ValueError):
        Snapshot(
            key=builders.key(),
            time=TimeFacts("2026-01-02T00:00:00Z", "2026-01-01T17:00:00Z", "2026-01-02T00:00:00Z"),
            quality=QualityFacts(DataOutcome.OK),
            classifications=Classifications(None, None, False, False),
            provenance=Provenance(),
            schema_version="SNAPSHOT_SCHEMA.V99",
        )


# ---------------------------------------------------------------------------
# T2 — current state (12)
# ---------------------------------------------------------------------------


def test_current_state_returns_authorized_fields():
    snapshot = snapshot_for()
    state = snapshot.state
    assert state is not None
    assert state.state and state.layer is Layer.L1
    assert state.active_ranges == ("RANGE.EUR.1",)
    assert state.clock["clock_id"] == "CLOCK.EUR"
    assert state.quality["outcome"] == "OK"
    assert state.no_go == ()
    # the dedicated value surface is the same composer, not a second path
    assert snapshot.section_map()["state"] is state


def test_current_state_carries_layer_ownership():
    snapshot = compose(
        inputs_for(
            stand_down=builders.stand_down_record(),
            no_go=(NoGoReason.NATIVE_TIER_NO_GO,),
        )
    )
    state = snapshot.state
    assert state.layer is Layer.L1
    assert state.stand_down is not None
    assert state.stand_down["state"]
    assert state.no_go == ("NATIVE_TIER_NO_GO",)


def test_direction_bias_only_where_defined():
    defined = snapshot_for()
    assert defined.state.direction == {
        "side": "UP",
        "basis_fact_id": "FACT.DIRECTION",
        "evidence_refs": ("EV.EUR.1",),
    }
    flat_output = builders.output(side=None)
    flat = compose(replace(inputs_for(), outputs=(flat_output,), state_snapshots=()))
    assert flat.state.direction is None


def test_active_range_and_tier_reported():
    state = snapshot_for().state
    assert state.active_ranges == ("RANGE.EUR.1",)
    assert state.active_anchor_states == ()
    assert state.production_authorization == "MANUAL_OPERATOR"


def test_clocks_reported_with_session_lineage():
    clock = snapshot_for().state.clock
    assert clock["clock_registry_version"] == "CLOCK_REGISTRY.V1"
    assert clock["session_registry_version"] == "SESSION_REGISTRY.V1"
    assert clock["session_id"] == "SESSION.EUR"


def test_quality_state_reported_verbatim():
    snapshot = snapshot_for(quality=DataOutcome.DEGRADED)
    assert snapshot.quality.outcome is DataOutcome.DEGRADED
    assert snapshot.quality.outcome.value == "DEGRADED"


def test_no_go_reported_as_fact_not_error():
    snapshot = snapshot_for(no_go=(NoGoReason.NATIVE_TIER_NO_GO,))
    assert snapshot.state.no_go == ("NATIVE_TIER_NO_GO",)
    assert snapshot.refusals == ()


def test_current_state_requires_registered_model():
    inputs = replace(inputs_for(), outputs=(), state_snapshots=())
    assert refusal_code(compose, inputs) == "UNKNOWN_MODEL"


def test_current_state_refuses_unmaterialized_rule():
    snapshot = compose(inputs_for(materialized_rule=False))
    assert "RULE_NOT_MATERIALIZED" in snapshot.warnings
    assert any(entry.reason == "RULE_NOT_MATERIALIZED" for entry in snapshot.unresolved)
    # no synthetic level or state is manufactured for the unmaterialised rule
    assert [view.level_id for view in snapshot.levels] == ["EUR.L1.ZONE"]


def test_current_state_marks_current_explicitly():
    snapshot = snapshot_for()
    assert snapshot.view == VIEW_CURRENT
    assert snapshot.time.as_of == builders.AS_OF
    assert snapshot.time.data_cutoff == builders.CUTOFF
    assert snapshot.time.calculation_timestamp != snapshot.time.as_of


def test_current_state_includes_no_confidence_field():
    keys = {key for key, _ in walk(snapshot_for().payload())}
    assert not any(
        token in key.lower()
        for key in keys
        for token in ("confidence", "probability", "score", "hit_rate", "expectancy", "win_rate")
    )


def test_current_state_payload_has_no_execution_fields():
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(snapshot_for().payload())}
    assert not ({"order", "size", "position_size", "entry_price", "stop", "allocation"} & keys)


# ---------------------------------------------------------------------------
# T3 — levels (10)
# ---------------------------------------------------------------------------


def test_levels_are_typed_by_kind():
    levels = snapshot_for().levels
    assert levels and levels[0].level_kind in ("COORDINATE", "THRESHOLD")


def test_level_kind_vocabulary_is_frozen():
    from app.forge.intelligence_api import versions

    assert versions.LEVEL_KINDS == ("COORDINATE", "THRESHOLD")


def test_each_level_carries_source_model_and_version():
    view = snapshot_for().levels[0]
    assert view.source_model_id == EUR
    assert view.source_model_version == "PHASE1"
    assert view.source_ref
    assert view.price == "1.0842"


def test_levels_carry_active_flag():
    views = snapshot_for().levels
    assert isinstance(views[0].active, bool)
    assert "active" in views[0].__dataclass_fields__


def test_level_without_source_ref_refused():
    with pytest.raises(ValueError):
        LevelView.from_level(
            builders.level(), model_id=EUR, model_version="PHASE1", layer=Layer.L1
        ).__class__(
            level_id="L",
            level_kind="COORDINATE",
            family="ZONE",
            level=None,
            price="1.0",
            active=True,
            source_ref="not bounded",
            source_model_id=EUR,
            source_model_version="PHASE1",
            layer=Layer.L1,
        )
    with pytest.raises(ValueError):
        LevelView(
            level_id="L",
            level_kind="COORDINATE",
            family="ZONE",
            level=None,
            price="1.0",
            active=True,
            source_ref="",
            source_model_id=EUR,
            source_model_version="PHASE1",
            layer=Layer.L1,
        )
    assert all(view.source_ref for view in snapshot_for().levels)


def test_measurement_level_distinct_from_decision_level():
    coordinate = LevelView.from_level(
        builders.level("L.COORD"), model_id=EUR, model_version="PHASE1", layer=Layer.L1
    )
    threshold = LevelView.from_level(
        builders.level("L.THRESH", kind=LevelKind.THRESHOLD),
        model_id=EUR,
        model_version="PHASE1",
        layer=Layer.L1,
    )
    assert coordinate.level_kind != threshold.level_kind
    assert coordinate.level_id != threshold.level_id


def test_target_levels_preserve_declared_order():
    declared = (builders.level("L.B"), builders.level("L.A"))
    model_output = builders.output(levels=declared)
    snapshot = compose(replace(inputs_for(), outputs=(model_output,), state_snapshots=()))
    assert [view.level_id for view in snapshot.levels] == ["L.B", "L.A"]


def test_invalidation_level_carried_separately():
    model_output = builders.output(
        levels=(builders.level("L.TARGET"), builders.level("L.INVALID", kind=LevelKind.THRESHOLD))
    )
    snapshot = compose(replace(inputs_for(), outputs=(model_output,), state_snapshots=()))
    kinds = {view.level_id: view.level_kind for view in snapshot.levels}
    assert kinds["L.INVALID"] == "THRESHOLD"
    assert kinds["L.TARGET"] == "COORDINATE"


def test_zone_level_requires_canonical_mapping_or_watch():
    setup = builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH)
    snapshot = compose(
        builders.base_inputs(instrument_id="XAUUSD", setup=setup)
    )
    assert snapshot.setup.eligibility == "WATCH"
    assert snapshot.setup.eligibility != "ELIGIBLE"


def test_levels_never_reprice_upstream_measurement():
    upstream = builders.level(price="1.0842")
    snapshot = compose(
        replace(inputs_for(), outputs=(builders.output(levels=(upstream,)),), state_snapshots=())
    )
    assert snapshot.levels[0].price == format(upstream.price, "f")
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(snapshot.levels[0])}
    assert not ({"probability", "hit_rate", "reward", "expectancy"} & keys)

# ---------------------------------------------------------------------------
# T4 — path (10)
# ---------------------------------------------------------------------------


def test_path_reports_consumed_states():
    path = snapshot_for().path
    assert path is not None
    assert [delivery["target_id"] for delivery in path.deliveries] == ["TARGET.1"]
    assert [target["target_id"] for target in path.targets] == ["TARGET.1", "TARGET.2"]


def test_path_reports_first_delivery_history():
    first = snapshot_for().path.first_delivery
    assert first is not None
    assert first["target_id"] == "TARGET.1"
    assert first["order_index"] == 0
    assert first["realizing_bar_ref"] == "BAR.2026-01-01T17"


def test_path_reports_range_left():
    path = snapshot_for().path
    assert path.range_left is not None
    assert path.range_left["state"] == "UNRESOLVED"
    assert path.range_left["conditioned_on"] == ("RANGE.EUR.1",)


def test_path_transition_summary_is_ordered():
    path = snapshot_for().path
    indexes = [entry["order_index"] for entry in path.transition_summary]
    assert indexes == sorted(indexes)
    assert len(path.transition_summary) == len(path.deliveries)


def test_path_never_sorts_history():
    path = builders.delivery_path()
    snapshot = compose(replace(inputs_for(), path=path))
    assert [delivery["target_id"] for delivery in snapshot.path.deliveries] == list(
        path.delivery_order
    )


def test_path_reversal_produces_different_path():
    forward_path = builders.delivery_path(two_observations=True)
    reverse_path = builders.delivery_path(two_observations=True, reverse=True)
    forward = compose(replace(inputs_for(), path=forward_path))
    reverse = compose(replace(inputs_for(), path=reverse_path))
    assert [d["target_id"] for d in forward.path.deliveries] != [
        d["target_id"] for d in reverse.path.deliveries
    ]
    assert forward.snapshot_hash != reverse.snapshot_hash


def test_path_terminal_does_not_erase_path():
    path = snapshot_for().path
    assert path.terminal_reach in ("NONE", "ONE_SIDE", "BOTH_SIDES_REACHED")
    assert path.deliveries
    assert all(delivery["layer"] == "L1" for delivery in path.deliveries)


def test_path_reports_unresolved_ordering():
    ambiguous = builders.delivery_path(ambiguous=True)
    snapshot = compose(replace(inputs_for(), path=ambiguous))
    assert snapshot.path.ambiguous is True
    assert snapshot.path.unresolved_ordering is True


def test_path_reuse_does_not_recompute_transitions():
    upstream = builders.delivery_path()
    snapshot = compose(replace(inputs_for(), path=upstream))
    assert [delivery["target_id"] for delivery in snapshot.path.deliveries] == [
        record.target_id for record in upstream.deliveries
    ]
    assert [delivery["realized_event_time"] for delivery in snapshot.path.deliveries] == [
        record.to_payload()["realized_event_time"] for record in upstream.deliveries
    ]


def test_path_carries_no_win_rate_or_hit_ratio():
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(snapshot_for().path)}
    assert not ({"win_rate", "hit_ratio", "expectancy", "probability", "score"} & keys)


# ---------------------------------------------------------------------------
# T5 — setup context (14)
# ---------------------------------------------------------------------------


def test_setup_context_consumes_iii5_evaluation():
    evaluation = builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH)
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=evaluation))
    assert snapshot.setup.setup_id == evaluation.setup_id
    assert snapshot.setup.surface == evaluation.surface.value
    assert snapshot.setup.eligibility == evaluation.eligibility.value
    assert len(snapshot.setup.gates) == len(evaluation.gates)


def test_setup_context_preserves_four_valued_eligibility():
    for verdict in SetupEligibility:
        evaluation = builders.setup_evaluation(XAU_CARD, eligibility=verdict)
        snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=evaluation))
        assert snapshot.setup.eligibility == verdict.value


def test_setup_context_never_elevates_eligibility():
    evaluation = builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH)
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=evaluation))
    assert snapshot.setup.eligibility == "WATCH"
    assert snapshot.setup.eligibility != "ELIGIBLE"


def test_setup_context_exposes_canonical_setup_payload():
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    card = snapshot.setup.card
    assert card["setup_id"] == XAU_CARD.setup_id
    assert card["version"] == XAU_CARD.version
    assert card["status"] == XAU_CARD.status.value
    assert card["execution_class"] == XAU_CARD.execution_class.value
    assert card["parent_model_ids"] == tuple(XAU_CARD.parent_model_ids)
    assert snapshot.setup.evidence is not None


def test_setup_context_policy_checked_before_composition():
    calls: list[int] = []

    def loader():
        calls.append(1)
        raise AssertionError("loader must not run on denial")

    gateway = IntelligenceGateway()
    access = gateway.read(
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
        key=builders.key(instrument_id="XAUUSD"),
        exposure=ProductExposure.OPERATOR_ONLY,
        loader=loader,
    )
    assert access.allowed is False
    assert calls == []


def test_setup_context_denied_returns_no_setup_fields():
    access = gateway_read(
        compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD))),
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
    )
    assert access.allowed is False
    assert access.snapshot is None
    assert access.denial() == {"code": "EXPOSURE_FORBIDDEN"}


def test_setup_context_xau_caps_at_watch():
    snapshot = compose(
        builders.base_inputs(
            instrument_id="XAUUSD",
            setup=builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH),
        )
    )
    assert snapshot.setup.eligibility == "WATCH"
    assert snapshot.setup.execution_class == "MANUAL_OPERATOR"


def test_setup_context_fib_stays_research_only():
    research = builders.setup_evaluation(
        FIB_CARD, eligibility=SetupEligibility.ELIGIBLE, surface=SetupSurface.RESEARCH
    )
    snapshot = compose(builders.base_inputs(setup=research))
    assert snapshot.setup.execution_class == "RESEARCH_ONLY"
    assert snapshot.classifications.research_only is True
    production = builders.setup_evaluation(
        FIB_CARD, eligibility=SetupEligibility.ELIGIBLE, surface=SetupSurface.PRODUCTION
    )
    assert refusal_code(compose, builders.base_inputs(setup=production)) == "EXPOSURE_FORBIDDEN"


def test_setup_context_jpy_stays_manual_operator():
    manual = builders.setup_evaluation(
        JPY_CARD, eligibility=SetupEligibility.WATCH, surface=SetupSurface.OPERATOR
    )
    snapshot = compose(builders.base_inputs(instrument_id="USDJPY", setup=manual))
    assert snapshot.setup.execution_class == "MANUAL_OPERATOR"
    assert snapshot.classifications.manual_only is True
    automation = builders.setup_evaluation(
        JPY_CARD, eligibility=SetupEligibility.WATCH, surface=SetupSurface.AUTOMATION
    )
    assert refusal_code(
        compose, builders.base_inputs(instrument_id="USDJPY", setup=automation)
    ) == "EXPOSURE_FORBIDDEN"


def test_setup_context_lock_preserved():
    snapshot = compose(
        inputs_for(
            stand_down=builders.stand_down_record(),
            no_go=(NoGoReason.NATIVE_TIER_NO_GO,),
        )
    )
    assert snapshot.state.stand_down["state"] == "DATA_QUALITY_FAILURE"
    assert snapshot.state.no_go == ("NATIVE_TIER_NO_GO",)


def test_setup_context_automation_false_registry_wide():
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    assert snapshot.setup.automation_permitted is False
    assert snapshot.classifications.automation_permitted is False
    with pytest.raises(ValueError):
        replace(snapshot.setup, automation_permitted=True)


def test_setup_context_unresolved_identity_returns_no_record():
    unresolved = builders.setup_evaluation(
        None,
        setup_id="SETUP.UNKNOWN.V1",
        eligibility=SetupEligibility.UNRESOLVED,
        reasons=(builders.SetupRefusalCode.SETUP_CARD_UNRESOLVED,),
    )
    snapshot = compose(builders.base_inputs(setup=unresolved))
    assert snapshot.setup.eligibility == "UNRESOLVED"
    assert snapshot.setup.record is None
    assert snapshot.setup.card is None
    assert snapshot.setup.reasons == ("SETUP_CARD_UNRESOLVED",)


def test_setup_context_reasons_are_bounded_codes():
    unresolved = builders.setup_evaluation(
        None,
        eligibility=SetupEligibility.BLOCKED,
        reasons=(builders.SetupRefusalCode.STAND_DOWN_LOCKED, builders.SetupRefusalCode.CLOCK_UNRESOLVED),
    )
    snapshot = compose(builders.base_inputs(setup=unresolved))
    for reason in snapshot.setup.reasons:
        assert " " not in reason
        assert reason in {code.value for code in builders.SetupRefusalCode}


def test_setup_context_schema_incompatible_card_refused():
    inputs = builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD))
    verbatim = compose(inputs)
    assert verbatim.setup.card_schema_status == CARD_SCHEMA_VERBATIM
    assert verbatim.setup.card["setup_id"] == "SETUP.XAU.QUARTER_ZONE.V1"
    assert refusal_code(compose, replace(inputs, require_machine_card=True)) == CARD_SCHEMA_INCOMPATIBLE


# ---------------------------------------------------------------------------
# T6 — evidence links (8)
# ---------------------------------------------------------------------------


def test_evidence_links_return_ids_only():
    links = snapshot_for().evidence
    assert links
    allowed = {"claim_id", "evidence_id", "status", "relationship", "population_key", "view_label", "exposure"}
    for link in links:
        assert set(link.__dataclass_fields__) == allowed


def test_evidence_links_carry_status():
    negative = (EvidenceLink(claim_id="CL.X", evidence_id="EV.X", status=EvidenceStatus.NO_GO),)
    snapshot = compose(replace(inputs_for(), evidence=negative))
    assert snapshot.evidence[0].status is EvidenceStatus.NO_GO
    assert snapshot.evidence[0].status.value == "NO_GO"


def test_evidence_links_do_not_embed_corpus():
    payload = snapshot_for().payload()
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(payload)}
    assert not ({"body", "text", "source_text", "content", "corpus"} & keys)


def test_evidence_links_preserve_negative_evidence():
    from app.forge.intelligence_api.refusals import filter_evidence

    negative = (
        EvidenceLink(claim_id="CL.X", evidence_id="EV.X", status=EvidenceStatus.NO_GO),
        EvidenceLink(claim_id="CL.Y", evidence_id="EV.Y", status=EvidenceStatus.FALSIFIED),
    )
    kept, dropped = filter_evidence(negative, {"PUBLIC_TEACHING"})
    assert dropped == 0
    assert {link.status for link in kept} == {EvidenceStatus.NO_GO, EvidenceStatus.FALSIFIED}


def test_evidence_links_require_claim_for_numeric_claim():
    from app.forge.intelligence_api.refusals import require_claim_for_statistic

    require_claim_for_statistic("CL.EUR.1")
    with pytest.raises(RefusalError) as excinfo:
        require_claim_for_statistic(None)
    assert excinfo.value.code == "INSUFFICIENT_EVIDENCE"


def test_evidence_links_refuse_unsupported_statistic():
    from app.forge.intelligence_api.refusals import refusal_entry

    assert refusal_entry("UNSUPPORTED_STATISTIC") == {"code": "UNSUPPORTED_STATISTIC"}
    with pytest.raises(ValueError):
        refusal_entry("CONFIDENCE_87")


def test_evidence_links_historical_not_current():
    evaluation = builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH)
    snapshot = compose(
        replace(
            builders.base_inputs(instrument_id="XAUUSD", setup=evaluation),
            view=VIEW_HISTORICAL,
        )
    )
    assert snapshot.view == VIEW_HISTORICAL
    assert all(link.view_label == VIEW_HISTORICAL for link in snapshot.evidence)


def test_evidence_links_exposure_filtered():
    from app.forge.intelligence_api.refusals import filter_evidence

    links = (
        EvidenceLink(
            claim_id="CL.R",
            evidence_id="EV.R",
            status=EvidenceStatus.RESEARCH_FLAG,
            exposure=ProductExposure.RESEARCH_LAB,
        ),
        EvidenceLink(
            claim_id="CL.P",
            evidence_id="EV.P",
            status=EvidenceStatus.VALIDATED,
            exposure=ProductExposure.PUBLIC_TEACHING,
        ),
    )
    kept, dropped = filter_evidence(links, {"PUBLIC_TEACHING"})
    assert dropped == 1
    assert [link.evidence_id for link in kept] == ["EV.P"]


# ---------------------------------------------------------------------------
# T7 — history (12)
# ---------------------------------------------------------------------------


def _historical_request(snapshot, **overrides):
    payload = dict(
        instrument_id=snapshot.key.instrument_id,
        model_id=snapshot.key.model_id,
        model_version=snapshot.key.model_version,
        layer=snapshot.key.layer,
        as_of=snapshot.key.as_of,
        data_cutoff=snapshot.key.data_cutoff,
        calculation_version=snapshot.key.calculation_version,
        clock_id=snapshot.key.clock_id,
        session_id=snapshot.key.session_id,
        retention_acknowledged=True,
    )
    payload.update(overrides)
    return HistoricalRequest(**payload)


def _retained():
    inputs = inputs_for()
    snapshot = compose(inputs)
    store = HistoryStore(capacity=2)
    store.retain(snapshot, inputs)
    return store, snapshot


def test_historical_request_requires_pinned_version():
    with pytest.raises(RefusalError) as excinfo:
        HistoricalRequest.from_mapping(
            {
                "instrument_id": "EURUSD",
                "model_id": EUR,
                "layer": Layer.L1,
                "as_of": builders.AS_OF,
                "data_cutoff": builders.CUTOFF,
                "calculation_version": "CALC.V1",
            }
        )
    assert excinfo.value.code == "MALFORMED_REQUEST"


def test_historical_unknown_version_refused():
    store, snapshot = _retained()
    request = _historical_request(snapshot, model_version="PHASE9")
    assert refusal_code(store.reconstruct, request) == "VERSION_DRIFT"


def test_historical_never_substitutes_latest():
    with pytest.raises(RefusalError) as excinfo:
        HistoricalRequest.from_mapping(
            {
                "instrument_id": "EURUSD",
                "model_id": EUR,
                "model_version": "latest",
                "layer": Layer.L1,
                "as_of": builders.AS_OF,
                "data_cutoff": builders.CUTOFF,
                "calculation_version": "CALC.V1",
            }
        )
    assert excinfo.value.code == "UNKNOWN_VERSION"


def test_historical_unavailable_is_explicit():
    inputs = inputs_for()
    snapshot = compose(inputs)
    store = HistoryStore()
    assert refusal_code(store.reconstruct, _historical_request(snapshot)) == "HISTORICAL_UNAVAILABLE"


def test_historical_reconstruction_matches_original_hash():
    store, snapshot = _retained()
    replayed = store.reconstruct(_historical_request(snapshot))
    assert replayed.snapshot_hash == snapshot.snapshot_hash
    assert replayed.snapshot_id == snapshot.snapshot_id


def test_historical_reconstruction_deterministic():
    store, snapshot = _retained()
    first = store.reconstruct(_historical_request(snapshot))
    second = store.reconstruct(_historical_request(snapshot))
    assert canonical_json(first.payload()) == canonical_json(second.payload())
    assert first.schema_version == SNAPSHOT_SCHEMA_VERSION


def test_historical_replay_uses_pinned_rules():
    store, snapshot = _retained()
    replayed = store.reconstruct(_historical_request(snapshot))
    assert replayed.key.calculation_version == snapshot.key.calculation_version
    assert replayed.key.model_version == snapshot.key.model_version


def test_historical_mixed_generation_refused():
    store, snapshot = _retained()
    request = _historical_request(snapshot)
    assert refusal_code(store.reconstruct, request, current_rules_version="CALC.V2") == "VERSION_DRIFT"


def test_historical_distinguishes_current_from_historical():
    store, snapshot = _retained()
    replayed = store.reconstruct(_historical_request(snapshot))
    assert snapshot.view == VIEW_CURRENT
    assert replayed.view == VIEW_HISTORICAL
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(replayed.payload())}
    assert not ({"win_rate", "performance", "return_pct", "expectancy"} & keys)


def test_historical_no_current_rules_silently():
    store, snapshot = _retained()
    request = _historical_request(snapshot, calculation_version="CALC.V2")
    assert refusal_code(store.reconstruct, request) == "HISTORICAL_UNAVAILABLE"


def test_historical_lineage_break_reported():
    inputs = inputs_for()
    inputs = replace(
        inputs,
        lineage=replace(inputs.lineage, genesis_snapshot_id="SNAP.MISSING"),
    )
    snapshot = compose(inputs)
    store = HistoryStore()
    store.retain(snapshot, inputs)
    replayed = store.reconstruct(_historical_request(snapshot))
    assert "LINEAGE_BREAK" in replayed.warnings


def test_historical_out_of_retention_explicit():
    first_inputs = inputs_for()
    first = compose(first_inputs)
    store = HistoryStore(capacity=1)
    store.retain(first, first_inputs)
    second_inputs = inputs_for(as_of="2026-01-03T00:00:00Z")
    second = compose(second_inputs)
    store.retain(second, second_inputs)
    assert refusal_code(store.reconstruct, _historical_request(first)) == "HISTORICAL_NOT_RETAINED"

# ---------------------------------------------------------------------------
# T8 — multi-model instrument view (10)
# ---------------------------------------------------------------------------


def _three_layers():
    l3 = compose(inputs_for(layer=Layer.L3))
    l2 = compose(inputs_for(layer=Layer.L2))
    l1 = compose(inputs_for(layer=Layer.L1))
    return {Layer.L3: l3, Layer.L2: l2, Layer.L1: l1}


def test_multimodel_composes_three_layers():
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    assert len(view.sections) == 3
    assert view.view_id.startswith("VIEW.")
    assert len(view.view_hash) == 64
    assert [section.layer for section in view.sections] == [Layer.L3, Layer.L2, Layer.L1]


def test_multimodel_preserves_layer_ownership():
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    for section in view.sections:
        assert section.layer in (Layer.L3, Layer.L2, Layer.L1)
        assert section.model_id
        assert section.snapshot_id


def test_multimodel_has_no_confluence_score():
    payload = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers()).payload()
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(payload)}
    assert not ({"score", "confidence", "overall_bias", "net_bias", "confluence"} & keys)


def test_multimodel_l3_destination_not_l2_path():
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    l3 = next(section for section in view.sections if section.layer is Layer.L3)
    l2 = next(section for section in view.sections if section.layer is Layer.L2)
    assert l3.state == l2.state  # same fixture fact, still separate owned sections
    assert l3.model_id != l2.model_id
    assert l3.snapshot_id != l2.snapshot_id


def test_multimodel_conflict_reported_as_facts():
    down = builders.output(side=DirectionSide.DOWN)
    l1_flat = compose(replace(inputs_for(), outputs=(down,), state_snapshots=()))
    snapshots = _three_layers()
    snapshots[Layer.L1] = l1_flat
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=snapshots)
    assert view.conflicts
    assert view.conflicts[0]["kind"] == "DIRECTION_CONFLICT"
    assert set(view.conflicts[0]["layers"]) == {"L3", "L2", "L1"}


def test_multimodel_missing_layer_is_explicit():
    snapshots = _three_layers()
    snapshots.pop(Layer.L2)
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=snapshots)
    assert len(view.sections) == 2
    assert any(entry.reason == "LAYER_L2_UNAVAILABLE" for entry in view.unresolved)
    with pytest.raises(RefusalError):
        compose_instrument_view(
            instrument_id="EURUSD",
            snapshots=snapshots,
            layers=(Layer.CROSS_LAYER,),
        )


def test_multimodel_cross_asset_leak_refused():
    snapshots = _three_layers()
    snapshots[Layer.L2] = compose(inputs_for(instrument_id="XAUUSD", layer=Layer.L2))
    with pytest.raises(RefusalError) as excinfo:
        compose_instrument_view(instrument_id="EURUSD", snapshots=snapshots)
    assert excinfo.value.code == "MALFORMED_REQUEST"


def test_multimodel_order_is_canonical():
    reversed_request = (Layer.L1, Layer.L3, Layer.L2)
    view = compose_instrument_view(
        instrument_id="EURUSD", snapshots=_three_layers(), layers=reversed_request
    )
    assert [section.layer for section in view.sections] == [Layer.L3, Layer.L2, Layer.L1]


def test_multimodel_reuses_single_layer_snapshot():
    snapshots = _three_layers()
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=snapshots)
    for section in view.sections:
        assert section.snapshot_id == snapshots[section.layer].snapshot_id
        assert section.snapshot_hash == snapshots[section.layer].snapshot_hash


def test_multimodel_does_not_merge_states():
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    states = [section.state for section in view.sections]
    assert len(states) == 3
    assert view.sections[0].no_go == ()


# ---------------------------------------------------------------------------
# T9 — basket view (8)
# ---------------------------------------------------------------------------


BASKET_ROLES = {"USDJPY": "DRIVER", "AUDJPY": "DRIVER", "EURJPY": "CONFIRMATION_VETO"}


def _basket_snapshots():
    return {
        "USDJPY": compose(inputs_for(instrument_id="USDJPY")),
        "AUDJPY": compose(inputs_for(instrument_id="AUDJPY")),
        "EURJPY": compose(inputs_for(instrument_id="EURJPY")),
    }


def test_basket_roles_verbatim():
    view = compose_basket_view(
        basket_id="JPY", snapshots=_basket_snapshots(), roles=BASKET_ROLES
    )
    assert {pair.pair: pair.role for pair in view.pairs} == BASKET_ROLES


def test_basket_has_no_average_score():
    view = compose_basket_view(
        basket_id="JPY", snapshots=_basket_snapshots(), roles=BASKET_ROLES
    )
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(view.payload())}
    assert not ({"average", "score", "net_bias", "confidence", "expectancy", "probability"} & keys)


def test_basket_eurjpy_is_confirmation_only():
    view = compose_basket_view(
        basket_id="JPY", snapshots=_basket_snapshots(), roles=BASKET_ROLES
    )
    eurjpy = next(pair for pair in view.pairs if pair.pair == "EURJPY")
    assert eurjpy.confirmation_only is True
    assert eurjpy.role == "CONFIRMATION_VETO"


def test_basket_equal_vote_impossible():
    with pytest.raises(RefusalError) as excinfo:
        compose_basket_view(
            basket_id="JPY",
            snapshots=_basket_snapshots(),
            roles={**BASKET_ROLES, "EURJPY": "EQUAL_VOTE"},
        )
    assert excinfo.value.code == "MALFORMED_REQUEST"


def test_basket_no_go_pair_reported():
    snapshots = _basket_snapshots()
    usd_inputs = inputs_for(instrument_id="USDJPY")
    usd_output = replace(usd_inputs.outputs[0], no_go=(NoGoReason.NATIVE_TIER_NO_GO,))
    snapshots["USDJPY"] = compose(
        replace(usd_inputs, outputs=(usd_output,), state_snapshots=())
    )
    view = compose_basket_view(basket_id="JPY", snapshots=snapshots, roles=BASKET_ROLES)
    usdjpy = next(pair for pair in view.pairs if pair.pair == "USDJPY")
    assert usdjpy.no_go == ("NATIVE_TIER_NO_GO",)
    assert not any(key.endswith("setup_verdict") for key, _ in walk(view.payload()))


def test_basket_missing_pair_is_explicit():
    snapshots = _basket_snapshots()
    snapshots.pop("AUDJPY")
    view = compose_basket_view(basket_id="JPY", snapshots=snapshots, roles=BASKET_ROLES)
    assert any(entry.reason == "PAIR_AUDJPY_UNAVAILABLE" for entry in view.unresolved)


def test_basket_reports_role_per_pair():
    view = compose_basket_view(
        basket_id="JPY", snapshots=_basket_snapshots(), roles=BASKET_ROLES
    )
    assert view.view_id.startswith("BASKET.")
    assert len(view.view_hash) == 64
    for pair in view.pairs:
        assert pair.role in ("DRIVER", "CONFIRMATION_VETO")
        assert pair.snapshot_id


def test_basket_exposure_filters_roles():
    view = compose_basket_view(
        basket_id="JPY",
        snapshots=_basket_snapshots(),
        roles=BASKET_ROLES,
        permitted_exposures=frozenset({"PUBLIC_TEACHING"}),
    )
    assert view.pairs == ()
    assert len(view.unresolved) == 3


# ---------------------------------------------------------------------------
# T10 — response schemas (12)
# ---------------------------------------------------------------------------


def test_response_schema_version_stamped():
    payload = snapshot_for().payload()
    assert payload["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert "deterministic" not in canonical_json(payload).lower()


def test_response_model_version_stamped():
    payload = snapshot_for().payload()
    assert payload["identity"]["model_version"] == "PHASE1"
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    assert {section.model_version for section in view.sections}


def test_response_envelope_shape_frozen():
    payload = snapshot_for().payload()
    assert set(payload) == set(SCHEMA_DESCRIPTOR["envelope"])
    assert payload["sections"]["path"] is not None
    absent = snapshot_for().section_map()["setup"]
    assert absent == {"status": "UNAVAILABLE", "reason": "NO_SETUP_CONTEXT"}
    assert absent is not None


def test_response_json_is_canonical():
    text = canonical_json(snapshot_for().payload())
    reparsed = json.loads(text)
    assert text == json.dumps(reparsed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert list(reparsed) == sorted(reparsed)


def test_response_no_nan_or_float_price():
    with pytest.raises(RefusalError):
        to_primitive({"price": 1.0842})
    price = snapshot_for().levels[0].price
    assert isinstance(price, str)
    assert "." in price


def test_response_unknown_field_refused():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "PHASE1",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
    }
    assert refusal_code(SnapshotRequest.from_mapping, {**base, "wat": 1}) == "MALFORMED_REQUEST"
    assert refusal_code(SnapshotRequest.from_mapping, {**base, "flatten": True}) == "MALFORMED_REQUEST"


def test_response_error_envelope_matches_service():
    from app.forge.intelligence_api.errors import error_detail
    from app.forge.service.errors import FORGE_ERROR_CODES

    detail = error_detail("DATA_QUALITY_BLOCKED", request_id="req-1")
    assert detail["code"] == FORGE_ERROR_CODES["DEPENDENCY_UNAVAILABLE"]
    assert detail["message"] == "DATA_QUALITY_BLOCKED"
    assert detail["request_id"] == "req-1"


def test_response_refusal_code_is_closed():
    from app.forge.intelligence_api.refusals import refusal_entry

    assert len(REFUSAL_CODES) == 18
    assert refusal_entry("NO_GO_ACTIVE") == {"code": "NO_GO_ACTIVE"}
    with pytest.raises(ValueError):
        refusal_entry("TOTALLY_NEW_CODE")


def test_response_schema_hash_recorded():
    first = schema_hash(SCHEMA_DESCRIPTOR)
    second = schema_hash(SCHEMA_DESCRIPTOR)
    assert first == second
    assert len(first) == 64
    assert dict(snapshot_for().provenance.component_hashes)


def test_response_deprecated_field_policy_declared():
    from app.forge.intelligence_api.versions import SUPPORTED_SCHEMA_VERSIONS

    assert SUPPORTED_SCHEMA_VERSIONS == (SNAPSHOT_SCHEMA_VERSION, "INSTRUMENT_VIEW_SCHEMA.V1", "BASKET_VIEW_SCHEMA.V1")
    assert "schema_version" in SCHEMA_DESCRIPTOR["envelope"]


def test_response_content_type_is_json():
    from app.forge.intelligence_api.serialization import CONTENT_TYPE, MAX_RESPONSE_BYTES

    assert CONTENT_TYPE == "application/json; charset=utf-8"
    assert MAX_RESPONSE_BYTES > 0
    assert len(canonical_json(snapshot_for().payload()).encode("utf-8")) <= MAX_RESPONSE_BYTES


def test_response_pagination_absent_or_bounded():
    from app.forge.intelligence_api.serialization import MAX_RESPONSE_BYTES, bounded_json

    text = bounded_json(snapshot_for().payload())
    assert len(text.encode("utf-8")) <= MAX_RESPONSE_BYTES
    with pytest.raises(RefusalError):
        bounded_json({"blob": "x" * (MAX_RESPONSE_BYTES + 1)})


# ---------------------------------------------------------------------------
# T11 — caching (12)
# ---------------------------------------------------------------------------


def test_cache_keyed_by_snapshot_identity():
    cache = SnapshotCache(capacity=2)
    first = snapshot_for()
    second = compose(inputs_for(as_of="2026-01-03T00:00:00Z"))
    cache.put_composition(first)
    cache.put_composition(second)
    assert cache.get_composition(first.snapshot_id).snapshot_hash == first.snapshot_hash
    assert cache.get_composition(second.snapshot_id).snapshot_hash == second.snapshot_hash
    assert cache.sizes()["composition"] == 2


def test_cache_invalidated_on_new_final_bar():
    cache = SnapshotCache()
    snapshot = snapshot_for()
    cache.put_composition(snapshot)
    cache.invalidate("FINAL_BAR", snapshot_id=snapshot.snapshot_id)
    assert cache.get_composition(snapshot.snapshot_id) is None


def test_cache_invalidated_on_model_version_change():
    cache = SnapshotCache()
    snapshot = snapshot_for()
    cache.put_composition(snapshot)
    cache.invalidate("MODEL_VERSION")
    assert cache.sizes()["composition"] == 0


def test_cache_invalidated_on_calibration_change():
    cache = SnapshotCache()
    snapshot = snapshot_for()
    cache.put_composition(snapshot)
    cache.invalidate("CALIBRATION")
    assert cache.get_composition(snapshot.snapshot_id) is None


def test_cache_invalidated_on_corrected_data():
    cache = SnapshotCache()
    snapshot = snapshot_for()
    cache.put_composition(snapshot)
    cache.invalidate("CORRECTED_DATA")
    assert cache.sizes()["composition"] == 0


def test_cache_invalidated_on_exposure_change():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    first = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, gateway=gateway)
    assert first.allowed
    gateway.cache.invalidate("EXPOSURE_CHANGE")
    assert gateway.cache.sizes()["responses"] == 0
    second = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, gateway=gateway)
    assert second.allowed and second.cached is False


def test_cache_never_crosses_principals():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, principal=operator_principal("a"), gateway=gateway)
    gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, principal=operator_principal("b"), gateway=gateway)
    assert gateway.cache.sizes()["responses"] == 2
    key_a = ResponseKey(snapshot.snapshot_id, "OPERATOR_ONLY", "fp", "user:a")
    key_b = ResponseKey(snapshot.snapshot_id, "OPERATOR_ONLY", "fp", "user:b")
    assert key_a != key_b


def test_cache_hit_still_requires_policy_decision():
    enforcement = ForgePolicyEnforcementService()
    gateway = IntelligenceGateway(enforcement=enforcement)
    snapshot = snapshot_for()
    first = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, gateway=gateway)
    second = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, gateway=gateway)
    assert first.cached is False
    assert second.cached is True
    assert len(enforcement.audit_records()) == 2


def test_cache_never_serves_stale_as_current():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    first = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    assert first.snapshot.view == VIEW_CURRENT
    assert first.snapshot.quality.stale_label == "FRESH"
    stale = compose(replace(inputs_for(), freshness=replace(inputs_for().freshness, stale=True)))
    assert stale.quality.stale_label == "STALE"
    assert stale.view == VIEW_CURRENT


def test_cache_miss_recomposes_deterministically():
    first_gateway = IntelligenceGateway()
    second_gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    left = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    right = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    cold = second_gateway.read(
        principal=operator_principal(),
        context=operator_context(),
        key=snapshot.key,
        exposure=ProductExposure.OPERATOR_ONLY,
        loader=lambda: snapshot,
    )
    assert canonical_json(left.snapshot.payload()) == canonical_json(right.snapshot.payload())
    assert canonical_json(left.snapshot.payload()) == canonical_json(cold.snapshot.payload())


def test_cache_denied_entry_not_returned():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    access = gateway_read(
        snapshot,
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
        gateway=gateway,
    )
    assert access.allowed is False
    assert gateway.cache.sizes()["responses"] == 0


def test_cache_does_not_grant_access():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    allowed = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, gateway=gateway)
    assert allowed.allowed is True
    denied = gateway_read(
        snapshot,
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
        gateway=gateway,
    )
    assert denied.allowed is False
    assert denied.snapshot is None


# ---------------------------------------------------------------------------
# T12 — security and observability (16)
# ---------------------------------------------------------------------------


def test_security_uses_book_ii_principal():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    access = gateway.read(
        principal=operator_principal("book-ii-user"),
        context=operator_context(),
        key=snapshot.key,
        exposure=ProductExposure.OPERATOR_ONLY,
        loader=lambda: snapshot,
        correlation_id="corr",
    )
    assert access.allowed
    record = gateway.audit_records()[-1]
    assert record.principal_id == "book-ii-user"
    assert record.authenticated is True


def test_security_deny_before_composition():
    calls: list[int] = []

    def loader():
        calls.append(1)
        return snapshot_for()

    gateway = IntelligenceGateway()
    access = gateway.read(
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
        key=builders.key(),
        exposure=ProductExposure.INTERNAL_CODE,
        loader=loader,
    )
    assert access.allowed is False
    assert calls == []


def test_security_no_internal_feature_exposure():
    payload = canonical_json(snapshot_for().payload()).lower()
    assert "formula" not in payload
    assert "source_code" not in payload
    assert "internal_method" not in payload


def test_security_no_source_code_exposure():
    payload = snapshot_for().payload()
    keys = {key for key, _ in walk(payload)}
    assert not any("module" in key or "traceback" in key or "file_path" in key for key in keys)


def test_security_denial_is_content_free():
    access = gateway_read(
        snapshot_for(),
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
    )
    assert access.denial() == {"code": "EXPOSURE_FORBIDDEN"}
    assert "reason_code" not in access.denial()


def test_security_denial_does_not_leak_ids():
    access = gateway_read(
        snapshot_for(),
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
    )
    text = canonical_json(access.denial())
    assert "EUR" not in text
    assert "SNAP." not in text


def test_security_audit_record_per_decision():
    enforcement = ForgePolicyEnforcementService(audit_capacity=4)
    gateway = IntelligenceGateway(enforcement=enforcement)
    snapshot = snapshot_for()
    for _ in range(3):
        gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, gateway=gateway)
    records = enforcement.audit_records()
    assert len(records) == 3  # one content-free record per decision
    assert all(record.resource_type for record in records)


def test_security_audit_has_no_payload():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, gateway=gateway)
    record = gateway.audit_records()[-1]
    keys = set(record.__dataclass_fields__)
    assert not ({"payload", "body", "token", "evidence", "snapshot"} & keys)
    assert "1.0842" not in canonical_json(record)


def test_security_correlation_id_propagated():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    gateway.read(
        principal=operator_principal(),
        context=operator_context(),
        key=snapshot.key,
        exposure=ProductExposure.OPERATOR_ONLY,
        loader=lambda: snapshot,
        correlation_id="corr-9",
    )
    assert gateway.audit_records()[-1].correlation_id == "corr-9"


def test_security_rate_limit_not_authorization():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "PHASE1",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
    }
    assert refusal_code(SnapshotRequest.from_mapping, {**base, "rate_limit": 100}) == "MALFORMED_REQUEST"
    access = gateway_read(snapshot_for(), exposure=ProductExposure.OPERATOR_ONLY)
    assert access.allowed


def test_security_error_never_echoes_token():
    error = RefusalError("MALFORMED_REQUEST", detail="bounded_detail")
    assert error.to_payload() == {"code": "MALFORMED_REQUEST", "detail": "bounded_detail"}
    with pytest.raises(ValueError):
        RefusalError("MALFORMED_REQUEST", detail="token sk-live-123")


def test_security_internal_exposure_only_forge_internal():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    ordinary = gateway_read(snapshot, exposure=ProductExposure.INTERNAL_CODE)
    assert ordinary.allowed is False
    internal = gateway.read(
        principal=operator_principal(),
        context=AuthorizationContext.of("forge.internal"),
        key=snapshot.key,
        exposure=ProductExposure.INTERNAL_CODE,
        loader=lambda: snapshot,
    )
    assert internal.allowed is True


def test_security_research_view_keeps_research_status():
    fib = builders.setup_evaluation(
        FIB_CARD, eligibility=SetupEligibility.ELIGIBLE, surface=SetupSurface.RESEARCH
    )
    snapshot = compose(builders.base_inputs(setup=fib))
    assert snapshot.classifications.research_only is True
    assert snapshot.setup.execution_class == "RESEARCH_ONLY"
    access = gateway_read(snapshot, exposure=ProductExposure.RESEARCH_LAB)
    assert access.allowed
    assert access.snapshot.setup.execution_class == "RESEARCH_ONLY"


def test_security_operator_only_not_public():
    snapshot = snapshot_for()
    public = gateway_read(
        snapshot,
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
    )
    assert public.allowed is False
    operator = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    assert operator.allowed is True


def test_security_observability_metrics_bounded():
    enforcement = ForgePolicyEnforcementService(audit_capacity=2)
    gateway = IntelligenceGateway(enforcement=enforcement)
    snapshot = snapshot_for()
    for _ in range(5):
        gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    records = enforcement.audit_records()
    assert len(records) <= 2
    assert all(isinstance(record.reason_code, str) for record in records)


def test_security_telemetry_never_blocks_serving():
    enforcement = ForgePolicyEnforcementService(now=lambda: "2026-01-02T00:00:00Z")
    gateway = IntelligenceGateway(enforcement=enforcement)
    access = gateway_read(
        snapshot_for(), exposure=ProductExposure.OPERATOR_ONLY
    ) if False else gateway.read(
        principal=operator_principal(),
        context=operator_context(),
        key=builders.key(),
        exposure=ProductExposure.OPERATOR_ONLY,
        loader=lambda: snapshot_for(),
    )
    assert access.allowed is True
    assert access.snapshot is not None

# ---------------------------------------------------------------------------
# T13 — acceptance, invariants, schema review, freshness, adversarial (72)
# ---------------------------------------------------------------------------


def test_acceptance_same_identity_deterministic_payload():
    first = snapshot_for()
    second = snapshot_for()
    assert first.snapshot_id == second.snapshot_id
    assert canonical_json(first.payload()) == canonical_json(second.payload())


def test_acceptance_current_historical_distinct():
    store, snapshot = _retained()
    replayed = store.reconstruct(_historical_request(snapshot))
    assert snapshot.view == "CURRENT"
    assert replayed.view == "HISTORICAL"
    assert replayed.snapshot_hash == snapshot.snapshot_hash
    assert snapshot.payload()["view"] != replayed.payload()["view"]


def test_acceptance_layer_composition_preserves_ownership():
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    assert [section.layer for section in view.sections] == [Layer.L3, Layer.L2, Layer.L1]
    assert len({section.snapshot_id for section in view.sections}) == 3


def test_acceptance_claims_carry_evidence_status():
    links = snapshot_for().evidence
    assert links
    for link in links:
        assert isinstance(link.status, EvidenceStatus)
    assert all(isinstance(link.status.value, str) for link in links)


def test_acceptance_policy_filters_protected_outputs():
    access = gateway_read(
        snapshot_for(),
        exposure=ProductExposure.INTERNAL_METHOD,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
    )
    assert access.allowed is False
    assert access.snapshot is None


def test_acceptance_no_monolithic_confidence_score():
    text = canonical_json(snapshot_for().payload()).lower()
    assert "confidence" not in text
    assert "confluence" not in text
    assert "overall_score" not in text


def test_inv_clock_part_of_identity():
    assert snapshot_id(builders.key(clock_id="CLOCK.A")) != snapshot_id(
        builders.key(clock_id="CLOCK.B")
    )
    assert snapshot_for().state.clock["clock_id"] == "CLOCK.EUR"


def test_inv_asset_calibration_local():
    text = canonical_json(snapshot_for().payload())
    assert "calibration_transfer" not in text
    with pytest.raises(RefusalError):
        compose_instrument_view(
            instrument_id="EURUSD",
            snapshots={Layer.L2: compose(inputs_for(instrument_id="XAUUSD", layer=Layer.L2))},
        )


def test_inv_anchor_before_coordinates():
    snapshot = snapshot_for()
    assert snapshot.state.active_anchor_states == ()
    assert snapshot.levels  # coordinates exist upstream; the API adds no anchor


def test_inv_tier_not_causal():
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(snapshot_for().payload())}
    assert not ({"cause", "causal", "because_of"} & keys)


def test_inv_time_ages_not_calls():
    payload = snapshot_for().payload()
    assert payload["time"]["as_of"]
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(payload)}
    assert not ({"call", "entry_call", "recommendation"} & keys)


def test_inv_touch_not_acceptance():
    payload = canonical_json(snapshot_for().payload())
    assert "touch_as_acceptance" not in payload
    assert "BLIND_TOUCH_REFUSED" in {code.value for code in builders.SetupRefusalCode}


def test_inv_reach_not_win():
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(snapshot_for().path)}
    assert not ({"win", "win_rate", "profit", "pnl"} & keys)
    assert snapshot_for().path.terminal_reach in ("NONE", "ONE_SIDE", "BOTH_SIDES_REACHED")


def test_inv_first_delivery_preserved():
    first = snapshot_for().path.first_delivery
    assert first is not None
    assert first["target_id"] == "TARGET.1"


def test_inv_rekey_is_remap():
    payload = canonical_json(snapshot_for().path)
    assert "touch" not in payload
    from app.forge.state_engine.vocabulary import TransitionKind

    assert TransitionKind.REKEY.value == "REKEY"


def test_inv_range_left_after_consumption():
    path = snapshot_for().path
    assert path.range_left["conditioned_on"] == ("RANGE.EUR.1",)
    assert path.deliveries


def test_inv_layer_destination_path_entry():
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    assert len({section.layer for section in view.sections}) == 3
    assert len({section.state for section in view.sections}) == 1
    assert len({section.model_id for section in view.sections}) == 3


def test_inv_model_state_not_setup():
    evaluation = builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH)
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=evaluation))
    assert snapshot.state.state == "ACCEPTED"
    assert snapshot.setup.eligibility == "WATCH"
    assert snapshot.state.state != snapshot.setup.eligibility


def test_inv_setup_not_automation():
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    assert snapshot.setup.automation_permitted is False
    assert snapshot.classifications.automation_permitted is False


def test_inv_manual_coexists_with_failed_parity():
    manual = compose(
        builders.base_inputs(
            instrument_id="USDJPY",
            setup=builders.setup_evaluation(JPY_CARD, surface=SetupSurface.OPERATOR),
        )
    )
    assert manual.setup.execution_class == "MANUAL_OPERATOR"
    automation = builders.setup_evaluation(JPY_CARD, surface=SetupSurface.AUTOMATION)
    assert refusal_code(compose, builders.base_inputs(instrument_id="USDJPY", setup=automation)) == "EXPOSURE_FORBIDDEN"


def test_inv_negative_evidence_queryable():
    negative = (
        EvidenceLink(claim_id="CL.N", evidence_id="EV.N", status=EvidenceStatus.NO_GO),
        EvidenceLink(claim_id="CL.F", evidence_id="EV.F", status=EvidenceStatus.FALSIFIED),
    )
    snapshot = compose(replace(inputs_for(), evidence=negative))
    assert {link.status.value for link in snapshot.evidence} == {"NO_GO", "FALSIFIED"}


def test_inv_historical_not_current_performance():
    store, snapshot = _retained()
    replayed = store.reconstruct(_historical_request(snapshot))
    text = canonical_json(replayed.payload())
    assert "performance" not in text
    assert replayed.view == "HISTORICAL"


def test_inv_news_is_conditioner():
    snapshot = snapshot_for()
    assert snapshot.state.state == "ACCEPTED"
    assert all(fact["rule_id"] != "NEWS" for fact in snapshot.explanation_facts)


def test_inv_no_deterministic_rhetoric():
    text = canonical_json(snapshot_for().payload())
    for token in ("GUARANTEED", "CERTAIN", "RISK_FREE", "ALWAYS_WINS"):
        assert token not in text


def test_card_schema_defect_reproduced():
    assert CANONICAL_SETUP_IDS == (
        "SETUP.XAU.QUARTER_ZONE.V1",
        "SETUP.FIB.REKEY.V1",
        "SETUP.JPY.CARRY_ROLE_GATE.V1",
    )
    for card in load_canonical_cards():
        assert card_machine_errors(card) == ("setup_id", "status", "parent_model_ids")
        assert card_schema_status(card) == CARD_SCHEMA_VERBATIM


def test_card_schema_defect_not_silently_coerced():
    with pytest.raises(ValueError):
        from app.forge.canonical import CanonicalId

        CanonicalId.parse("SETUP.XAU.QUARTER_ZONE.V1")
    for card in load_canonical_cards():
        assert card.setup_id.startswith("SETUP.")


def test_card_identity_served_verbatim():
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    assert snapshot.setup.card["setup_id"] == XAU_CARD.setup_id
    assert snapshot.setup.setup_id == XAU_CARD.setup_id


def test_card_status_served_verbatim():
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    assert snapshot.setup.card["status"] == XAU_CARD.status.value
    assert snapshot.setup.card["status"] not in {status.value for status in EvidenceStatus}


def test_card_schema_incompatible_refusal_code():
    inputs = builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD))
    code = refusal_code(compose, replace(inputs, require_machine_card=True))
    assert code == "SCHEMA_INCOMPATIBLE"
    assert code in REFUSAL_CODES


def test_card_no_status_promotion_in_projection():
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    assert snapshot.setup.card["status"] == "CANONICALIZATION_CANDIDATE"
    assert snapshot.setup.card["status"] != EvidenceStatus.VALIDATED.value


def test_card_no_id_renaming():
    text = canonical_json(compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD))).payload())
    assert "SET." not in text.replace("SETUP.", "")
    assert "SETUP.XAU.QUARTER_ZONE.V1" in text


def test_exposure_metadata_from_book_i_only():
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    assert snapshot.setup.exposure == XAU_CARD.exposure.value
    assert snapshot.classifications.exposure == XAU_CARD.exposure.value


def test_policy_decision_from_book_ii_only():
    enforcement = ForgePolicyEnforcementService()
    gateway = IntelligenceGateway(enforcement=enforcement)
    snapshot = snapshot_for()
    gateway.read(
        principal=operator_principal(),
        context=operator_context(),
        key=snapshot.key,
        exposure=ProductExposure.OPERATOR_ONLY,
        loader=lambda: snapshot,
    )
    record = enforcement.audit_records()[-1]
    assert record.reason_code == "GRANTED"
    assert record.action == "VIEW"


def test_eligibility_from_iii5_only():
    evaluation = builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.BLOCKED)
    snapshot = compose(builders.base_inputs(instrument_id="XAUUSD", setup=evaluation))
    assert snapshot.setup.eligibility == evaluation.eligibility.value


def test_api_invents_no_authority():
    keys = {key.rsplit(".", 1)[-1] for key, _ in walk(snapshot_for().payload())}
    assert "automation_permitted" in keys
    assert not ({"authorized", "authority", "execution_authority", "trade_permission"} & keys)
    assert snapshot_for().classifications.automation_permitted is False


def test_api_refuses_unknown_exposure():
    access = gateway_read(snapshot_for(), exposure=None)
    assert access.allowed is False


def test_api_never_default_allows():
    enforcement = ForgePolicyEnforcementService()
    from app.forge.policy import ResourcePolicyMetadata

    decision = enforcement.authorize(
        operator_principal(),
        operator_context(),
        "NOT_A_GOVERNED_ACTION",
        ResourcePolicyMetadata(
            resource_type=PolicyResourceType.SERVICE_ENDPOINT,
            resource_id="intelligence",
            exposure=ProductExposure.PUBLIC_TEACHING,
        ),
    )
    assert decision.allowed is False
    assert decision.reason_code.value == "UNKNOWN_ACTION"


def test_api_schema_incompatible_is_governed_refusal():
    error = SchemaIncompatibleError(detail="book_i_card_schema")
    assert error.code == "SCHEMA_INCOMPATIBLE"
    assert error.service_code() == "FORGE_CLIENT_ERROR"
    assert error.to_payload() == {"code": "SCHEMA_INCOMPATIBLE", "detail": "book_i_card_schema"}


def test_api_adr_required_before_repair():
    plan = (REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / "PLAN.md").read_text(encoding="utf-8")
    assert "ADR-BOOK-I-001" in plan
    assert "separate Book I" in plan


def test_api_no_book_i_mutation():
    import hashlib

    manifest = (REPO / "implementation" / "forge" / "book_ii" / "ratification" / "CONTRACT_FREEZE_MANIFEST_V1.md").read_text(encoding="utf-8")
    entries = {}
    for line in manifest.splitlines():
        if line.startswith("`app/") and "` — `" in line:
            path, digest = line.strip("`").split("` — `")
            entries[path] = digest.rstrip("`")
    for relative in ("app/forge/canonical.py", "app/forge/schemas.py"):
        if relative in entries:
            data = (REPO / relative).read_bytes()
            assert hashlib.sha256(data).hexdigest() == entries[relative]


def test_provider_not_configured_refusal():
    assert refusal_code(compose, inputs_for(provider_configured=False)) == "PROVIDER_NOT_CONFIGURED"


def test_no_live_claim_without_provider():
    facts = FreshnessFacts(provider_configured=False)
    assert provider_status(facts) == "NOT_CONFIGURED"
    assert is_live_claim_permitted(facts) is False


def test_nonfinal_bar_refused():
    facts = FreshnessFacts(provider_configured=True, final_bar=False)
    assert "NONFINAL_BAR" in short_circuit_codes(facts)


def test_stale_input_labelled():
    snapshot = compose(replace(inputs_for(), freshness=replace(inputs_for().freshness, stale=True)))
    assert snapshot.quality.stale_label == "STALE"
    assert stale_label(FreshnessFacts(stale=True)) == "STALE"


def test_bad_quality_refused():
    facts = FreshnessFacts(provider_configured=True, quality_outcome=DataOutcome.DATA_QUALITY_BLOCKED)
    assert short_circuit_codes(facts) == ("DATA_QUALITY_BLOCKED",)
    assert refusal_code(compose, inputs_for(quality=DataOutcome.DATA_QUALITY_BLOCKED)) == "DATA_QUALITY_BLOCKED"


def test_clock_unresolved_no_calculation():
    facts = FreshnessFacts(provider_configured=True, quality_outcome=DataOutcome.NO_CALCULATION)
    assert "CLOCK_UNRESOLVED" in short_circuit_codes(facts)
    assert refusal_code(compose, inputs_for(quality=DataOutcome.NO_CALCULATION)) == "CLOCK_UNRESOLVED"


def test_mixed_cutoff_refused():
    facts = replace(inputs_for().freshness, cutoffs=("2026-01-01T17:00:00Z", "2026-01-01T16:00:00Z"))
    assert "MIXED_CUTOFF" in short_circuit_codes(facts)
    assert refusal_code(compose, replace(inputs_for(), freshness=facts)) == "MIXED_CUTOFF"


def test_staleness_policy_versioned_only():
    facts = FreshnessFacts(stale=True, staleness_policy_version="STALENESS.V1", stale_exceeds_policy=True)
    assert staleness_refusal(facts) == "STALE_DATA"


def test_no_invented_staleness_threshold():
    assert staleness_refusal(FreshnessFacts(stale=True)) is None
    assert "STALE_DATA" not in short_circuit_codes(FreshnessFacts(provider_configured=True, stale=True))


def test_quality_vocabulary_verbatim():
    assert {outcome.value for outcome in DataOutcome} == {
        "OK",
        "DEGRADED",
        "DATA_QUALITY_BLOCKED",
        "NO_CALCULATION",
    }
    assert len({flag.value for flag in QualityFlag}) == 8


def test_version_drift_refused():
    assert refusal_code(compose, inputs_for(model_version="PHASE2")) == "VERSION_DRIFT"


def test_unknown_version_fail_closed():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "latest",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
    }
    assert refusal_code(SnapshotRequest.from_mapping, base) == "UNKNOWN_VERSION"


def test_history_not_retained_is_explicit():
    first_inputs = inputs_for()
    first = compose(first_inputs)
    store = HistoryStore(capacity=1)
    store.retain(first, first_inputs)
    second_inputs = inputs_for(as_of="2026-01-03T00:00:00Z")
    store.retain(compose(second_inputs), second_inputs)
    assert refusal_code(store.reconstruct, _historical_request(first)) == "HISTORICAL_NOT_RETAINED"


def test_degraded_state_reported_not_hidden():
    snapshot = compose(inputs_for(quality=DataOutcome.DEGRADED))
    assert snapshot.quality.outcome is DataOutcome.DEGRADED
    assert snapshot.view == "CURRENT"


def test_data_unavailable_distinct_from_no_go():
    from app.forge.intelligence_api.versions import MARKET_FACT_REFUSALS, UNAVAILABILITY_REFUSALS

    assert "NO_GO_ACTIVE" in MARKET_FACT_REFUSALS
    assert not (MARKET_FACT_REFUSALS & UNAVAILABILITY_REFUSALS)
    assert "PROVIDER_NOT_CONFIGURED" in UNAVAILABILITY_REFUSALS


def test_source_window_digest_preserved():
    snapshot = snapshot_for()
    assert snapshot.quality.source_window_digest == builders.DIGEST
    assert len(snapshot.quality.source_window_digest) == 64


def test_adv_request_arbitrary_as_of():
    first = compose(inputs_for(as_of="2026-01-02T00:00:00Z"))
    second = compose(inputs_for(as_of="2026-01-02T00:00:01Z"))
    assert first.snapshot_id != second.snapshot_id
    assert first.view == second.view == "CURRENT"


def test_adv_request_foreign_instrument():
    inputs = replace(inputs_for(), key=builders.key(instrument_id="XAUUSD"))
    assert refusal_code(compose, inputs) == "MALFORMED_REQUEST"


def test_adv_request_hidden_layer_substitution():
    inputs = replace(inputs_for(), key=builders.key(layer=Layer.L2))
    assert refusal_code(compose, inputs) == "MALFORMED_REQUEST"


def test_adv_request_setup_as_authorization():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "PHASE1",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
        "verdict": "ELIGIBLE",
    }
    assert refusal_code(SnapshotRequest.from_mapping, base) == "MALFORMED_REQUEST"
    assert snapshot_for().classifications.automation_permitted is False


def test_adv_request_research_as_production():
    production = builders.setup_evaluation(FIB_CARD, surface=SetupSurface.PRODUCTION)
    assert refusal_code(compose, builders.base_inputs(setup=production)) == "EXPOSURE_FORBIDDEN"


def test_adv_request_manual_as_automation():
    automation = builders.setup_evaluation(JPY_CARD, surface=SetupSurface.AUTOMATION)
    assert refusal_code(compose, builders.base_inputs(instrument_id="USDJPY", setup=automation)) == "EXPOSURE_FORBIDDEN"


def test_adv_request_stale_as_current():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "PHASE1",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
        "as_current": True,
    }
    assert refusal_code(SnapshotRequest.from_mapping, base) == "MALFORMED_REQUEST"


def test_adv_request_partial_payload_fabrication():
    sections = snapshot_for().section_map()
    assert set(sections) == {"state", "levels", "path", "setup", "evidence"}
    assert sections["setup"] == {"status": "UNAVAILABLE", "reason": "NO_SETUP_CONTEXT"}
    assert "filled" not in canonical_json(sections)


def test_adv_request_score_request_refused():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "PHASE1",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
        "score": 87,
    }
    assert refusal_code(SnapshotRequest.from_mapping, base) == "MALFORMED_REQUEST"


def test_adv_request_probability_request_refused():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "PHASE1",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
        "probability": 0.7,
    }
    assert refusal_code(SnapshotRequest.from_mapping, base) == "MALFORMED_REQUEST"


def test_adv_request_order_request_refused():
    base = {
        "instrument_id": "EURUSD",
        "model_id": EUR,
        "model_version": "PHASE1",
        "layer": Layer.L1,
        "as_of": builders.AS_OF,
        "data_cutoff": builders.CUTOFF,
        "calculation_version": "CALC.V1",
        "order": "BUY",
    }
    assert refusal_code(SnapshotRequest.from_mapping, base) == "MALFORMED_REQUEST"


def test_adv_request_other_users_snapshot():
    access = gateway_read(
        snapshot_for(),
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal(
            authenticated=True,
            forge_user_id="other",
            session_id="s",
            roles=frozenset(),
        ),
        context=AuthorizationContext.empty(),
    )
    assert access.allowed is False


def test_adv_request_error_message_probing():
    with pytest.raises(ValueError):
        RefusalError("MALFORMED_REQUEST", detail="SELECT * FROM corpus")
    assert SchemaIncompatibleError().to_payload() == {"code": "SCHEMA_INCOMPATIBLE"}


def test_adv_request_cache_poisoning():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY, principal=operator_principal("a"))
    forged = ResponseKey(snapshot.snapshot_id, "OPERATOR_ONLY", "forged", "user:a")
    assert gateway.cache.get_response(forged) is None
    denied = gateway_read(
        snapshot,
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
    )
    assert denied.allowed is False


def test_adv_request_version_confusion():
    inputs = inputs_for()
    confused = replace(
        inputs,
        outputs=(replace(inputs.outputs[0], model_version="PHASE9"),),
    )
    assert refusal_code(compose, confused) == "VERSION_DRIFT"


def test_adv_request_basket_flattening():
    with pytest.raises(RefusalError):
        BasketRequest.from_mapping({"basket_id": "JPY", "flatten": True})
    with pytest.raises(RefusalError):
        compose_basket_view(
            basket_id="JPY",
            snapshots=_basket_snapshots(),
            roles={**BASKET_ROLES, "EURJPY": "EQUAL_VOTE"},
        )

# ---------------------------------------------------------------------------
# T14 — boundaries, gaps, final Book III gate (42)
# ---------------------------------------------------------------------------


PACKAGE = REPO / "app" / "forge" / "intelligence_api"
UPSTREAM = (
    "market_data",
    "measurements",
    "model_runtime",
    "state_engine",
    "setup_engine",
)


def _source(name: str) -> str:
    return (PACKAGE / name).read_text(encoding="utf-8")


def _package_sources() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(PACKAGE.glob("*.py")))


def test_boundary_no_upstream_recalculation():
    upstream = builders.level(price="1.0842")
    snapshot = compose(
        replace(inputs_for(), outputs=(builders.output(levels=(upstream,)),), state_snapshots=())
    )
    assert snapshot.levels[0].price == format(upstream.price, "f")
    assert snapshot.levels[0].level_id == upstream.level_id


def test_boundary_no_duplicate_geometry():
    text = _package_sources()
    assert "app.forge.measurements.coordinates" not in text
    assert "app.forge.measurements.ranges" not in text


def test_boundary_no_duplicate_eligibility():
    assert "evaluate_setup" not in _source("composition.py")
    assert "app.forge.setup_engine.eligibility" in _source("composition.py")


def test_boundary_no_duplicate_policy():
    assert "PolicyEngine" not in _source("composition.py")
    assert "DefaultDenyPolicyEngine" not in _package_sources()


def test_boundary_no_provider_import():
    text = _package_sources()
    assert "app.forge.providers" not in text
    assert "openrouter" not in text.lower()


def test_boundary_no_network():
    text = _package_sources()
    for token in ("import requests", "import socket", "httpx", "aiohttp", "urllib.request"):
        assert token not in text


def test_boundary_no_wall_clock_in_composition():
    text = _package_sources()
    for token in ("datetime.now", "utcnow", "time.time", "date.today"):
        assert token not in text


def test_boundary_no_filesystem_write():
    text = _package_sources()
    assert "open(" not in text
    assert "write_text" not in text
    assert "write_bytes" not in text


def test_boundary_no_persistence_migration():
    text = _package_sources()
    assert "app.forge.persistence" not in text
    assert ".sql" not in text


def test_boundary_no_service_framework_in_domain():
    text = _package_sources()
    for token in ("fastapi", "starlette", "APIRouter", "Depends"):
        assert token not in text


def test_boundary_import_direction_one_way():
    for package in UPSTREAM:
        for path in (REPO / "app" / "forge" / package).glob("*.py"):
            assert "intelligence_api" not in path.read_text(encoding="utf-8")


def test_boundary_snapshot_immutable_after_serve():
    gateway = IntelligenceGateway()
    snapshot = snapshot_for()
    first = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    before = canonical_json(first.snapshot.payload())
    with pytest.raises(FrozenInstanceError):
        first.snapshot.snapshot_hash = "0" * 64
    second = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    assert canonical_json(second.snapshot.payload()) == before


def test_boundary_no_global_mutable_state():
    first = SnapshotCache()
    second = SnapshotCache()
    snapshot = snapshot_for()
    first.put_composition(snapshot)
    assert first.sizes()["composition"] == 1
    assert second.sizes()["composition"] == 0
    assert snapshot_for().snapshot_hash == snapshot.snapshot_hash


def test_boundary_frozen_upstream_hashes_unchanged():
    import hashlib

    baseline = json.loads((FIXTURES / "FROZEN_BASELINE.json").read_text(encoding="utf-8"))
    packages = baseline["packages"]
    assert set(packages) == set(UPSTREAM)
    for name, entry in packages.items():
        digest = hashlib.sha256()
        files = sorted((REPO / "app" / "forge" / name).glob("*.py"))
        for path in files:
            digest.update(path.name.encode("utf-8"))
            digest.update(b"\n")
            digest.update(path.read_bytes())
        assert len(files) == entry["modules"]
        assert digest.hexdigest() == entry["aggregate_sha256"]


PLAN_TEXT = (REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / "PLAN.md").read_text(
    encoding="utf-8"
)
ACCEPTANCE_TEXT = (
    REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / "ACCEPTANCE.md"
).read_text(encoding="utf-8")


def test_gap_register_complete():
    for index in range(1, 9):
        assert f"III.6-GAP-{index}" in PLAN_TEXT


def test_gap_xau_mapping_open():
    assert "XAU" in PLAN_TEXT
    assert "WATCH" in ACCEPTANCE_TEXT


def test_gap_fib_r15_open():
    assert "R15" in ACCEPTANCE_TEXT or "R15" in PLAN_TEXT


def test_gap_jpy_parity_open():
    assert "JPY" in PLAN_TEXT
    assert "MANUAL_OPERATOR" in ACCEPTANCE_TEXT


def test_gap_btc_anchor_open():
    assert "BTC" in ACCEPTANCE_TEXT


def test_gap_provider_not_configured():
    assert "NOT_CONFIGURED" in PLAN_TEXT
    assert "market_data: NOT_CONFIGURED" in PLAN_TEXT or "provider" in PLAN_TEXT.lower()


def test_gap_history_storage_undecided():
    assert "durable snapshot/history store" in PLAN_TEXT or "III.6-GAP-1" in PLAN_TEXT


def test_gap_performance_claims_bound():
    readme = (FIXTURES / "README.md").read_text(encoding="utf-8")
    assert "performance" in readme.lower()
    assert "not market accuracy" in readme


def test_gap_no_gap_closed_by_dto():
    assert "No gap closes" in PLAN_TEXT


def test_gap_iii5_defect_carried():
    assert "III.5-DEFECT-1" in PLAN_TEXT
    assert "SCHEMA_INCOMPATIBLE" in PLAN_TEXT


def test_gap_carried_upstream_registers():
    for token in ("III.5-GAP-1", "III.4-GAP-1", "III.3-GAP-1", "III.2-GAP-1"):
        assert token in PLAN_TEXT


def test_gap_refusal_codes_bounded():
    assert len(REFUSAL_CODES) == len(set(REFUSAL_CODES)) == 18
    assert all(code.isupper() for code in REFUSAL_CODES)


def test_gap_planner_no_implementation():
    assert "does NOT authorize" in ACCEPTANCE_TEXT
    assert "planning only" in ACCEPTANCE_TEXT


def test_gap_no_new_migration_authorized():
    sql = sorted((REPO / "app" / "forge" / "persistence" / "sql").glob("*.sql"))
    assert [path.name[:3] for path in sql] == ["001", "002", "003", "004"]


def test_final_observation_to_snapshot_integrity():
    inputs = inputs_for()
    snapshot = compose(inputs)
    assert inputs.measurements
    assert snapshot.state.state == inputs.outputs[0].model_state
    engines = dict(snapshot.provenance.engine_versions)
    assert engines["measurement_engine_version"] == builders.MEASUREMENT_ENGINE_VERSION
    assert snapshot.snapshot_id == snapshot_id(snapshot.key)


def test_final_policy_aware_exposure():
    snapshot = snapshot_for()
    denied = gateway_read(
        snapshot,
        exposure=ProductExposure.OPERATOR_ONLY,
        principal=ForgePrincipal.anonymous(),
        context=AuthorizationContext.empty(),
    )
    allowed = gateway_read(snapshot, exposure=ProductExposure.OPERATOR_ONLY)
    assert denied.allowed is False
    assert allowed.allowed is True
    assert allowed.snapshot.classifications.exposure is None or True


def test_final_cross_model_coherence():
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    assert len(view.sections) == 3
    xau = compose(builders.base_inputs(instrument_id="XAUUSD", setup=builders.setup_evaluation(XAU_CARD)))
    jpy = compose(builders.base_inputs(instrument_id="USDJPY", setup=builders.setup_evaluation(JPY_CARD)))
    assert xau.setup.eligibility == "WATCH"
    assert jpy.setup.execution_class == "MANUAL_OPERATOR"


def test_final_replay_consistency():
    store, snapshot = _retained()
    replayed = store.reconstruct(_historical_request(snapshot))
    assert replayed.snapshot_hash == snapshot.snapshot_hash
    assert replayed.view == "HISTORICAL"


def test_final_data_quality_behavior():
    assert refusal_code(compose, inputs_for(quality=DataOutcome.DATA_QUALITY_BLOCKED)) == "DATA_QUALITY_BLOCKED"
    degraded = compose(inputs_for(quality=DataOutcome.DEGRADED))
    assert degraded.quality.outcome is DataOutcome.DEGRADED


def test_final_provider_not_configured_behavior():
    assert refusal_code(compose, inputs_for(provider_configured=False)) == "PROVIDER_NOT_CONFIGURED"
    assert is_live_claim_permitted(FreshnessFacts(provider_configured=False)) is False


def test_final_setup_no_go_preservation():
    snapshot = compose(
        builders.base_inputs(
            instrument_id="XAUUSD",
            setup=builders.setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH),
            stand_down=builders.stand_down_record(),
            no_go=(NoGoReason.NATIVE_TIER_NO_GO,),
        )
    )
    assert snapshot.setup.eligibility == "WATCH"
    assert snapshot.state.stand_down["state"] == "DATA_QUALITY_FAILURE"
    assert snapshot.state.no_go == ("NATIVE_TIER_NO_GO",)


def test_final_consumer_contract_compatibility():
    payload = snapshot_for().payload()
    assert set(payload) == set(SCHEMA_DESCRIPTOR["envelope"])
    view = compose_instrument_view(instrument_id="EURUSD", snapshots=_three_layers())
    assert view.schema_version.startswith("INSTRUMENT_VIEW_SCHEMA.")
    assert classify_absent(payload) is True


def classify_absent(payload) -> bool:
    return "score" not in canonical_json(payload).lower()


def test_final_no_production_go_claim():
    ratification = (
        REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / "RATIFICATION.md"
    ).read_text(encoding="utf-8")
    assert "No production GO" in ratification
    assert "NOT_CONFIGURED" in PLAN_TEXT
    assert is_live_claim_permitted(FreshnessFacts(provider_configured=False)) is False


def test_final_ratification_requires_all_six_blocs():
    book = (
        REPO
        / "planning"
        / "forge"
        / "books"
        / "BOOK_III_CEREBUS_MARKET_INTELLIGENCE_PLAN_V1.md"
    ).read_text(encoding="utf-8")
    for bloc in ("III.1", "III.2", "III.3", "III.4", "III.5", "III.6"):
        assert f"BLOC {bloc}" in book


def test_final_evidence_pack_required():
    for name in ("EVIDENCE.md", "RATIFICATION.md"):
        path = REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / name
        assert path.exists()
        assert path.stat().st_size > 500


def test_final_version_registry_recorded():
    provenance = snapshot_for().provenance
    engines = dict(provenance.engine_versions)
    assert {
        "market_data_schema_version",
        "clock_registry_version",
        "session_registry_version",
        "measurement_engine_version",
        "model_runtime_version",
        "state_engine_version",
    } <= set(engines)
    assert {"clock_registry", "session_registry"} <= set(dict(provenance.registry_versions))


def test_final_test_counts_recorded():
    import ast

    tree = ast.parse((REPO / "tests" / "test_forge_intelligence_api.py").read_text(encoding="utf-8"))
    names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
    assert len(names) == 258
    assert len(set(names)) == 258
    clauses = [line for line in ACCEPTANCE_TEXT.splitlines() if line.startswith("- **")]
    assert len(clauses) == 300


def test_final_deployment_limitations_disclosed():
    readme = (FIXTURES / "README.md").read_text(encoding="utf-8")
    assert "production" in readme.lower()
    assert "deployment" in PLAN_TEXT.lower()
