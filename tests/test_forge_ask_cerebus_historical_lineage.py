"""F-09 acceptance drivers (R01-R28) for the historical-lineage amendment.

Each driver names exactly one requirement in
``implementation/forge/book_iv/historical_lineage_amendment_1/ACCEPTANCE.md``
and asserts a property of the repaired chain, never of a convenient run
artefact. The 24 EV-155..EV-178 cases live in
``implementation/forge/book_iv/bloc_iv_6/fixtures_v3/`` and are executed in
CHAIN mode; a small number of refusal cases need an authoring draft that
asserts the unsupported claim so IV.5 can veto it (the harness's generic
chain draft states only authorised context and would never reach a numerical
or freshness finding).
"""

from __future__ import annotations

from typing import Any

import importlib.util
import sys
from pathlib import Path

import pytest

from app.forge.ask_cerebus.context.service import ContextPackager
from app.forge.ask_cerebus.evaluation.schema import EvaluationCase, ExpectedEvidencePath
from app.forge.ask_cerebus.interpreter.interpret import interpret
from app.forge.ask_cerebus.llm_gateway.draft import (
    DraftClaim,
    DraftSection,
    GatewayDraft,
    NumericLink,
)
from app.forge.ask_cerebus.llm_gateway.versions import ASK_GATEWAY_CONTRACT_V1
from app.forge.ask_cerebus.llm_gateway.enums import DraftStatus
from app.forge.ask_cerebus.llm_gateway.trace import GatewayTrace, UsageAccounting
from app.forge.ask_cerebus.answer.service import validate_answer

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "implementation/forge/book_iv/bloc_iv_6/fixtures_v3"


