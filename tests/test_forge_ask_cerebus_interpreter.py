"""Bloc IV.1 acceptance suite — 60 frozen drivers (A-01–A-60, groups T1–T12).

Authoritative contract:
`implementation/forge/book_iv/bloc_iv_1/ACCEPTANCE.md`.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from app.forge.ask_cerebus.interpreter import (
    ASK_QUERY_CONTRACT_V1,
    AmbiguityOutcome,
    AmbiguityReason,
    Depth,
    EntityKind,
    Intent,
    InterpreterContext,
    PlanConfidence,
    TimeScope,
    interpret,
)
from app.forge.model_runtime.contract import Layer

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "implementation" / "forge" / "book_iv" / "bloc_iv_1" / "fixtures"
PACKAGE = REPO / "app" / "forge" / "ask_cerebus"

UPSTREAM_HASHES = {
    "app/forge/canonical.py": "fa984b4505113593232474c236d031870724bee185d7829cab4a7e2beff450d4",
    "app/forge/retrieval/aliases.py": "7452590ccca32bb80e43c913ab14a5992fd976f2a7310d81d2fb54d116249614",
    "app/forge/model_runtime/contract.py": "d0dc91f79e8183638d5eef606541c290b29d2cbdc759aef35341d1004c3f9056",
    "app/forge/intelligence_api/contracts.py": "7d8f90adf8aeca993b94d473f61fe16ea13170a1cd977cb47fb186d64697d4f0",
    "app/forge/intelligence_api/requests.py": "b2e484023dc55d1fafd90136a6654f07ba713ddfd8ca7d8da2b0ca4499237146",
    "app/forge/service/routes.py": "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af",
}

PLAN_KEYS = {
    "query_contract_version",
    "plan_id",
    "intent",
    "entities",
    "model_ids",
    "setup_ids",
    "market",
    "layer",
    "time_scope",
    "requested_depth",
    "effective_depth",
    "requires_live_intelligence",
    "requires_evidence",
    "requires_lineage",
    "requires_setup_context",
    "actionable",
    "requested_fields",
    "confidence",
    "ambiguities",
}


def ctx(maximum: Depth = Depth.RESEARCHER) -> InterpreterContext:
    return InterpreterContext(principal_scope="test", max_authorized_depth=maximum)


def plan_for(text: str, maximum: Depth = Depth.RESEARCHER):
    return interpret(text, ctx(maximum))


def walk(value, path=""):
    out = []
    if isinstance(value, dict):
        for key, item in value.items():
            out.extend(walk(item, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            out.extend(walk(item, f"{path}[{index}]"))
    else:
        out.append((path, value))
    return out


def numeric_scalars(value) -> list:
    return [
        item
        for _, item in walk(value)
        if isinstance(item, (int, float)) and not isinstance(item, bool)
    ]


def ambiguity_codes(plan) -> set[str]:
    return {entry.code.value for entry in plan.ambiguities}


# ---------------------------------------------------------------------------
# T1 — intent taxonomy (12)
# ---------------------------------------------------------------------------


def test_intent_definition():
    assert plan_for("What is rekey?").intent is Intent.DEFINITION


def test_intent_model_description():
    assert plan_for("What does the Gold Game mean?").intent is Intent.MODEL_DESCRIPTION


def test_intent_current_state():
    assert plan_for("What's EURUSD doing today?").intent is Intent.CURRENT_STATE


def test_intent_level_coordinate():
    assert plan_for("Show the 132 level.").intent is Intent.LEVEL_COORDINATE


def test_intent_setup_context():
    assert plan_for("What's the current Gold setup?").intent is Intent.SETUP_CONTEXT


def test_intent_statistic_evidence():
    assert plan_for("What is the EUR win rate?").intent is Intent.STATISTIC_EVIDENCE


def test_intent_comparison():
    assert plan_for("Is BTC Game the same as BTC Tracker?").intent is Intent.COMPARISON


def test_intent_historical_lineage():
    assert plan_for("Show the original P90 model.").intent is Intent.HISTORICAL_LINEAGE


def test_intent_methodology_research():
    assert plan_for("Explain JPY carry confirmation.").intent is Intent.METHODOLOGY_RESEARCH


def test_intent_indicator_navigation():
    assert plan_for("Open the indicator vault.").intent is Intent.INDICATOR_NAVIGATION


def test_intent_troubleshooting():
    assert plan_for("The EUR model is not working.").intent is Intent.TROUBLESHOOTING


def test_intent_general_market_knowledge():
    assert plan_for("What moves the dollar?").intent is Intent.GENERAL_MARKET_KNOWLEDGE


# ---------------------------------------------------------------------------
# T2 — entity identity (8)
# ---------------------------------------------------------------------------


def test_instrument_resolution():
    plan = plan_for("What's EURUSD and Gold doing?")
    ids = {
        entity.canonical_id for entity in plan.entities if entity.kind is EntityKind.INSTRUMENT
    }
    assert {"EURUSD", "XAUUSD"} <= ids
    assert plan.market == "EURUSD"


def test_model_resolution():
    plan = plan_for("What was the EUR weekly state last Wednesday?")
    assert plan.model_ids == ("EUR.WEEKLY",)
    assert all(entity.canonical_id for entity in plan.entities if entity.kind is EntityKind.MODEL)


def test_setup_resolution():
    plan = plan_for("Show SET.XAU.TEST setup with the XAU Game model.")
    assert plan.setup_ids == ("SET.XAU.TEST",)
    assert plan.model_ids == ("XAU.GAME",)


def test_alias_resolution_is_exact():
    resolved = plan_for("What is rekey?")
    assert any(
        entity.kind is EntityKind.TERM and entity.canonical_id == "TERM.REKEY"
        for entity in resolved.entities
    )
    near_miss = plan_for("What is rekeyish?")
    assert not any(entity.kind is EntityKind.TERM for entity in near_miss.entities)


def test_layer_resolution():
    plan = plan_for("What's the EURUSD L2 state?")
    assert plan.layer is Layer.L2
    assert plan_for("What's the EURUSD L9 state?").layer is None


def test_session_timeframe_resolution():
    plan = plan_for("What's EURUSD doing on the daily?")
    sessions = {
        entity.canonical_id for entity in plan.entities if entity.kind is EntityKind.SESSION
    }
    assert "D1" in sessions
    assert any(entity.kind is EntityKind.SESSION for entity in plan.entities)


def test_generation_token_retained():
    plan = plan_for("Show the EUR weekly model v2.")
    assert any(entity.generation == "v2" for entity in plan.entities)
    assert plan.time_scope is TimeScope.MODEL_VERSION


def test_btc_game_not_tracker():
    plan = plan_for("What is BTC Game?")
    assert "BTC.GAME" in plan.model_ids
    assert "BTC.TRACKER" not in plan.model_ids
    assert any(entity.generation == "RESEARCH_ARTIFACT" for entity in plan.entities)


# ---------------------------------------------------------------------------
# T3 — historical collisions (5)
# ---------------------------------------------------------------------------


def test_p90_generation_preserved():
    plan = plan_for("Show the original P90 model.")
    p90 = next(entity for entity in plan.entities if entity.canonical_id == "P90")
    assert p90.generation == "P90.ORIGINAL"
    assert plan.time_scope is TimeScope.HISTORICAL_RESEARCH
    assert plan.requires_lineage is True


def test_st_and_base80_generation():
    plan = plan_for("Show the old Base80 and ST framework.")
    generations = {
        entity.canonical_id: entity.generation
        for entity in plan.entities
        if entity.kind is EntityKind.MODEL
    }
    assert generations["BASE80"] == "BASE80"
    assert generations["ST"] == "ST.MANUAL"


def test_old_markov_and_fib_generation():
    plan = plan_for("Show the legacy Markov and old Fib generation.")
    generations = {
        entity.canonical_id: entity.generation
        for entity in plan.entities
        if entity.kind is EntityKind.MODEL
    }
    assert generations["MARKOV"] == "MARKOV.LEGACY"
    assert generations["FIB.RANGE_BIRTH"] == "FIB"


def test_historical_not_current():
    plan = plan_for("Give me the historical ST automation results.")
    assert plan.time_scope is TimeScope.HISTORICAL_RESEARCH
    assert plan.requires_live_intelligence is False


def test_generations_stay_distinct():
    original = plan_for("Show the original P90 model.")
    current = plan_for("Show the current P90 model.")
    first = next(entity.generation for entity in original.entities if entity.canonical_id == "P90")
    second = next(entity.generation for entity in current.entities if entity.canonical_id == "P90")
    assert first != second
    assert current.outcome is AmbiguityOutcome.MATERIAL_AMBIGUITY


# ---------------------------------------------------------------------------
# T4 — depth (4)
# ---------------------------------------------------------------------------


def test_depth_beginner():
    assert plan_for("What is rekey?").requested_depth is Depth.BEGINNER


def test_depth_operator():
    assert plan_for("What's EURUSD doing today?").requested_depth is Depth.OPERATOR


def test_depth_researcher():
    assert plan_for("Show the original P90 model.").requested_depth is Depth.RESEARCHER


def test_depth_capped_by_entitlement():
    plan = plan_for("Give me a researcher explanation of rekey.", maximum=Depth.BEGINNER)
    assert plan.requested_depth is Depth.RESEARCHER
    assert plan.effective_depth is Depth.BEGINNER
    assert "DEPTH_CAPPED" in ambiguity_codes(plan)
    assert "max_authorized_depth" not in plan.payload()
    assert plan.effective_depth.rank <= plan.requested_depth.rank


# ---------------------------------------------------------------------------
# T5 — temporal routing (6)
# ---------------------------------------------------------------------------


def test_current_requires_book_iii():
    plan = plan_for("What's EURUSD doing today?")
    assert plan.time_scope is TimeScope.CURRENT
    assert plan.requires_live_intelligence is True


def test_as_of_pins_cutoff():
    plan = plan_for("What was the EUR weekly state last Wednesday?")
    assert plan.time_scope is TimeScope.AS_OF
    assert plan.requires_lineage is True
    assert plan.requires_live_intelligence is False


def test_historical_research_scope():
    plan = plan_for("Give me the historical ST automation results.")
    assert plan.time_scope is TimeScope.HISTORICAL_RESEARCH
    assert plan.requires_lineage is True


def test_model_version_scope():
    plan = plan_for("Show the EUR weekly model v2.")
    assert plan.time_scope is TimeScope.MODEL_VERSION
    assert any(entity.generation == "v2" for entity in plan.entities)


def test_general_scope_no_live():
    plan = plan_for("What is rekey?")
    assert plan.time_scope is TimeScope.GENERAL
    assert plan.requires_live_intelligence is False


def test_unavailable_not_substituted():
    plan = plan_for("What's Gold doing today when the provider is down?")
    assert plan.time_scope is TimeScope.CURRENT
    assert plan.requires_live_intelligence is True
    assert "P90" not in plan.model_ids
    historical = plan_for("Show the original P90 model.")
    assert historical.requires_live_intelligence is False


# ---------------------------------------------------------------------------
# T6 — actionability (5)
# ---------------------------------------------------------------------------


def test_entry_question_actionable():
    assert plan_for("Should I enter Gold now?").actionable is True


def test_target_stop_question_actionable():
    assert plan_for("Where's the Gold target and stop?").actionable is True


def test_actionable_requires_setup_context():
    assert plan_for("Should I enter Gold now?").requires_setup_context is True


def test_no_action_approval():
    plan = plan_for("Should I enter Gold now?")
    payload = plan.payload()
    assert not ({"verdict", "eligible", "eligibility", "exposure", "authorization"} & set(payload))
    assert numeric_scalars(payload) == []


def test_position_question_actionable():
    assert plan_for("What position size for Gold?").actionable is True


# ---------------------------------------------------------------------------
# T7 — numerical evidence (5)
# ---------------------------------------------------------------------------


def test_rate_probability_detected():
    assert plan_for("What is the EUR win rate?").requires_evidence is True


def test_sample_and_correlation_detected():
    plan = plan_for("What's the correlation and sample size for EURUSD?")
    assert plan.requires_evidence is True


def test_evidence_flag_set_for_history_stats():
    assert plan_for("Give me the historical ST automation results.").requires_evidence is True


def test_deterministic_measurement_exception():
    plan = plan_for("What's the current EURUSD price?")
    assert plan.time_scope is TimeScope.CURRENT
    assert plan.requires_evidence is True
    assert numeric_scalars(plan.payload()) == []


def test_unsupported_statistic_not_invented():
    plan = plan_for("What's the 132% target win rate?")
    assert plan.requires_evidence is True
    assert plan.outcome is AmbiguityOutcome.UNSUPPORTED_STATISTIC
    assert numeric_scalars(plan.payload()) == []


# ---------------------------------------------------------------------------
# T8 — ambiguity (6)
# ---------------------------------------------------------------------------


def test_ambiguity_resolved():
    plan = plan_for("What's EURUSD doing today?")
    assert plan.outcome is AmbiguityOutcome.RESOLVED
    assert plan.confidence is PlanConfidence.CERTAIN


def test_ambiguity_resolved_with_scope():
    plan = plan_for("Show the original P90 model.")
    assert plan.outcome is AmbiguityOutcome.RESOLVED_WITH_EXPLICIT_SCOPE
    assert plan.confidence is PlanConfidence.EXPLICIT_SCOPE


def test_material_ambiguity():
    plan = plan_for("What's the P90 win rate?")
    assert plan.outcome is AmbiguityOutcome.MATERIAL_AMBIGUITY
    assert any(
        entry.code is AmbiguityReason.AMBIGUOUS_GENERATION and entry.material
        for entry in plan.ambiguities
    )


def test_unsupported_identity():
    plan = plan_for("Show MOD.DOES.NOT.EXIST state.")
    assert plan.outcome is AmbiguityOutcome.UNSUPPORTED_IDENTITY
    assert any(entity.canonical_id is None for entity in plan.entities)


def test_unavailable_generation():
    plan = plan_for("Show the P90 v7 generation.")
    assert plan.outcome is AmbiguityOutcome.UNAVAILABLE_GENERATION
    assert "UNAVAILABLE_GENERATION" in ambiguity_codes(plan)


def test_candidates_and_no_confidence_number():
    plan = plan_for("Show the original P90 model.")
    p90 = next(entry for entry in plan.ambiguities if entry.code is AmbiguityReason.AMBIGUOUS_GENERATION)
    assert p90.candidates == ("P90.ORIGINAL",)
    assert isinstance(plan.confidence, PlanConfidence)
    assert not isinstance(plan.confidence, float)
    assert numeric_scalars(plan.payload()) == []


# ---------------------------------------------------------------------------
# T9 — III.6 handoff (4)
# ---------------------------------------------------------------------------


def test_plan_maps_to_snapshot_request():
    plan = plan_for("What's the EUR weekly L2 state right now?")
    assert plan.market == "EURUSD"
    assert plan.model_ids == ("EUR.WEEKLY",)
    assert plan.layer is Layer.L2
    assert plan.time_scope is TimeScope.CURRENT
    assert "snapshot_id" not in plan.payload()
    assert not hasattr(plan, "snapshot_id")


def test_model_and_setup_ids_are_separate():
    plan = plan_for("Show SET.XAU.TEST setup with the XAU Game model.")
    assert plan.model_ids == ("XAU.GAME",)
    assert plan.setup_ids == ("SET.XAU.TEST",)
    assert set(plan.model_ids).isdisjoint(plan.setup_ids)


def test_layer_and_market_mapping():
    plan = plan_for("What's the EURUSD L1 level?")
    assert plan.market == "EURUSD"
    assert plan.layer is Layer.L1


def test_requirement_flags_match_scope():
    current = plan_for("What's EURUSD doing today?")
    assert current.requires_live_intelligence is True
    assert current.requires_evidence is False
    assert current.requires_lineage is False
    historical = plan_for("Show the original P90 model.")
    assert historical.requires_live_intelligence is False
    assert historical.requires_lineage is True
    assert plan_for("Should I enter Gold now?").requires_setup_context is True


# ---------------------------------------------------------------------------
# T10 — security and policy (3)
# ---------------------------------------------------------------------------


def test_no_entitlement_laundering():
    plan = plan_for("Give me a researcher explanation of rekey.", maximum=Depth.BEGINNER)
    assert plan.effective_depth is Depth.BEGINNER
    assert plan.effective_depth.rank < plan.requested_depth.rank
    payload = plan.payload()
    assert "max_authorized_depth" not in payload
    assert "entitlement" not in json.dumps(payload).lower()


def test_no_identity_substitution():
    plan = plan_for("Is BTC Game the same as BTC Tracker?")
    assert len(plan.model_ids) == 2
    assert len(set(plan.model_ids)) == 2
    assert "BTC.GAME" in plan.model_ids and "BTC.TRACKER" in plan.model_ids
    btc = plan_for("What is BTC doing?")
    assert btc.market == "BTCUSD"
    assert btc.market != "XAUUSD"


def test_no_authoritative_fields_injected():
    plan = plan_for("Should I enter Gold now?")
    payload = plan.payload()
    forbidden = {
        "verdict",
        "eligible",
        "eligibility",
        "exposure",
        "execution_class",
        "probability",
        "win_rate",
        "expectancy",
        "entry_price",
        "position_size",
        "snapshot_id",
        "snapshot_hash",
        "authorization",
    }
    assert not (forbidden & set(payload))
    assert not any(
        token in json.dumps(payload).lower()
        for token in ("verdict", "probability", "win_rate", "snapshot_id")
    )


# ---------------------------------------------------------------------------
# T11 — determinism (1)
# ---------------------------------------------------------------------------


def test_plan_is_deterministic():
    first = plan_for("What's the EUR weekly L2 state right now?")
    second = plan_for("What's the EUR weekly L2 state right now?")
    assert first.to_json() == second.to_json()
    assert first.plan_id == second.plan_id
    assert first.query_contract_version == ASK_QUERY_CONTRACT_V1

    manifest = json.loads((FIXTURES / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["fixture_count"] == 12
    context = InterpreterContext(
        principal_scope="fixture",
        max_authorized_depth=Depth.RESEARCHER,
        policy_fingerprint="fixture-policy",
    )
    for entry in manifest["fixtures"]:
        text = (FIXTURES / entry["expected"]).read_text(encoding="utf-8")
        expected = json.loads(text)
        plan = interpret(entry["question"], context)
        assert plan.payload() == expected
        assert plan.plan_id == entry["plan_id"]
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == entry["sha256"]


# ---------------------------------------------------------------------------
# T12 — frozen integrity (1)
# ---------------------------------------------------------------------------


def test_upstream_sources_untouched():
    for relative, expected in UPSTREAM_HASHES.items():
        raw = (REPO / relative).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(raw).hexdigest() == expected, relative
    for path in PACKAGE.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert not re.search(
            r"^\s*(?:import|from)\s+(requests|httpx|openai|aiohttp|urllib|socket)\b",
            source,
            re.MULTILINE,
        ), path
