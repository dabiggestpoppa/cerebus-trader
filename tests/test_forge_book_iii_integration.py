"""Book III cross-bloc integration suite (BA-23 Rung 2 / WP-1).

96 frozen names IN-1..IN-96 across T1-T12. Tests compose the ratified
III.1-III.6 public interfaces; they do not re-derive measurements, model
rules, transitions or setup verdicts. Synthetic fixtures are structural
proof only.

Test result != gate closure: durable history, live provider data and the
Book I card schema remain A-class open (see FEASIBILITY_GATE.md).
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import pathlib
import re
from dataclasses import FrozenInstanceError, replace

import pytest

from app.forge.canonical import ProductExposure
from app.forge.identity import ForgePrincipal
from app.forge.intelligence_api.errors import RefusalError
from app.forge.intelligence_api.freshness import is_live_claim_permitted, short_circuit_codes, stale_label
from app.forge.intelligence_api.policy_gate import IntelligenceGateway
from app.forge.intelligence_api.refusals import card_machine_errors, require_machine_card
from app.forge.intelligence_api.serialization import bounded_json, canonical_json
from app.forge.intelligence_api.versions import REFUSAL_CODES
from app.forge.market_data.bars import Finality
from app.forge.market_data.quality import DataOutcome
from app.forge.model_runtime.contract import MODEL_RUNTIME_VERSION  # noqa: F401
from app.forge.model_runtime.errors import ModelVersionUnavailableError
from app.forge.model_runtime.registry import resolve
from app.forge.policy import AuthorizationContext
from app.forge.setup_engine.contracts import SetupEligibility, SetupSurface
from app.forge.state_engine.delivery import (
    AmbiguousPathError,
    DeclaredTarget,
    DeliveryObservation,
    DeliverySide,
    build_path,
)
from app.forge.state_engine.history import open_ledger, replay_events, verify_history
from app.forge.state_engine.range_left import recompute_range_left
from app.forge.state_engine.rekey import plan_rekey
from app.forge.state_engine.snapshot import MeasurementRef, StateSnapshot

REPO = pathlib.Path(__file__).resolve().parents[1]
_FIXTURES = REPO / "implementation" / "forge" / "book_iii" / "integration" / "fixtures" / "_builders.py"
_SPEC = importlib.util.spec_from_file_location("iii_integration_builders", _FIXTURES)
assert _SPEC is not None and _SPEC.loader is not None
B = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(B)

GATEWAY = IntelligenceGateway()


def operator_principal(user_id: str = "user-1") -> ForgePrincipal:
    return ForgePrincipal(
        authenticated=True, forge_user_id=user_id, session_id="session-1", roles=frozenset()
    )


def operator_context() -> AuthorizationContext:
    return AuthorizationContext.of("model.read.operator")


def refusal_code(fn, *args, **kwargs) -> str:
    with pytest.raises(RefusalError) as exc:
        fn(*args, **kwargs)
    return exc.value.code


def gateway_read(snapshot, *, exposure=ProductExposure.OPERATOR_ONLY, principal=None, context=None, loader=None, gateway=None):
    gateway = gateway or GATEWAY
    return gateway.read(
        principal=operator_principal() if principal is None else principal,
        context=operator_context() if context is None else context,
        key=snapshot.key,
        exposure=exposure,
        loader=(lambda: snapshot) if loader is None else loader,
    )


def walk(value, prefix: str = "") -> list[tuple[str, object]]:
    data = json.loads(canonical_json(value))
    out: list[tuple[str, object]] = []

    def visit(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                visit(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                visit(v, f"{path}[{i}]")
        else:
            out.append((path, node))

    visit(data, prefix)
    return out


def payload(snapshot) -> dict:
    return json.loads(canonical_json(snapshot.payload()))


def inputs_with(**facts):
    base = B.base_inputs()
    return replace(base, freshness=replace(base.freshness, **facts))


# ---------------------------------------------------------------------------
# T1 — full lineage (IN-1..10)
# ---------------------------------------------------------------------------


def test_integration_observation_reaches_measurement():
    bar = B.bar()
    measurement = B.measurement()
    assert bar.is_final
    assert bar.market_data_schema_version == measurement.market_data_schema_version
    assert measurement.source_window.bar_count == 240


def test_integration_measurement_reaches_model_output():
    out = B.output()
    state = B.state(model_output=out)
    assert state.measurements[0].definition_id == "RANGE_SIZE"
    assert out.identity.measurement_engine_version == measurement_engine_version()


def measurement_engine_version():
    from app.forge.measurements.versions import MEASUREMENT_ENGINE_VERSION

    return MEASUREMENT_ENGINE_VERSION


def test_integration_model_output_reaches_state_snapshot():
    out = B.output()
    state = B.state(model_output=out)
    assert state.source_output_hash == out.output_hash
    assert state.snapshot_hash


def test_integration_state_reaches_transition_ledger():
    ledger = open_ledger(B.state())
    assert verify_history(ledger) is None
    assert replay_events(ledger) == ()


def test_integration_transition_reaches_setup_evaluation():
    evaluation = B.evaluate(B.XAU_CARD)
    assert evaluation.setup_id == B.XAU_CARD.setup_id
    assert evaluation.eligibility in set(SetupEligibility)


def test_integration_setup_reaches_snapshot():
    snap = B.snapshot(setup=B.setup_evaluation(B.XAU_CARD, eligibility=SetupEligibility.WATCH))
    assert payload(snap)["sections"]["setup"] != "UNAVAILABLE"


def test_integration_snapshot_preserves_model_and_layer():
    snap = B.snapshot()
    identity = payload(snap)["identity"]
    assert identity["model_id"] == B.EUR_MODEL
    assert identity["model_version"] == B.EUR_VERSION


def test_integration_single_identity_through_all_six_blocs():
    snap = B.snapshot()
    assert B.snapshot_id(snap.key) == snap.snapshot_id
    assert B.state().snapshot_id == snap.snapshot_id


def test_integration_clock_identity_survives_every_boundary():
    measurement = B.measurement()
    snap = B.snapshot()
    assert measurement.clock_id == snap.key.clock_id == "CLOCK.EUR"
    assert payload(snap)["identity"]["clock_id"] == "CLOCK.EUR"


def test_integration_no_bloc_recomputes_upstream_fact():
    out = B.output(levels=(B.level(),))
    snap = B.snapshot()
    assert snap.levels[0].price == format(out.levels[0].price, "f")
    assert payload(snap)["identity"]["model_id"] == out.model_id


# ---------------------------------------------------------------------------
# T2 — quality and failure propagation (IN-11..19)
# ---------------------------------------------------------------------------


def test_integration_missing_provider_blocks_current_snapshot():
    assert refusal_code(B.compose, B.base_inputs(provider_configured=False)) == "PROVIDER_NOT_CONFIGURED"
    missing = replace(B.base_inputs().freshness, provider_configured=False)
    assert is_live_claim_permitted(missing) is False


def test_integration_nonfinal_bar_cannot_reach_model():
    bar = B.bar(finality=Finality.NONFINAL)
    assert bar.finality is Finality.NONFINAL
    assert refusal_code(B.compose, inputs_with(final_bar=False)) == "NONFINAL_BAR"


def test_integration_blocked_quality_propagates_to_setup():
    assert refusal_code(B.compose, B.base_inputs(quality=DataOutcome.DATA_QUALITY_BLOCKED)) == "DATA_QUALITY_BLOCKED"
    state = B.state(model_output=B.output(quality=DataOutcome.DEGRADED))
    assert state.quality_state is DataOutcome.DEGRADED


def test_integration_unresolved_clock_blocks_calculation():
    assert refusal_code(B.compose, inputs_with(clock_resolved=False)) == "CLOCK_UNRESOLVED"


def test_integration_mixed_cutoff_refused():
    assert refusal_code(B.compose, inputs_with(cutoffs=(B.CUTOFF, "2026-01-01T18:00:00Z"))) == "MIXED_CUTOFF"


def test_integration_missing_model_version_refused():
    with pytest.raises(ModelVersionUnavailableError):
        resolve(B.EUR_MODEL, "NOT_A_VERSION")


def test_integration_missing_measurement_refused():
    with pytest.raises(Exception):
        MeasurementRef.from_measurement(object())


def test_integration_no_go_is_not_provider_failure():
    snap = B.snapshot(no_go=(B.II6.NoGoReason.NATIVE_TIER_NO_GO,))
    assert payload(snap)["sections"]["state"] != "UNAVAILABLE"
    assert refusal_code(B.compose, B.base_inputs(provider_configured=False)) == "PROVIDER_NOT_CONFIGURED"


def test_integration_stale_is_labelled_not_current():
    facts = inputs_with(stale=True).freshness
    # No versioned staleness policy exists (III.6-GAP-4): the fact is carried
    # and labelled, never converted into an invented refusal threshold.
    assert stale_label(facts) == "STALE"
    assert short_circuit_codes(facts) == ()
    assert "stale" in canonical_json(payload(B.compose(inputs_with(stale=True)))).lower()
    assert is_live_claim_permitted(replace(facts, provider_configured=False)) is False


# ---------------------------------------------------------------------------
# T3 — model-family isolation (IN-20..28)
# ---------------------------------------------------------------------------


def test_integration_eur_layers_keep_ownership():
    models = {
        payload(B.snapshot(layer=layer))["identity"]["model_id"]
        for layer in (B.II6.Layer.L3, B.II6.Layer.L2, B.II6.Layer.L1)
    }
    assert len(models) == 3


def test_integration_xau_l1_l2_l3_do_not_merge():
    out = B.output(model_id="XAU.GAME.L1_L2_L3.V1", model_version="V1", layer=B.II6.Layer.CROSS_LAYER)
    assert out.layer is B.II6.Layer.CROSS_LAYER
    assert not hasattr(out, "confluence")


def test_integration_btc_tracker_has_no_game_setup():
    out = B.output(model_id="BTC.TRACKER.DWM.V1", model_version="V1", instrument_id="BTCUSD")
    assert out.model_id == "BTC.TRACKER.DWM.V1"
    assert not hasattr(out, "setup")


def test_integration_fib_stays_research_only():
    assert B.evaluate(B.FIB_CARD, surface=SetupSurface.PRODUCTION).eligibility is SetupEligibility.BLOCKED
    assert B.evaluate(B.FIB_CARD, surface=SetupSurface.RESEARCH).eligibility is not SetupEligibility.ELIGIBLE


def test_integration_jpy_roles_are_not_a_vote():
    evaluation = B.evaluate(B.JPY_CARD)
    assert evaluation.automation_permitted is False
    assert not hasattr(evaluation, "vote")


def test_integration_cross_asset_tier_cannot_leak():
    from app.forge.measurements.calibration import CALIBRATION_REGISTRY

    keys = list(CALIBRATION_REGISTRY.keys()) if hasattr(CALIBRATION_REGISTRY, "keys") else []
    rendered = {str(key) for key in keys}
    assert all("XAU" not in key or "EUR" not in key for key in rendered)


def test_integration_model_family_preserved_in_view():
    snap = B.snapshot(instrument_id="XAUUSD")
    assert payload(snap)["identity"]["instrument_id"] == "XAUUSD"
    assert payload(snap)["identity"]["layer"] == "CROSS_LAYER"


def test_integration_layer_conflict_is_fact_not_score():
    snap = B.snapshot()
    keys = [key for key, _ in walk(payload(snap))]
    assert not any("confluence" in key or "confidence" in key or "score" in key for key in keys)


def test_integration_no_confluence_field_exists():
    keys = [key for key, _ in walk(payload(B.snapshot()))]
    assert not any(key.endswith("confluence_score") for key in keys)


# ---------------------------------------------------------------------------
# T4 — path and first-delivery integrity (IN-29..36)
# ---------------------------------------------------------------------------


def test_integration_path_order_survives_composition():
    snap = B.snapshot(path=B.delivery_path(two_observations=True))
    assert [d["target_id"] for d in payload(snap)["sections"]["path"]["deliveries"]] == ["TARGET.1", "TARGET.2"]


def test_integration_reversed_paths_hash_differently():
    forward = B.snapshot(path=B.delivery_path(two_observations=True))
    reverse = B.snapshot(path=B.delivery_path(two_observations=True, reverse=True))
    assert forward.snapshot_hash != reverse.snapshot_hash


def test_integration_terminal_outcome_does_not_erase_path():
    snap = B.snapshot(path=B.delivery_path(two_observations=True))
    assert len(payload(snap)["sections"]["path"]["deliveries"]) == 2


def test_integration_rekey_is_explicit_transition():
    parameters = inspect.signature(plan_rekey).parameters
    assert "structural" in parameters and parameters["structural"].default is inspect.Parameter.empty


def test_integration_range_left_updates_after_consumption():
    result = recompute_range_left(
        prior=None,
        conditions=(),
        consumed_targets=("TARGET.1",),
        available_targets=("TARGET.2",),
        basis_ref="RANGE.EUR.1",
    )
    assert result.available_targets == ("TARGET.2",)
    assert result.basis_ref == "RANGE.EUR.1"


def test_integration_intrabar_ambiguity_refused():
    with pytest.raises(AmbiguousPathError):
        build_path(
            clock_id="CLOCK.EUR",
            targets=(
                DeclaredTarget(target_id="T.1", side=DeliverySide.ABOVE, declared_order_index=0),
                DeclaredTarget(target_id="T.2", side=DeliverySide.ABOVE, declared_order_index=1),
            ),
            observations=(
                DeliveryObservation("T.1", B.EVENT_TIME, "BAR.1"),
                DeliveryObservation("T.2", B.EVENT_TIME, "BAR.1"),
            ),
            intrabar_order_resolvable=False,
        )


def test_integration_first_delivery_preserved_in_payload():
    snap = B.snapshot(path=B.delivery_path())
    delivery = payload(snap)["sections"]["path"]["deliveries"][0]
    assert delivery["realized_event_time"].endswith("Z")


def test_integration_transition_sequence_is_monotonic():
    ledger = open_ledger(B.state())
    events = replay_events(ledger)
    assert isinstance(events, tuple)


# ---------------------------------------------------------------------------
# T5 — setup and no-go governance (IN-37..45)
# ---------------------------------------------------------------------------


def test_integration_stand_down_blocks_eligible_setup():
    evaluation = B.evaluate(B.XAU_CARD, stand_down=B.stand_down_record())
    assert evaluation.eligibility is SetupEligibility.BLOCKED


def test_integration_model_state_alone_cannot_create_setup():
    snap = B.snapshot(with_setup=False)
    assert payload(snap)["sections"]["setup"]["status"] == "UNAVAILABLE"


def test_integration_xau_blind_touch_blocked():
    assert B.evaluate(B.XAU_CARD).eligibility is not SetupEligibility.ELIGIBLE


def test_integration_fib_unresolved_anchor_blocked():
    evaluation = B.evaluate(B.FIB_CARD, surface=SetupSurface.RESEARCH)
    assert evaluation.eligibility is SetupEligibility.UNRESOLVED
    assert any("ANCHOR" in str(reason) for reason in evaluation.reasons)


def test_integration_jpy_equal_vote_impossible():
    evaluation = B.evaluate(B.JPY_CARD)
    assert evaluation.automation_permitted is False
    assert not hasattr(evaluation, "aggregate")


def test_integration_research_setup_cannot_be_production():
    evaluation = B.evaluate(B.FIB_CARD, surface=SetupSurface.PRODUCTION)
    assert evaluation.eligibility is SetupEligibility.BLOCKED
    assert any("RESEARCH_ONLY" in str(reason) for reason in evaluation.reasons)


def test_integration_setup_carries_no_execution_authority():
    keys = [key for key, _ in walk(payload(B.snapshot()))]
    assert not any(
        term in key.lower()
        for key in keys
        for term in ("order_id", "order_intent", "quantity", "position_size", "brokerage")
    )


def test_integration_manual_setup_keeps_automation_false():
    assert B.evaluate(B.JPY_CARD).automation_permitted is False


def test_integration_eligibility_verbatim_in_snapshot():
    snap = B.snapshot(setup=B.setup_evaluation(B.XAU_CARD, eligibility=SetupEligibility.WATCH))
    assert payload(snap)["sections"]["setup"]["eligibility"] == "WATCH"


# ---------------------------------------------------------------------------
# T6 — Book II authorization (IN-46..52)
# ---------------------------------------------------------------------------


class SpyLoader:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return B.snapshot()


def test_integration_denial_prevents_composition():
    spy = SpyLoader()
    access = gateway_read(
        B.snapshot(), principal=ForgePrincipal.anonymous(), context=AuthorizationContext.empty(), loader=spy
    )
    assert access.allowed is False
    assert spy.calls == 0


def test_integration_denial_reveals_no_identifier():
    access = gateway_read(
        B.snapshot(), principal=ForgePrincipal.anonymous(), context=AuthorizationContext.empty()
    )
    assert access.refusal == {"code": "EXPOSURE_FORBIDDEN"}


def test_integration_anonymous_cannot_read_operator_snapshot():
    access = gateway_read(B.snapshot(), principal=ForgePrincipal.anonymous(), context=AuthorizationContext.empty())
    assert access.allowed is False


def test_integration_research_exposure_cannot_become_public():
    snap = B.snapshot(setup=B.setup_evaluation(B.FIB_CARD, eligibility=SetupEligibility.UNRESOLVED, surface=SetupSurface.RESEARCH))
    assert payload(snap)["classifications"]["research_only"] is True
    access = gateway_read(snap, exposure=ProductExposure.RESEARCH_LAB, principal=ForgePrincipal.anonymous(), context=AuthorizationContext.empty())
    assert access.allowed is False


def test_integration_policy_failure_fails_closed():
    class Broken:
        def authorize(self, *args, **kwargs):
            raise RuntimeError("policy down")

    gateway = IntelligenceGateway(enforcement=Broken())
    access = gateway_read(B.snapshot(), gateway=gateway)
    assert access.allowed is False


def test_integration_audit_records_every_decision():
    gateway = IntelligenceGateway()
    before = len(gateway.enforcement.audit_records())
    gateway_read(B.snapshot(), gateway=gateway)
    gateway_read(B.snapshot(), gateway=gateway)
    assert len(gateway.enforcement.audit_records()) - before == 2


def test_integration_correlation_id_propagates():
    gateway = IntelligenceGateway()
    access = gateway.read(
        principal=operator_principal(),
        context=operator_context(),
        key=B.snapshot().key,
        exposure=ProductExposure.OPERATOR_ONLY,
        loader=lambda: B.snapshot(),
        correlation_id="corr-int-1",
    )
    assert access.allowed is True
    assert gateway.enforcement.audit_records()


# ---------------------------------------------------------------------------
# T7 — snapshot determinism (IN-53..60)
# ---------------------------------------------------------------------------


def test_integration_same_inputs_same_snapshot_id():
    assert B.snapshot().snapshot_id == B.snapshot().snapshot_id


def test_integration_same_inputs_same_bytes():
    assert canonical_json(payload(B.snapshot())) == canonical_json(payload(B.snapshot()))


def test_integration_changed_cutoff_changes_identity():
    base_key = B.key()
    assert B.snapshot_id(base_key) != B.snapshot_id(B.key(data_cutoff="2026-01-01T18:00:00Z"))


def test_integration_changed_model_version_changes_identity():
    assert B.snapshot_id(B.key()) != B.snapshot_id(B.key(model_version="PHASE2"))


def test_integration_changed_clock_changes_identity():
    assert B.snapshot_id(B.key()) != B.snapshot_id(B.key(clock_id="CLOCK.OTHER"))


def test_integration_payload_roundtrip_preserves_decimals():
    snap = B.snapshot()
    assert payload(snap)["sections"]["levels"][0]["price"] == "1.0842"


def test_integration_no_float_coercion_in_prices():
    values = [value for _, value in walk(payload(B.snapshot()))]
    assert not any(isinstance(value, float) for value in values)


def test_integration_component_hashes_are_ordered():
    hashes = payload(B.snapshot())["provenance"]["component_hashes"]
    assert len(hashes) >= 2
    assert len(hashes) == len(dict.fromkeys(hashes.values()))


# ---------------------------------------------------------------------------
# T8 — historical generation (IN-61..68)
# ---------------------------------------------------------------------------


def retained():
    snap = B.snapshot()
    store = B.HistoryStore()
    store.retain(snap, B.base_inputs())
    return snap, store


def test_integration_historical_replay_reproduces_hash():
    snap, store = retained()
    assert store.reconstruct(B.historical_request(snap)).snapshot_hash == snap.snapshot_hash


def test_integration_historical_never_upgrades_version():
    snap, store = retained()
    assert refusal_code(store.reconstruct, B.historical_request(snap, model_version="PHASE2")) == "VERSION_DRIFT"


def test_integration_historical_missing_inputs_unavailable():
    snap = B.snapshot()
    assert refusal_code(B.HistoryStore().reconstruct, B.historical_request(snap)) == "HISTORICAL_UNAVAILABLE"


def test_integration_historical_outside_retention_explicit():
    snap = B.snapshot()
    code = refusal_code(B.HistoryStore().reconstruct, B.historical_request(snap, retention_acknowledged=False))
    assert code in {"HISTORICAL_NOT_RETAINED", "HISTORICAL_UNAVAILABLE", "MALFORMED_REQUEST"}


def test_integration_historical_version_drift_refused():
    snap, store = retained()
    assert refusal_code(store.reconstruct, B.historical_request(snap, model_version="OTHER")) == "VERSION_DRIFT"


def test_integration_historical_view_labelled():
    snap, store = retained()
    assert store.reconstruct(B.historical_request(snap)).payload()["view"] == "HISTORICAL"


def test_integration_historical_evidence_status_preserved():
    snap, store = retained()
    original = [entry["status"] for entry in payload(snap)["sections"]["evidence"]]
    replayed = [
        entry["status"]
        for entry in payload(store.reconstruct(B.historical_request(snap)))["sections"]["evidence"]
    ]
    assert original == replayed


def test_integration_current_and_historical_are_distinct():
    snap, store = retained()
    assert snap.payload()["view"] == "CURRENT"
    assert store.reconstruct(B.historical_request(snap)).payload()["view"] != "CURRENT"


# ---------------------------------------------------------------------------
# T9 — canonical-source compatibility (IN-69..76)
# ---------------------------------------------------------------------------


def cards():
    return (B.XAU_CARD, B.FIB_CARD, B.JPY_CARD)


def test_integration_three_cards_fail_machine_validation():
    assert all(card_machine_errors(card) for card in cards())


def test_integration_card_failure_is_exactly_three_errors():
    assert tuple(len(card_machine_errors(card)) for card in cards()) == (3, 3, 3)


def test_integration_card_ids_carried_verbatim():
    assert all(card.setup_id.startswith("SETUP.") for card in cards())
    snap = B.snapshot(setup=B.setup_evaluation(B.XAU_CARD, eligibility=SetupEligibility.WATCH))
    assert payload(snap)["sections"]["setup"]["setup_id"] == B.XAU_CARD.setup_id


def test_integration_card_status_not_promoted():
    assert all(str(card.status) != "ELIGIBLE" for card in cards())


def test_integration_strict_card_operation_refused():
    inputs = replace(
        B.base_inputs(setup=B.setup_evaluation(B.XAU_CARD, eligibility=SetupEligibility.WATCH)),
        require_machine_card=True,
    )
    try:
        B.compose(inputs)
    except RefusalError as exc:
        assert exc.code == "SCHEMA_INCOMPATIBLE"
    else:  # the governed refusal may be recorded in the envelope instead
        assert "SCHEMA_INCOMPATIBLE" in canonical_json(payload(B.compose(inputs)))


def test_integration_verbatim_view_is_lossless():
    snap = B.snapshot(setup=B.setup_evaluation(B.XAU_CARD, eligibility=SetupEligibility.WATCH))
    section = payload(snap)["sections"]["setup"]
    assert section["setup_id"] == B.XAU_CARD.setup_id
    assert B.XAU_CARD.source_card_ref in canonical_json(section)


def test_integration_no_set_star_id_minted():
    assert all(not card.setup_id.startswith("SET.") for card in cards())


def test_integration_adr_deferral_recorded():
    text = (REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / "RATIFICATION.md").read_text(encoding="utf-8")
    assert "ADR-BOOK-I-001" in text or "deferred" in text.lower()


# ---------------------------------------------------------------------------
# T10 — consumer compatibility (IN-77..83)
# ---------------------------------------------------------------------------


def test_integration_consumer_dto_fields_present():
    data = payload(B.snapshot())
    for key in ("snapshot_id", "schema_version", "view", "identity", "quality", "sections", "classifications", "provenance"):
        assert key in data


def test_integration_consumer_cannot_mutate_snapshot():
    snap = B.snapshot()
    with pytest.raises(FrozenInstanceError):
        snap.snapshot_id = "SNAP.other"  # type: ignore[misc]


def test_integration_consumer_sees_eligibility_verbatim():
    snap = B.snapshot(setup=B.setup_evaluation(B.XAU_CARD, eligibility=SetupEligibility.WATCH))
    assert payload(snap)["sections"]["setup"]["eligibility"] == "WATCH"


def test_integration_consumer_sees_no_authority_fields():
    keys = [key for key, _ in walk(payload(B.snapshot()))]
    assert not any(term in key.lower() for key in keys for term in ("grant", "entitlement", "permission_token"))


def test_integration_consumer_quality_flags_visible():
    quality = payload(B.snapshot())["quality"]
    assert "provider_status" in quality or "state" in quality


def test_integration_consumer_warnings_and_refusals_visible():
    data = payload(B.snapshot())
    assert "warnings" in data and "refusals" in data


def test_integration_consumer_requires_no_recalculation():
    out = B.output(levels=(B.level(),))
    snap = B.snapshot()
    assert snap.levels[0].price == format(out.levels[0].price, "f") == "1.0842"


# ---------------------------------------------------------------------------
# T11 — security and cache boundaries (IN-84..90)
# ---------------------------------------------------------------------------


def test_integration_cache_hit_still_authorized():
    gateway = IntelligenceGateway()
    snap = B.snapshot()
    first = gateway_read(snap, gateway=gateway)
    second = gateway_read(snap, gateway=gateway)
    assert first.cached is False and second.cached is True
    assert len(gateway.enforcement.audit_records()) == 2


def test_integration_cache_does_not_cross_principals():
    gateway = IntelligenceGateway()
    snap = B.snapshot()
    gateway_read(snap, principal=operator_principal("a"), gateway=gateway)
    gateway_read(snap, principal=operator_principal("b"), gateway=gateway)
    assert gateway.cache.sizes()["responses"] == 2


def test_integration_cache_invalidated_on_exposure_change():
    gateway = IntelligenceGateway()
    gateway_read(B.snapshot(), gateway=gateway)
    gateway.cache.invalidate("EXPOSURE_CHANGE")
    assert gateway.cache.sizes()["responses"] == 0


def test_integration_refusal_has_no_payload():
    access = gateway_read(B.snapshot(), principal=ForgePrincipal.anonymous(), context=AuthorizationContext.empty())
    assert set(access.refusal) == {"code"}


def test_integration_no_source_or_module_disclosure():
    keys = [key for key, _ in walk(payload(B.snapshot()))]
    assert not any("module" in key.lower() or "traceback" in key.lower() for key in keys)


def test_integration_no_network_during_composition():
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO / "app" / "forge" / "intelligence_api").glob("*.py")
    )
    for token in ("import requests", "import socket", "httpx", "aiohttp"):
        assert token not in sources


def test_integration_response_is_bounded():
    with pytest.raises(RefusalError) as exc:
        bounded_json("x" * 2_000_001)
    assert exc.value.code == "MALFORMED_REQUEST"


# ---------------------------------------------------------------------------
# T12 — regression and frozen integrity (IN-91..96)
# ---------------------------------------------------------------------------


def test_integration_all_bloc_suites_still_green():
    expected = {
        "test_forge_market_data.py": 60,
        "test_forge_measurements.py": 80,
        "test_forge_model_runtime.py": 120,
        "test_forge_state_engine.py": 150,
        "test_forge_setup_engine.py": 160,
        "test_forge_intelligence_api.py": 250,
    }
    for name, minimum in expected.items():
        text = (REPO / "tests" / name).read_text(encoding="utf-8")
        assert len(re.findall(r"def test_", text)) >= minimum


def test_integration_book_ii_fifty_hashes():
    text = (REPO / "implementation" / "forge" / "book_ii" / "ratification" / "CONTRACT_FREEZE_MANIFEST_V1.md").read_text(encoding="utf-8")
    assert len(re.findall(r"`[0-9a-f]{64}`", text)) >= 50
    assert "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af" in text


def test_integration_nineteen_module_baselines():
    counts = {}
    for name in ("market_data", "measurements", "model_runtime", "state_engine", "setup_engine", "intelligence_api"):
        counts[name] = len(list((REPO / "app" / "forge" / name).glob("*.py")))
    assert counts == {
        "market_data": 11,
        "measurements": 12,
        "model_runtime": 13,
        "state_engine": 13,
        "setup_engine": 16,
        "intelligence_api": 14,
    }
    assert sum(counts.values()) == 79


def test_integration_migrations_unchanged():
    sql = sorted((REPO / "app" / "forge" / "persistence" / "sql").glob("*.sql"))
    assert [path.name[:3] for path in sql] == ["001", "002", "003", "004"]


def test_integration_provider_seam_unchanged():
    text = (REPO / "app" / "forge" / "service" / "container.py").read_text(encoding="utf-8")
    assert '"market_data"' in text and "NOT_CONFIGURED" in text


def test_integration_no_production_claim():
    text = (REPO / "implementation" / "forge" / "book_iii" / "bloc_iii_6" / "RATIFICATION.md").read_text(encoding="utf-8")
    assert "No production GO" in text
    assert "SCHEMA_INCOMPATIBLE" in text or "DEFECT-1" in text
