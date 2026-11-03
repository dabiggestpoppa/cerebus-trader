"""Bloc III.4 acceptance suite — State, Path & Transition Engine.

Implements the frozen ``ACCEPTANCE.md`` clause map (A1…R12) as the
proposed tests T1–T12.  Every test is deterministic, offline, network
free and clock injected; nothing here is empirical trading evidence.

The suite is a *contract* suite: it proves that a transition is earned
(prior state + canonical rule + source lineage), that a terminal outcome
never erases the ordered path, and that no downstream authority
(eligibility, setup, execution, probability) is manufactured at this
layer.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import re
import socket
import sys
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = REPO_ROOT / "app" / "forge" / "state_engine"
FIXTURE_DIR = (
    REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_4" / "fixtures"
)
BOOK_II_MANIFEST = (
    REPO_ROOT / "implementation/forge/book_ii/ratification/CONTRACT_FREEZE_MANIFEST_V1.md"
)
PLANNING_MANIFEST = REPO_ROOT / "planning/forge/PLANNING_FREEZE_MANIFEST_V1.md"
III3_PLAN = REPO_ROOT / "implementation/forge/book_iii/bloc_iii_3/PLAN.md"
III3_RATIFICATION = (
    REPO_ROOT / "implementation/forge/book_iii/bloc_iii_3/RATIFICATION.md"
)
III4_PLAN = REPO_ROOT / "implementation/forge/book_iii/bloc_iii_4/PLAN.md"

for _path in (REPO_ROOT, FIXTURE_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import _builders as B  # noqa: E402

import app.forge.state_engine as se  # noqa: E402
from app.forge.market_data import (  # noqa: E402
    CLOCK_REGISTRY_VERSION,
    MARKET_DATA_SCHEMA_VERSION,
    SESSION_REGISTRY_VERSION,
    DataOutcome,
    NativeUnit,
)
from app.forge.measurements import (  # noqa: E402
    MEASUREMENT_ENGINE_VERSION,
    NativeMagnitude,
    RemainingState,
    RuleMaterialization,
)
from app.forge.model_runtime import (  # noqa: E402
    MODEL_RUNTIME_VERSION,
    DirectionBias,
    InputIdentity,
    Layer,
    ModelOutput,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    compute_hash,
    finalize_output,
)

TS, T1, T2, T3 = B.TS, B.T1, B.T2, B.T3
CARD = B.EUR_DAILY_CARD
XAU_CARD = "XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md"
BTC_CARD = "BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md"
WEEKLY_CARD = "EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md"
FIB_CARD = "FIB_RANGE_BIRTH_MODEL_CARD_V1.md"

KINDS = {kind.value for kind in se.TransitionKind}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def snap(family: str = "EUR_DAILY", state: str = "SEED_T1", sid: str | None = None, **kw):
    return B.make_snapshot(family, state, sid or f"SNAP.{family}.{state}", **kw)


def rule(
    rule_id: str = "EUR_DAILY_DELIVERY",
    *,
    materialization: RuleMaterialization = RuleMaterialization.CANONICAL,
    source: str = CARD,
) -> se.TransitionRule:
    return se.TransitionRule(
        rule_id=rule_id,
        rule_version="V1",
        materialization=materialization,
        source_ref=source,
    )


def req(
    kind: se.TransitionKind,
    prior: se.StateSnapshot,
    resulting: str,
    *,
    rule_obj: se.TransitionRule | None = None,
    event_time: datetime | None = None,
    conditions: frozenset = frozenset(),
    **kw,
) -> se.TransitionRequest:
    return se.TransitionRequest(
        kind=kind,
        prior_snapshot=prior,
        rule=rule_obj or rule(),
        event_time=event_time or (prior.event_time + timedelta(minutes=1)),
        resulting_state=resulting,
        resulting_state_id=f"STATE.{resulting}",
        conditions=conditions,
        **kw,
    )


def earned(kind, prior, resulting, **kw):
    return se.evaluate_transition(req(kind, prior, resulting, **kw))


def code_of(exc: Exception) -> str:
    return getattr(exc, "code", "")


def package_sources() -> list[Path]:
    return sorted(PACKAGE_DIR.glob("*.py"))


def package_text() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in package_sources()}


def package_trees() -> dict[str, ast.Module]:
    return {
        path.name: ast.parse(path.read_text(encoding="utf-8"))
        for path in package_sources()
    }


def package_modules() -> list:
    modules = [se]
    for path in package_sources():
        if path.stem in ("__init__",):
            continue
        modules.append(importlib.import_module(f"app.forge.state_engine.{path.stem}"))
    return modules


def dataclass_field_names() -> set[str]:
    names: set[str] = set()
    for module in package_modules():
        for value in vars(module).values():
            if isinstance(value, type) and is_dataclass(value):
                names |= {item.name for item in fields(value)}
    return names


def enum_member_values() -> set[str]:
    values: set[str] = set()
    for module in package_modules():
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, se.StateEngineError):
                continue
            if isinstance(value, type) and hasattr(value, "__members__"):
                values |= {str(member.value) for member in value}
    return values


def magnitude(value: str = "150", unit: NativeUnit = NativeUnit.PIP, instrument: str = "EURUSD"):
    return NativeMagnitude(instrument_id=instrument, unit=unit, value=Decimal(value))


def targets(*specs) -> tuple[se.DeclaredTarget, ...]:
    return tuple(
        se.DeclaredTarget(
            target_id=target_id, side=se.DeliverySide(side), declared_order_index=index
        )
        for target_id, side, index in specs
    )


def observation(target_id: str, when: datetime, bar: str = "BAR.1"):
    return se.DeliveryObservation(
        target_id=target_id, realized_event_time=when, realizing_bar_ref=bar
    )


def eur_ledger():
    return B.build_eur_daily_ledger()


def tampered(ledger: se.TransitionLedger, index_a: int, index_b: int):
    events = list(ledger.events)
    events[index_a], events[index_b] = events[index_b], events[index_a]
    return replace(ledger, events=tuple(events))


# ---------------------------------------------------------------------------
# T1 — State snapshot (Ch III.4.1)
# ---------------------------------------------------------------------------


class TestT1Snapshot:
    def test_snapshot_immutable(self):
        snapshot = snap()
        with pytest.raises(FrozenInstanceError):
            snapshot.active_state = "REKEY_100"  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            snapshot.snapshot_hash = "0" * 64  # type: ignore[misc]

    def test_snapshot_version_identity_complete(self):
        snapshot = snap()
        assert snapshot.snapshot_hash and snapshot.snapshot_id
        assert snapshot.state_engine_version == se.STATE_ENGINE_VERSION
        assert snapshot.model_runtime_version == MODEL_RUNTIME_VERSION
        assert snapshot.market_data_schema_version == MARKET_DATA_SCHEMA_VERSION
        assert snapshot.clock_registry_version == CLOCK_REGISTRY_VERSION
        assert snapshot.session_registry_version == SESSION_REGISTRY_VERSION
        assert snapshot.measurement_engine_version == MEASUREMENT_ENGINE_VERSION

    def test_snapshot_model_and_layer_from_source(self):
        output = B.make_output("XAU", "PROMOTION_PENDING")
        snapshot = se.StateSnapshot.from_output(
            output, event_time=TS, snapshot_id="SNAP.XAU.PROMOTION_PENDING"
        )
        assert snapshot.model_id == output.model_id
        assert snapshot.model_version == output.model_version
        assert snapshot.layer is output.layer is Layer.CROSS_LAYER

    def test_snapshot_timestamps_injected_not_wall(self):
        snapshot = snap(event_time=TS)
        assert snapshot.event_time == TS
        assert snapshot.calculation_timestamp == TS
        assert snapshot.event_time.tzinfo is not None
        assert snapshot.calculation_timestamp.tzinfo is not None
        assert snapshot.event_time.year == 2026  # not "now"

    def test_snapshot_active_state_verbatim(self):
        output = B.make_output("EUR_DAILY", "REKEY_132")
        snapshot = se.StateSnapshot.from_output(
            output, event_time=TS, snapshot_id="SNAP.EUR_DAILY.REKEY_132"
        )
        assert snapshot.active_state == output.model_state == "REKEY_132"

    def test_snapshot_measurements_referenced_not_recomputed(self):
        names = {item.name for item in fields(se.MeasurementRef)}
        assert names == {
            "definition_id",
            "definition_version",
            "source_window_digest",
            "bar_count",
            "quality_state",
        }
        assert not hasattr(se.MeasurementRef, "value")
        with pytest.raises(se.StateContractError):
            se.MeasurementRef.from_measurement(object())  # type: ignore[arg-type]

    def test_no_measurement_subclassing(self):
        for name, tree in package_trees().items():
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    bases = {
                        getattr(base, "id", getattr(base, "attr", "")) for base in node.bases
                    }
                    assert "Measurement" not in bases, name
                    assert "ModelOutput" not in bases, name

    def test_snapshot_active_ranges_and_levels(self):
        snapshot = snap(ranges=("RANGE.EUR_DAILY.SEED.V1",))
        assert snapshot.active_ranges == ("RANGE.EUR_DAILY.SEED.V1",)
        assert snapshot.levels == ()
        assert isinstance(snapshot.range_left, RangeLeftField)

    def test_snapshot_quality_frozen_vocabulary(self):
        snapshot = snap(quality=DataOutcome.DEGRADED)
        assert snapshot.quality_state is DataOutcome.DEGRADED
        assert snapshot.quality_state in set(DataOutcome)

    def test_snapshot_evidence_refs_read_only(self):
        snapshot = snap()
        assert snapshot.evidence_refs == ("EV.SYNTHETIC.III4.V1",)
        assert snapshot.claim_refs == ()
        with pytest.raises(FrozenInstanceError):
            snapshot.claim_refs = ("CLAIM.X",)  # type: ignore[misc]

    def test_snapshot_authorization_verbatim(self):
        snapshot = snap(authorization=ProductionAuthorization.RESEARCH_ONLY)
        assert snapshot.production_authorization is ProductionAuthorization.RESEARCH_ONLY

    def test_snapshot_requires_finalized_source(self):
        output = B.make_output("EUR_DAILY", "SEED_T1")
        unfinalized = replace(output, output_hash="")
        with pytest.raises(se.SourceLineageMissingError):
            se.StateSnapshot.from_output(
                unfinalized, event_time=TS, snapshot_id="SNAP.X"
            )

    def test_snapshot_rejects_unregistered_model(self):
        output = B.make_output("EUR_DAILY", "SEED_T1")
        unknown = replace(output, model_id="EUR.DAILY.UNKNOWN.V9")
        with pytest.raises(se.ModelVersionUnavailableError):
            se.StateSnapshot.from_output(unknown, event_time=TS, snapshot_id="SNAP.X")

    def test_snapshot_hash_deterministic(self):
        first = snap(event_time=TS)
        second = snap(event_time=TS)
        assert first.snapshot_hash == second.snapshot_hash
        later = snap(event_time=T1)
        assert later.snapshot_hash != first.snapshot_hash

    def test_snapshot_prior_chain_same_model_key(self):
        genesis = snap()
        chained = snap("EUR_DAILY", "REKEY_100", event_time=T1, prior=genesis)
        assert chained.prior_snapshot_id == genesis.snapshot_id
        foreign = snap("BTC_TRACKER", "SEED_T1")
        with pytest.raises(se.PriorStateMismatchError):
            snap("EUR_DAILY", "REKEY_125", event_time=T1, prior=foreign)


# ---------------------------------------------------------------------------
# T2 — Transition vocabulary and guards (Ch III.4.2)
# ---------------------------------------------------------------------------


class TestT2Vocabulary:
    def test_vocabulary_exact_twelve(self):
        assert KINDS == {
            "ENTER_STATE",
            "ACCEPT",
            "REJECT",
            "FAIL",
            "REPAIR",
            "PROMOTE",
            "DELIVER",
            "REKEY",
            "INVALIDATE",
            "COMPRESS",
            "RELEASE",
            "STAND_DOWN",
        }
        assert len(KINDS) == 12

    def test_family_restriction_enforced(self):
        prior = snap("BTC_TRACKER", "SEED_T1")
        with pytest.raises(se.TransitionNotInFamilyVocabularyError):
            earned(
                se.TransitionKind.PROMOTE,
                prior,
                "SEED_T2",
                rule_obj=rule("BTC_PROMOTE", source=BTC_CARD),
                evidence_refs=("EV.SYNTHETIC.III4.V1",),
            )

    def test_no_vocabulary_expansion_possible(self):
        with pytest.raises(ValueError):
            se.TransitionKind("SIGNAL")  # type: ignore[arg-type]
        for entry in se.TRANSITION_AUTHORITY.values():
            assert entry.allowed <= set(se.TransitionKind)

    def test_qualifying_prior_state_required(self):
        prior = snap("EUR_DAILY", "REKEY_185")
        with pytest.raises(se.TransitionNotEarnedError):
            earned(
                se.TransitionKind.REKEY,
                prior,
                "REKEY_168",
                conditions=frozenset({se.Condition.STRUCTURAL_EVENT}),
            )

    def test_canonical_rule_required(self):
        with pytest.raises(se.StateContractError):
            se.TransitionRule(
                rule_id="bad-rule",
                rule_version="V1",
                materialization=RuleMaterialization.CANONICAL,
                source_ref=CARD,
            )
        with pytest.raises(se.StateContractError):
            se.TransitionRule(
                rule_id="EUR_RULE",
                rule_version="",
                materialization=RuleMaterialization.CANONICAL,
                source_ref=CARD,
            )

    def test_unmaterialized_rule_cannot_earn_transition(self):
        prior = snap()
        with pytest.raises(se.RuleNotMaterializedError):
            earned(
                se.TransitionKind.DELIVER,
                prior,
                "REKEY_100",
                rule_obj=rule(
                    "EUR_DAILY_DELIVERY", materialization=RuleMaterialization.NOT_MATERIALIZED
                ),
            )

    def test_source_lineage_required(self):
        prior = replace(snap(), snapshot_hash="")
        with pytest.raises(se.SourceLineageMissingError):
            earned(se.TransitionKind.DELIVER, prior, "REKEY_100")

    def test_cross_family_transition_refused(self):
        prior = snap("BTC_TRACKER", "SEED_T1")
        with pytest.raises(se.TransitionAuthorityMismatchError):
            earned(
                se.TransitionKind.DELIVER,
                prior,
                "SEED_T2",
                rule_obj=rule("XAU_DELIVERY", source=XAU_CARD),
            )

    def test_event_time_injected_and_ordered(self):
        prior = snap()
        with pytest.raises(se.StateContractError):
            earned(
                se.TransitionKind.DELIVER,
                prior,
                "REKEY_100",
                event_time=TS - timedelta(minutes=1),
            )
        with pytest.raises(se.TransitionOrderAmbiguousError):
            earned(
                se.TransitionKind.DELIVER,
                prior,
                "REKEY_100",
                event_time=prior.event_time,
            )
        decision = earned(
            se.TransitionKind.DELIVER,
            prior,
            "REKEY_100",
            event_time=prior.event_time,
            order_key="ORDER.1",
        )
        assert decision.order_key == "ORDER.1"

    def test_accept_requires_prior_touch(self):
        prior = snap("EUR_DAILY", "REKEY_100")
        with pytest.raises(se.AcceptWithoutTouchError):
            earned(se.TransitionKind.ACCEPT, prior, "REKEY_125")
        decision = earned(
            se.TransitionKind.ACCEPT,
            prior,
            "REKEY_125",
            conditions=frozenset({se.Condition.TOUCHED}),
        )
        assert decision.kind is se.TransitionKind.ACCEPT

    def test_family_authority_matrix_matches_fixture(self):
        payload = json.loads((FIXTURE_DIR / "model_family_transition_authority.json").read_text())
        by_family = {entry["family"]: entry for entry in payload["entries"]}
        assert set(by_family) == {entry.family for entry in se.TRANSITION_AUTHORITY.values()}
        for (model_id, version), entry in se.TRANSITION_AUTHORITY.items():
            fixture = by_family[entry.family]
            assert fixture["model_id"] == model_id
            assert fixture["model_version"] == version
            assert fixture["layer"] == entry.layer.value
            assert fixture["allowed"] == sorted(kind.value for kind in entry.allowed)
            assert fixture["restricted"] == sorted(kind.value for kind in entry.restricted)
            assert fixture["unresolved"] == sorted(kind.value for kind in entry.unresolved)
            assert fixture["never"] == sorted(KINDS - {k.value for k in entry.allowed})
            assert fixture["canonical_sources"] == sorted(entry.canonical_source_refs)

    def test_promote_requires_evidence_and_rule(self):
        prior = snap("XAU", "PROMOTION_PENDING")
        xau_rule = rule("XAU_PROMOTION_68_80", source=XAU_CARD)
        with pytest.raises(se.PromotionWithoutAuthorityError):
            earned(
                se.TransitionKind.PROMOTE,
                prior,
                "PROMOTION_ELIGIBLE",
                rule_obj=xau_rule,
            )
        decision = earned(
            se.TransitionKind.PROMOTE,
            prior,
            "PROMOTION_ELIGIBLE",
            rule_obj=xau_rule,
            evidence_refs=("EV.XAU.PROMOTION.68_80.V1",),
        )
        assert decision.evidence_refs == ("EV.XAU.PROMOTION.68_80.V1",)

    def test_invalidate_preserves_lineage(self):
        prior = snap("FIB_RANGE_BIRTH", "RANGE_ACTIVE")
        decision = earned(
            se.TransitionKind.INVALIDATE,
            prior,
            "ANCHOR_INVALIDATED",
            rule_obj=rule("FIB_INVALIDATION", source=FIB_CARD),
        )
        assert decision.prior_state == "RANGE_ACTIVE"
        assert decision.prior_snapshot_id == prior.snapshot_id
        assert decision.prior_snapshot_hash == prior.snapshot_hash
        assert decision.source_output_hash == prior.source_output_hash

    def test_compress_release_declared_only(self):
        weekly = snap("EUR_WEEKLY", "ROUTE_OPEN")
        with pytest.raises(se.RuleNotMaterializedError):
            earned(
                se.TransitionKind.COMPRESS,
                weekly,
                "NODE_PROMOTED",
                rule_obj=rule("EUR_WEEKLY_COMPRESS", source=WEEKLY_CARD),
                conditions=frozenset({se.Condition.FAILED}),
            )
        prior = snap("EUR_DAILY", "REKEY_100")
        decision = earned(
            se.TransitionKind.COMPRESS,
            prior,
            "REKEY_125",
            conditions=frozenset({se.Condition.FAILED}),
        )
        assert decision.kind is se.TransitionKind.COMPRESS

    def test_no_op_transition_refused(self):
        prior = snap("EUR_DAILY", "REKEY_100")
        with pytest.raises(se.TransitionNoOpError):
            earned(se.TransitionKind.DELIVER, prior, "REKEY_100")

    def test_unknown_version_fails_closed(self):
        with pytest.raises(se.ModelVersionUnavailableError):
            se.authority_for("EUR.DAILY.NEWS_REKEY.V1", "V9")
        with pytest.raises(se.ModelVersionUnavailableError):
            se.authority_for("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM")

    def test_time_alone_cannot_earn_transition(self):
        prior = snap("EUR_DAILY", "SEED_T2")
        with pytest.raises(se.RekeyNotStructuralError):
            earned(
                se.TransitionKind.REKEY,
                prior,
                "REKEY_132",
                event_time=prior.event_time + timedelta(hours=8),
            )

    def test_event_fact_cannot_earn_geometry_transition(self):
        prior = snap("EUR_DAILY", "SOURCE_NO_GO")
        with pytest.raises(se.TransitionNotEarnedError):
            earned(
                se.TransitionKind.DELIVER,
                prior,
                "REKEY_100",
                payload=(("event_family", "EUR_OFFICIAL_HIGH"),),
            )


# ---------------------------------------------------------------------------
# T3 — First delivery (Ch III.4.3)
# ---------------------------------------------------------------------------


class TestT3Delivery:
    def test_delivery_order_recorded(self):
        path = se.build_path(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
            observations=(
                observation("TARGET_A", TS, "BAR.1"),
                observation("TARGET_B", T1, "BAR.2"),
            ),
        )
        assert [record.order_index for record in path.deliveries] == [0, 1]
        assert path.delivery_order == ("TARGET_A", "TARGET_B")

    def test_first_hit_side_and_timing(self):
        path = se.build_path(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
            observations=(
                observation("TARGET_B", TS, "BAR.1"),
                observation("TARGET_A", T1, "BAR.2"),
            ),
        )
        first = path.first_delivery
        assert first is not None
        assert first.target_id == "TARGET_B"
        assert first.side is se.DeliverySide.BELOW
        assert first.realized_event_time == TS

    def test_both_side_reach_preserves_sequence(self):
        path = se.build_path(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
            observations=(
                observation("TARGET_A", TS, "BAR.1"),
                observation("TARGET_B", T1, "BAR.2"),
            ),
        )
        assert path.terminal_reach is se.TerminalReach.BOTH_SIDES_REACHED
        assert len(path.deliveries) == 2
        assert path.first_delivery.target_id == "TARGET_A"
        se.assert_terminal_does_not_erase_path(path)

    def test_first_delivery_order_reversal(self):
        common = dict(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
        )
        ab = se.build_path(
            **common,
            observations=(
                observation("TARGET_A", TS, "BAR.1"),
                observation("TARGET_B", T1, "BAR.2"),
            ),
        )
        ba = se.build_path(
            **common,
            observations=(
                observation("TARGET_B", TS, "BAR.1"),
                observation("TARGET_A", T1, "BAR.2"),
            ),
        )
        assert ab.delivery_order != ba.delivery_order
        assert ab.terminal_result == ba.terminal_result
        se.assert_paths_differ_under_reversal(ab, ba, compute_hash)

    def test_target_order_stable(self):
        declared = targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1))
        assert se.target_order(declared) == ("TARGET_A", "TARGET_B")
        first = se.build_path(
            clock_id="CLOCK.UTC",
            targets=declared,
            observations=(observation("TARGET_A", TS, "BAR.1"),),
        )
        second = se.build_path(
            clock_id="CLOCK.UTC",
            targets=declared,
            observations=(observation("TARGET_A", TS, "BAR.1"),),
        )
        se.assert_target_order_stable(first, second)
        assert compute_hash(first.to_payload()) == compute_hash(second.to_payload())

    def test_first_delivery_required_refuses_without_order(self):
        with pytest.raises(se.AmbiguousPathError):
            se.build_path(
                clock_id="CLOCK.UTC",
                targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
                observations=(
                    observation("TARGET_A", TS, "BAR.1"),
                    observation("TARGET_B", TS, "BAR.1"),
                ),
                intrabar_order_resolvable=False,
                requires_first_delivery=True,
            )

    def test_ambiguous_intrabar_refuses(self):
        with pytest.raises(se.AmbiguousPathError) as excinfo:
            se.build_path(
                clock_id="CLOCK.UTC",
                targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
                observations=(
                    observation("TARGET_A", TS, "BAR.7"),
                    observation("TARGET_B", TS, "BAR.7"),
                ),
                intrabar_order_resolvable=False,
            )
        assert code_of(excinfo.value) == "AMBIGUOUS_PATH"

    def test_delivery_references_source_bar(self):
        path = se.build_path(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0),),
            observations=(observation("TARGET_A", TS, "BAR.42"),),
        )
        assert path.deliveries[0].realizing_bar_ref == "BAR.42"

    def test_delivery_sequence_roundtrip(self):
        path = se.build_path(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
            observations=(
                observation("TARGET_B", TS, "BAR.1"),
                observation("TARGET_A", T1, "BAR.2"),
            ),
        )
        payload = path.to_payload()
        assert [item["target_id"] for item in payload["deliveries"]] == [
            "TARGET_B",
            "TARGET_A",
        ]
        assert compute_hash(payload) == se.path_hash(path, compute_hash)

    def test_undeclared_target_refused(self):
        with pytest.raises(se.TargetNotDeclaredError):
            se.build_path(
                clock_id="CLOCK.UTC",
                targets=targets(("TARGET_A", "ABOVE", 0),),
                observations=(observation("TARGET_Z", TS, "BAR.1"),),
            )

    def test_delivery_clock_unresolvable_refuses(self):
        with pytest.raises(se.NoCalculationError):
            se.build_path(
                clock_id=None,
                targets=targets(("TARGET_A", "ABOVE", 0),),
                observations=(observation("TARGET_A", TS, "BAR.1"),),
            )


# ---------------------------------------------------------------------------
# T4 — Failure and repair (Ch III.4.4)
# ---------------------------------------------------------------------------


class TestT4FailureRepair:
    def test_failure_grammar_declared_only(self):
        for model_id, version in (
            ("BTC.TRACKER.DWM.V1", "V1"),
            ("EUR.HIGHER_ORDER.V1", "V1"),
        ):
            with pytest.raises(se.FailureGrammarNotDeclaredError):
                se.failure_grammar_for(model_id, version)
        assert se.FAILURE_GRAMMARS

    def test_declared_chain_representable(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.ACCEPT, grammar=grammar, event_time=T1,
            acceptance_ref="ACCEPTANCE.1",
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.FAIL, grammar=grammar, event_time=T1
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T2
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.COMPRESS, grammar=grammar, event_time=T2
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.RELEASE, grammar=grammar, event_time=T3
        )
        assert chain.steps == ("ACCEPT", "FAIL", "REPAIR", "COMPRESS", "RELEASE")
        assert chain.state is se.FailureState.OPPOSITE_ACCEPTED

    def test_repair_without_prior_failure_refused(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.ACCEPT, grammar=grammar, event_time=T1,
            acceptance_ref="ACCEPTANCE.1",
        )
        with pytest.raises(se.RepairWithoutFailureError):
            se.advance_failure(
                chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T2
            )

    def test_failure_without_acceptance_refused(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        with pytest.raises(se.FailureWithoutAcceptanceError):
            se.advance_failure(
                chain, se.TransitionKind.FAIL, grammar=grammar, event_time=T1
            )

    def test_failure_repair_acceptance_distinct(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.ACCEPT, grammar=grammar, event_time=T1,
            acceptance_ref="ACCEPTANCE.1",
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.FAIL, grammar=grammar, event_time=T1
        )
        attempted = se.advance_failure(
            chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T2
        )
        confirmed = se.advance_failure(
            chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T2, confirmed=True
        )
        assert chain.state is se.FailureState.FAILED
        assert attempted.state is se.FailureState.REPAIR_ATTEMPTED
        assert confirmed.state is se.FailureState.REPAIR_CONFIRMED
        assert len(
            {
                se.FailureState.ACCEPTED.value,
                chain.state.value,
                attempted.state.value,
                confirmed.state.value,
            }
        ) == 4

    def test_confirmed_repair_not_new_acceptance(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.ACCEPT, grammar=grammar, event_time=T1,
            acceptance_ref="ACCEPTANCE.1",
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.FAIL, grammar=grammar, event_time=T1
        )
        confirmed = se.advance_failure(
            chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T2, confirmed=True
        )
        assert confirmed.acceptance_ref == "ACCEPTANCE.1"
        assert not confirmed.is_new_acceptance
        attempted = se.advance_failure(
            chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T2
        )
        reaccepted = se.advance_failure(
            attempted, se.TransitionKind.COMPRESS, grammar=grammar, event_time=T2
        )
        reaccepted = se.advance_failure(
            reaccepted,
            se.TransitionKind.RELEASE,
            grammar=grammar,
            event_time=T3,
            reaccepted=True,
            acceptance_ref="ACCEPTANCE.2",
        )
        assert reaccepted.acceptance_ref == "ACCEPTANCE.2"
        assert reaccepted.is_new_acceptance

    def test_p90_grammar_not_generalized(self):
        eur = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        xau = se.failure_grammar_for("XAU.GAME.L1_L2_L3.V1", "V1")
        assert eur.rule.rule_id != xau.rule.rule_id
        xau_chain = se.start_failure_chain("XAU.GAME.L1_L2_L3.V1", "V1", event_time=TS)
        with pytest.raises(se.TransitionAuthorityMismatchError):
            se.advance_failure(
                xau_chain,
                se.TransitionKind.ACCEPT,
                grammar=eur,
                event_time=T1,
                acceptance_ref="ACCEPTANCE.X",
            )

    def test_compression_requires_failure(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.ACCEPT, grammar=grammar, event_time=T1,
            acceptance_ref="ACCEPTANCE.1",
        )
        with pytest.raises(se.CompressionWithoutFailureError):
            se.advance_failure(
                chain, se.TransitionKind.COMPRESS, grammar=grammar, event_time=T2
            )

    def test_release_requires_compression(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.ACCEPT, grammar=grammar, event_time=T1,
            acceptance_ref="ACCEPTANCE.1",
        )
        chain = se.advance_failure(
            chain, se.TransitionKind.FAIL, grammar=grammar, event_time=T1
        )
        with pytest.raises(se.ReleaseWithoutCompressionError):
            se.advance_failure(
                chain, se.TransitionKind.RELEASE, grammar=grammar, event_time=T2
            )

    def test_xau_band_transitions_evidence_linked(self):
        grammar = se.failure_grammar_for("XAU.GAME.L1_L2_L3.V1", "V1")
        chain = se.start_failure_chain("XAU.GAME.L1_L2_L3.V1", "V1", event_time=TS)
        chain = se.advance_failure(
            chain,
            se.TransitionKind.ACCEPT,
            grammar=grammar,
            event_time=T1,
            acceptance_ref="ACCEPTANCE.XAU.1",
        )
        with pytest.raises(se.EvidenceRequiredError):
            se.advance_failure(
                chain, se.TransitionKind.FAIL, grammar=grammar, event_time=T2
            )
        linked = se.advance_failure(
            chain,
            se.TransitionKind.FAIL,
            grammar=grammar,
            event_time=T2,
            evidence_refs=("EV.XAU.FAILURE_BAND.50_68.V1",),
        )
        assert linked.evidence_refs == ("EV.XAU.FAILURE_BAND.50_68.V1",)


# ---------------------------------------------------------------------------
# T5 — Rekey (Ch III.4.5)
# ---------------------------------------------------------------------------


def rekey_case(**overrides):
    prior = overrides.pop("prior", None) or snap(
        "EUR_DAILY", "SEED_T2", ranges=("RANGE.EUR_DAILY.SEED.V1",)
    )
    payload = dict(
        snapshot=prior,
        rule=rule("EUR_DAILY_REKEY"),
        qualifying_event_ref="EVENT.STRUCTURAL.132",
        new_mapping_ref="RANGE.EUR_DAILY.REKEY_132.V1",
        new_state="REKEY_132",
        eligibility_change="REKEYED",
        event_time=prior.event_time + timedelta(minutes=5),
        structural=True,
        prior_range_ref="RANGE.EUR_DAILY.SEED.V1",
        rekey_id="REKEY.EUR_DAILY.132",
    )
    payload.update(overrides)
    return se.plan_rekey(**payload)


class TestT5Rekey:
    def test_rekey_record_complete(self):
        record = rekey_case()
        assert record.decision.kind is se.TransitionKind.REKEY
        assert record.prior_range_ref == "RANGE.EUR_DAILY.SEED.V1"
        assert record.qualifying_event_ref == "EVENT.STRUCTURAL.132"
        assert record.new_mapping_ref == "RANGE.EUR_DAILY.REKEY_132.V1"
        assert record.new_state == "REKEY_132"
        assert record.eligibility_change == "REKEYED"
        assert record.decision.rule_id == "EUR_DAILY_REKEY"
        assert record.decision.rule_version == "V1"

    def test_132_touch_alone_refuses_rekey(self):
        with pytest.raises(se.RekeyNotStructuralError):
            rekey_case(structural=False)

    def test_rekey_replaces_prior_mapping(self):
        record = rekey_case()
        assert record.closed is True
        assert record.replaces == record.prior_range_ref
        assert record.new_mapping_ref != record.prior_range_ref
        se.assert_rekey_explicit(record)

    def test_eur_ladder_steps_distinct(self):
        assert se.EUR_DAILY_LADDER == (
            "REKEY_100",
            "REKEY_125",
            "REKEY_132",
            "REKEY_168",
            "REKEY_185",
        )
        assert len(set(se.EUR_DAILY_LADDER)) == 5

    def test_rekey_preserves_lineage(self):
        record = rekey_case()
        assert record.prior_lineage
        assert record.decision.prior_snapshot_id in record.prior_lineage
        assert record.decision.prior_state == "SEED_T2"

    def test_rekey_from_unresolved_anchor_refuses(self):
        from app.forge.measurements import AnchorStatus

        with pytest.raises(se.RekeyFromUnresolvedAnchorError):
            rekey_case(anchor_status=AnchorStatus.UNRESOLVED)

    def test_fib_rekey_requires_born_range(self):
        prior = snap("FIB_RANGE_BIRTH", "RANGE_BIRTH_UNRESOLVED", ranges=("RANGE.UNBORN",))
        with pytest.raises(se.TransitionNotEarnedError):
            se.plan_rekey(
                snapshot=prior,
                rule=rule("FIB_REKEY", source=FIB_CARD),
                qualifying_event_ref="EVENT.STRUCTURAL.1",
                new_mapping_ref="RANGE.FIB.NEW",
                new_state="REKEY_REMAPPED",
                eligibility_change="REKEYED",
                event_time=prior.event_time + timedelta(minutes=5),
                structural=True,
            )

    def test_xau_132_never_rekeys_to_168(self):
        prior = snap(
            "XAU", "REKEY_132", ranges=("RANGE.XAU.132.V1",)
        )
        with pytest.raises(se.TransitionPairForbiddenError):
            se.plan_rekey(
                snapshot=prior,
                rule=rule("XAU_REKEY", source=XAU_CARD),
                qualifying_event_ref="EVENT.STRUCTURAL.XAU",
                new_mapping_ref="RANGE.XAU.168.V1",
                new_state="REKEY_168",
                eligibility_change="REKEYED",
                event_time=prior.event_time + timedelta(minutes=5),
                structural=True,
            )

    def test_btc_weekly_monthly_rekey_unresolved(self):
        prior = snap("BTC_TRACKER", "SEED_T2")
        with pytest.raises(se.RuleNotMaterializedError):
            earned(
                se.TransitionKind.REKEY,
                prior,
                "SEED_T3",
                rule_obj=rule("BTC_WEEKLY_REKEY", source=BTC_CARD),
                conditions=frozenset({se.Condition.STRUCTURAL_EVENT}),
            )

    def test_ambiguous_rekey_order_refuses(self):
        prior = snap("EUR_DAILY", "SEED_T2", ranges=("RANGE.EUR_DAILY.SEED.V1",))
        with pytest.raises(se.TransitionOrderAmbiguousError):
            se.plan_rekey(
                snapshot=prior,
                rule=rule("EUR_DAILY_REKEY"),
                qualifying_event_ref="EVENT.STRUCTURAL.132",
                new_mapping_ref="RANGE.EUR_DAILY.REKEY_132.V1",
                new_state="REKEY_132",
                eligibility_change="REKEYED",
                event_time=prior.event_time,
                structural=True,
            )


# ---------------------------------------------------------------------------
# T6 — Layer handoff (Ch III.4.6)
# ---------------------------------------------------------------------------


def handoff(source, destination, **kw):
    return se.build_handoff(
        source_snapshot=source,
        destination_snapshot=destination,
        handoff_id=kw.pop("handoff_id", "HANDOFF.SYNTHETIC.1"),
        destination_context_ref=kw.pop("destination_context_ref", "CONTEXT.L3.DESTINATION"),
        **kw,
    )


class TestT6Handoff:
    def test_handoff_direction_downward_only(self):
        l3 = snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED")
        l2 = snap("EUR_WEEKLY", "ROUTE_OPEN")
        l1 = snap("EUR_DAILY", "SEED_T1")
        assert handoff(l3, l2).ownership is se.OwnershipScope.PATH
        assert handoff(l2, l1).ownership is se.OwnershipScope.EXECUTION
        with pytest.raises(se.LayerOwnershipViolationError):
            handoff(l1, l2)

    def test_three_layer_records_typed(self):
        l3 = snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED")
        l2 = snap("EUR_WEEKLY", "ROUTE_OPEN")
        record = handoff(l3, l2, path_ref="PATH.EUR.WEEKLY.V1")
        assert record.source_layer is Layer.L3
        assert record.destination_layer is Layer.L2
        assert record.ownership is se.OwnershipScope.PATH
        assert record.destination_context_ref == "CONTEXT.L3.DESTINATION"
        assert record.path_ref == "PATH.EUR.WEEKLY.V1"

    def test_no_upward_probability_laundering(self):
        names = {item.name for item in fields(se.LayerHandoff)}
        assert not any("probab" in name or "confidence" in name for name in names)
        l1 = snap("EUR_DAILY", "SEED_T1")
        l3 = snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED")
        with pytest.raises(se.LayerOwnershipViolationError):
            handoff(l1, l3)

    def test_l1_cannot_mutate_l3(self):
        l1 = snap("EUR_DAILY", "SEED_T1")
        l3 = snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED")
        with pytest.raises(se.LayerOwnershipViolationError) as excinfo:
            handoff(l1, l3)
        assert code_of(excinfo.value) == "LAYER_OWNERSHIP_VIOLATION"

    def test_handoff_creates_no_entry_eligibility(self):
        names = {item.name for item in fields(se.LayerHandoff)}
        assert not any("eligib" in name or "entry" in name for name in names)
        record = handoff(
            snap("EUR_WEEKLY", "ROUTE_OPEN"), snap("EUR_DAILY", "SEED_T1")
        )
        assert record.ownership is se.OwnershipScope.EXECUTION

    def test_no_monolithic_confluence_score(self):
        names = {item.name for item in fields(se.LayerHandoff)}
        assert not any("score" in name for name in names)
        record = handoff(
            snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED"),
            snap("EUR_WEEKLY", "ROUTE_OPEN"),
            agreement=se.HandoffAgreement.CONFLICT,
        )
        assert record.conflict_facts == ("MODEL_CONFLICT.L3_TO_L2",)

    def test_xau_layers_separately_typed(self):
        l3 = snap("XAU", "UNRESOLVED", layer=Layer.L3)
        l2 = snap("XAU", "ROUTE_OPEN", layer=Layer.L2)
        l1 = snap("XAU", "PROMOTION_PENDING", layer=Layer.L1)
        assert handoff(l3, l2).ownership is se.OwnershipScope.PATH
        assert handoff(l2, l1).ownership is se.OwnershipScope.EXECUTION
        # L2 state is never a direct entry: no handoff field carries one.
        assert not any("entry" in item.name for item in fields(se.LayerHandoff))

    def test_eur_l3_l2_l1_chain(self):
        l3 = snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED")
        l2 = snap("EUR_WEEKLY", "ROUTE_OPEN")
        l1 = snap("EUR_DAILY", "SEED_T1")
        first = handoff(l3, l2, handoff_id="HANDOFF.EUR.1")
        second = handoff(l2, l1, handoff_id="HANDOFF.EUR.2")
        assert first.destination_snapshot_id == second.source_snapshot_id
        se.assert_layer_isolation(first)
        se.assert_layer_isolation(second)

    def test_layer_conflict_returns_facts(self):
        facts = se.layer_conflict_facts(
            source_layer=Layer.L3,
            destination_layer=Layer.L2,
            agreement=se.HandoffAgreement.CONFLICT,
        )
        assert facts == ("MODEL_CONFLICT.L3_TO_L2",)
        assert se.layer_conflict_facts(
            source_layer=Layer.L3, destination_layer=Layer.L2
        ) == ()

    def test_handoff_requires_both_snapshots(self):
        l3 = snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED")
        with pytest.raises(se.StateContractError):
            se.build_handoff(
                source_snapshot=l3,
                destination_snapshot=None,  # type: ignore[arg-type]
                handoff_id="HANDOFF.X",
                destination_context_ref="CONTEXT.X",
            )
        foreign = snap("BTC_TRACKER", "SEED_T1")
        with pytest.raises(se.TransitionAuthorityMismatchError):
            handoff(l3, foreign)

    def test_handoff_roundtrip_preserves_ownership(self):
        record = handoff(
            snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED"),
            snap("EUR_WEEKLY", "ROUTE_OPEN"),
        )
        payload = record.to_payload()
        assert payload["ownership"] == record.ownership.value
        assert payload["source_layer"] == "L3"
        assert payload["destination_layer"] == "L2"


# ---------------------------------------------------------------------------
# T7 — Range-left (Ch III.4.7)
# ---------------------------------------------------------------------------


def condition(event: se.ConsumedEvent, ref: str) -> se.RangeLeftCondition:
    return se.RangeLeftCondition(event=event, ref=ref)


class TestT7RangeLeft:
    def test_range_left_conditional_on_consumed(self):
        record = se.recompute_range_left(
            prior=None,
            conditions=(condition(se.ConsumedEvent.DELIVERY, "TARGET.EUR.100"),),
            measurement=magnitude("80"),
        )
        assert record.state is RemainingState.MEASURED
        assert record.conditioned_on == ("TARGET.EUR.100",)
        assert record.value is not None

    def test_range_left_updates_after_each_event(self):
        prior = None
        expected = 0
        for index, event in enumerate(se.ConsumedEvent):
            prior = se.recompute_range_left(
                prior=prior,
                conditions=(condition(event, f"EVENT.{index}.{event.value}"),),
                measurement=magnitude(str(80 - index)),
            )
            expected += 1
            assert len(prior.conditioned_on) == expected

    def test_unconditional_frequency_refused(self):
        with pytest.raises(se.UnconditionalFrequencyRefusedError):
            se.from_historical_frequency(frequency="0.68")
        with pytest.raises(se.UnconditionalFrequencyRefusedError):
            se.recompute_range_left(prior=None, conditions=(), measurement=magnitude("120"))

    def test_range_left_unresolved_honest(self):
        record = se.recompute_range_left(prior=None, conditions=(), measurement=None)
        assert record.state is RemainingState.UNRESOLVED
        assert record.value is None
        assert record.conditioned_on == ()

    def test_consumed_target_not_requoted(self):
        prior = se.recompute_range_left(
            prior=None,
            conditions=(condition(se.ConsumedEvent.DELIVERY, "TARGET.EUR.100"),),
            measurement=magnitude("80"),
        )
        with pytest.raises(se.ConsumedTargetRequotedError):
            se.recompute_range_left(
                prior=prior,
                conditions=(condition(se.ConsumedEvent.ACCEPTANCE, "TARGET.EUR.100"),),
                measurement=magnitude("70"),
                available_targets=("TARGET.EUR.100",),
            )

    def test_btc_slot_tier_range_left(self):
        record = se.recompute_range_left(
            prior=None,
            conditions=(condition(se.ConsumedEvent.DELIVERY, "SLOT.BTC.03_19"),),
            measurement=magnitude("900", unit=NativeUnit.DOLLAR, instrument="BTCUSD"),
        )
        assert record.state is RemainingState.MEASURED
        assert record.unit == NativeUnit.DOLLAR.value
        assert record.value.instrument_id == "BTCUSD"

    def test_exhausted_state_not_reopened(self):
        with pytest.raises(se.ConsumedStateReopenedError):
            se.recompute_range_left(
                prior=None,
                conditions=(condition(se.ConsumedEvent.EXHAUSTION, "TARGET.EUR.185"),),
                measurement=magnitude("10"),
                exhausted=True,
            )

    def test_range_left_native_units(self):
        value = magnitude("42", unit=NativeUnit.POINT, instrument="XAUUSD")
        record = se.recompute_range_left(
            prior=None,
            conditions=(condition(se.ConsumedEvent.ACCEPTANCE, "LEVEL.XAU.80"),),
            measurement=value,
        )
        assert record.value is value
        assert record.value.unit is NativeUnit.POINT
        assert record.unit == "POINT"


# ---------------------------------------------------------------------------
# T8 — No-go / stand-down (Ch III.4.8)
# ---------------------------------------------------------------------------


def sd(reason: NoGoReason = NoGoReason.ASIAN_RANGE_NO_GO, **kw):
    return se.stand_down_for_no_go(
        reason,
        blocking_rule_ref=kw.pop("blocking_rule_ref", "RULE.SYNTHETIC.V1"),
        snapshot_id=kw.pop("snapshot_id", "SNAP.BTC_TRACKER.SEED_T1"),
        **kw,
    )


class TestT8StandDown:
    def test_stand_down_states_bounded(self):
        assert {state.value for state in se.StandDownState} == {
            "DATA_QUALITY_FAILURE",
            "INVALID_RANGE",
            "UNRESOLVED_ANCHOR",
            "MODEL_CONFLICT",
            "PARKED_OR_EXHAUSTED",
            "EVIDENCE_UNAVAILABLE",
        }
        with pytest.raises(ValueError):
            se.StandDownState("SOMETHING_ELSE")  # type: ignore[arg-type]

    def test_stand_down_reason_bounded(self):
        record = sd()
        assert isinstance(record.reason, se.StandDownReason)
        with pytest.raises(se.StateContractError):
            se.StandDownRecord(
                state=record.state,
                reason="RANGE_TOO_LARGE",  # type: ignore[arg-type]
                blocking_rule_ref="RULE.X",
                snapshot_id="SNAP.X",
            )

    def test_no_go_blocks_eligibility(self):
        record = sd()
        with pytest.raises(se.EligibilityWithoutAuthorityError):
            se.assert_setup_eligibility_allowed(record)
        prior = snap("XAU", "PARKED_OR_EXHAUSTED")
        with pytest.raises(se.EligibilityWithoutAuthorityError):
            earned(
                se.TransitionKind.PROMOTE,
                prior,
                "PROMOTION_ELIGIBLE",
                rule_obj=rule("XAU_PROMOTION_68_80", source=XAU_CARD),
                evidence_refs=("EV.XAU.PROMOTION.68_80.V1",),
            )

    def test_stand_down_exposes_eligibility_lock(self):
        record = sd()
        assert record.eligibility_lock is True
        assert "SETUP_ELIGIBILITY" in record.capabilities_locked
        payload = record.to_payload()
        assert payload["eligibility_lock"] is True

    def test_parked_state_not_cleared(self):
        prior = snap("XAU", "PARKED")
        with pytest.raises(se.TransitionNotEarnedError):
            earned(
                se.TransitionKind.PROMOTE,
                prior,
                "PROMOTION_ELIGIBLE",
                rule_obj=rule("XAU_PROMOTION_68_80", source=XAU_CARD),
                evidence_refs=("EV.XAU.PROMOTION.68_80.V1",),
            )

    def test_data_quality_failure_stand_down(self):
        record = se.StandDownRecord(
            state=se.StandDownState.DATA_QUALITY_FAILURE,
            reason=se.StandDownReason.DATA_BAD,
            blocking_rule_ref="RULE.QUALITY.V1",
            snapshot_id="SNAP.EUR_DAILY.SEED_T1",
        )
        assert record.state is se.StandDownState.DATA_QUALITY_FAILURE
        with pytest.raises(se.EligibilityWithoutAuthorityError):
            se.assert_setup_eligibility_allowed(record)

    def test_unresolved_anchor_stand_down(self):
        record = sd(NoGoReason.RULE_NOT_MATERIALIZED)
        assert record.state is se.StandDownState.UNRESOLVED_ANCHOR
        assert record.reason is se.StandDownReason.ANCHOR_UNRESOLVED

    def test_evidence_unavailable_blocks_statistics(self):
        record = se.StandDownRecord(
            state=se.StandDownState.EVIDENCE_UNAVAILABLE,
            reason=se.StandDownReason.INSUFFICIENT_EVIDENCE,
            blocking_rule_ref="RULE.EVIDENCE.V1",
            snapshot_id="SNAP.EUR_HIGHER_ORDER.PRIOR_DECLARED",
        )
        payload = record.to_payload()
        assert not any(
            token in str(payload).lower()
            for token in ("probability", "expectancy", "win_rate")
        )
        with pytest.raises(se.EligibilityWithoutAuthorityError):
            se.assert_setup_eligibility_allowed(record)

    def test_family_no_go_maps_to_stand_down(self):
        assert sd(NoGoReason.ASIAN_RANGE_NO_GO).state is se.StandDownState.INVALID_RANGE
        assert sd(NoGoReason.AR_SOURCE_NO_GO).state is se.StandDownState.INVALID_RANGE
        assert sd(NoGoReason.NATIVE_TIER_NO_GO).state is se.StandDownState.INVALID_RANGE
        assert (
            sd(NoGoReason.PROMOTION_PARKED).state
            is se.StandDownState.PARKED_OR_EXHAUSTED
        )

    def test_stand_down_is_state_not_erasure(self):
        record = sd()
        assert record.snapshot_id == "SNAP.BTC_TRACKER.SEED_T1"
        assert record.blocking_rule_ref == "RULE.SYNTHETIC.V1"
        assert record.reason is se.StandDownReason.RANGE_TOO_LARGE


# ---------------------------------------------------------------------------
# T9 — Transition history (Ch III.4.9)
# ---------------------------------------------------------------------------


class TestT9History:
    def test_repair_chain_replays_identically(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        runs = []
        for _ in range(2):
            chain = se.start_failure_chain(
                "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
            )
            chain = se.advance_failure(
                chain, se.TransitionKind.ACCEPT, grammar=grammar, event_time=T1,
                acceptance_ref="ACCEPTANCE.1",
            )
            chain = se.advance_failure(
                chain, se.TransitionKind.FAIL, grammar=grammar, event_time=T1
            )
            chain = se.advance_failure(
                chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T2
            )
            runs.append(chain)
        assert runs[0].steps == runs[1].steps
        assert runs[0].state is runs[1].state

    def test_history_append_only(self):
        genesis, snapshots, ledger = eur_ledger()
        assert len(ledger.events) == 3
        assert not hasattr(ledger, "pop") and not hasattr(ledger, "remove")
        with pytest.raises(FrozenInstanceError):
            ledger.events = ()  # type: ignore[misc]
        se.verify_history(ledger)

    def test_history_sequence_gapless(self):
        _genesis, _snapshots, ledger = eur_ledger()
        assert [event.sequence for event in ledger.events] == [0, 1, 2]
        broken = replace(
            ledger, events=(replace(ledger.events[0], sequence=5),) + ledger.events[1:]
        )
        with pytest.raises(se.HistorySequenceGapError):
            se.verify_history(broken)

    def test_event_required_fields(self):
        _genesis, _snapshots, ledger = eur_ledger()
        for event in ledger.events:
            assert event.source_snapshot_ref
            assert event.event_time.tzinfo is not None
            assert event.rule_id and event.rule_version
            assert event.resulting_state_id
            assert event.engine_version == se.STATE_ENGINE_VERSION
            assert event.prev_event_hash and event.event_hash

    def test_replay_reconstructs_current_state(self):
        genesis, snapshots, ledger = eur_ledger()
        mapping = {
            genesis.snapshot_id: genesis,
            **{
                snapshot.snapshot_id: snapshot
                for snapshot in snapshots.values()
            },
        }
        reconstructed = se.reconstruct_state(ledger, mapping)
        assert reconstructed.snapshot_id == ledger.current_state_id
        assert reconstructed.snapshot_hash == mapping[ledger.current_state_id].snapshot_hash

    def test_explanation_is_ordered_facts_no_prose(self):
        _genesis, _snapshots, ledger = eur_ledger()
        facts = se.explain(ledger)
        assert len(facts) == len(ledger.events)
        pattern = re.compile(r"^[A-Za-z0-9_.:+/=\-]*$")
        for fact in facts:
            assert re.match(r"^[A-Z][A-Z0-9_.]*$", fact.fact_id)
            for _key, value in fact.payload:
                assert pattern.match(value)
                assert " " not in value

    def test_historical_state_queryable(self):
        genesis, snapshots, ledger = eur_ledger()
        mapping = {
            genesis.snapshot_id: genesis,
            **{snapshot.snapshot_id: snapshot for snapshot in snapshots.values()},
        }
        first = se.state_at(ledger, 1, genesis=genesis, snapshots=mapping)
        assert first.snapshot_id == snapshots["s1"].snapshot_id
        assert first.active_state == "REKEY_100"
        assert se.state_at(ledger, 0, genesis=genesis, snapshots=mapping) is genesis

    def test_event_order_mutation_detected(self):
        _genesis, _snapshots, ledger = eur_ledger()
        with pytest.raises(se.HistoryChainMismatchError):
            se.verify_history(tampered(ledger, 0, 1))

    def test_replay_hash_deterministic(self):
        _genesis, _snapshots, first = eur_ledger()
        _genesis2, _snapshots2, second = eur_ledger()
        assert first.history_hash == second.history_hash
        assert first.event_hashes == second.event_hashes

    def test_negative_evidence_queryable(self):
        _genesis, _snapshots, ledger = eur_ledger()
        negative = ledger.negative_events()
        assert len(negative) == 1
        assert negative[0].kind is se.TransitionKind.STAND_DOWN
        assert negative[0].resulting_state == "INVALID_RANGE"

    def test_history_hash_cross_platform_stable(self):
        _genesis, _snapshots, ledger = eur_ledger()
        recomputed = se.history_hash(
            genesis_snapshot_hash=ledger.genesis_snapshot_hash, events=ledger.events
        )
        assert recomputed == ledger.history_hash
        assert len(ledger.history_hash) == 64


# ---------------------------------------------------------------------------
# T10 — Path invariants and the adversarial matrix (Ch III.4.10)
# ---------------------------------------------------------------------------


class TestT10PathInvariants:
    def test_touch_without_acceptance(self):
        prior = snap("EUR_DAILY", "REKEY_100")
        with pytest.raises(se.AcceptWithoutTouchError):
            earned(se.TransitionKind.ACCEPT, prior, "REKEY_125")

    def test_same_terminal_result_different_path(self):
        common = dict(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
        )
        ab = se.build_path(
            **common,
            observations=(
                observation("TARGET_A", TS, "BAR.1"),
                observation("TARGET_B", T1, "BAR.2"),
            ),
        )
        ba = se.build_path(
            **common,
            observations=(
                observation("TARGET_B", TS, "BAR.1"),
                observation("TARGET_A", T1, "BAR.2"),
            ),
        )
        assert ab.terminal_result == ba.terminal_result
        assert compute_hash(ab.to_payload()) != compute_hash(ba.to_payload())

    def test_ambiguous_intrabar_events(self):
        with pytest.raises(se.AmbiguousPathError):
            se.build_path(
                clock_id="CLOCK.UTC",
                targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
                observations=(
                    observation("TARGET_A", TS, "BAR.9"),
                    observation("TARGET_B", TS, "BAR.9"),
                ),
                intrabar_order_resolvable=False,
            )

    def test_repair_without_prior_failure(self):
        grammar = se.failure_grammar_for("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
        chain = se.start_failure_chain(
            "EUR.DAILY.NEWS_REKEY.V1", "PHASE1", event_time=TS
        )
        with pytest.raises(se.RepairWithoutFailureError):
            se.advance_failure(
                chain, se.TransitionKind.REPAIR, grammar=grammar, event_time=T1
            )

    def test_invalid_rekey(self):
        with pytest.raises(se.RekeyNotStructuralError):
            rekey_case(structural=False)

    def test_l1_mutation_of_l3(self):
        with pytest.raises(se.LayerOwnershipViolationError):
            handoff(
                snap("EUR_DAILY", "SEED_T1"),
                snap("EUR_HIGHER_ORDER", "PRIOR_DECLARED"),
            )

    def test_no_go_does_not_allow_setup_eligibility(self):
        record = sd()
        with pytest.raises(se.EligibilityWithoutAuthorityError):
            se.assert_setup_eligibility_allowed(record)
        with pytest.raises(se.EligibilityWithoutAuthorityError):
            earned(
                se.TransitionKind.ACCEPT,
                snap("EUR_DAILY", "INVALID_RANGE"),
                "REKEY_100",
                conditions=frozenset({se.Condition.TOUCHED}),
            )

    def test_event_order_mutation(self):
        _genesis, _snapshots, ledger = eur_ledger()
        with pytest.raises(se.HistoryChainMismatchError):
            se.verify_history(tampered(ledger, 1, 2))

    def test_non_deterministic_replay_detected(self):
        _genesis, _snapshots, ledger = eur_ledger()
        event = ledger.events[1]
        rewritten = replace(event, resulting_state="REKEY_185")
        broken = replace(
            ledger, events=(ledger.events[0], rewritten, ledger.events[2])
        )
        with pytest.raises(se.HistoryChainMismatchError):
            se.verify_history(broken)

    def test_terminal_outcome_cannot_erase_path(self):
        path = se.build_path(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
            observations=(
                observation("TARGET_B", TS, "BAR.1"),
                observation("TARGET_A", T1, "BAR.2"),
            ),
        )
        se.assert_terminal_does_not_erase_path(path)
        assert path.delivery_order == ("TARGET_B", "TARGET_A")
        assert path.first_delivery.target_id == "TARGET_B"

    def test_target_order_stable_under_replay(self):
        declared = targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1))
        runs = [
            se.build_path(
                clock_id="CLOCK.UTC",
                targets=declared,
                observations=(
                    observation("TARGET_A", TS, "BAR.1"),
                    observation("TARGET_B", T1, "BAR.2"),
                ),
            )
            for _ in range(2)
        ]
        se.assert_target_order_stable(runs[0], runs[1])
        assert compute_hash(runs[0].to_payload()) == compute_hash(runs[1].to_payload())

    def test_rekey_closes_or_replaces_mapping(self):
        record = rekey_case()
        se.assert_rekey_explicit(record)
        assert record.closed is True
        assert record.replaces == record.prior_range_ref

    def test_first_delivery_order_reversal(self):
        common = dict(
            clock_id="CLOCK.UTC",
            targets=targets(("TARGET_A", "ABOVE", 0), ("TARGET_B", "BELOW", 1)),
        )
        ab = se.build_path(
            **common,
            observations=(
                observation("TARGET_A", TS, "BAR.1"),
                observation("TARGET_B", T1, "BAR.2"),
            ),
        )
        ba = se.build_path(
            **common,
            observations=(
                observation("TARGET_B", TS, "BAR.1"),
                observation("TARGET_A", T1, "BAR.2"),
            ),
        )
        se.assert_paths_differ_under_reversal(ab, ba, compute_hash)

    def test_parked_xau_promotion_refused(self):
        with pytest.raises(se.TransitionNotEarnedError):
            earned(
                se.TransitionKind.PROMOTE,
                snap("XAU", "PARKED"),
                "PROMOTION_ELIGIBLE",
                rule_obj=rule("XAU_PROMOTION_68_80", source=XAU_CARD),
                evidence_refs=("EV.XAU.PROMOTION.68_80.V1",),
            )

    def test_btc_game_into_tracker_refused(self):
        with pytest.raises(se.TransitionAuthorityMismatchError):
            earned(
                se.TransitionKind.DELIVER,
                snap("BTC_TRACKER", "SEED_T1"),
                "SEED_T2",
                rule_obj=rule("XAU_PROMOTION_68_80", source=XAU_CARD),
            )

    def test_jpy_equal_vote_impossible(self):
        entry = se.authority_for("JPY.CARRY_GAME.L1_L3.V1", "V1")
        assert se.TransitionKind.ACCEPT not in entry.allowed
        assert se.TransitionKind.PROMOTE not in entry.allowed
        text = " ".join(package_text().values()).upper()
        assert "MAJORITY" not in text
        assert "EQUAL_VOTE" not in text
        assert not any("vote" in name.lower() for name in dataclass_field_names())

    def test_missing_source_evidence_refuses(self):
        prior = snap()
        object.__setattr__(prior, "source_output_hash", "")
        with pytest.raises(se.SourceLineageMissingError):
            earned(se.TransitionKind.DELIVER, prior, "REKEY_100")

    def test_nonfinal_or_poor_quality_bars_refuse(self):
        blocked = snap(quality=DataOutcome.DATA_QUALITY_BLOCKED)
        with pytest.raises(se.DataQualityBlockedError):
            earned(se.TransitionKind.DELIVER, blocked, "REKEY_100")
        uncalculable = snap(quality=DataOutcome.NO_CALCULATION)
        with pytest.raises(se.NoCalculationError):
            earned(se.TransitionKind.DELIVER, uncalculable, "REKEY_100")

    def test_historical_version_drift_refused(self):
        with pytest.raises(se.ModelVersionUnavailableError):
            se.authority_for("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM")
        with pytest.raises(se.ModelVersionUnavailableError):
            se.authority_for("XAU.GAME.L1_L2_L3.V1", "V0")

    def test_unearned_transition_refused(self):
        prior = snap("EUR_DAILY", "REKEY_185")

        def attempt():
            return earned(
                se.TransitionKind.REKEY,
                prior,
                "REKEY_168",
                conditions=frozenset({se.Condition.STRUCTURAL_EVENT}),
            )

        se.assert_unearned_refused(attempt)
        with pytest.raises(se.TransitionNotEarnedError):
            attempt()


# ---------------------------------------------------------------------------
# T11 — Label and serialization discipline
# ---------------------------------------------------------------------------


PERFORMANCE_TOKENS = (
    "probab",
    "confidence",
    "confluen",
    "win_rate",
    "winrate",
    "expectancy",
    "risk_reward",
    "prediction",
    "profit",
    "pnl",
)


class TestT11Discipline:
    def test_snapshot_grants_no_eligibility(self):
        names = {item.name for item in fields(se.StateSnapshot)}
        assert not any("eligib" in name for name in names)
        assert "production_authorization" in names
        snapshot = snap()
        assert snapshot.production_authorization in set(ProductionAuthorization)

    def test_vocabulary_carries_no_trading_semantics(self):
        for kind in KINDS:
            assert not any(
                token in kind.lower()
                for token in ("signal", "entry", "target", "profit", "long", "short")
            )

    def test_delivery_carries_no_performance_semantics(self):
        names = {item.name for item in fields(se.DeliveryPath)}
        assert not any(token in name for name in names for token in PERFORMANCE_TOKENS)
        assert not any("target_before_stop" in name for name in names)

    def test_repair_carries_no_probability(self):
        names = {item.name for item in fields(se.FailureRecord)}
        assert not any(token in name for name in names for token in PERFORMANCE_TOKENS)

    def test_rekey_carries_no_probability(self):
        names = {item.name for item in fields(se.RekeyRecord)}
        assert not any(token in name for name in names for token in PERFORMANCE_TOKENS)

    def test_range_left_carries_no_probability(self):
        names = {item.name for item in fields(se.ConditionalRangeLeft)}
        assert not any(token in name for name in names for token in PERFORMANCE_TOKENS)

    def test_history_carries_no_performance_metric(self):
        for cls in (se.TransitionEvent, se.TransitionLedger):
            names = {item.name for item in fields(cls)}
            assert not any(
                token in name for name in names for token in PERFORMANCE_TOKENS
            )

    def test_no_probability_confidence_or_performance_fields(self):
        names = dataclass_field_names()
        for name in names:
            assert not any(token in name for token in PERFORMANCE_TOKENS), name

    def test_no_setup_objects_exist(self):
        forbidden = ("setup", "entry", "trigger", "position", "sizing")
        for name, tree in package_trees().items():
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    assert not any(token in node.name.lower() for token in forbidden), (
                        f"{name}:{node.name}"
                    )

    def test_missing_evidence_attaches_no_statistic(self):
        record = se.StandDownRecord(
            state=se.StandDownState.EVIDENCE_UNAVAILABLE,
            reason=se.StandDownReason.INSUFFICIENT_EVIDENCE,
            blocking_rule_ref="RULE.EVIDENCE.V1",
            snapshot_id="SNAP.EUR_HIGHER_ORDER.PRIOR_DECLARED",
        )
        payload = record.to_payload()
        assert set(payload) == {
            "state",
            "reason",
            "blocking_rule_ref",
            "snapshot_id",
            "capabilities_locked",
            "eligibility_lock",
        }

    def test_no_new_derived_semantics(self):
        forbidden = ("classify_tier", "measure_range", "measure_path", "project_coordinates")
        for name, tree in package_trees().items():
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    assert node.name not in forbidden, f"{name}:{node.name}"

    def test_model_state_not_setup(self):
        snapshot = snap()
        assert snapshot.active_state
        assert not any("setup" in name for name in dataclass_field_names())

    def test_no_automation_approval_field(self):
        for name in dataclass_field_names():
            assert "automation" not in name, name

    def test_manual_operator_preserved(self):
        snapshot = snap("JPY_CARRY", "BASKET_UNRESOLVED",
                        authorization=ProductionAuthorization.MANUAL_OPERATOR)
        assert snapshot.production_authorization is ProductionAuthorization.MANUAL_OPERATOR

    def test_no_performance_claims_from_fixtures(self):
        for path in sorted(FIXTURE_DIR.glob("*.json")):
            if path.name == "FIXTURE_MANIFEST.json":
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert "data_classification" in payload, path.name
            assert "SYNTHETIC_FIXTURE" in payload["data_classification"] or (
                "CANONICAL_SOURCE_SLICE" in payload["data_classification"]
            ), path.name
            text = json.dumps(payload).lower()
            for token in ("win_rate", "expectancy", "profit_factor"):
                assert token not in text, f"{path.name}:{token}"

    def test_no_free_text_labels(self):
        for value in enum_member_values():
            assert re.match(r"^[A-Za-z0-9_.:/\-]*$", value), value

    def test_no_claims_created(self):
        snapshot = snap()
        assert snapshot.claim_refs == ()
        with pytest.raises(se.StateContractError):
            replace(snapshot, claim_refs=("CLAIM.X",))

    def test_no_prediction_or_signal_vocabulary(self):
        for value in enum_member_values():
            lowered = value.lower()
            assert "predict" not in lowered
            assert "signal" not in lowered


# ---------------------------------------------------------------------------
# T12 — Boundaries, frozen surfaces, determinism
# ---------------------------------------------------------------------------


class TestT12Boundaries:
    def test_no_persistence_migration_added(self):
        from app.forge.persistence.sql.migrations import discover_migrations

        assert [migration.version for migration in discover_migrations()] == [1, 2, 3, 4]
        assert not list(
            (REPO_ROOT / "app/forge/persistence/sql").glob("005_*.sql")
        )

    def test_state_engine_version_recorded(self):
        assert se.STATE_ENGINE_VERSION == "STATE_ENGINE_V1"
        snapshot = snap()
        assert snapshot.state_engine_version == se.STATE_ENGINE_VERSION
        _genesis, _snapshots, ledger = eur_ledger()
        assert all(
            event.engine_version == se.STATE_ENGINE_VERSION for event in ledger.events
        )
        manifest = json.loads((FIXTURE_DIR / "FIXTURE_MANIFEST.json").read_text())
        assert manifest["engine_version"] == se.STATE_ENGINE_VERSION

    def test_fixture_manifest_hashes_reproduce(self):
        manifest = json.loads((FIXTURE_DIR / "FIXTURE_MANIFEST.json").read_text())
        assert manifest["algorithm"] == "sha256"
        files = manifest["files"]
        assert len(files) == 12
        for name, expected in files.items():
            raw = (FIXTURE_DIR / name).read_bytes().replace(b"\r\n", b"\n")
            assert hashlib.sha256(raw).hexdigest() == expected, name

    def test_import_discipline(self):
        allowed_roots = {
            "__future__",
            "dataclasses",
            "datetime",
            "decimal",
            "enum",
            "re",
            "types",
            "typing",
        }
        allowed_app = {
            "app.forge.market_data",
            "app.forge.measurements",
            "app.forge.model_runtime",
        }
        for name, tree in package_trees().items():
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if node.level:
                        continue
                    root = module.split(".")[0]
                    if module.startswith("app."):
                        assert module in allowed_app, f"{name}: {module}"
                    else:
                        assert root in allowed_roots, f"{name}: {module}"
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        assert root in {"app"} or root in allowed_roots, (
                            f"{name}: {alias.name}"
                        )

    def test_no_legacy_state_engine_import(self):
        for name, text in package_text().items():
            assert "app.state_engine" not in text, name
            assert "from app import state_engine" not in text, name

    def test_no_network_access(self):
        def boom(*_args, **_kwargs):
            raise AssertionError("network access is forbidden in Bloc III.4")

        import socket as socket_module

        original_socket = socket_module.socket
        original_connect = socket_module.create_connection
        original_resolve = socket_module.getaddrinfo
        socket_module.socket = boom  # type: ignore[assignment]
        socket_module.create_connection = boom  # type: ignore[assignment]
        socket_module.getaddrinfo = boom  # type: ignore[assignment]
        try:
            _genesis, _snapshots, ledger = eur_ledger()
            se.verify_history(ledger)
            se.explain(ledger)
        finally:
            socket_module.socket = original_socket
            socket_module.create_connection = original_connect
            socket_module.getaddrinfo = original_resolve

    def test_no_io_or_wallclock(self):
        for name, tree in package_trees().items():
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name):
                        assert func.id not in {"open", "print", "input"}, name
                    if isinstance(func, ast.Attribute):
                        assert func.attr not in {"now", "utcnow", "today", "time"}, name
                if isinstance(node, ast.Attribute):
                    assert node.attr not in {"write_text", "write_bytes"}, name

    def test_no_composition_root_import(self):
        for name, text in package_text().items():
            assert "ForgeServiceContainer" not in text, name

    def test_no_corpus_or_ledger_writes(self):
        for name, text in package_text().items():
            assert "corpus/" not in text, name
            assert "open(" not in text, name

    def test_market_data_readiness_seam_unchanged(self):
        from app.forge.config import ForgeConfig
        from app.forge.service.container import ForgeServiceContainer

        container = ForgeServiceContainer(config=ForgeConfig(environment="test"))
        dependencies = container.as_readiness_dependencies()
        assert dependencies["market_data"] == {
            "status": "NOT_CONFIGURED",
            "required": False,
            "note": "market-data providers belong to Book III; not wired at II.1",
        }
        for name, text in package_text().items():
            assert "ForgeServiceContainer" not in text, name

    def test_frozen_manifests_unchanged(self):
        text = BOOK_II_MANIFEST.read_text(encoding="utf-8")
        entries = re.findall(r"`([^`\s]+)`\s+—\s+`([0-9a-f]{64})`", text)
        assert len(entries) == 50, len(entries)
        for rel_path, expected in entries:
            raw = (REPO_ROOT / rel_path).read_bytes()
            normalized = raw.replace(b"\r\n", b"\n")
            candidates = {
                hashlib.sha256(raw).hexdigest(),
                hashlib.sha256(normalized).hexdigest(),
                hashlib.sha256(normalized.replace(b"\n", b"\r\n")).hexdigest(),
            }
            assert expected in candidates, rel_path

        planning = PLANNING_MANIFEST.read_text(encoding="utf-8")
        pins = re.findall(
            r"^-\s+(\S+)\s*\r?\n\s+commit\s+([0-9a-f]{40})\s*$",
            planning,
            re.MULTILINE,
        )
        assert len(pins) == 23, len(pins)
        for rel_path, _sha in pins:
            assert (REPO_ROOT / rel_path).exists(), rel_path

        for pkg, count in (
            ("market_data", 11),
            ("measurements", 12),
            ("model_runtime", 13),
        ):
            directory = REPO_ROOT / "app" / "forge" / pkg
            assert len(sorted(directory.glob("*.py"))) == count

        baseline = III3_RATIFICATION.read_text(encoding="utf-8")
        pairs = re.findall(r"`([A-Za-z_]+\.py) ([0-9a-f]{8})…([0-9a-f]{4,5})`", baseline)
        assert len(pairs) == 13
        package = REPO_ROOT / "app" / "forge" / "model_runtime"
        for name, prefix, suffix in pairs:
            raw = (package / name).read_bytes().replace(b"\r\n", b"\n")
            digest = hashlib.sha256(raw).hexdigest()
            assert digest.startswith(prefix) and digest.endswith(suffix), name

    def test_no_secrets_or_free_text(self):
        for name, text in package_text().items():
            lowered = text.lower()
            for token in ("api_key", "password", "secret_key", "bearer "):
                assert token not in lowered, name

    def test_deterministic_repeat_run(self):
        first = eur_ledger()
        second = eur_ledger()
        assert first[2].history_hash == second[2].history_hash
        assert first[2].event_hashes == second[2].event_hashes
        snapshot_a = snap()
        snapshot_b = snap()
        assert snapshot_a.snapshot_hash == snapshot_b.snapshot_hash

    def test_no_float_prices(self):
        for name, tree in package_trees().items():
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, float):
                    raise AssertionError(f"{name}: float literal {node.value}")
                annotation = None
                if isinstance(node, ast.arg):
                    annotation = node.annotation
                elif isinstance(node, ast.AnnAssign):
                    annotation = node.annotation
                if isinstance(annotation, ast.Name):
                    assert annotation.id != "float", name
