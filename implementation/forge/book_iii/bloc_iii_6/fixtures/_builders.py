"""Deterministic synthetic builders for the III.6 golden fixtures.

Structural proof only: these builders produce fixture inputs, never market
claims, probabilities or performance figures. Upstream truth is constructed
through the ratified III.1-III.5 types and evaluated by their own code.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.forge.canonical import EvidenceStatus, ProductExposure, SetupClass
from app.forge.identity import ForgePrincipal
from app.forge.intelligence_api.composition import CompositionInputs, compose
from app.forge.intelligence_api.contracts import EvidenceLink, LineageFacts, SnapshotKey
from app.forge.intelligence_api.errors import RefusalError
from app.forge.intelligence_api.freshness import FreshnessFacts
from app.forge.intelligence_api.history import HistoryStore
from app.forge.intelligence_api.policy_gate import IntelligenceGateway
from app.forge.intelligence_api.requests import HistoricalRequest, SetupContextRequest
from app.forge.intelligence_api.versions import VIEW_CURRENT
from app.forge.market_data.quality import DataOutcome, QualityFlag
from app.forge.market_data.versions import MARKET_DATA_SCHEMA_VERSION
from app.forge.measurements.contracts import Measurement, SourceWindow
from app.forge.measurements.path_metrics import RemainingState
from app.forge.measurements.versions import MEASUREMENT_ENGINE_VERSION
from app.forge.model_runtime.contract import (
    DirectionBias,
    DirectionSide,
    ExplanationFact,
    InputIdentity,
    Layer,
    LevelKind,
    ModelOutput,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    SubState,
    TypedLevel,
    WarningCode,
)
from app.forge.policy import AuthorizationContext
from app.forge.setup_engine.contracts import (
    EvidenceReference,
    SetupEligibility,
    SetupRefusalCode,
    SetupSurface,
)
from app.forge.setup_engine.eligibility import GateOutcome, SetupEvaluation
from app.forge.setup_engine.registry import CardStatus, load_canonical_cards
from app.forge.setup_engine.versions import SETUP_CONTRACT_VERSION, SETUP_ENGINE_VERSION
from app.forge.state_engine.delivery import (
    DeclaredTarget,
    DeliveryObservation,
    DeliverySide,
    build_path,
)
from app.forge.state_engine.snapshot import MeasurementRef, StateSnapshot, finalize_snapshot
from app.forge.state_engine.stand_down import StandDownReason, StandDownRecord, StandDownState

AS_OF = "2026-01-02T00:00:00Z"
CUTOFF = "2026-01-01T17:00:00Z"
CALC = "CALC.V1"
EVENT_TIME = datetime(2026, 1, 1, 17, 0, tzinfo=timezone.utc)
CALC_TS = datetime(2026, 1, 2, 0, 5, tzinfo=timezone.utc)
EUR_MODEL = "EUR.DAILY.NEWS_REKEY.V1"
EUR_VERSION = "PHASE1"
MODEL_BY_INSTRUMENT = {
    "EURUSD": (EUR_MODEL, EUR_VERSION, Layer.L1),
    "XAUUSD": ("XAU.GAME.L1_L2_L3.V1", "V1", Layer.CROSS_LAYER),
    "USDJPY": ("JPY.CARRY_GAME.L1_L3.V1", "V1", Layer.CROSS_LAYER),
    "AUDJPY": ("JPY.CARRY_GAME.L1_L3.V1", "V1", Layer.CROSS_LAYER),
    "EURJPY": ("JPY.CARRY_GAME.L1_L3.V1", "V1", Layer.CROSS_LAYER),
}
MODEL_BY_LAYER = {
    Layer.L3: ("EUR.HIGHER_ORDER.V1", "V1"),
    Layer.L2: ("EUR.WEEKLY.V1_1", "V1_1"),
    Layer.L1: (EUR_MODEL, EUR_VERSION),
}
DIGEST = "a" * 64

_CARDS = {card.setup_id: card for card in load_canonical_cards()}
XAU_CARD = next(card for card in _CARDS.values() if card.setup_id.startswith("SETUP.XAU"))
FIB_CARD = next(card for card in _CARDS.values() if card.setup_id.startswith("SETUP.FIB"))
JPY_CARD = next(card for card in _CARDS.values() if card.setup_id.startswith("SETUP.JPY"))


def key(
    *,
    instrument_id: str = "EURUSD",
    model_id: str = EUR_MODEL,
    model_version: str = EUR_VERSION,
    layer: Layer = Layer.L1,
    as_of: str = AS_OF,
    data_cutoff: str = CUTOFF,
    calculation_version: str = CALC,
    clock_id: str | None = "CLOCK.EUR",
    session_id: str | None = "SESSION.EUR",
) -> SnapshotKey:
    return SnapshotKey(
        instrument_id=instrument_id,
        model_id=model_id,
        model_version=model_version,
        layer=layer,
        as_of=as_of,
        data_cutoff=data_cutoff,
        calculation_version=calculation_version,
        clock_id=clock_id,
        session_id=session_id,
    )


def level(
    level_id: str = "EUR.L1.ZONE",
    *,
    price: str = "1.0842",
    kind: LevelKind = LevelKind.COORDINATE,
    active: bool = True,
    family: str = "ZONE",
    source_ref: str = "EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md",
) -> TypedLevel:
    return TypedLevel(
        level_id=level_id,
        level_kind=kind,
        family=family,
        level=None,
        price=Decimal(price),
        active=active,
        source_ref=source_ref,
    )


def output(
    *,
    model_id: str = EUR_MODEL,
    model_version: str = EUR_VERSION,
    layer: Layer = Layer.L1,
    state: str = "ACCEPTED",
    side: DirectionSide | None = DirectionSide.UP,
    quality: DataOutcome = DataOutcome.OK,
    no_go: tuple[NoGoReason, ...] = (),
    warnings: tuple[WarningCode, ...] = (),
    levels: tuple[TypedLevel, ...] = (),
    authorization: ProductionAuthorization = ProductionAuthorization.MANUAL_OPERATOR,
    instrument_id: str = "EURUSD",
) -> ModelOutput:
    bias = (
        DirectionBias(side=side, basis_fact_id="FACT.DIRECTION", evidence_refs=("EV.EUR.1",))
        if side is not None
        else DirectionBias.none()
    )
    identity = InputIdentity(
        instrument_id=instrument_id,
        calibration_key=None,
        clock_id="CLOCK.EUR",
        session_id="SESSION.EUR",
        calculation_timestamp=CALC_TS,
        market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        clock_registry_version="CLOCK_REGISTRY.V1",
        session_registry_version="SESSION_REGISTRY.V1",
        measurement_engine_version=MEASUREMENT_ENGINE_VERSION,
        model_runtime_version="MODEL_RUNTIME_V1",
        prior_state_ref=None,
    )
    return ModelOutput(
        model_id=model_id,
        model_version=model_version,
        model_runtime_version="MODEL_RUNTIME_V1",
        output_hash="b" * 64,
        model_state=state,
        layer=layer,
        direction_bias=bias,
        active_ranges=("RANGE.EUR.1",),
        active_anchor_states=(),
        levels=levels,
        range_left=RangeLeftField.unresolved(conditioned_on=("RANGE.EUR.1",)),
        no_go=no_go,
        warnings=warnings,
        claim_refs=(),
        evidence_refs=("EV.EUR.1",),
        quality_state=quality,
        production_authorization=authorization,
        explanation_facts=(
            ExplanationFact(
                fact_id="FACT.DIRECTION",
                rule_id="RULE.EUR.DIRECTION",
                rule_version="V1",
                source_ref="EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md",
                payload=(("side", "UP"),),
            ),
        ),
        sub_states=(SubState(label="DAILY", layer=Layer.L1, state=state, fact_ids=("FACT.DIRECTION",)),),
        identity=identity,
    )


def state_snapshot(model_output: ModelOutput, *, snapshot_id: str) -> StateSnapshot:
    snapshot = StateSnapshot.from_output(
        model_output,
        event_time=EVENT_TIME,
        snapshot_id=snapshot_id,
        measurements=(
            Measurement(
                definition_id="RANGE_SIZE",
                definition_version="V1",
                instrument_id=model_output.identity.instrument_id,
                source_window=SourceWindow(
                    window_open_utc=EVENT_TIME,
                    window_close_utc=EVENT_TIME,
                    input_digest=DIGEST,
                    bar_count=240,
                ),
                clock_id="CLOCK.EUR",
                clock_registry_version="CLOCK_REGISTRY.V1",
                session_id="SESSION.EUR",
                session_registry_version="SESSION_REGISTRY.V1",
                calculation_timestamp=CALC_TS,
                quality_state=(
                    DataOutcome.DEGRADED
                    if model_output.quality_state is DataOutcome.DEGRADED
                    else DataOutcome.OK
                ),
                native_unit=None,
                market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
                measurement_engine_version=MEASUREMENT_ENGINE_VERSION,
                evidence_refs=("EV.EUR.1",),
            ),
        ),
    )
    return finalize_snapshot(snapshot)


def delivery_path(*, ambiguous: bool = False, two_observations: bool = False, reverse: bool = False):
    observations = [
        DeliveryObservation(
            target_id="TARGET.1",
            realized_event_time=EVENT_TIME,
            realizing_bar_ref="BAR.2026-01-01T17",
        )
    ]
    if two_observations:
        observations.append(
            DeliveryObservation(
                target_id="TARGET.2",
                realized_event_time=EVENT_TIME,
                realizing_bar_ref="BAR.2026-01-01T18",
            )
        )
    if reverse:
        observations = list(reversed(observations))
    path = build_path(
        clock_id="CLOCK.EUR",
        targets=(
            DeclaredTarget(target_id="TARGET.1", side=DeliverySide.ABOVE, declared_order_index=0),
            DeclaredTarget(target_id="TARGET.2", side=DeliverySide.ABOVE, declared_order_index=1),
        ),
        observations=tuple(observations),
        intrabar_order_resolvable=True,
    )
    if ambiguous:
        from dataclasses import replace as _replace

        path = _replace(path, ambiguous=True)
    return path


def evidence_links(*, exposure: ProductExposure | None = None) -> tuple[EvidenceLink, ...]:
    return (
        EvidenceLink(
            claim_id="CL.EUR.1",
            evidence_id="EV.EUR.1",
            status=EvidenceStatus.OBSERVED,
            relationship=True,
            population_key="EUR_DAILY",
            exposure=exposure,
        ),
    )


def setup_evaluation(
    card=None,
    *,
    setup_id: str | None = None,
    eligibility: SetupEligibility = SetupEligibility.WATCH,
    surface: SetupSurface = SetupSurface.OPERATOR,
    reasons: tuple[SetupRefusalCode, ...] = (),
    record=None,
) -> SetupEvaluation:
    return SetupEvaluation(
        setup_id=setup_id or (card.setup_id if card is not None else "SETUP.UNKNOWN.V1"),
        setup_version=(card.version if card is not None else None),
        surface=surface,
        card=card,
        eligibility=eligibility,
        reasons=reasons,
        gates=(GateOutcome(gate="REGISTRY", verdict=eligibility),),
        record=record,
    )


def base_inputs(
    *,
    with_setup: bool = False,
    setup: SetupEvaluation | None = None,
    path=None,
    quality: DataOutcome = DataOutcome.OK,
    provider_configured: bool = True,
    stale: bool = False,
    model_version: str | None = None,
    output_version: str | None = None,
    instrument_id: str = "EURUSD",
    layer: Layer | None = None,
    as_of: str = AS_OF,
    data_cutoff: str = CUTOFF,
    calculation_version: str = CALC,
    stand_down: StandDownRecord | None = None,
    no_go: tuple[NoGoReason, ...] = (),
    warnings: tuple[WarningCode, ...] = (),
    materialized_rule: bool = True,
) -> CompositionInputs:
    default_model, default_version, default_layer = MODEL_BY_INSTRUMENT.get(
        instrument_id, (EUR_MODEL, EUR_VERSION, Layer.L1)
    )
    resolved_layer = default_layer if layer is None else layer
    if resolved_layer is not default_layer and instrument_id == "EURUSD":
        default_model, default_version = MODEL_BY_LAYER[resolved_layer]
    resolved_version = default_version if model_version is None else model_version
    emitted_version = default_version if output_version is None else output_version
    model_output = output(
        model_id=default_model,
        model_version=emitted_version,
        layer=resolved_layer,
        quality=quality,
        no_go=no_go,
        warnings=warnings,
        levels=(level(),),
        instrument_id=instrument_id,
    )
    model_key = key(
        instrument_id=instrument_id,
        model_id=default_model,
        model_version=resolved_version,
        layer=resolved_layer,
        as_of=as_of,
        data_cutoff=data_cutoff,
        calculation_version=calculation_version,
    )
    from app.forge.intelligence_api.identity import snapshot_id as derive

    blocked = quality in (DataOutcome.DATA_QUALITY_BLOCKED, DataOutcome.NO_CALCULATION)
    snapshot = None if blocked else state_snapshot(model_output, snapshot_id=derive(model_key))
    return CompositionInputs(
        key=model_key,
        outputs=(model_output,),
        state_snapshots=() if snapshot is None else (snapshot,),
        measurements=() if snapshot is None else snapshot.measurements,
        path=delivery_path() if path is None else path,
        setup=setup,
        evidence=evidence_links(),
        freshness=FreshnessFacts(
            provider_configured=provider_configured,
            final_bar=True,
            stale=stale,
            quality_outcome=quality,
            cutoffs=(CUTOFF,),
            request_model_version=resolved_version,
            component_model_version=emitted_version,
        ),
        stand_down=stand_down,
        lineage=LineageFacts(
            prior_snapshot_id=None,
            genesis_snapshot_id=(snapshot.snapshot_id if snapshot is not None else None),
        ),
        engine_versions=(),
        registry_versions=(
            ("clock_registry", "CLOCK_REGISTRY.V1"),
            ("session_registry", "SESSION_REGISTRY.V1"),
        ),
        source_window_digest=DIGEST,
        materialized_rule=materialized_rule,
        view=VIEW_CURRENT,
    )


def stand_down_record(snapshot_ref: str = "SNAP.FIXTURE") -> StandDownRecord:
    return StandDownRecord(
        state=StandDownState.DATA_QUALITY_FAILURE,
        reason=StandDownReason.DATA_BAD,
        blocking_rule_ref="RULE.STANDDOWN.DATA",
        snapshot_id=snapshot_ref,
    )


def instrument_path_inputs() -> tuple[CompositionInputs, CompositionInputs, CompositionInputs]:
    l3 = base_inputs(layer=Layer.L3)
    l2 = base_inputs(layer=Layer.L2)
    l1 = base_inputs(layer=Layer.L1)
    return l3, l2, l1


def case_inputs(name: str) -> CompositionInputs:
    if name == "consistent_eur_snapshot":
        return base_inputs()
    if name == "model_only_no_setup":
        return base_inputs(with_setup=False)
    if name == "stand_down_lock":
        return base_inputs(stand_down=stand_down_record(), no_go=(NoGoReason.NATIVE_TIER_NO_GO,))
    if name == "missing_provider":
        return base_inputs(provider_configured=False)
    if name == "data_quality_failure":
        return base_inputs(quality=DataOutcome.DATA_QUALITY_BLOCKED)
    if name == "research_only_fib":
        return base_inputs(
            setup=setup_evaluation(FIB_CARD, eligibility=SetupEligibility.ELIGIBLE, surface=SetupSurface.RESEARCH),
        )
    if name == "manual_jpy":
        return base_inputs(
            setup=setup_evaluation(JPY_CARD, eligibility=SetupEligibility.WATCH, surface=SetupSurface.OPERATOR),
            instrument_id="USDJPY",
        )
    if name == "xau_watch_ceiling":
        return base_inputs(
            setup=setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH),
            instrument_id="XAUUSD",
        )
    if name == "historical_version_mismatch":
        return base_inputs(model_version="PHASE2")
    if name == "card_schema_incompatibility":
        return base_inputs(
            setup=setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH),
            instrument_id="XAUUSD",
        )
    if name == "restricted_exposure":
        return base_inputs(with_setup=True, setup=setup_evaluation(XAU_CARD, eligibility=SetupEligibility.WATCH))
    if name == "deterministic_reconstruction":
        return base_inputs()
    raise ValueError(f"unknown fixture case: {name}")


CASE_NAMES = (
    "consistent_eur_snapshot",
    "model_only_no_setup",
    "stand_down_lock",
    "missing_provider",
    "data_quality_failure",
    "research_only_fib",
    "manual_jpy",
    "xau_watch_ceiling",
    "historical_version_mismatch",
    "card_schema_incompatibility",
    "restricted_exposure",
    "deterministic_reconstruction",
)


def build_case(name: str) -> dict:
    inputs = case_inputs(name)
    if name == "historical_version_mismatch":
        try:
            compose(inputs)
        except RefusalError as exc:
            return {"case": name, "kind": "REFUSAL", "code": exc.code}
        raise AssertionError("historical version mismatch must be refused")
    if name == "card_schema_incompatibility":
        from dataclasses import replace

        try:
            compose(replace(inputs, require_machine_card=True))
        except RefusalError as exc:
            return {"case": name, "kind": "REFUSAL", "code": exc.code}
        raise AssertionError("machine card projection must be refused")
    if name == "restricted_exposure":
        snapshot = compose(inputs)
        gateway = IntelligenceGateway()
        access = gateway.read(
            principal=ForgePrincipal.anonymous(),
            context=AuthorizationContext.empty(),
            key=snapshot.key,
            exposure=ProductExposure.OPERATOR_ONLY,
            loader=lambda: snapshot,
        )
        return {
            "case": name,
            "kind": "DENIAL" if not access.allowed else "SNAPSHOT",
            "code": access.refusal["code"] if access.refusal else None,
        }
    if name == "deterministic_reconstruction":
        snapshot = compose(inputs)
        store = HistoryStore()
        store.retain(snapshot, inputs)
        request = HistoricalRequest(
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
        replayed = store.reconstruct(request)
        return {
            "case": name,
            "kind": "RECONSTRUCTION",
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_hash": snapshot.snapshot_hash,
            "replayed_hash": replayed.snapshot_hash,
            "match": snapshot.snapshot_hash == replayed.snapshot_hash,
        }
    try:
        snapshot = compose(inputs)
    except RefusalError as exc:
        return {"case": name, "kind": "REFUSAL", "code": exc.code}
    return {"case": name, "kind": "SNAPSHOT", "payload": snapshot.payload()}
