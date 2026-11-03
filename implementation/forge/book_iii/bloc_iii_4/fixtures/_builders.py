"""Committed fixture builders for Bloc III.4.

These builders construct the synthetic, provenance-labelled inputs the
golden fixtures are generated from **and** the same inputs the acceptance
suite reproduces them with.  Keeping one builder module means a fixture
can never drift from its reproduction.

Every value here is a deterministic synthetic construction.  It is
structural validation material only — never empirical market evidence and
never citable for a performance claim.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.forge.market_data import (
    CLOCK_REGISTRY_VERSION,
    MARKET_DATA_SCHEMA_VERSION,
    SESSION_REGISTRY_VERSION,
    DataOutcome,
)
from app.forge.measurements import MEASUREMENT_ENGINE_VERSION, RuleMaterialization
from app.forge.model_runtime import (
    MODEL_RUNTIME_VERSION,
    DirectionBias,
    InputIdentity,
    Layer,
    ModelOutput,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    finalize_output,
)
from app.forge.state_engine import (
    Condition,
    StandDownState,
    StateSnapshot,
    TransitionKind,
    TransitionRequest,
    TransitionRule,
    append_event,
    evaluate_transition,
    open_ledger,
)

__all__ = [
    "EUR_DAILY_CARD",
    "FALCON_FAMILIES",
    "FAMILY_INSTRUMENT",
    "FAMILY_LAYER",
    "FAMILY_MODEL",
    "FAMILY_STATE",
    "T1",
    "T2",
    "T3",
    "TS",
    "build_contract_cases",
    "build_eur_daily_ledger",
    "build_family_snapshots",
    "eur_rule",
    "make_output",
    "make_snapshot",
    "stand_down_case",
]

TS = datetime(2026, 3, 3, 9, 0, tzinfo=timezone.utc)
T1 = TS + timedelta(minutes=5)
T2 = TS + timedelta(minutes=10)
T3 = TS + timedelta(minutes=15)

EUR_DAILY_CARD = "EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"

#: family -> (model_id, model_version, layer, genesis state, instrument)
FAMILY_MODEL: dict[str, tuple[str, str, Layer, str, str]] = {
    "EUR_DAILY": ("EUR.DAILY.NEWS_REKEY.V1", "PHASE1", Layer.L1, "SEED_T1", "EURUSD"),
    "EUR_WEEKLY": ("EUR.WEEKLY.V1_1", "V1_1", Layer.L2, "ROUTE_OPEN", "EURUSD"),
    "EUR_HIGHER_ORDER": (
        "EUR.HIGHER_ORDER.V1",
        "V1",
        Layer.L3,
        "PRIOR_DECLARED",
        "EURUSD",
    ),
    "XAU": ("XAU.GAME.L1_L2_L3.V1", "V1", Layer.CROSS_LAYER, "PROMOTION_PENDING", "XAUUSD"),
    "BTC_TRACKER": ("BTC.TRACKER.DWM.V1", "V1", Layer.CROSS_LAYER, "SEED_T1", "BTCUSD"),
    "FIB_RANGE_BIRTH": (
        "CROSSASSET.FIB.RANGE_BIRTH.V1",
        "R15",
        Layer.CROSS_LAYER,
        "RANGE_BIRTH_UNRESOLVED",
        "EURUSD",
    ),
    "JPY_CARRY": (
        "JPY.CARRY_GAME.L1_L3.V1",
        "V1",
        Layer.CROSS_LAYER,
        "BASKET_UNRESOLVED",
        "USDJPY",
    ),
}

FAMILY_LAYER = {family: spec[2] for family, spec in FAMILY_MODEL.items()}
FAMILY_STATE = {family: spec[3] for family, spec in FAMILY_MODEL.items()}
FAMILY_INSTRUMENT = {family: spec[4] for family, spec in FAMILY_MODEL.items()}

#: Families in registry order (stable fixture ordering).
FALCON_FAMILIES: tuple[str, ...] = (
    "EUR_DAILY",
    "EUR_WEEKLY",
    "EUR_HIGHER_ORDER",
    "XAU",
    "BTC_TRACKER",
    "FIB_RANGE_BIRTH",
    "JPY_CARRY",
)


def make_output(
    family: str,
    state: str,
    *,
    ranges: tuple[str, ...] = (),
    no_go: tuple[NoGoReason, ...] = (),
    authorization: ProductionAuthorization = ProductionAuthorization.NOT_AUTHORIZED,
    quality: DataOutcome = DataOutcome.OK,
    layer: Layer | None = None,
) -> ModelOutput:
    """Build and finalize a synthetic III.3 output for one family.

    ``layer`` may be overridden for the layer-isolation cases (XAU L3/L2/L1,
    EUR L3 -> L2 -> L1); the default is the family's registered layer.
    """

    model_id, model_version, family_layer, _genesis, instrument = FAMILY_MODEL[family]
    resolved_layer = family_layer if layer is None else layer
    identity = InputIdentity(
        instrument_id=instrument,
        calibration_key=None,
        clock_id="CLOCK.UTC",
        session_id="SESSION.SYNTHETIC",
        calculation_timestamp=TS,
        market_data_schema_version=MARKET_DATA_SCHEMA_VERSION,
        clock_registry_version=CLOCK_REGISTRY_VERSION,
        session_registry_version=SESSION_REGISTRY_VERSION,
        measurement_engine_version=MEASUREMENT_ENGINE_VERSION,
        model_runtime_version=MODEL_RUNTIME_VERSION,
        prior_state_ref=None,
    )
    output = ModelOutput(
        model_id=model_id,
        model_version=model_version,
        model_runtime_version=MODEL_RUNTIME_VERSION,
        output_hash="",
        model_state=state,
        layer=resolved_layer,
        direction_bias=DirectionBias.none(),
        active_ranges=tuple(ranges),
        active_anchor_states=(),
        levels=(),
        range_left=RangeLeftField.unresolved(),
        no_go=tuple(no_go),
        warnings=(),
        claim_refs=(),
        evidence_refs=("EV.SYNTHETIC.III4.V1",),
        quality_state=quality,
        production_authorization=authorization,
        explanation_facts=(),
        sub_states=(),
        identity=identity,
    )
    return finalize_output(output)


def make_snapshot(
    family: str,
    state: str,
    snapshot_id: str,
    *,
    event_time: datetime = TS,
    prior: StateSnapshot | None = None,
    ranges: tuple[str, ...] = (),
    authorization: ProductionAuthorization = ProductionAuthorization.NOT_AUTHORIZED,
    quality: DataOutcome = DataOutcome.OK,
    layer: Layer | None = None,
) -> StateSnapshot:
    """Build a finalized snapshot from a synthetic output."""

    output = make_output(
        family,
        state,
        ranges=ranges,
        authorization=authorization,
        quality=quality,
        layer=layer,
    )
    return StateSnapshot.from_output(
        output,
        event_time=event_time,
        snapshot_id=snapshot_id,
        prior_snapshot=prior,
    )


def eur_rule(rule_id: str) -> TransitionRule:
    """A canonical EUR Daily rule identity."""

    return TransitionRule(
        rule_id=rule_id,
        rule_version="V1",
        materialization=RuleMaterialization.CANONICAL,
        source_ref=EUR_DAILY_CARD,
    )


def build_family_snapshots() -> dict[str, StateSnapshot]:
    """One genesis snapshot per family (deterministic ids)."""

    return {
        family: make_snapshot(
            family,
            FAMILY_STATE[family],
            f"SNAP.{family}.{FAMILY_STATE[family]}",
            ranges=("RANGE.SYNTHETIC.V1",),
        )
        for family in FALCON_FAMILIES
    }


def build_eur_daily_ledger():
    """A three-event EUR Daily ledger: deliver -> rekey -> stand down."""

    genesis = make_snapshot(
        "EUR_DAILY",
        "SEED_T1",
        "SNAP.EUR_DAILY.SEED_T1",
        ranges=("RANGE.EUR_DAILY.SEED.V1",),
    )
    s1 = make_snapshot(
        "EUR_DAILY",
        "REKEY_100",
        "SNAP.EUR_DAILY.REKEY_100",
        event_time=T1,
        prior=genesis,
        ranges=("RANGE.EUR_DAILY.SEED.V1",),
    )
    s2 = make_snapshot(
        "EUR_DAILY",
        "REKEY_125",
        "SNAP.EUR_DAILY.REKEY_125",
        event_time=T2,
        prior=s1,
        ranges=("RANGE.EUR_DAILY.REKEY_100.V1",),
    )
    s3 = make_snapshot(
        "EUR_DAILY",
        "INVALID_RANGE",
        "SNAP.EUR_DAILY.INVALID_RANGE",
        event_time=T3,
        prior=s2,
        ranges=("RANGE.EUR_DAILY.REKEY_100.V1",),
    )

    ledger = open_ledger(genesis)
    ledger = append_event(
        ledger,
        evaluate_transition(
            TransitionRequest(
                kind=TransitionKind.DELIVER,
                prior_snapshot=genesis,
                rule=eur_rule("EUR_DAILY_DELIVERY"),
                event_time=T1,
                resulting_state="REKEY_100",
                resulting_state_id=s1.snapshot_id,
                conditions=frozenset({Condition.DELIVERED}),
                payload=(("target", "TARGET.EUR_DAILY.100"),),
            )
        ),
        resulting_snapshot=s1,
        event_id="EV.EUR_DAILY.1",
    )
    ledger = append_event(
        ledger,
        evaluate_transition(
            TransitionRequest(
                kind=TransitionKind.REKEY,
                prior_snapshot=s1,
                rule=eur_rule("EUR_DAILY_REKEY"),
                event_time=T2,
                resulting_state="REKEY_125",
                resulting_state_id=s2.snapshot_id,
                conditions=frozenset({Condition.STRUCTURAL_EVENT}),
                payload=(("qualifying_event", "EVENT.STRUCTURAL.125"),),
            )
        ),
        resulting_snapshot=s2,
        event_id="EV.EUR_DAILY.2",
    )
    ledger = append_event(
        ledger,
        evaluate_transition(
            TransitionRequest(
                kind=TransitionKind.STAND_DOWN,
                prior_snapshot=s2,
                rule=eur_rule("EUR_DAILY_STAND_DOWN"),
                event_time=T3,
                resulting_state="INVALID_RANGE",
                resulting_state_id=s3.snapshot_id,
                stand_down_state=StandDownState.INVALID_RANGE,
                payload=(("reason", "RANGE_TOO_LARGE"),),
            )
        ),
        resulting_snapshot=s3,
        event_id="EV.EUR_DAILY.3",
    )
    return genesis, {"s1": s1, "s2": s2, "s3": s3}, ledger


def stand_down_case(reason: NoGoReason) -> dict:
    """A declarative stand-down mapping case."""

    from app.forge.state_engine import stand_down_for_no_go

    record = stand_down_for_no_go(
        reason,
        blocking_rule_ref="RULE.SYNTHETIC.V1",
        snapshot_id="SNAP.BTC_TRACKER.SEED_T1",
    )
    return {
        "no_go": reason.value,
        "state": record.state.value,
        "reason": record.reason.value,
        "eligibility_lock": record.eligibility_lock,
    }


def build_contract_cases() -> dict:
    """Declarative cases that the suite executes against the engine."""

    return {
        "first_delivery": [
            {
                "case_id": "ORDER_AB",
                "targets": [["TARGET_A", "ABOVE", 0], ["TARGET_B", "BELOW", 1]],
                "hits": [
                    ["TARGET_A", "2026-03-03T09:00:00+00:00", "BAR.1"],
                    ["TARGET_B", "2026-03-03T09:05:00+00:00", "BAR.2"],
                ],
                "expected_order": ["TARGET_A", "TARGET_B"],
                "terminal": "BOTH_SIDES_REACHED",
            },
            {
                "case_id": "ORDER_BA",
                "targets": [["TARGET_A", "ABOVE", 0], ["TARGET_B", "BELOW", 1]],
                "hits": [
                    ["TARGET_B", "2026-03-03T09:00:00+00:00", "BAR.1"],
                    ["TARGET_A", "2026-03-03T09:05:00+00:00", "BAR.2"],
                ],
                "expected_order": ["TARGET_B", "TARGET_A"],
                "terminal": "BOTH_SIDES_REACHED",
            },
            {
                "case_id": "AMBIGUOUS_SAME_BAR",
                "targets": [["TARGET_A", "ABOVE", 0], ["TARGET_B", "BELOW", 1]],
                "hits": [
                    ["TARGET_A", "2026-03-03T09:00:00+00:00", "BAR.1"],
                    ["TARGET_B", "2026-03-03T09:00:00+00:00", "BAR.1"],
                ],
                "expected_error": "AMBIGUOUS_PATH",
            },
        ],
        "failure_repair": [
            {
                "case_id": "DECLARED_CHAIN",
                "steps": ["ACCEPT", "FAIL", "REPAIR", "COMPRESS", "RELEASE"],
                "expected_states": [
                    "ACCEPTED",
                    "FAILED",
                    "REPAIR_ATTEMPTED",
                    "COMPRESSED",
                    "OPPOSITE_ACCEPTED",
                ],
            },
            {
                "case_id": "REPAIR_WITHOUT_FAILURE",
                "steps": ["ACCEPT", "REPAIR"],
                "expected_error": "REPAIR_WITHOUT_FAILURE",
            },
            {
                "case_id": "FAILURE_WITHOUT_ACCEPTANCE",
                "steps": ["FAIL"],
                "expected_error": "FAILURE_WITHOUT_ACCEPTANCE",
            },
        ],
        "rekey": [
            {"case_id": "LADDER", "states": list(("REKEY_100", "REKEY_125", "REKEY_132", "REKEY_168", "REKEY_185"))},
            {
                "case_id": "TOUCH_ONLY",
                "structural": False,
                "expected_error": "REKEY_NOT_STRUCTURAL",
            },
            {
                "case_id": "XAU_132_TO_168",
                "family": "XAU",
                "prior_state": "REKEY_132",
                "new_state": "REKEY_168",
                "expected_error": "TRANSITION_PAIR_FORBIDDEN",
            },
        ],
        "layer_handoff": [
            {"case_id": "L3_TO_L2", "source": "EUR_HIGHER_ORDER", "destination": "EUR_WEEKLY", "expected_ownership": "PATH"},
            {"case_id": "L2_TO_L1", "source": "EUR_WEEKLY", "destination": "EUR_DAILY", "expected_ownership": "EXECUTION"},
            {"case_id": "L1_TO_L3", "source": "EUR_DAILY", "destination": "EUR_HIGHER_ORDER", "expected_error": "LAYER_OWNERSHIP_VIOLATION"},
            {"case_id": "L3_TO_L1", "source": "EUR_HIGHER_ORDER", "destination": "EUR_DAILY", "expected_error": "LAYER_HANDOFF_DIRECTION"},
        ],
        "range_left": [
            {"case_id": "CONDITIONED", "events": ["DELIVERY"], "expected_state": "MEASURED"},
            {"case_id": "UNRESOLVED", "events": [], "measurement": None, "expected_state": "UNRESOLVED"},
            {"case_id": "UNCONDITIONAL", "events": [], "measurement": "150", "expected_error": "UNCONDITIONAL_FREQUENCY_REFUSED"},
        ],
        "stand_down": [
            "AR_SOURCE_NO_GO",
            "ASIAN_RANGE_NO_GO",
            "NATIVE_TIER_NO_GO",
            "RULE_NOT_MATERIALIZED",
            "PROMOTION_PARKED",
        ],
    }
