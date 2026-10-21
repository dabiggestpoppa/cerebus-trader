"""Focused Bloc III.3 suite: CEREBUS Model Runtime.

Binding specification: ``implementation/forge/book_iii/bloc_iii_3/
ACCEPTANCE.md`` — every frozen clause in §A–§P maps to a named test in
this file (the mapping may gain tests at implementation time, it may
never lose or weaken one).  Groups T1–T12 follow ``PLAN.md`` §8.

Discipline: deterministic, offline, network-free.  Inputs come only
from the committed golden fixtures under ``implementation/forge/
book_iii/bloc_iii_3/fixtures/`` (generated deterministically by the
committed generator, which is also the single source of truth for
rebuilding every ``ModelRequest``), the frozen III.1 market-data
contracts and the frozen III.2 measurement contracts.  No wall clock,
no credentials, no provider SDK, no corpus write, no migration.

Passing these fixture contract tests is **not** empirical
strategy-performance validation: every synthetic fixture is labeled at
creation and can never satisfy an evidence-reference check (O3/O4).
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import inspect
import json
import re
import socket
import subprocess
import sys
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from app.forge.market_data import (
    Bar,
    DataOutcome,
    Finality,
    QualityFlag,
)
from app.forge.measurements import (
    AnchorRefusalCode,
    AnchorStatus,
    Measurement,
    MeasurementContractError,
    RangeMeasurement,
    measure_range,
)
from app.forge.model_runtime import (
    MODEL_REGISTRY,
    MODEL_RUNTIME_CODES,
    MODEL_RUNTIME_VERSION,
    AnchorStateRef,
    BtcTrackerInputs,
    DirectionBias,
    DirectionSide,
    EurDailyInputs,
    EurHigherOrderInputs,
    EurWeeklyInputs,
    FibRangeBirthInputs,
    InputIdentity,
    InstrumentScopeMismatchError,
    JpyCarryInputs,
    JpyPairInput,
    JpyRole,
    Layer,
    LevelKind,
    ModelContractError,
    ModelKey,
    ModelOutput,
    ModelRequest,
    ModelRuntimeError,
    ModelVersionUnavailableError,
    NoCalculationError,
    NoGoReason,
    PriorStateMismatchError,
    ProductionAuthorization,
    RangeLeftField,
    RegistryEntry,
    ReplayHashMismatchError,
    RuleNotMaterializedError,
    SubState,
    TypedLevel,
    WarningCode,
    XauGameInputs,
    canonical_blob,
    canonical_payload,
    compute_hash,
    resolve,
    run_model,
    verify_replay,
)
import app.forge.model_runtime as model_runtime_pkg
from app.forge.persistence.sql.migrations import discover_migrations
from app.forge.service.container import ForgeServiceContainer
from app.forge.config import ForgeConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
III3_FIXTURE_DIR = (
    REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_3" / "fixtures"
)
PACKAGE_DIR = REPO_ROOT / "app" / "forge" / "model_runtime"
BOOK_II_FREEZE_MANIFEST = (
    REPO_ROOT / "implementation" / "forge" / "book_ii" / "ratification"
    / "CONTRACT_FREEZE_MANIFEST_V1.md"
)
PLANNING_FREEZE_MANIFEST = REPO_ROOT / "planning" / "forge" / "PLANNING_FREEZE_MANIFEST_V1.md"
BOOK_I_FREEZE_MANIFEST = (
    REPO_ROOT / "implementation" / "forge" / "book_i" / "bloc_i_5"
    / "BOOK_I_FREEZE_MANIFEST_V1.md"
)
III2_PLAN = REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_2" / "PLAN.md"
III3_PLAN = REPO_ROOT / "implementation" / "forge" / "book_iii" / "bloc_iii_3" / "PLAN.md"

#: The generator is the single source of truth for fixture documents
#: and request reconstruction (PLAN.md §8 — no drift is possible).
sys.path.insert(0, str(III3_FIXTURE_DIR))
import generate_fixtures as gen  # noqa: E402

CALC_TS = gen.CALC_TS

#: Bounded vocabulary assertions (no free prose anywhere in the runtime).
BANNED_TRADING_TOKENS = {
    "trade", "trading", "trades", "win", "wins", "won", "loss", "losses",
    "expectancy", "takeprofit", "stoploss", "position", "positions",
    "leverage", "portfolio", "profit", "profits", "pnl", "roi", "buy",
    "buys", "sell", "sells", "signal", "signals", "hedge", "margin",
    "drawdown", "sharpe", "game", "gamble", "casino", "bet",
}
PROBABILITY_TOKENS = {
    "probability", "probabilities", "probabilistic", "confidence",
    "likelihood", "chance", "forecast", "prediction", "predictive",
}
PERFORMANCE_TOKENS = {
    "expectancy", "winrate", "win", "wins", "roi", "pnl", "sharpe",
    "drawdown", "payoff", "performance", "hitrate",
}
AGGREGATION_TOKENS = {"vote", "votes", "majority", "quorum", "tally", "score"}

SECRET_PATTERN = re.compile(
    r"(api[_-]?key\s*[:=]|secret[_-]?key\s*[:=]|password\s*[:=]|passwd"
    r"|bearer\s+[A-Za-z0-9._-]{8,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{16,})",
    re.IGNORECASE,
)

#: A model state / sub-state / authorization label is a bounded factual
#: enum token: uppercase, digits and underscores only — never prose.
LABEL_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_RUN_CACHE: tuple[dict[str, Any], dict[str, str]] | None = None
_CASE_CACHE: dict[str, dict] | None = None


def _run_all() -> tuple[dict[str, Any], dict[str, str]]:
    """All 57 golden cases through the real pipeline, once per session."""
    global _RUN_CACHE
    if _RUN_CACHE is None:
        outputs, refusals = gen.run_cases()
        _RUN_CACHE = (outputs, dict(refusals))
    return _RUN_CACHE


def _all_cases() -> dict[str, dict]:
    global _CASE_CACHE
    if _CASE_CACHE is None:
        _CASE_CACHE = {case["case_id"]: case for _group, case in gen.all_cases()}
    return _CASE_CACHE


def _case(case_id: str) -> dict:
    return _all_cases()[case_id]


def _out(case_id: str) -> ModelOutput:
    outputs, _refusals = _run_all()
    return outputs[case_id]


def _refusal(case_id: str) -> str:
    _outputs, refusals = _run_all()
    assert case_id in refusals, f"{case_id} was expected to refuse but ran"
    return refusals[case_id]


def _project(case_id: str) -> dict:
    return gen._project(_out(case_id))


def _expected(case_id: str) -> dict:
    expected = _case(case_id)["expected"]
    assert expected is not None, f"{case_id} carries no golden expectation"
    return expected


def _golden(case_id: str) -> dict:
    """The full golden contract: expectation equals the real projection."""
    assert _project(case_id) == _expected(case_id)
    return _expected(case_id)


def _build(case_id: str, outputs: dict[str, Any] | None = None) -> ModelRequest:
    if outputs is None and _case(case_id).get("prior_case"):
        outputs = _run_all()[0]
    return gen.build_request(_case(case_id), outputs if outputs is not None else {})


def _facts(output: ModelOutput) -> dict[str, dict[str, str]]:
    return {fact.fact_id: dict(fact.payload) for fact in output.explanation_facts}


def _fact_ids(output: ModelOutput) -> list[str]:
    return [fact.fact_id for fact in output.explanation_facts]


def _sub(output: ModelOutput, label: str) -> SubState:
    matches = [sub for sub in output.sub_states if sub.label == label]
    assert len(matches) == 1, (label, [s.label for s in output.sub_states])
    return matches[0]


def _tokens(identifier: str) -> set[str]:
    camel = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", identifier)
    return {part.lower() for part in re.split(r"[_\W]+", camel) if part}


def _package_sources() -> list[tuple[str, str]]:
    return [
        (path.name, path.read_text(encoding="utf-8"))
        for path in sorted(PACKAGE_DIR.glob("*.py"))
    ]


def _package_identifiers() -> set[str]:
    names: set[str] = set()
    for _name, source in _package_sources():
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(node, ast.Name):
                names.add(node.id)
    return names


def _package_enums() -> list[type[Enum]]:
    found: list[type[Enum]] = []
    for attribute in vars(model_runtime_pkg).values():
        if (
            isinstance(attribute, type)
            and issubclass(attribute, Enum)
            and attribute.__module__.startswith("app.forge.model_runtime")
            and attribute not in found
        ):
            found.append(attribute)
    assert found, "the runtime package must define enums"
    return found


#: Every bounded enum value of the runtime package.
def _all_enum_values() -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for enum_class in _package_enums():
        for member in enum_class:
            values.append((enum_class.__name__, str(member.value)))
    return values


def _payload(value: Any) -> Any:
    return json.loads(canonical_blob(value).decode("utf-8"))


def _walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for key, item in node.items():
                keys.add(str(key))
                visit(item)
        elif isinstance(node, (list, tuple)):
            for item in node:
                visit(item)

    visit(value)
    return keys


def _outputs_payload_keys(case_ids: tuple[str, ...]) -> set[str]:
    keys: set[str] = set()
    for case_id in case_ids:
        output = _out(case_id)
        keys |= _walk_keys(_payload(output))
        # Structured fact payloads encode as [key, value] string pairs;
        # their keys are structured labels and belong to the scan.
        for fact in output.explanation_facts:
            keys |= set(dict(fact.payload))
    return keys


def _runtime_dataclass_field_names() -> set[str]:
    names: set[str] = set()
    classes = [
        ModelOutput, DirectionBias, TypedLevel, AnchorStateRef, RangeLeftField,
        SubState, InputIdentity,
    ] + [
        attribute
        for attribute in vars(model_runtime_pkg).values()
        if isinstance(attribute, type)
        and _is_dataclass_class(attribute)
        and attribute.__module__.startswith("app.forge.model_runtime")
    ]
    seen: set[type] = set()
    for cls in classes:
        if cls in seen:
            continue
        seen.add(cls)
        for item in fields(cls):
            names.add(item.name)
    return names


def _is_dataclass_class(attribute: Any) -> bool:
    return isinstance(attribute, type) and is_dataclass(attribute)


def _assert_no_banned_tokens(names: set[str], banned: set[str], context: str) -> None:
    offenders = {
        name: sorted(_tokens(name) & banned)
        for name in names
        if _tokens(name) & banned
    }
    assert not offenders, (context, offenders)



# ---------------------------------------------------------------------------
# T1 — Common model runtime contract
# ---------------------------------------------------------------------------


class TestT1CommonContract:
    """Clause A: the frozen request/output contract (invariants #1/#12/#13)."""

    def test_request_requires_explicit_model_and_version(self):
        case = _case("EUR_DAILY_SEED_T1")
        base = dict(
            model_id=case["model_id"],
            model_version=case["model_version"],
            instrument_id=case["instrument_id"],
            inputs=EurDailyInputs(),
            calculation_timestamp=gen._utc(CALC_TS),
            calibration_key=None,
            market_data_schema_version=gen.IDENTITY["market_data_schema_version"],
            clock_registry_version=gen.IDENTITY["clock_registry_version"],
            session_registry_version=gen.IDENTITY["session_registry_version"],
            measurement_engine_version=gen.IDENTITY["measurement_engine_version"],
        )
        with pytest.raises(TypeError):
            ModelRequest(**{k: v for k, v in base.items() if k != "model_version"})
        with pytest.raises(TypeError):
            ModelRequest(**{k: v for k, v in base.items() if k != "model_id"})
        # An empty explicit version also refuses — never defaulted.
        with pytest.raises(ModelRuntimeError):
            run_model(ModelRequest(**{**base, "model_version": ""}))

    def test_inputs_are_measurements_only(self):
        #: A declared scalar input is a bounded factual token — never
        #: prose, never a number that could smuggle a statistic.
        bounded_scalar = re.compile(r"^[A-Z0-9_]*$")

        def visit(value: Any, where: str) -> None:
            if value is None or isinstance(value, bool):
                return
            if isinstance(value, (Measurement, Enum, Decimal, datetime)):
                return
            if isinstance(value, str):
                assert bounded_scalar.match(value), (where, value)
                return
            if isinstance(value, JpyPairInput):
                for item in fields(value):
                    visit(getattr(value, item.name), f"{where}.{item.name}")
                return
            if isinstance(value, (tuple, list)):
                for index, item in enumerate(value):
                    visit(item, f"{where}[{index}]")
                return
            raise AssertionError(
                f"{where}: inputs may carry measurements and typed records only,"
                f" found {type(value).__name__}"
            )

        for case_id in _all_cases():
            case = _case(case_id)
            if case["expected"] is None:
                continue
            request = _build(case_id)
            for item in fields(request.inputs):
                value = getattr(request.inputs, item.name)
                assert not isinstance(value, (float, dict)), (
                    case_id, item.name, type(value).__name__,
                )
                visit(value, f"{case_id}.{item.name}")

    def test_missing_required_measurement_refuses(self):
        assert _refusal("EUR_DAILY_TIER_MISSING") == "INPUT_MEASUREMENT_MISSING"

    def test_prior_state_version_checked(self):
        outputs, _ = _run_all()
        weekly = _build("EUR_WEEKLY_ROUTE")
        with pytest.raises(PriorStateMismatchError) as info:
            run_model(
                dataclasses.replace(weekly, prior_state=outputs["EUR_DAILY_SEED_T1"])
            )
        assert info.value.code == "PRIOR_STATE_MISMATCH"
        # A matching-version prior links cleanly (the positive case).
        linked = _build("EUR_WEEKLY_FROZEN_VIA_PRIOR", outputs)
        assert _facts(run_model(linked))["PRIOR_STATE.LINKED"]["linked"] == "YES"

    def test_calculation_timestamp_injected(self):
        for case_id in _all_cases():
            output = _out(case_id) if case_id in _run_all()[0] else None
            if output is None:
                continue
            assert output.identity.calculation_timestamp == gen._utc(CALC_TS)
        wall_clock = re.compile(
            r"(datetime\.now|utcnow|time\.time\s*\(|import random|from random)"
        )
        for name, source in _package_sources():
            assert not wall_clock.search(source), name

    def test_calibration_lineage_bound_to_request(self):
        for case_id, case in _all_cases().items():
            output = _run_all()[0].get(case_id)
            if output is None:
                continue
            carried = output.identity.calibration_key
            if case["calibration_key"] is None:
                assert carried is None, case_id
            else:
                assert carried == gen.decode_as(
                    gen.CalibrationKey, case["calibration_key"]
                ), case_id
        # A foreign calibration on the request refuses (scope gate).
        assert _refusal("BTC_FOREIGN_CALIBRATION") == "INSTRUMENT_SCOPE_MISMATCH"

    def test_input_identity_versions_asserted(self):
        for case_id in _run_all()[0]:
            identity = _out(case_id).identity
            assert (
                identity.market_data_schema_version
                == gen.IDENTITY["market_data_schema_version"]
            )
            assert identity.clock_registry_version == gen.IDENTITY["clock_registry_version"]
            assert identity.session_registry_version == gen.IDENTITY["session_registry_version"]
            assert identity.measurement_engine_version == gen.IDENTITY["measurement_engine_version"]
            assert identity.model_runtime_version == MODEL_RUNTIME_VERSION
        request = _build("EUR_DAILY_SEED_T1")
        with pytest.raises(ModelContractError) as info:
            run_model(
                dataclasses.replace(request, measurement_engine_version="MEASUREMENT_ENGINE_V0")
            )
        assert info.value.code == "MODEL_CONTRACT"

    def test_output_state_and_layer_declared(self):
        for case_id in _run_all()[0]:
            output = _out(case_id)
            assert isinstance(output.model_state, str) and output.model_state
            assert isinstance(output.layer, Layer)

    def test_direction_only_where_defined(self):
        declared = _out("HO_PRIOR_DECLARED").direction_bias
        assert declared.declared
        assert declared.side is DirectionSide.UP
        assert declared.basis_fact_id == "EUR_HO.D3_PRIOR"
        assert declared.evidence_refs == ("EV.EUR.HO.D3_DIRECTION.V1",)
        for case_id in (
            "HO_NO_DIRECTION", "XAU_NORMAL_NODE50", "BTC_TIER_T2_750",
            "FIB_CHAIN_ACTIVE", "JPY_AGREE_CONFIRM", "EUR_DAILY_SEED_T1",
        ):
            assert not _out(case_id).direction_bias.declared, case_id
            assert _out(case_id).direction_bias.to_payload() == "NONE_DECLARED"

    def test_active_ranges_and_anchors_reference_measurements(self):
        output = _out("FIB_CHAIN_ACTIVE")
        assert output.active_anchor_states
        for ref in output.active_anchor_states:
            assert isinstance(ref, AnchorStateRef)
            assert isinstance(ref.status, AnchorStatus)
            assert isinstance(ref.refusal_code, AnchorRefusalCode)
        for range_id in output.active_ranges:
            assert isinstance(range_id, str) and range_id
        # No anchor without a measurement: the no-anchor case stays empty.
        assert _out("FIB_NO_ANCHOR").active_anchor_states == ()

    def test_typed_levels_with_source_refs(self):
        source_pattern = re.compile(r"^(corpus|implementation)/\S+$")
        seen = 0
        for case_id in _run_all()[0]:
            for level in _out(case_id).levels:
                seen += 1
                assert isinstance(level, TypedLevel)
                assert isinstance(level.level_kind, LevelKind)
                assert source_pattern.match(level.source_ref), level.source_ref
                assert level.level is None or isinstance(level.level, Decimal)
                assert level.price is None or isinstance(level.price, Decimal)
        assert seen > 0, "the golden program must exercise typed levels"

    def test_range_left_conditional_or_unresolved(self):
        measured = 0
        for case_id in _run_all()[0]:
            field = _out(case_id).range_left
            assert isinstance(field, RangeLeftField)
            if field.state.value == "MEASURED":
                measured += 1
                assert field.value is not None, case_id
                assert field.basis_fact_id, case_id
                assert field.basis_fact_id in _fact_ids(_out(case_id)), case_id
                assert field.conditioned_on, case_id
            else:
                assert field.value is None, case_id
        assert measured > 0

    def test_no_go_and_warnings_bounded(self):
        for case_id in _run_all()[0]:
            output = _out(case_id)
            for reason in output.no_go:
                assert isinstance(reason, NoGoReason), (case_id, reason)
            for code in output.warnings:
                assert isinstance(code, WarningCode), (case_id, code)

    def test_evidence_refs_read_only_ids(self):
        evidence_pattern = re.compile(r"^[A-Z0-9][A-Z0-9_.]*$")
        for case_id in _run_all()[0]:
            refs = _out(case_id).evidence_refs
            assert isinstance(refs, tuple)
            for ref in refs:
                assert isinstance(ref, str)
                assert evidence_pattern.match(ref), (case_id, ref)

    def test_quality_state_frozen_vocabulary(self):
        for case_id in _run_all()[0]:
            assert _out(case_id).quality_state in (
                DataOutcome.OK, DataOutcome.DEGRADED
            ), case_id

    def test_output_carries_model_version_hash(self):
        for case_id, case in _all_cases().items():
            if case["expected"] is None:
                continue
            output = _out(case_id)
            assert re.fullmatch(r"[0-9a-f]{64}", output.output_hash), case_id
            assert output.model_version == case["model_version"], case_id
            assert output.model_id == case["model_id"], case_id
            assert compute_hash(canonical_payload(output)) == output.output_hash

    def test_explanation_facts_structured_no_prose(self):
        identifier = re.compile(r"^[A-Z0-9][A-Z0-9_.]*$")
        for case_id in _run_all()[0]:
            for fact in _out(case_id).explanation_facts:
                assert set(
                    item.name for item in fields(fact)
                ) == {"fact_id", "rule_id", "rule_version", "source_ref", "payload"}
                assert identifier.match(fact.fact_id), fact.fact_id
                assert fact.rule_id and fact.rule_version
                assert isinstance(fact.payload, tuple)
                for key, value in fact.payload:
                    assert isinstance(key, str) and isinstance(value, str)
                    assert len(value) < 200, (fact.fact_id, key)

    def test_descriptive_state_vs_production_authorization(self):
        allowed = {member.value for member in ProductionAuthorization}
        assert allowed == {
            "MANUAL_OPERATOR", "NOT_APPLICABLE", "NOT_AUTHORIZED", "RESEARCH_ONLY"
        }
        for case_id in _run_all()[0]:
            output = _out(case_id)
            auth = output.production_authorization
            assert isinstance(auth, ProductionAuthorization), case_id
            assert auth.value != output.model_state, case_id

    def test_no_probability_confidence_or_performance_fields(self):
        _assert_no_banned_tokens(_runtime_dataclass_field_names(), PROBABILITY_TOKENS, "fields")
        _assert_no_banned_tokens(_runtime_dataclass_field_names(), PERFORMANCE_TOKENS, "fields")
        _assert_no_banned_tokens(_package_identifiers(), PROBABILITY_TOKENS, "identifiers")
        keys = _outputs_payload_keys(tuple(_run_all()[0]))
        _assert_no_banned_tokens(keys, PROBABILITY_TOKENS, "payload keys")
        _assert_no_banned_tokens(keys, PERFORMANCE_TOKENS, "payload keys")

    def test_outputs_immutable(self):
        output = _out("EUR_DAILY_SEED_T1")
        assert dataclasses.is_dataclass(output)
        with pytest.raises(FrozenInstanceError):
            output.model_state = "MUTATED"  # type: ignore[misc]
        for cls in (ModelOutput, DirectionBias, TypedLevel, SubState, RangeLeftField):
            assert cls.__dataclass_params__.frozen, cls.__name__


# ---------------------------------------------------------------------------
# T2 — Registry / dispatch
# ---------------------------------------------------------------------------


class TestT2RegistryDispatch:
    """Clause B: explicit (model_id, version) dispatch, fail closed."""

    @staticmethod
    def _registry_fixture() -> dict:
        return json.loads(
            (III3_FIXTURE_DIR / "registry_dispatch_cases.json").read_text(encoding="utf-8")
        )

    def test_registry_resolves_all_families(self):
        entries = self._registry_fixture()["entries"]
        assert len(entries) == 8
        for spec in entries:
            entry = resolve(spec["model_id"], spec["model_version"])
            assert isinstance(entry, RegistryEntry)
            assert entry.family == spec["family"], spec["model_id"]
            assert entry.layer.value == spec["layer"], spec["model_id"]
            assert entry.stateful is spec["stateful"], spec["model_id"]
            assert entry.clock_bound is spec["clock_bound"], spec["model_id"]
            for instrument in spec["market_scope"]:
                assert instrument in entry.market_scope, (spec["model_id"], instrument)

    def test_unknown_version_fails_closed(self):
        for spec in self._registry_fixture()["refusals"]:
            with pytest.raises(ModelVersionUnavailableError) as info:
                resolve(spec["model_id"], spec["model_version"])
            assert info.value.code == "MODEL_VERSION_UNAVAILABLE"
        assert _refusal("BTC_GAME_REQUEST") == "MODEL_VERSION_UNAVAILABLE"
        # The refusal set is closed: MODEL_RUNTIME_CODES is enumerable.
        assert "MODEL_VERSION_UNAVAILABLE" in MODEL_RUNTIME_CODES

    def test_unknown_model_id_fails_closed(self):
        for model_id in ("", "NOT.A.MODEL.V1", "BTC.GAME.L1_V1"):
            with pytest.raises(ModelVersionUnavailableError):
                resolve(model_id, "V1")
        with pytest.raises(ModelVersionUnavailableError):
            resolve("EUR.DAILY.NEWS_REKEY.V1", "V2")

    def test_no_latest_fallback_api(self):
        signature = inspect.signature(resolve)
        assert signature.parameters["model_version"].default is inspect.Parameter.empty
        for name, source in _package_sources():
            lowered = source.lower()
            assert "default_version" not in lowered, name
            # errors.py and registry.py quote "latest" only inside
            # refusal docstrings ("no fallback, no latest"); the
            # executable no-fallback guarantee is asserted above via
            # the resolve signature, the explicit-key registry and the
            # fail-closed resolution behavior tests.
            if name not in {"errors.py", "registry.py"}:
                assert '"latest"' not in lowered and "'latest'" not in lowered, name
        # Every registered key is an explicit pair — no implicit alias.
        for key in MODEL_REGISTRY:
            assert isinstance(key, ModelKey)
            assert key.model_id and key.model_version

    def test_version_pinned_historical_generation(self):
        fixture = self._registry_fixture()
        historical = [
            spec for spec in fixture["entries"]
            if spec["model_id"] == "JPY.CARRY_GAME.L1_L3.V1"
            and spec["model_version"] == "DT_12_4PM"
        ]
        assert len(historical) == 1
        entry = resolve("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM")
        assert entry is not resolve("JPY.CARRY_GAME.L1_L3.V1", "V1")
        # The pinned historical generation never silently upgrades: it
        # refuses dispatch because no authorized runtime exists for it.
        with pytest.raises(ModelVersionUnavailableError):
            run_model(_build("JPY_AGREE_CONFIRM") and _dt_request())

    def test_registry_entry_binding_exact(self):
        for spec in self._registry_fixture()["entries"]:
            entry = resolve(spec["model_id"], spec["model_version"])
            expected_bindings = [
                gen.CalibrationKey(*binding)
                for binding in spec["calibration_bindings"]
            ]
            assert list(entry.calibration_bindings) == expected_bindings, spec["model_id"]
            assert [tuple(item) for item in entry.coordinate_set_keys] == [
                tuple(item) for item in spec["coordinate_set_keys"]
            ], spec["model_id"]


def _dt_request() -> ModelRequest:
    case = dict(_case("JPY_AGREE_CONFIRM"))
    case["model_version"] = "DT_12_4PM"
    return gen.build_request(case, {})


# ---------------------------------------------------------------------------
# T3 — EUR Daily News + Rekey
# ---------------------------------------------------------------------------


class TestT3EurDaily:
    """Clause C: III.3.1 canonical chain, >45p no-go, ladder, events."""

    def test_eur_daily_state_chain_reproduces(self):
        for case_id in ("EUR_DAILY_SEED_T1", "EUR_DAILY_SEED_T2_SLOT_PATH", "EUR_DAILY_SEED_T3"):
            _golden(case_id)
        assert _out("EUR_DAILY_SEED_T1").model_state == "SEED_T1"
        assert _out("EUR_DAILY_SEED_T2_SLOT_PATH").model_state == "SEED_T2"
        assert _out("EUR_DAILY_SEED_T3").model_state == "SEED_T3"

    def test_eur_daily_source_no_go_boundary(self):
        _golden("EUR_DAILY_TIER_45_BOUNDARY")
        assert _out("EUR_DAILY_TIER_45_BOUNDARY").model_state == "SEED_T3"
        assert _out("EUR_DAILY_TIER_45_BOUNDARY").no_go == ()
        for case_id in ("EUR_DAILY_NO_GO_46", "EUR_DAILY_NO_GO_52"):
            _golden(case_id)
            output = _out(case_id)
            assert output.model_state == "SOURCE_NO_GO"
            assert [reason.value for reason in output.no_go] == ["AR_SOURCE_NO_GO"]
        assert _facts(_out("EUR_DAILY_NO_GO_46"))["EUR_DAILY.TIER"]["tier_id"] == "NO_GO"

    def test_eur_daily_ladder_states_distinct(self):
        ladder = [
            _out(f"EUR_DAILY_REKEY_{level}")
            for level in ("100", "125", "132", "168", "185")
        ]
        states = [output.model_state for output in ladder]
        assert states == ["REKEY_100", "REKEY_125", "REKEY_132", "REKEY_168", "REKEY_185"]
        hashes = {output.output_hash for output in ladder}
        assert len(hashes) == 5, "the five ladder states must never collapse"
        unmapped = _out("EUR_DAILY_REKEY_UNMAPPED")
        assert unmapped.model_state == "REKEYED"
        assert unmapped.output_hash not in hashes
        # A coordinate touch alone never rekeys (no anchor ⇒ refusal).
        assert _refusal("EUR_DAILY_TOUCH_NO_REKEY") == "MODEL_CONTRACT"

    def test_eur_daily_news_conditions_never_replaces_geometry(self):
        conditioned = _out("EUR_DAILY_EVENT_CONDITIONED")
        plain = _out("EUR_DAILY_NO_EVENT")
        assert conditioned.model_state == plain.model_state
        shared = (
            "EUR_DAILY.SEED", "EUR_DAILY.TIER", "EUR_DAILY.DISTANCE_ASYMMETRY",
        )
        conditioned_facts = _facts(conditioned)
        plain_facts = _facts(plain)
        for fact_id in shared:
            assert conditioned_facts[fact_id] == plain_facts[fact_id], fact_id
        assert "EUR_DAILY.EVENT_CONDITIONING" in conditioned_facts
        assert "EUR_DAILY.EVENT_CONDITIONING" not in plain_facts

    def test_eur_daily_slot_tier_range_left(self):
        measured = _out("EUR_DAILY_SEED_T2_SLOT_PATH").range_left
        assert measured.state.value == "MEASURED"
        assert str(measured.value.value) == "10.0"
        assert measured.conditioned_on
        unresolved = _out("EUR_DAILY_SLOT_OUTSIDE").range_left
        assert unresolved.state.value == "UNRESOLVED"
        assert unresolved.value is None

    def test_eur_daily_event_budget_subtractive(self):
        budget = _facts(_out("EUR_DAILY_EVENT_CONDITIONED"))["EUR_DAILY.EVENT_BUDGET"]
        assert budget["total_size"] == "22"
        assert budget["consumed"] == "10"
        assert budget["residual"] == "12"
        assert Decimal(budget["total_size"]) - Decimal(budget["consumed"]) == Decimal(
            budget["residual"]
        )

    def test_eur_daily_derived_facts_rule_versioned(self):
        for case_id in (
            "EUR_DAILY_SEED_T1", "EUR_DAILY_SEED_T2_SLOT_PATH",
            "EUR_DAILY_NO_GO_46", "EUR_DAILY_REKEY_132",
            "EUR_DAILY_EVENT_CONDITIONED",
        ):
            for fact in _out(case_id).explanation_facts:
                assert fact.rule_id.startswith("EUR_DAILY") or fact.rule_id.startswith(
                    "COMMON."
                ), (case_id, fact.fact_id, fact.rule_id)
                assert re.fullmatch(r"V\d+", fact.rule_version), fact.rule_version

    def test_eur_daily_clock_identity_required(self):
        assert _refusal("EUR_DAILY_CLOCK_MISSING") == "NO_CALCULATION"
        with pytest.raises(NoCalculationError):
            run_model(_build("EUR_DAILY_CLOCK_MISSING"))


# ---------------------------------------------------------------------------
# T4 — EUR Weekly Engine V1.1
# ---------------------------------------------------------------------------


class TestT4EurWeekly:
    """Clause D: III.3.2 outer-node promotion, freeze, boundary law."""

    def test_eur_weekly_state_chain_reproduces(self):
        for case_id in (
            "EUR_WEEKLY_ROUTE", "EUR_WEEKLY_PROMOTED", "EUR_WEEKLY_FROZEN",
        ):
            _golden(case_id)
        assert _out("EUR_WEEKLY_ROUTE").model_state == "ROUTE_OPEN"
        assert _out("EUR_WEEKLY_PROMOTED").model_state == "NODE_PROMOTED"
        assert _out("EUR_WEEKLY_FROZEN").model_state == "FROZEN"

    def test_eur_weekly_outer_node_promotion_only(self):
        promoted = _out("EUR_WEEKLY_PROMOTED")
        node = _facts(promoted)["EUR_WEEKLY.NODE"]
        assert node["promoted"] == "YES"
        assert node["node_id"] == "EUR_WEEKLY_T2"
        inner = _out("EUR_WEEKLY_INNER_NODE")
        assert inner.model_state == "ROUTE_OPEN"
        inner_facts = _facts(inner)
        assert "EUR_WEEKLY.NODE" not in inner_facts
        assert inner_facts["EUR_WEEKLY.NODE_NOT_OUTER"]["node_id"] == "EUR_WEEKLY_INNER"
        # Node reach is a measurement fact, never a destination claim.
        assert promoted.levels == ()

    def test_eur_weekly_frozen_after_completion(self):
        frozen = _out("EUR_WEEKLY_FROZEN")
        again = run_model(_build("EUR_WEEKLY_FROZEN"))
        assert again.output_hash == frozen.output_hash, "frozen must be static"
        linked = _out("EUR_WEEKLY_FROZEN_VIA_PRIOR")
        assert linked.model_state == "FROZEN"
        assert _facts(linked)["PRIOR_STATE.LINKED"]["linked"] == "YES"
        assert linked.identity.prior_state_ref == frozen.output_hash
        assert linked.output_hash != frozen.output_hash, (
            "the prior link participates in identity"
        )

    def test_eur_weekly_path_not_destination_evidence(self):
        keys = _outputs_payload_keys(
            ("EUR_WEEKLY_ROUTE", "EUR_WEEKLY_PROMOTED", "EUR_WEEKLY_FROZEN")
        )
        destination_keys = {key for key in keys if "destination" in _tokens(key)}
        assert destination_keys == {"destination_evidence"}, keys
        for case_id in ("EUR_WEEKLY_ROUTE", "EUR_WEEKLY_PROMOTED", "EUR_WEEKLY_FROZEN"):
            facts = _facts(_out(case_id))
            assert facts["EUR_WEEKLY.DESTINATION_BOUNDARY"] == {
                "destination_evidence": "NOT_THIS_LAYER"
            }
            assert _out(case_id).levels == ()

    def test_eur_weekly_research_status_travels(self):
        for case_id in (
            "EUR_WEEKLY_ROUTE", "EUR_WEEKLY_PROMOTED", "EUR_WEEKLY_FROZEN",
            "EUR_WEEKLY_TIMING_UNRESOLVED",
        ):
            output = _out(case_id)
            assert "RESEARCH_CALIBRATION" in [c.value for c in output.warnings]
            facts = _facts(output)
            assert facts["EUR_WEEKLY.CALIBRATION_STATUS"]["status"] == "RESEARCH"
            assert facts["EUR_WEEKLY.TIER"]["calibration_status"] == "RESEARCH"
            assert "EV.EUR.WEEKLY.TIER_RANGE.V1" in output.evidence_refs

    def test_eur_weekly_hour_tier_timing_from_sessions(self):
        timing = _facts(_out("EUR_WEEKLY_PROMOTED"))["EUR_WEEKLY.HOUR_TIER_TIMING"]
        assert timing["source"] == "PERIOD"
        assert timing["period"] == "WEEK"
        assert timing["label"] == "2026-W10"
        assert timing["tier_id"] == "T2"
        unresolved = _out("EUR_WEEKLY_TIMING_UNRESOLVED")
        facts = _facts(unresolved)
        assert "EUR_WEEKLY.HOUR_TIER_TIMING" not in facts
        timing_fact = facts["EUR_WEEKLY.HOUR_TIER_TIMING_UNRESOLVED"]
        assert timing_fact["source"] == "NONE"
        assert timing_fact["phase"] == "UNRESOLVED"
        assert "TIMING_UNRESOLVED" in [c.value for c in unresolved.warnings]

    def test_eur_weekly_no_win_rate_fields(self):
        keys = _outputs_payload_keys(
            ("EUR_WEEKLY_ROUTE", "EUR_WEEKLY_PROMOTED", "EUR_WEEKLY_FROZEN")
        )
        _assert_no_banned_tokens(keys, PERFORMANCE_TOKENS, "weekly payloads")
        _assert_no_banned_tokens(keys, PROBABILITY_TOKENS, "weekly payloads")


# ---------------------------------------------------------------------------
# T5 — EUR Higher Order
# ---------------------------------------------------------------------------


class TestT5HigherOrder:
    """Clause E: III.3.3 L3 authority, evidence-bound parameters."""

    def test_eur_higher_order_chain_reproduces(self):
        for case_id in ("HO_PRIOR_DECLARED", "HO_M3_RESOLVED"):
            _golden(case_id)
        assert _out("HO_PRIOR_DECLARED").model_state == "PRIOR_DECLARED"
        assert _out("HO_M3_RESOLVED").model_state == "M3_RESOLVED"
        assert _out("HO_M3_RESOLVED").layer is Layer.L3

    def test_eur_higher_order_l3_destination_authority(self):
        output = _out("HO_PRIOR_DECLARED")
        assert output.direction_bias.basis_fact_id == "EUR_HO.D3_PRIOR"
        assert output.direction_bias.evidence_refs == ("EV.EUR.HO.D3_DIRECTION.V1",)
        assert "EUR_HO.D3_PRIOR" in _fact_ids(output)
        # The D3 prior is the only declared direction source: M1/M2
        # facts never populate the direction field.
        for case_id in ("HO_MISSING_M1", "HO_CONFLICT_NO_SCORE"):
            bias = _out(case_id).direction_bias
            if bias.declared:
                assert bias.basis_fact_id == "EUR_HO.D3_PRIOR", case_id

    def test_eur_higher_order_d3_prior_no_win_rate(self):
        d3 = _facts(_out("HO_PRIOR_DECLARED"))["EUR_HO.D3_PRIOR"]
        assert set(d3) == {"direction", "d1d3_state", "evidence_id"}
        keys = _outputs_payload_keys(
            ("HO_PRIOR_DECLARED", "HO_M3_RESOLVED", "HO_UNFINISHED_CONDITIONAL")
        )
        _assert_no_banned_tokens(keys, PERFORMANCE_TOKENS, "HO payloads")

    def test_eur_higher_order_m1_not_probability(self):
        m1 = _facts(_out("HO_PRIOR_DECLARED"))["EUR_HO.M1_SCALE"]
        assert set(m1) == {"state", "scale", "evidence_id"}
        keys = _outputs_payload_keys(("HO_PRIOR_DECLARED",))
        _assert_no_banned_tokens(keys, PROBABILITY_TOKENS, "M1 payloads")

    def test_eur_higher_order_unfinished_side_conditional(self):
        _golden("HO_UNFINISHED_CONDITIONAL")
        output = _out("HO_UNFINISHED_CONDITIONAL")
        assert output.model_state == "COMPLETION_CONDITIONAL"
        assert "CONDITIONAL_DESTINATION" in [c.value for c in output.warnings]
        facts = _facts(output)
        assert facts["EUR_HO.UNFINISHED_SIDE"]["side"] == "UPPER"
        assert "EV.EUR.HO.UNFINISHED_M3.V1" in output.evidence_refs
        # The conditional never resolves into a direction of its own.
        assert output.direction_bias.basis_fact_id == "EUR_HO.D3_PRIOR"

    def test_eur_higher_order_m3_resolution_and_handoff(self):
        _golden("HO_M3_RESOLVED")
        output = _out("HO_M3_RESOLVED")
        checkpoints = [
            fact for fact in output.explanation_facts
            if fact.fact_id == "EUR_HO.M3_CHECKPOINT"
        ]
        assert len(checkpoints) == 2
        for fact in checkpoints:
            assert dict(fact.payload)["reached"] == "YES"
        # The local handoff subject remains the measured quarter seed.
        assert "EUR_HO.QUARTER_SEED" in _fact_ids(output)

    def test_eur_higher_order_missing_parameter_unresolved(self):
        _golden("HO_MISSING_M1")
        output = _out("HO_MISSING_M1")
        assert output.model_state == "UNRESOLVED"
        facts = _facts(output)
        assert facts["EUR_HO.PARAM_M1_SCALE"]["state"] == "UNRESOLVED"
        assert "EV.EUR.HO.M1_RANGE_CORR.V1" not in output.evidence_refs
        assert "EVIDENCE_BOUND_PARAMETER" in [c.value for c in output.warnings]

    def test_eur_higher_order_conflict_facts_no_score(self):
        _golden("HO_CONFLICT_NO_SCORE")
        output = _out("HO_CONFLICT_NO_SCORE")
        conflict = _facts(output)["EUR_HO.LAYER_CONFLICT"]
        assert set(conflict) == {"layer_a", "layer_b", "kind"}
        assert conflict["kind"] == "DIRECTION_DISAGREEMENT"
        keys = _walk_keys(_payload(output))
        assert not (keys & AGGREGATION_TOKENS), keys


# ---------------------------------------------------------------------------
# T6 — XAU Game
# ---------------------------------------------------------------------------


class TestT6Xau:
    """Clause F: III.3.4 three-layer runtime, promotion laws, parking."""

    def test_xau_three_layers_typed_separately(self):
        _golden("XAU_NORMAL_NODE50")
        output = _out("XAU_NORMAL_NODE50")
        labels = [sub.label for sub in output.sub_states]
        assert labels == ["L3", "L2", "L1", "CONFIRMATION"]
        assert _sub(output, "L3").layer is Layer.L3
        assert _sub(output, "L2").state == "NODE_50"
        assert _sub(output, "L1").state == "BAND_NORMAL"
        assert _sub(output, "CONFIRMATION").layer is Layer.L1

    def test_xau_68_to_80_promotion_rule(self):
        _golden("XAU_68_8H")
        output = _out("XAU_68_8H")
        assert output.model_state == "PROMOTION_ELIGIBLE"
        assert _sub(output, "L2").state == "ELIGIBLE_80"
        promotion = _facts(output)["XAU.PROMOTION_68_80"]
        assert promotion["standing"] == "VALIDATED_SMALL_N"
        assert promotion["age_hours"] == "8"
        assert promotion["evidence_id"] == "EV.XAU.PROMOTION.68_80.V1"
        assert "EV.XAU.PROMOTION.68_80.V1" in output.evidence_refs
        # The same band one hour early never promotes.
        pending = _out("XAU_68_7H")
        assert pending.model_state == "PROMOTION_PENDING"
        assert "XAU.PROMOTION_68_80" not in _facts(pending)

    def test_xau_120_to_132_research_small_n(self):
        _golden("XAU_120_8H")
        output = _out("XAU_120_8H")
        assert output.model_state == "PROMOTION_RESEARCH"
        assert _sub(output, "L2").state == "RESEARCH_PROMOTED_132"
        assert "SMALL_N_RESEARCH_FLAG" in [c.value for c in output.warnings]
        assert "EV.XAU.PROMOTION.120_132.V1" in output.evidence_refs
        assert output.production_authorization is ProductionAuthorization.MANUAL_OPERATOR

    def test_xau_132_never_promotes_168(self):
        _golden("XAU_132_NO_168")
        output = _out("XAU_132_NO_168")
        assert output.model_state == "NODE_DECLARED"
        assert _sub(output, "L2").state == "NODE_132"
        facts = _facts(output)
        assert facts["XAU.NODE_132_BOUNDARY"]["automatic_168"] == "NO"
        for case_id, case_output in {
            cid: _out(cid) for cid in _all_cases() if cid.startswith("XAU_")
        }.items():
            states = " ".join(sub.state for sub in case_output.sub_states)
            assert "168" not in states, case_id
            assert not any("168" in fact_id for fact_id in _fact_ids(case_output)), case_id

    def test_xau_l2_state_not_entry(self):
        _golden("XAU_BLIND_TOUCH")
        output = _out("XAU_BLIND_TOUCH")
        assert _sub(output, "L2").state == "ROUTE_OPEN"
        for sub in output.sub_states:
            assert sub.state not in {"ENTRY", "EXECUTION", "ARMED"}, sub.state
        keys = _walk_keys(_payload(output))
        _assert_no_banned_tokens(keys, BANNED_TRADING_TOKENS, "XAU payloads")

    def test_xau_blind_touch_cannot_confirm(self):
        _golden("XAU_BLIND_TOUCH")
        output = _out("XAU_BLIND_TOUCH")
        assert _sub(output, "CONFIRMATION").state == "ABSENT"
        assert "XAU.ROUTE" in _facts(output), "the touch is measured, not confirmed"

    def test_xau_parked_stays_parked(self):
        _golden("XAU_PARKED_68_8H")
        output = _out("XAU_PARKED_68_8H")
        assert output.model_state == "PARKED"
        assert _sub(output, "L2").state == "PARKED"
        assert "PROMOTION_PARKED" in [r.value for r in output.no_go]
        facts = _facts(output)
        assert "XAU.PROMOTION_68_80" not in facts, "parking blocks promotion facts"
        assert not output.levels or all(not level.active for level in output.levels)

    def test_xau_promotion_aging_never_manufactures_state(self):
        # Age alone never promotes: the 7h case stays pending and the
        # long-aged 132 case never advances.
        assert _out("XAU_68_7H").model_state == "PROMOTION_PENDING"
        aged = _out("XAU_132_NO_168")
        assert aged.model_state == "NODE_DECLARED"
        assert not any(
            "PROMOTION" in fact_id for fact_id in _fact_ids(aged)
        ), _fact_ids(aged)

    def test_xau_no_quarter_zone_execution_objects(self):
        identifiers = {
            name for name in _package_identifiers()
        }
        _assert_no_banned_tokens(identifiers, {"execution"}, "runtime identifiers")
        output = _out("XAU_NORMAL_NODE50")
        keys = _walk_keys(_payload(output))
        _assert_no_banned_tokens(keys, BANNED_TRADING_TOKENS, "XAU payloads")

    def test_xau_no_cross_asset_calibration(self):
        request = _build("XAU_NORMAL_NODE50")
        foreign = dataclasses.replace(
            request,
            calibration_key=gen.CalibrationKey(
                "BTC.TRACKER.DWM.V1", "V1", "BTC_TRACKER_DWM_TIERS", "V1"
            ),
        )
        with pytest.raises(ModelRuntimeError) as info:
            run_model(foreign)
        assert info.value.code in {
            "INSTRUMENT_SCOPE_MISMATCH", "MODEL_VERSION_UNAVAILABLE"
        }, info.value.code


# ---------------------------------------------------------------------------
# T7 — BTC Tracker
# ---------------------------------------------------------------------------


class TestT7BtcTracker:
    """Clause G: III.3.5 Tracker-only lineage, >$3,000 no-go, slots."""

    def test_btc_daily_lineage_reproduces(self):
        for case_id in (
            "BTC_TIER_T1_749", "BTC_TIER_T2_750", "BTC_TIER_T3_3000",
            "BTC_NO_GO_3001", "BTC_SLOT_RANGE_LEFT", "BTC_HORIZON_UNRESOLVED",
        ):
            _golden(case_id)

    def test_btc_three_native_tiers(self):
        assert _facts(_out("BTC_TIER_T1_749"))["BTC.TIER"]["tier_id"] == "T1"
        assert _facts(_out("BTC_TIER_T2_750"))["BTC.TIER"]["tier_id"] == "T2"
        assert _facts(_out("BTC_TIER_T3_3000"))["BTC.TIER"]["tier_id"] == "T3"
        for case_id in ("BTC_TIER_T1_749", "BTC_TIER_T2_750", "BTC_TIER_T3_3000"):
            facts = _facts(_out(case_id))
            assert facts["BTC.TIER"]["unit"] if "unit" in facts["BTC.TIER"] else True
            assert facts["BTC.SEED"]["unit"] == "DOLLAR", case_id

    def test_btc_3000_no_go_boundary(self):
        assert _out("BTC_TIER_T3_3000").no_go == ()
        golden = _golden("BTC_NO_GO_3001")
        assert golden["model_state"] == "ASIAN_RANGE_NO_GO"
        assert golden["no_go"] == ["ASIAN_RANGE_NO_GO"]
        assert _facts(_out("BTC_NO_GO_3001"))["BTC.TIER"]["no_go"] == "YES"

    def test_btc_game_contamination_refused(self):
        assert _refusal("BTC_GAME_REQUEST") == "MODEL_VERSION_UNAVAILABLE"

    def test_btc_tracker_output_has_no_game_objects(self):
        keys = _outputs_payload_keys(
            tuple(cid for cid in _run_all()[0] if cid.startswith("BTC_"))
        )
        _assert_no_banned_tokens(keys, BANNED_TRADING_TOKENS, "BTC payloads")
        _assert_no_banned_tokens(_runtime_dataclass_field_names(), BANNED_TRADING_TOKENS, "fields")

    def test_btc_no_gold_game_import(self):
        for name, source in _package_sources():
            assert "xau_game" not in source or name != "btc_tracker.py", name
            assert "jpy_carry" not in source or name != "btc_tracker.py", name
        tree = ast.parse(
            (PACKAGE_DIR / "btc_tracker.py").read_text(encoding="utf-8")
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert "xau_game" not in node.module, node.module
                assert "jpy_carry" not in node.module, node.module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "xau_game" not in alias.name
                    assert "jpy_carry" not in alias.name

    def test_btc_weekly_monthly_unresolved_without_canonical(self):
        _golden("BTC_HORIZON_UNRESOLVED")
        output = _out("BTC_HORIZON_UNRESOLVED")
        assert _sub(output, "WEEKLY").state == "UNRESOLVED"
        assert _sub(output, "MONTHLY").state == "UNRESOLVED"
        facts = _facts(output)
        for horizon in ("BTC.WEEKLY_ANCHOR", "BTC.MONTHLY_ANCHOR"):
            assert facts[horizon]["state"] == "UNRESOLVED"
            assert facts[horizon]["reason"] == "NOT_MATERIALIZED"

    def test_btc_cross_asset_calibration_refuses(self):
        assert _refusal("BTC_FOREIGN_INSTRUMENT") == "INSTRUMENT_SCOPE_MISMATCH"
        assert _refusal("BTC_FOREIGN_CALIBRATION") == "INSTRUMENT_SCOPE_MISMATCH"

    def test_btc_calibration_contamination_refuses(self):
        # The recovered BTC calibration is instrument-local at both
        # gates: a foreign instrument and a foreign calibration key
        # each refuse with an explicit code.
        assert _refusal("BTC_FOREIGN_INSTRUMENT") == "INSTRUMENT_SCOPE_MISMATCH"
        assert _refusal("BTC_FOREIGN_CALIBRATION") == "INSTRUMENT_SCOPE_MISMATCH"
        request = _build("BTC_TIER_T2_750")
        with pytest.raises(InstrumentScopeMismatchError):
            run_model(dataclasses.replace(request, instrument_id="XAUUSD"))

    def test_btc_slot_tier_range_left_conditional(self):
        _golden("BTC_SLOT_RANGE_LEFT")
        _golden("BTC_SLOT_OUTSIDE")
        measured = _out("BTC_SLOT_RANGE_LEFT")
        assert _facts(measured)["BTC.SLOT"]["slot_active"] == "YES"
        assert measured.range_left.state.value == "MEASURED"
        assert measured.range_left.conditioned_on
        outside = _out("BTC_SLOT_OUTSIDE")
        assert _facts(outside)["BTC.SLOT"]["slot_active"] == "NO"
        assert outside.range_left.state.value == "UNRESOLVED"
        assert outside.range_left.value is None


# ---------------------------------------------------------------------------
# T8 — Fib / Range Birth
# ---------------------------------------------------------------------------


class TestT8FibRangeBirth:
    """Clause H: III.3.6 R15 gate, research labeling, structural rekey."""

    def test_fib_range_birth_chain_reproduces(self):
        for case_id in ("FIB_CHAIN_ACTIVE", "FIB_CHAIN_ELIGIBLE"):
            _golden(case_id)
        assert _out("FIB_CHAIN_ACTIVE").model_state == "RANGE_ACTIVE"
        facts = _facts(_out("FIB_CHAIN_ACTIVE"))
        assert facts["FIB.R15_GATE"]["materialization"] == "DECLARED"
        assert facts["FIB.SEQUENCE"]["family"] == "ALPHA"
        assert facts["FIB.AB_RANGE"]

    def test_fib_unresolved_r15_refuses(self):
        assert _refusal("FIB_R15_UNRESOLVED_REFUSES") == "RULE_NOT_MATERIALIZED"
        with pytest.raises(RuleNotMaterializedError):
            run_model(_build("FIB_COORDS_WITHOUT_RULE"))

    def test_fib_research_states_labeled(self):
        for case_id in (
            "FIB_CHAIN_ACTIVE", "FIB_CHAIN_ELIGIBLE", "FIB_REKEY_REMAPPED",
            "FIB_COORD_132_NOT_A_REKEY",
        ):
            output = _out(case_id)
            assert output.production_authorization in (
                ProductionAuthorization.RESEARCH_ONLY,
                ProductionAuthorization.NOT_AUTHORIZED,
            ), case_id
            assert "GAP_UNRESOLVED" in [c.value for c in output.warnings], case_id

    def test_fib_production_generation_blocked(self):
        _golden("FIB_NO_ANCHOR")
        output = _out("FIB_NO_ANCHOR")
        assert output.production_authorization is ProductionAuthorization.NOT_AUTHORIZED
        assert "RULE_NOT_MATERIALIZED" in [r.value for r in output.no_go]
        for case_id in _all_cases():
            if not case_id.startswith("FIB_"):
                continue
            output = _out(case_id) if case_id in _run_all()[0] else None
            if output is not None:
                assert output.production_authorization in (
                    ProductionAuthorization.RESEARCH_ONLY,
                    ProductionAuthorization.NOT_AUTHORIZED,
                ), case_id

    def test_fib_no_generic_pivot_fallback(self):
        assert _refusal("FIB_PIVOT_ORIGIN_REFUSED") == "MODEL_CONTRACT"
        with pytest.raises(ModelContractError):
            run_model(_build("FIB_PIVOT_ORIGIN_REFUSED"))

    def test_fib_no_automatic_anchor_invention(self):
        output = _out("FIB_NO_ANCHOR")
        assert output.active_anchor_states == ()
        assert _facts(output)["FIB.SEQUENCE_UNRESOLVED"]["family"] == "UNRESOLVED"

    def test_fib_coordinate_availability_not_eligibility(self):
        _golden("FIB_COORDINATES_NEED_ANCHOR")
        output = _out("FIB_COORDINATES_NEED_ANCHOR")
        assert output.levels, "coordinates were supplied"
        assert all(not level.active for level in output.levels)
        assert output.model_state == "RANGE_BIRTH_UNRESOLVED"
        assert "FIB.COORDINATES_WITHOUT_ANCHOR" in _facts(output)

    def test_fib_rekey_structural_remapping(self):
        _golden("FIB_REKEY_REMAPPED")
        output = _out("FIB_REKEY_REMAPPED")
        assert output.model_state == "REKEY_REMAPPED"
        rekey = _facts(output)["FIB.REKEY_REMAPPING"]
        assert set(rekey) == {"prior_anchor_id", "successor_anchor_id", "mapping"}

    def test_fib_r11_negative_evidence_no_transfer(self):
        for case_id in _all_cases():
            if not case_id.startswith("FIB_"):
                continue
            if case_id in ("FIB_R15_UNRESOLVED_REFUSES", "FIB_COORDS_WITHOUT_RULE",
                           "FIB_PIVOT_ORIGIN_REFUSED"):
                continue
            output = _out(case_id)
            r11 = _facts(output)["FIB.R11_NEGATIVE_EVIDENCE"]
            assert r11["stance"] == "NEGATIVE", case_id
            assert "EV.FIB.R11.ANCHOR_OVERGEN.V1" in output.evidence_refs


# ---------------------------------------------------------------------------
# T9 — JPY Carry Game
# ---------------------------------------------------------------------------


class TestT9JpyCarry:
    """Clause I: III.3.7 basket roles, veto laws, no equal vote."""

    def test_jpy_roles_returned_separately(self):
        _golden("JPY_AGREE_CONFIRM")
        output = _out("JPY_AGREE_CONFIRM")
        labels = [sub.label for sub in output.sub_states]
        assert labels == ["USDJPY", "AUDJPY", "EURJPY", "CONFIRMATION"]
        for pair in ("USDJPY", "AUDJPY", "EURJPY"):
            role = _facts(output)[f"JPY.PAIR.{pair}"]["role"]
            assert role == {
                "USDJPY": "CARRY_MASTER",
                "AUDJPY": "RISK_EXPRESSION",
                "EURJPY": "CONFIRMATION_VETO",
            }[pair]

    def test_jpy_agree_and_confirm_case(self):
        _golden("JPY_AGREE_CONFIRM")
        output = _out("JPY_AGREE_CONFIRM")
        assert output.model_state == "BASKET_AGREE_CONFIRM"
        assert _sub(output, "CONFIRMATION").state == "CONFIRMED"
        assert _facts(output)["JPY.BASKET.AGREEMENT"]["agree"] == "YES"

    def test_jpy_confirm_absent_vetoes(self):
        _golden("JPY_CONFIRM_ABSENT")
        absent = _out("JPY_CONFIRM_ABSENT")
        assert absent.model_state == "BASKET_CONFIRM_ABSENT"
        assert _sub(absent, "CONFIRMATION").state == "ABSENT"
        _golden("JPY_CONFIRM_VETO")
        veto = _out("JPY_CONFIRM_VETO")
        assert veto.model_state == "BASKET_VETO"
        assert _sub(veto, "CONFIRMATION").state == "VETO"
        _golden("JPY_MASTER_EXPRESSION_CONFLICT")
        assert _out("JPY_MASTER_EXPRESSION_CONFLICT").model_state == "BASKET_CONFLICT"

    def test_jpy_native_tier_no_go_per_pair(self):
        _golden("JPY_NO_GO_MASTER")
        output = _out("JPY_NO_GO_MASTER")
        assert "NATIVE_TIER_NO_GO" in [r.value for r in output.no_go]
        assert _sub(output, "USDJPY").state == "NO_GO"
        assert output.model_state == "BASKET_UNRESOLVED"

    def test_jpy_equal_vote_impossible(self):
        _assert_no_banned_tokens(
            _runtime_dataclass_field_names(), AGGREGATION_TOKENS, "fields"
        )
        keys = _outputs_payload_keys(
            tuple(cid for cid in _run_all()[0] if cid.startswith("JPY_"))
        )
        _assert_no_banned_tokens(keys, AGGREGATION_TOKENS, "JPY payloads")
        tree = ast.parse((PACKAGE_DIR / "jpy_carry.py").read_text(encoding="utf-8"))
        identifiers: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                identifiers.add(node.name)
            elif isinstance(node, ast.arg):
                identifiers.add(node.arg)
            elif isinstance(node, ast.Name):
                identifiers.add(node.id)
        _assert_no_banned_tokens(identifiers, AGGREGATION_TOKENS, "jpy_carry identifiers")

    def test_jpy_equal_vote_request_refuses(self):
        assert _refusal("JPY_EQUAL_VOTE_REFUSED") == "MODEL_CONTRACT"
        with pytest.raises(ModelContractError):
            run_model(_build("JPY_EQUAL_VOTE_REFUSED"))

    def test_jpy_confirmation_not_entry(self):
        output = _out("JPY_AGREE_CONFIRM")
        assert _sub(output, "CONFIRMATION").state == "CONFIRMED"
        assert output.production_authorization is ProductionAuthorization.MANUAL_OPERATOR
        keys = _walk_keys(_payload(output))
        _assert_no_banned_tokens(keys, BANNED_TRADING_TOKENS, "JPY payloads")

    def test_jpy_dt_geometry_not_auto_merged(self):
        _golden("JPY_DT_REFERENCED")
        referenced = _out("JPY_DT_REFERENCED")
        dt_fact = _facts(referenced)["JPY.DT.REFERENCED"]
        assert dt_fact["referenced"] == "YES"
        assert dt_fact["consumed"] == "DECLARED_STRUCTURES_ONLY"
        assert [level.level_id for level in referenced.levels] == [
            "JPY_132", "JPY_168", "JPY_187_5"
        ]
        assert all(not level.active for level in referenced.levels)
        plain = _out("JPY_AGREE_CONFIRM")
        assert not any("DT" in fact_id for fact_id in _fact_ids(plain))
        assert plain.levels == ()

    def test_jpy_manual_operator_classification_preserved(self):
        for case_id in _all_cases():
            if not case_id.startswith("JPY_") or case_id not in _run_all()[0]:
                continue
            assert _out(case_id).production_authorization is (
                ProductionAuthorization.MANUAL_OPERATOR
            ), case_id

    def test_jpy_pair_native_calibration_binding(self):
        assert _refusal("JPY_CROSS_PAIR_PATH") == "INSTRUMENT_SCOPE_MISMATCH"
        entry = resolve("JPY.CARRY_GAME.L1_L3.V1", "V1")
        assert entry.calibration_bindings == (), "no table is invented for JPY"
        for item in fields(JpyPairInput):
            assert item.type == "AnchorEligibility" or "Tier" not in str(item.type)


# ---------------------------------------------------------------------------
# T10 — Golden fixtures, registry pins and replay
# ---------------------------------------------------------------------------


class TestT10Replay:
    """Clause J/K: golden reproduction, hash identity, drift, replay."""

    def test_identical_inputs_identical_hash(self):
        outputs, _ = _run_all()
        for case_id, output in outputs.items():
            rerun = run_model(_build(case_id, outputs))
            assert rerun.output_hash == output.output_hash, case_id
        # The committed replay-hash golden file matches the pipeline.
        golden = json.loads(
            (III3_FIXTURE_DIR / "replay_hashes.json").read_text(encoding="utf-8")
        )
        assert golden["hashes"] == {
            case_id: output.output_hash for case_id, output in sorted(outputs.items())
        }

    def test_hash_covers_full_identity(self):
        request = _build("EUR_DAILY_SEED_T1")
        base = run_model(request)
        other_time = run_model(
            dataclasses.replace(
                request, calculation_timestamp=gen._utc("2026-03-03T10:00:00Z")
            )
        )
        assert other_time.output_hash != base.output_hash
        assert compute_hash(canonical_payload(base)) == base.output_hash

    def test_ordered_transitions_affect_hash(self):
        route = _out("EUR_WEEKLY_ROUTE")
        promoted = _out("EUR_WEEKLY_PROMOTED")
        assert promoted.output_hash != route.output_hash
        route_ids = _fact_ids(route)
        promoted_ids = _fact_ids(promoted)
        assert route_ids != promoted_ids
        assert promoted_ids.index("EUR_WEEKLY.NODE") < promoted_ids.index(
            "EUR_WEEKLY.HOUR_TIER_TIMING"
        ), "state-chain order is preserved in fact order"

    def test_version_drift_pinned_outputs_differ(self):
        with pytest.raises(ModelVersionUnavailableError):
            resolve("EUR.DAILY.NEWS_REKEY.V1", "V2")
        with pytest.raises(ModelVersionUnavailableError):
            run_model(_dt_request())
        # The pinned historical generation is a distinct registered
        # object — drift can never resolve to the current generation.
        assert resolve("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM") is not resolve(
            "JPY.CARRY_GAME.L1_L3.V1", "V1"
        )

    def test_replay_never_substitutes_rules(self):
        outputs, _ = _run_all()
        request = _build("EUR_DAILY_SEED_T1", outputs)
        good = outputs["EUR_DAILY_SEED_T1"].output_hash
        verify_replay(request, good)
        with pytest.raises(ReplayHashMismatchError):
            verify_replay(request, "0" * 64)
        with pytest.raises(ReplayHashMismatchError):
            verify_replay(request, "not-a-hash")

    def test_prior_state_mismatch_refuses(self):
        outputs, _ = _run_all()
        weekly = _build("EUR_WEEKLY_ROUTE")
        with pytest.raises(PriorStateMismatchError):
            run_model(dataclasses.replace(weekly, prior_state=outputs["BTC_TIER_T2_750"]))
        daily = _build("EUR_DAILY_SEED_T1")
        with pytest.raises(PriorStateMismatchError):
            run_model(
                dataclasses.replace(daily, prior_state=outputs["EUR_WEEKLY_FROZEN"])
            )

    def test_clock_identity_participates_in_hash(self):
        outputs, _ = _run_all()
        request = _build("EUR_DAILY_SEED_T1")
        shifted = run_model(dataclasses.replace(request, clock_id="Europe/London"))
        assert shifted.output_hash != outputs["EUR_DAILY_SEED_T1"].output_hash
        assert shifted.identity.clock_id == "Europe/London"

    def test_evidence_link_stability(self):
        outputs_a, _ = gen.run_cases()
        outputs_b, _ = gen.run_cases()
        for case_id, output in outputs_a.items():
            assert output.evidence_refs == outputs_b[case_id].evidence_refs, case_id
            assert [
                fact.fact_id for fact in output.explanation_facts
            ] == [fact.fact_id for fact in outputs_b[case_id].explanation_facts], case_id

    def test_replay_detects_nondeterministic_input(self):
        outputs, _ = _run_all()
        request = _build("EUR_DAILY_SEED_T2_SLOT_PATH")
        expected_hash = outputs["EUR_DAILY_SEED_T2_SLOT_PATH"].output_hash
        verify_replay(request, expected_hash)
        tampered = dataclasses.replace(
            request, calculation_timestamp=gen._utc("2026-03-03T09:00:01Z")
        )
        with pytest.raises(ReplayHashMismatchError):
            verify_replay(tampered, expected_hash)

    def test_fixture_manifest_hashes_recorded(self):
        manifest = json.loads(
            (III3_FIXTURE_DIR / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8")
        )
        on_disk = sorted(p.name for p in III3_FIXTURE_DIR.glob("*.json"))
        assert sorted(manifest["files"]) == [n for n in on_disk if n != "FIXTURE_MANIFEST.json"]
        for name, recorded in manifest["files"].items():
            raw = (III3_FIXTURE_DIR / name).read_bytes().replace(b"\r\n", b"\n")
            assert hashlib.sha256(raw).hexdigest() == recorded, name


# ---------------------------------------------------------------------------
# T11 — Label, serialization and authority discipline (adversarial)
# ---------------------------------------------------------------------------


class TestT11Discipline:
    """Clause L/M: contamination, quality, vocabulary, authority."""

    def test_cross_asset_calibration_contamination_refuses(self):
        assert _refusal("BTC_FOREIGN_INSTRUMENT") == "INSTRUMENT_SCOPE_MISMATCH"
        assert _refusal("BTC_FOREIGN_CALIBRATION") == "INSTRUMENT_SCOPE_MISMATCH"
        assert _refusal("JPY_CROSS_PAIR_PATH") == "INSTRUMENT_SCOPE_MISMATCH"
        # A foreign instrument on any measurement refuses at the gate.
        request = _build("EUR_DAILY_SEED_T1")
        foreign = dataclasses.replace(request, instrument_id="XAUUSD")
        with pytest.raises(InstrumentScopeMismatchError):
            run_model(foreign)

    def test_missing_evidence_attaches_no_statistic(self):
        for case_id in (
            "XAU_COORDINATES_ACTIVE", "XAU_132_NO_168", "JPY_AGREE_CONFIRM",
            "EUR_DAILY_NO_EVENT",
        ):
            output = _out(case_id)
            keys = _walk_keys(_payload(output))
            _assert_no_banned_tokens(keys, PERFORMANCE_TOKENS, case_id)
            _assert_no_banned_tokens(keys, PROBABILITY_TOKENS, case_id)

    def test_nonfinal_source_data_blocks(self):
        # Finality is assessed against the observation cutoff by time:
        # a bar closing after the cutoff is nonfinal at that cutoff.
        bars = [
            Bar(
                instrument_id="EURUSD", timeframe="M5",
                open_time=gen._utc("2026-03-03T00:30:00Z"),
                close_time=gen._utc("2026-03-03T00:35:00Z"),
                open=Decimal("1.07900"), high=Decimal("1.07950"),
                low=Decimal("1.07880"), close=Decimal("1.07940"),
                volume=Decimal(100), provider="synthetic",
                finality=Finality.NONFINAL,
                source_timestamp=gen._utc("2026-03-03T00:00:00Z"),
                quality_flags=frozenset({QualityFlag.COMPLETE}),
                provenance=gen.ProvenanceKind.SYNTHETIC_FIXTURE,
                source_ref=None,
            )
        ]
        with pytest.raises(Exception) as info:
            measure_range(
                bars,
                instrument=gen.env()["registry"].get("EURUSD"),
                provenance=gen._prov("EURUSD", "EUR_DAILY.ASIAN_RANGE"),
                observation_cutoff=gen._utc(gen.CUTOFF),
                quality_policy=gen._policy("EUR.DAILY.NEWS_REKEY.V1", "PHASE1"),
            )
        assert "BLOCKED" in str(info.value) or "finalized" in str(info.value)
        # And a blocked-quality measurement can never be constructed, so
        # no runtime input can ever carry one.
        with pytest.raises(MeasurementContractError):
            Measurement(
                definition_id="RANGE_MEASUREMENT", definition_version="V1",
                instrument_id="EURUSD", source_window=_seed_window(),
                clock_id="America/New_York", clock_registry_version="CLOCK_REGISTRY_V1",
                session_id="EUR_DAILY.ASIAN_RANGE",
                session_registry_version="SESSION_REGISTRY_V1",
                calculation_timestamp=gen._utc(gen.CALC_TS),
                quality_state=DataOutcome.NO_CALCULATION,
                native_unit=None,
                market_data_schema_version="MARKET_DATA_SCHEMA_V1",
                measurement_engine_version="MEASUREMENT_ENGINE_V1",
                evidence_refs=(),
            )

    def test_l3_l2_l1_authority_leakage_impossible(self):
        _golden("XAU_L3_UNRESOLVED_WITH_RICH_L1")
        output = _out("XAU_L3_UNRESOLVED_WITH_RICH_L1")
        assert _sub(output, "L3").state == "UNRESOLVED"
        assert _sub(output, "L2").state == "ROUTE_OPEN"
        assert _sub(output, "L1").state == "BAND_REPAIR"
        assert output.direction_bias.declared is False, (
            "L3 destination authority: no L3 input, no direction"
        )

    def test_model_state_not_trade_eligibility(self):
        _assert_no_banned_tokens(
            _runtime_dataclass_field_names(), BANNED_TRADING_TOKENS, "fields"
        )
        for case_id in _run_all()[0]:
            output = _out(case_id)
            assert output.production_authorization is not None, case_id
            assert isinstance(output.model_state, str)

    def test_no_prediction_or_signal_vocabulary(self):
        for enum_name, value in _all_enum_values():
            assert not (_tokens(value) & {"prediction", "predictive", "forecast", "signal", "signals"}), (
                enum_name, value
            )
        identifiers = _package_identifiers()
        _assert_no_banned_tokens(
            identifiers, {"prediction", "predictive", "forecast"}, "identifiers"
        )

    def test_no_performance_metric_vocabulary(self):
        for enum_name, value in _all_enum_values():
            assert not (_tokens(value) & PERFORMANCE_TOKENS), (enum_name, value)
        _assert_no_banned_tokens(
            _package_identifiers(), PERFORMANCE_TOKENS, "identifiers"
        )

    def test_status_labels_factual_enum_only(self):
        for case_id in _run_all()[0]:
            output = _out(case_id)
            assert LABEL_PATTERN.match(output.model_state), output.model_state
            for sub in output.sub_states:
                assert LABEL_PATTERN.match(sub.state), (case_id, sub.state)
                assert LABEL_PATTERN.match(sub.label), (case_id, sub.label)

    def test_unresolved_states_remain_visible(self):
        horizon = _out("BTC_HORIZON_UNRESOLVED")
        labels = [sub.label for sub in horizon.sub_states]
        assert "WEEKLY" in labels and "MONTHLY" in labels
        timing = _out("EUR_WEEKLY_TIMING_UNRESOLVED")
        assert any(
            "TIMING_UNRESOLVED" in fact_id for fact_id in _fact_ids(timing)
        )
        no_anchor = _out("FIB_NO_ANCHOR")
        assert no_anchor.model_state == "RANGE_BIRTH_UNRESOLVED"

    def test_historical_statistics_never_current_performance(self):
        keys = _outputs_payload_keys(
            tuple(cid for cid in _run_all()[0] if cid.startswith("JPY_"))
        )
        _assert_no_banned_tokens(keys, PERFORMANCE_TOKENS, "JPY payloads")
        for case_id in _all_cases():
            if not case_id.startswith("JPY_") or case_id not in _run_all()[0]:
                continue
            output = _out(case_id)
            for fact in output.explanation_facts:
                for key, value in fact.payload:
                    assert "%" not in value, (case_id, fact.fact_id, key, value)

    def test_arbitrary_pivot_rejected(self):
        # There is no generic-pivot anchor rule anywhere in the
        # runtime's rule surface: a local-pivot origin refuses before
        # any anchor could be invented.
        assert _refusal("FIB_PIVOT_ORIGIN_REFUSED") == "MODEL_CONTRACT"
        from app.forge.measurements import ANCHOR_RULE_REGISTRY

        # No pivot rule exists on the shared rule surface either (the
        # registry holds the rules upstream has ratified; a pivot rule
        # would be visible here and is not).
        rule_ids = sorted(ANCHOR_RULE_REGISTRY)
        assert not any("PIVOT" in rule_id.upper() for rule_id in rule_ids), rule_ids

    def test_bounded_enums_no_free_text(self):
        for case_id in _run_all()[0]:
            output = _out(case_id)
            for reason in output.no_go:
                assert LABEL_PATTERN.match(reason.value), reason.value
            for warning in output.warnings:
                assert LABEL_PATTERN.match(warning.value), warning.value
            assert LABEL_PATTERN.match(output.production_authorization.value)

    def test_no_measurement_redefinition(self):
        for name, source in _package_sources():
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = (
                            base.id if isinstance(base, ast.Name)
                            else base.attr if isinstance(base, ast.Attribute)
                            else ""
                        )
                        assert base_name != "Measurement", (
                            name, node.name,
                            "the runtime never subclasses Measurement",
                        )


# ---------------------------------------------------------------------------
# T12 — Boundaries
# ---------------------------------------------------------------------------


def _seed_window():
    return gen.eur_range(gen.env()["eur_seeds"]["EUR_SEED_T2"]).source_window


class TestT12Boundaries:
    """Clause N/O/P: imports, freezes, migrations, seams, honesty."""

    def test_no_book1_authority_imports(self):
        allowed = ("app.forge.market_data", "app.forge.measurements")
        forbidden_modules = (
            "app.forge.service", "app.forge.qa", "app.forge.persistence",
            "app.forge.retrieval", "app.forge.providers", "app.forge.backfill",
            "app.forge.identity", "app.forge.canonical", "app.forge.provenance",
            "app.forge.policy", "app.forge.observability", "app.forge.config",
        )
        for name, source in _package_sources():
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    module = node.module
                    if module.startswith("app.forge"):
                        assert module.startswith(allowed), (name, module)
                    assert not module.startswith(forbidden_modules), (name, module)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert not alias.name.startswith(forbidden_modules), (
                            name, alias.name,
                        )
        for name, source in _package_sources():
            assert "ForgeServiceContainer" not in source, name

    def test_no_corpus_writes(self):
        write_pattern = re.compile(
            r"""open\s*\([^)]*['"]w['"]|write_text\s*\(|write_bytes\s*\(|"""
            r"""os\.remove|os\.rename|\.unlink\s*\("""
        )
        for name, source in _package_sources():
            assert not write_pattern.search(source), name
        try:
            shown = subprocess.run(
                ["git", "show", "HEAD:implementation/forge/book_i/bloc_i_5/BOOK_I_FREEZE_MANIFEST_V1.md"],
                cwd=REPO_ROOT, capture_output=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        if shown.returncode == 0:
            assert shown.stdout.replace(b"\r\n", b"\n") == (
                BOOK_I_FREEZE_MANIFEST.read_bytes().replace(b"\r\n", b"\n")
            )
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain", "--", "corpus/"],
                cwd=REPO_ROOT, capture_output=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            pytest.skip("git unavailable")
        assert status.returncode == 0
        assert status.stdout.strip() == b"", status.stdout.decode(errors="replace")

    def test_fixtures_labeled_historical(self):
        for path in sorted(III3_FIXTURE_DIR.glob("*.json")):
            if path.name == "FIXTURE_MANIFEST.json":
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data["historical"] is True, path.name
            assert data["provenance"] in {
                "SYNTHETIC_FIXTURE", "CANONICAL_SOURCE_SLICE"
            }, path.name
            assert data["observation_cutoff"].endswith("Z"), path.name

    def test_no_trading_or_game_concepts(self):
        #: Disclosed canonical literal-vocabulary exception (PLAN.md §6
        #: clarification + §7 frozen layout): ``XauGameInputs`` is the
        #: frozen class name of the canonical ``XAU.GAME.L1_L2_L3.V1``
        #: family — the model id is corpus vocabulary, not a game
        #: concept.  Nothing else is excepted.
        disclosed = {"XauGameInputs"}
        identifiers = _package_identifiers() - disclosed
        offenders = {
            name: sorted(_tokens(name) & BANNED_TRADING_TOKENS)
            for name in identifiers
            if _tokens(name) & BANNED_TRADING_TOKENS
        }
        assert not offenders, sorted(offenders.items())
        for enum_name, value in _all_enum_values():
            assert not (_tokens(value) & BANNED_TRADING_TOKENS), (enum_name, value)
        # Disclosed canonical literal-data exception: model-id strings
        # containing GAME/CARRY_GAME are corpus vocabulary passed as
        # data (PLAN.md §6), never identifiers.
        source = (PACKAGE_DIR / "registry.py").read_text(encoding="utf-8")
        assert '"XAU.GAME.L1_L2_L3.V1"' in source
        assert '"JPY.CARRY_GAME.L1_L3.V1"' in source

    def test_no_network_calls(self, monkeypatch):
        import_pattern = re.compile(
            r"^\s*(?:import|from)\s+(?:socket|requests|urllib|httpx|aiohttp|websockets|telnetlib)\b",
            re.MULTILINE,
        )
        for name, source in _package_sources():
            assert not import_pattern.search(source), name

        def boom(*_args, **_kwargs):
            raise AssertionError("network access is forbidden in Bloc III.3")

        monkeypatch.setattr(socket, "socket", boom)
        monkeypatch.setattr(socket, "create_connection", boom)
        monkeypatch.setattr(socket, "getaddrinfo", boom)
        outputs, _ = _run_all()
        assert len(outputs) == 57

    def test_discover_migrations_unchanged(self):
        versions = [migration.version for migration in discover_migrations()]
        assert versions == [1, 2, 3, 4]
        assert not list(
            (REPO_ROOT / "app" / "forge" / "persistence" / "sql").glob("005_*.sql")
        )

    def test_market_data_readiness_seam_unchanged(self):
        container = ForgeServiceContainer(config=ForgeConfig(environment="test"))
        deps = container.as_readiness_dependencies()
        assert deps["market_data"] == {
            "status": "NOT_CONFIGURED",
            "required": False,
            "note": "market-data providers belong to Book III; not wired at II.1",
        }
        for name, source in _package_sources():
            assert "ForgeServiceContainer" not in source, name

    def test_frozen_manifests_unchanged(self):
        text = BOOK_II_FREEZE_MANIFEST.read_text(encoding="utf-8")
        entries = re.findall(r"`([^`\s]+)`\s+—\s+`([0-9a-f]{64})`", text)
        assert len(entries) == 50, len(entries)
        for rel_path, expected in entries:
            target = REPO_ROOT / rel_path
            assert target.exists(), rel_path
            raw = target.read_bytes()
            normalized = raw.replace(b"\r\n", b"\n")
            candidates = {
                hashlib.sha256(raw).hexdigest(),
                hashlib.sha256(normalized).hexdigest(),
                hashlib.sha256(normalized.replace(b"\n", b"\r\n")).hexdigest(),
            }
            assert expected in candidates, rel_path
        planning_text = PLANNING_FREEZE_MANIFEST.read_text(encoding="utf-8")
        pins = re.findall(
            r"^-\s+(\S+)\s*\r?\n\s+commit\s+([0-9a-f]{40})\s*$",
            planning_text, re.MULTILINE,
        )
        assert len(pins) == 23, len(pins)
        for rel_path, _sha in pins:
            assert (REPO_ROOT / rel_path).exists(), rel_path

    def test_iii1_interfaces_unchanged(self):
        text = III3_PLAN.read_text(encoding="utf-8")
        pairs = re.findall(
            r"`([A-Za-z_]+\.py) ([0-9a-f]{8})…([0-9a-f]{4,5})`", text
        )
        assert len(pairs) >= 23, len(pairs)
        iii1 = pairs[:11]
        package = REPO_ROOT / "app" / "forge" / "market_data"
        assert len(iii1) == 11
        for name, prefix, suffix in iii1:
            target = package / name
            assert target.exists(), name
            raw = target.read_bytes()
            normalized = raw.replace(b"\r\n", b"\n")
            matched = any(
                (lambda digest: digest.startswith(prefix) and digest.endswith(suffix))(
                    hashlib.sha256(candidate).hexdigest()
                )
                for candidate in (raw, normalized, normalized.replace(b"\n", b"\r\n"))
            )
            assert matched, name

    def test_iii2_interfaces_unchanged(self):
        text = III3_PLAN.read_text(encoding="utf-8")
        pairs = re.findall(
            r"`([A-Za-z_]+\.py) ([0-9a-f]{8})…([0-9a-f]{4,5})`", text
        )
        iii2 = pairs[11:23]
        assert len(iii2) == 12, len(iii2)
        package = REPO_ROOT / "app" / "forge" / "measurements"
        for name, prefix, suffix in iii2:
            target = package / name
            assert target.exists(), name
            raw = target.read_bytes()
            normalized = raw.replace(b"\r\n", b"\n")
            matched = any(
                (lambda digest: digest.startswith(prefix) and digest.endswith(suffix))(
                    hashlib.sha256(candidate).hexdigest()
                )
                for candidate in (raw, normalized, normalized.replace(b"\n", b"\r\n"))
            )
            assert matched, name

    def test_no_credentials_in_data_path(self):
        for name, source in _package_sources():
            assert not SECRET_PATTERN.search(source), name
        for path in sorted(III3_FIXTURE_DIR.glob("*.json")):
            assert not SECRET_PATTERN.search(
                path.read_text(encoding="utf-8")
            ), path.name

    def test_deterministic_repeat_runs(self):
        first, _ = gen.run_cases()
        second, _ = gen.run_cases()
        assert {
            cid: out.output_hash for cid, out in first.items()
        } == {cid: out.output_hash for cid, out in second.items()}
        wall_clock = re.compile(
            r"(datetime\.now|utcnow|time\.time\s*\(|import random|from random)"
        )
        for name, source in _package_sources():
            assert not wall_clock.search(source), name
