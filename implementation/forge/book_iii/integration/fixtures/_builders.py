"""Deterministic builders for the Book III cross-bloc integration program.

Structural proof only. Every object is constructed through the ratified
public interfaces of III.1-III.6; nothing here re-derives a measurement,
model rule, transition or setup verdict. The III.6 fixture builders are
reused rather than duplicated so that the integration fixtures and the
bloc fixtures describe the same synthetic inputs.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.forge.intelligence_api.composition import compose
from app.forge.intelligence_api.errors import RefusalError
from app.forge.intelligence_api.freshness import FreshnessFacts
from app.forge.intelligence_api.history import HistoryStore
from app.forge.intelligence_api.identity import snapshot_id as derive_snapshot_id
from app.forge.intelligence_api.requests import HistoricalRequest
from app.forge.market_data.bars import Bar, Finality, ProvenanceKind
from app.forge.market_data.quality import DataOutcome, QualityFlag
from app.forge.market_data.versions import MARKET_DATA_SCHEMA_VERSION
from app.forge.measurements.contracts import Measurement, SourceWindow
from app.forge.measurements.versions import MEASUREMENT_ENGINE_VERSION
from app.forge.model_runtime.contract import ModelOutput
from app.forge.setup_engine.contracts import SetupEligibility, SetupSurface
from app.forge.setup_engine.eligibility import SetupEvaluationRequest, evaluate_setup
from app.forge.state_engine.delivery import DeclaredTarget, DeliveryObservation, DeliverySide, build_path
from app.forge.state_engine.snapshot import MeasurementRef, StateSnapshot, finalize_snapshot

_HERE = pathlib.Path(__file__).resolve()
_BLOC_III_6 = _HERE.parents[2] / "bloc_iii_6" / "fixtures" / "_builders.py"
_SPEC = importlib.util.spec_from_file_location("ii6_fixture_builders", _BLOC_III_6)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - structural
    raise RuntimeError("III.6 fixture builders are not importable")
II6 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(II6)

AS_OF = II6.AS_OF
CUTOFF = II6.CUTOFF
CALC = II6.CALC
CALC_TS = II6.CALC_TS
EVENT_TIME = II6.EVENT_TIME
DIGEST = II6.DIGEST
EUR_MODEL = II6.EUR_MODEL
EUR_VERSION = II6.EUR_VERSION
XAU_CARD = II6.XAU_CARD
FIB_CARD = II6.FIB_CARD
JPY_CARD = II6.JPY_CARD
key = II6.key
output = II6.output
evidence_links = II6.evidence_links
stand_down_record = II6.stand_down_record
base_inputs = II6.base_inputs
setup_evaluation = II6.setup_evaluation
delivery_path = II6.delivery_path
level = II6.level
snapshot_id = derive_snapshot_id

__all__ = [
    "Bar", "Finality", "QualityFlag", "DataOutcome", "Measurement", "SourceWindow",
    "StateSnapshot", "MeasurementRef", "SetupEvaluationRequest", "evaluate_setup",
    "SetupEligibility", "SetupSurface", "CompositionInputs", "compose", "HistoryStore",
    "HistoricalRequest", "FreshnessFacts", "snapshot_id", "level", "builders",
]


# ---------------------------------------------------------------------------
# III.1 observation
# ---------------------------------------------------------------------------


def bar(
    *,
    finality: Finality = Finality.FINAL,
    flags: frozenset[QualityFlag] = frozenset(),
    close_time: datetime = EVENT_TIME,
    instrument_id: str = "EURUSD",
) -> Bar:
    """A normalized III.1 bar. Synthetic provenance can never cite evidence."""

    return Bar(
        instrument_id=instrument_id,
        timeframe="M5",
        open_time=close_time - timedelta(minutes=5),
        close_time=close_time,
        open=Decimal("1.0840"),
        high=Decimal("1.0860"),
        low=Decimal("1.0830"),
        close=Decimal("1.0850"),
        volume=Decimal("1200"),
        provider="synthetic_fixture",
        finality=finality,
        source_timestamp=close_time,
        quality_flags=flags,
        provenance=ProvenanceKind.SYNTHETIC_FIXTURE,
        source_ref=None,
        market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
    )


def measurement(*, quality: DataOutcome = DataOutcome.OK, digest: str = DIGEST) -> Measurement:
    return Measurement(
        definition_id="RANGE_SIZE",
        definition_version="V1",
        instrument_id="EURUSD",
        source_window=SourceWindow(
            window_open_utc=EVENT_TIME,
            window_close_utc=EVENT_TIME,
            input_digest=digest,
            bar_count=240,
        ),
        clock_id="CLOCK.EUR",
        clock_registry_version="CLOCK_REGISTRY.V1",
        session_id="SESSION.EUR",
        session_registry_version="SESSION_REGISTRY.V1",
        calculation_timestamp=CALC_TS,
        quality_state=quality,
        native_unit=None,
        market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        measurement_engine_version=MEASUREMENT_ENGINE_VERSION,
        evidence_refs=("EV.EUR.1",),
    )


def state(*, model_output: ModelOutput | None = None) -> StateSnapshot:
    out = model_output or output()
    snap = StateSnapshot.from_output(
        out,
        event_time=EVENT_TIME,
        snapshot_id=derive_snapshot_id(key(model_id=out.model_id, model_version=out.model_version, layer=out.layer)),
        measurements=(measurement(quality=out.quality_state),),
    )
    return finalize_snapshot(snap)


def composition_inputs(**overrides):
    return base_inputs(**overrides)


def snapshot(**overrides):
    return compose(base_inputs(**overrides))


def inputs_with_freshness(**facts):
    return replace(base_inputs(), freshness=replace(base_inputs().freshness, **facts))


def historical_request(snapshot_obj, **overrides) -> HistoricalRequest:
    k = snapshot_obj.key
    values = dict(
        instrument_id=k.instrument_id,
        model_id=k.model_id,
        model_version=k.model_version,
        layer=k.layer,
        as_of=k.as_of,
        data_cutoff=k.data_cutoff,
        calculation_version=k.calculation_version,
        clock_id=k.clock_id,
        session_id=k.session_id,
        retention_acknowledged=True,
    )
    values.update(overrides)
    return HistoricalRequest(**values)


def setup_request(card, *, surface: SetupSurface = SetupSurface.OPERATOR, stand_down=None, anchors=()) -> SetupEvaluationRequest:
    return SetupEvaluationRequest(
        setup_id=card.setup_id,
        setup_version=card.version,
        surface=surface,
        parents=(output(),),
        anchors=tuple(anchors),
        stand_down=stand_down,
        evaluation_time=AS_OF,
    )


def evaluate(card, **kwargs):
    return evaluate_setup(setup_request(card, **kwargs))


# ---------------------------------------------------------------------------
# Fixture cases
# ---------------------------------------------------------------------------


def _lineage() -> dict:
    b = bar()
    m = measurement()
    out = output()
    st = state(model_output=out)
    snap = compose(base_inputs())
    return {
        "bar_digest": b.dumps(),
        "measurement_digest": m.source_window.input_digest,
        "output_hash": out.output_hash,
        "state_hash": st.snapshot_hash,
        "snapshot_id": snap.snapshot_id,
        "snapshot_hash": snap.snapshot_hash,
    }


def case(name: str) -> dict:
    if name == "full_eur_lineage":
        data = _lineage()
        return {"case": name, "kind": "LINEAGE", **{k: v for k, v in data.items() if k != "bar_digest"}}
    if name == "xau_promotion_chain":
        evaluation = evaluate(XAU_CARD)
        return {"case": name, "kind": "SETUP", "eligibility": evaluation.eligibility.value}
    if name == "btc_tracker_no_game":
        out = output(model_id="BTC.TRACKER.DWM.V1", model_version="V1", instrument_id="BTCUSD")
        return {"case": name, "kind": "OUTPUT", "model_id": out.model_id, "setup": None}
    if name == "fib_unresolved_anchor":
        evaluation = evaluate(FIB_CARD, surface=SetupSurface.PRODUCTION)
        return {"case": name, "kind": "SETUP", "eligibility": evaluation.eligibility.value}
    if name == "jpy_basket_roles":
        evaluation = evaluate(JPY_CARD)
        return {"case": name, "kind": "SETUP", "eligibility": evaluation.eligibility.value, "automation": False}
    if name == "stand_down_lock":
        snap = compose(base_inputs(stand_down=stand_down_record(), no_go=(II6.NoGoReason.NATIVE_TIER_NO_GO,)))
        return {
            "case": name,
            "kind": "SNAPSHOT",
            "manual_only": snap.classifications.manual_only,
            "automation_permitted": snap.classifications.automation_permitted,
            "no_go": True,
        }
    if name == "provider_missing":
        try:
            compose(base_inputs(provider_configured=False))
        except RefusalError as exc:
            return {"case": name, "kind": "REFUSAL", "code": exc.code}
        raise AssertionError("missing provider must refuse")
    if name == "historical_pinned_replay":
        snap = compose(base_inputs())
        store = HistoryStore()
        store.retain(snap, base_inputs())
        replayed = store.reconstruct(historical_request(snap))
        return {
            "case": name,
            "kind": "RECONSTRUCTION",
            "snapshot_id": snap.snapshot_id,
            "match": snap.snapshot_hash == replayed.snapshot_hash,
            "view": replayed.view,
        }
    if name == "card_schema_incompatible":
        from app.forge.intelligence_api.refusals import card_machine_errors

        return {
            "case": name,
            "kind": "CARD",
            "errors": [list(card_machine_errors(card)) for card in (XAU_CARD, FIB_CARD, JPY_CARD)],
        }
    if name == "restricted_exposure":
        snap = compose(base_inputs())
        from app.forge.canonical import ProductExposure
        from app.forge.identity import ForgePrincipal
        from app.forge.intelligence_api.policy_gate import IntelligenceGateway
        from app.forge.policy import AuthorizationContext

        access = IntelligenceGateway().read(
            principal=ForgePrincipal.anonymous(),
            context=AuthorizationContext.empty(),
            key=snap.key,
            exposure=ProductExposure.OPERATOR_ONLY,
            loader=lambda: snap,
        )
        return {"case": name, "kind": "DENIAL", "code": access.refusal["code"] if access.refusal else None}
    raise ValueError(f"unknown integration fixture: {name}")


CASE_NAMES = (
    "full_eur_lineage",
    "xau_promotion_chain",
    "btc_tracker_no_game",
    "fib_unresolved_anchor",
    "jpy_basket_roles",
    "stand_down_lock",
    "provider_missing",
    "historical_pinned_replay",
    "card_schema_incompatible",
    "restricted_exposure",
)