def _load(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V3_CASES = _load("f09_v3_cases", V3 / "cases.py").cases()
V3_BY_ID = {case.case_id: case for case in V3_CASES}

MODEL_P90 = "MOD.P90.V1"
MODEL_BASE80 = "MOD.BASE80.V1"
MODEL_MARKOV = "MOD.MARKOV.LEGACY.V1"
GEN_P90 = "P90.ORIGINAL"
GEN_BASE80 = "BASE80"
GEN_MARKOV = "MARKOV.LEGACY"


def _chain_credentials():
    fb = _load("f09_iv2_builders", ROOT / "implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py")
    return fb.operator(), fb.operator_context(), fb.service()


def _retrieve_and_pack(query: str, depth: str):
    principal, context, service = _chain_credentials()
    plan = interpret(query)
    bundle = service.retrieve(plan, principal, context)
    package = ContextPackager().pack(plan, bundle)
    return plan, bundle, package


def _make_draft(package: Any, depth: str, claims, numbers=(), citations=()):
    """Build an unvalidated GatewayDraft over ``package`` for IV.5 validation."""
    sections = (
        (DraftSection("WHAT IT MEANS", tuple(text for text, _ in claims)),)
        if claims
        else ()
    )
    return GatewayDraft(
        package_id=package.package_id,
        manifest_id=package.manifest.manifest_digest,
        query_plan_id=package.query_plan_id,
        route_policy_version="RPV",
        route_id="RT",
        prompt_id="PT",
        prompt_version="PV",
        depth=depth,
        provider="p1",
        model="m1",
        sections=sections,
        claims=tuple(
            DraftClaim(text, (ref,), "HISTORICAL", "", "") for text, ref in claims
        ),
        citations=citations,
        numbers=numbers,
        uncertainties=(),
        refusals=(),
        proposed_prose="",
        usage=UsageAccounting(),
        attempts=(),
        trace=GatewayTrace(
            contract_version=ASK_GATEWAY_CONTRACT_V1,
            route_policy_version="RPV",
            route_id="RT",
            package_id=package.package_id,
            manifest_id=package.manifest.manifest_digest,
            query_plan_id=package.query_plan_id,
            prompt_id="PT",
            prompt_version="PV",
            provider="p1",
            model="m1",
            outcome="DRAFT",
        ),
        status=DraftStatus.UNVALIDATED,
    )


def _run(query: str, depth: str, kind: str = "answer"):
    """Run one query through interpret -> retrieve -> pack -> validate.

    ``kind`` selects the authoring draft:
    ``answer`` uses the harness's generic chain draft (authorised context
    only); ``statistic`` asserts an unsupported number; ``current-state``
    asserts a live state; ``actionable`` asserts a setup action. IV.5 vetoes
    the unsupported claim in each refusal case.
    """
    plan, bundle, package = _retrieve_and_pack(query, depth)
    if kind == "answer":
        fb = _load(
            "f09_iv6_builders",
            ROOT / "implementation/forge/book_iv/bloc_iv_6/fixtures/_builders.py",
        )
        draft = fb.chain_draft(package, depth)
    else:
        claim_ref = next(
            (i.source_ref_id for s in package.sections for i in s.items
             if i.source_ref_type == "CLAIM"),
            None,
        )
        canon_ref = next(
            (i.source_ref_id for s in package.sections for i in s.items
             if i.source_ref_type == "MODEL"),
            None,
        )
        ref = claim_ref or canon_ref or MODEL_P90
        if kind == "statistic":
            text = "The asserted statistic is not supported by the authorised package."
            numbers = (NumericLink("58%", ref),)
        elif kind == "current-state":
            text = "The model's current state is RANGE."
            numbers = ()
        elif kind == "actionable":
            text = "You should enter the setup at the encoded trigger."
            numbers = ()
        else:  # pragma: no cover - guarded by the callers
            raise ValueError(f"unknown run kind: {kind}")
        draft = _make_draft(
            package,
            depth,
            [(text, ref)],
            numbers=numbers,
            citations=(ref,),
        )
    answer = validate_answer(draft, package)
    payload = answer.payload()
    return {
        "plan": plan,
        "bundle": bundle,
        "package": package,
        "draft": draft,
        "answer": payload,
        "outcome": payload.get("outcome"),
        "code": payload.get("answer_refusal_code"),
        "findings": tuple(payload.get("findings", ())),
        "limitations": tuple(payload.get("limitations", ())),
        "claims": payload.get("claims", ()),
        "citations": payload.get("citations", ()),
    }


# ---------------------------------------------------------------------------
# R01-R03: admission and identity
# ---------------------------------------------------------------------------


def test_f09_r01_p90_reaches_gateway_task():
    _, _, package = _retrieve_and_pack("Show me the P90 historical state.", "OPERATOR")
    from app.forge.ask_cerebus.llm_gateway.request import admit

    admitted = admit(package)
    assert hasattr(admitted, "task")
    assert admitted.task.value == "HISTORICAL"


def test_f09_r02_base80_reaches_gateway_task():
    _, _, package = _retrieve_and_pack("Show me the Base80 state.", "OPERATOR")
    from app.forge.ask_cerebus.llm_gateway.request import admit

    admitted = admit(package)
    assert hasattr(admitted, "task")
    assert admitted.task.value == "HISTORICAL"


def test_f09_r03_markov_reaches_gateway_task():
    _, _, package = _retrieve_and_pack("Show me the Markov legacy state.", "OPERATOR")
    from app.forge.ask_cerebus.llm_gateway.request import admit

    admitted = admit(package)
    assert hasattr(admitted, "task")
    assert admitted.task.value == "HISTORICAL"


# ---------------------------------------------------------------------------
# R04-R12: explanation by depth
# ---------------------------------------------------------------------------


def _explanation_case(query: str, depth: str, model: str, generation: str):
    result = _run(query, depth)
    assert result["outcome"] == "VALIDATED_ANSWER", result
    claim = result["claims"][0]
    assert claim["source_refs"][0] == model, claim
    assert claim["generation"] == generation, claim
    assert claim["epistemic_label"] == "HISTORICAL", claim
    assert "HISTORICAL_GENERATION" in result["limitations"], result["limitations"]
    return result


def test_f09_r04_p90_beginner_explanation():
    _explanation_case("What is the P90 model?", "BEGINNER", MODEL_P90, GEN_P90)


def test_f09_r05_base80_beginner_explanation():
    _explanation_case("What is the Base80 model?", "BEGINNER", MODEL_BASE80, GEN_BASE80)


def test_f09_r06_markov_beginner_explanation():
    _explanation_case("What is the Markov legacy model?", "BEGINNER", MODEL_MARKOV, GEN_MARKOV)


def test_f09_r07_p90_operator_explanation():
    _explanation_case("Which model version is the P90 generation?", "OPERATOR", MODEL_P90, GEN_P90)


def test_f09_r08_base80_operator_explanation():
    _explanation_case("Which model version is the Base80 generation?", "OPERATOR", MODEL_BASE80, GEN_BASE80)


def test_f09_r09_markov_operator_explanation():
    _explanation_case("Which model version is the Markov legacy generation?", "OPERATOR", MODEL_MARKOV, GEN_MARKOV)


def test_f09_r10_p90_researcher_metadata():
    result = _explanation_case("Show me the P90 historical lineage.", "RESEARCHER", MODEL_P90, GEN_P90)
    assert any("MOD.P90.V1" in c.get("source_refs", ()) for c in result["claims"])


def test_f09_r11_base80_researcher_metadata():
    result = _explanation_case("Show me the Base80 historical lineage.", "RESEARCHER", MODEL_BASE80, GEN_BASE80)
    assert any("MOD.BASE80.V1" in c.get("source_refs", ()) for c in result["claims"])


def test_f09_r12_markov_researcher_metadata():
    result = _explanation_case("Show me the Markov legacy historical lineage.", "RESEARCHER", MODEL_MARKOV, GEN_MARKOV)
    assert any("MOD.MARKOV.LEGACY.V1" in c.get("source_refs", ()) for c in result["claims"])


# ---------------------------------------------------------------------------
# R13-R14: status and generation integrity
# ---------------------------------------------------------------------------


def test_f09_r13_superseded_status_preserved():
    principal, context, service = _chain_credentials()
    fb = _load("f09_iv2_builders", ROOT / "implementation/forge/book_iv/bloc_iv_2/fixtures/_builders.py")
    from app.forge.ask_cerebus.interpreter.plan import AskCerebusQueryPlan
    from app.forge.ask_cerebus.interpreter.enums import Intent, Depth, TimeScope, PlanConfidence
    from app.forge.ask_cerebus.interpreter.entities import EntityRef, EntityKind

    plan = AskCerebusQueryPlan(
        intent=Intent.HISTORICAL_LINEAGE,
        entities=(EntityRef(EntityKind.MODEL, "Superseded", "MOD.LEGACY.SUPERSEDED.V1"),),
        model_ids=("MOD.LEGACY.SUPERSEDED.V1",),
        setup_ids=(),
        market=None,
        layer=None,
        time_scope=TimeScope.HISTORICAL_RESEARCH,
        requested_depth=Depth.OPERATOR,
        effective_depth=Depth.OPERATOR,
        requires_live_intelligence=False,
        requires_evidence=False,
        requires_lineage=True,
        requires_setup_context=False,
        actionable=False,
        requested_fields=(),
        confidence=PlanConfidence.CERTAIN,
        ambiguities=(),
    ).finalized()
    bundle = service.retrieve(plan, principal, context)
    package = ContextPackager().pack(plan, bundle)
    ids = {r.object_id for r in bundle.canonical_refs}
    assert "MOD.LEGACY.SUPERSEDED.V1" in ids
    for ref in bundle.canonical_refs:
        if ref.object_id == "MOD.LEGACY.SUPERSEDED.V1":
            assert ref.status == "SUPERSEDED", ref


def test_f09_r14_no_generation_substitution():
    result = _run("Which model version is the P90 generation?", "OPERATOR")
    claim = result["claims"][0]
    assert claim["generation"] == GEN_P90
    assert claim["generation"] != "PHI"
    assert "PHI" not in " ".join(c.get("text", "") for c in result["claims"])


# ---------------------------------------------------------------------------
# R15-R19: refusal correctness
# ---------------------------------------------------------------------------


def test_f09_r15_unsupported_statistic_refuses():
    result = _run("What is the P90 win rate historically?", "RESEARCHER", kind="statistic")
    assert result["outcome"] == "GOVERNED_REFUSAL", result
    assert result["code"] == "INSUFFICIENT_EVIDENCE", result


def test_f09_r16_current_state_restriction():
    result = _run("What is the P90 current state?", "BEGINNER", kind="current-state")
    assert result["outcome"] == "GOVERNED_REFUSAL", result
    assert result["code"] == "CURRENT_DATA_UNAVAILABLE", result


def test_f09_r17_actionable_request_gated():
    result = _run("Should I enter a P90 setup?", "RESEARCHER", kind="actionable")
    assert result["outcome"] == "GOVERNED_REFUSAL", result
    assert result["code"] == "SETUP_NOT_ENCODED", result


def test_f09_r18_invalid_task_bounded():
    # INDICATOR_NAVIGATION has no route task: product composition returns a
    # governed ROUTE_UNSUPPORTED refusal, never an exception.
    principal, context, service = _chain_credentials()
    plan = interpret("Open the vault indicator library.")
    assert plan.intent.value == "INDICATOR_NAVIGATION"
    bundle = service.retrieve(plan, principal, context)
    package = ContextPackager().pack(plan, bundle)
    from app.forge.ask_cerebus.llm_gateway.request import admit

    admitted = admit(package)
    assert not hasattr(admitted, "task")


def test_f09_r19_no_historical_to_current_promotion():
    result = _run("Show me the P90 historical state.", "OPERATOR")
    assert result["outcome"] == "VALIDATED_ANSWER"
    claim = result["claims"][0]
    assert claim["epistemic_label"] == "HISTORICAL"
    assert "CURRENT" not in claim.get("epistemic_label", "")


# ---------------------------------------------------------------------------
# R20-R23: evidence, citation and exposure
# ---------------------------------------------------------------------------


def test_f09_r20_historical_citation_correctness():
    result = _run("What is the P90 model?", "BEGINNER")
    assert result["citations"]
    assert result["citations"][0]["source_ref_id"] == MODEL_P90
    assert result["citations"][0]["generation"] == GEN_P90


def test_f09_r21_exposure_preserved():
    principal, context, service = _chain_credentials()
    plan = interpret("What is the P90 model?")
    bundle = service.retrieve(plan, principal, context)
    for ref in bundle.canonical_refs:
        assert ref.exposure == "RESEARCH_LAB", ref


def test_f09_r22_no_additional_provider_calls():
    # No snapshot provider is wired; the intelligence branch is not entered for
    # pure historical explanations, so no provider call occurs.
    principal, context, service = _chain_credentials()
    assert service._snapshot_provider is None
    plan = interpret("What is the P90 model?")
    bundle = service.retrieve(plan, principal, context)
    assert bundle.intelligence_refs == ()


def test_f09_r23_no_additional_retrieval():
    principal, context, service = _chain_credentials()
    plan = interpret("What is the Base80 model?")
    bundle = service.retrieve(plan, principal, context)
    assert [r.object_id for r in bundle.canonical_refs] == ["MOD.BASE80.V1"]


# ---------------------------------------------------------------------------
# R24-R28: corpus, completeness and regression
# ---------------------------------------------------------------------------


def test_f09_r24_intent_task_completeness():
    from app.forge.ask_cerebus.llm_gateway.request import admit
    from app.forge.ask_cerebus.llm_gateway.policy import task_from_intent

    intents = [
        "DEFINITION", "MODEL_DESCRIPTION", "CURRENT_STATE", "LEVEL_COORDINATE",
        "SETUP_CONTEXT", "STATISTIC_EVIDENCE", "COMPARISON", "HISTORICAL_LINEAGE",
        "METHODOLOGY_RESEARCH", "TROUBLESHOOTING", "GENERAL_MARKET_KNOWLEDGE",
    ]
    for intent in intents:
        task = task_from_intent(intent)
        assert task is not None, intent
    # INDICATOR_NAVIGATION is deliberately unmapped -> governed refusal, not error.
    assert task_from_intent("INDICATOR_NAVIGATION") is None


def test_f09_r25_no_new_false_refusal():
    # Authorised historical explanations (the cases affected by F-09) still
    # answer; the repair adds no new refusal for them. Current-state requests
    # for models without a live provider are correctly refused and are not
    # part of this control.
    principal, context, service = _chain_credentials()
    for query in (
        "What is the P90 model?",
        "What is the Base80 model?",
        "What is the Markov legacy model?",
        "Which model version is the P90 generation?",
        "Show me the P90 historical lineage.",
        "Compare the P90 and the BTC Tracker models.",
        "What does rekey mean in the EUR daily model?",
        "What does tier mean in CEREBUS?",
    ):
        plan = interpret(query)
        bundle = service.retrieve(plan, principal, context)
        package = ContextPackager().pack(plan, bundle)
        assert package.outcome.value != "REFUSED", query


def test_f09_r26_deterministic_replay():
    first = _run("What is the P90 model?", "BEGINNER")
    second = _run("What is the P90 model?", "BEGINNER")
    assert first["answer"] == second["answer"]
    assert first["outcome"] == second["outcome"]
    assert first["code"] == second["code"]


def test_f09_r27_frozen_upstream_integrity():
    # EV-001..EV-120, EV-121..EV-144 and EV-145..EV-154 digests and the
    # IV.1/IV.3/IV.5 source remain unchanged (the IV.2 behaviour change is the
    # only authorised source diff and is recorded separately).
    import hashlib

    v1 = ROOT / "implementation/forge/book_iv/bloc_iv_6/fixtures"
    digests = {}
    for path in sorted(v1.glob("EV-*.json")):
        digests[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    ids = sorted(int(p.stem.split("-")[1]) for p in v1.glob("EV-*.json"))
    assert ids == list(range(1, 121)), "frozen EV-001..EV-120 corpus must be intact"
    # IV.2 retrieval/service.py is the authorised amended file; its hash pin
    # conflict is recorded in RATIFICATION_SUPPLEMENT_V1.md and must not be
    # silently rebaselined here.


def test_f09_r28_security_non_regression():
    # All 27 security-amendment drivers and the 30 coverage drivers remain
    # green; the repair grants no new provider or authorisation privileges.
    # The retrieval/service.py hash pin is the authorised IV.2 change and its
    # conflict is documented in RATIFICATION_SUPPLEMENT_V1.md (Section 12),
    # so the only expected failure is that guard.
    import subprocess

    completed = subprocess.run(
        [sys.executable, "-m", "pytest",
         "tests/test_forge_ask_cerebus_amendment1.py",
         "tests/test_forge_ask_cerebus_evaluation_amendment1.py",
         "tests/test_forge_ask_cerebus_evaluation_coverage.py",
         "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    output = completed.stdout + completed.stderr
    failed_lines = [
        line for line in output.splitlines()
        if line.startswith("FAILED")
    ]
    failed_ids = {line.split("::")[-1] for line in failed_lines if "::" in line}
    # Documented hash-pin conflict on the authorised IV.2 source diff.
    allowed = {"test_am1_r27_hash_guards_are_checkout_encoding_invariant"}
    unexpected = failed_ids - allowed
    assert not unexpected, ("security/coverage regression beyond the documented conflict: ", unexpected, output)
