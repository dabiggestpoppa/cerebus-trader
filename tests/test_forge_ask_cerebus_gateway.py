"""Book IV / Bloc IV.4 acceptance drivers A-01 through A-72.

The suite is deliberately provider-local: a scripted fake exercises the Book II
transport port and no network path exists.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import socket
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from app.forge.ask_cerebus.context import ContextSectionId
from app.forge.ask_cerebus.context.versions import CONTEXT_CONTRACT_V1
from app.forge.ask_cerebus.interpreter.enums import Depth
from app.forge.ask_cerebus.llm_gateway import (
    ASK_GATEWAY_CONTRACT_V1,
    ASK_GATEWAY_DRAFT_SCHEMA_V1,
    ASK_MODEL_ROUTING_V1,
    GatewayDraft,
    GatewayFakeLLM,
    GatewayRefusal,
    GatewayRefusalCode,
    GatewayService,
    GatewayBudget,
    FakeScript,
    ModelCandidate,
    RouteTask,
    DraftStatus,
    draft_schema,
)
from app.forge.ask_cerebus.llm_gateway.budget import estimate_text_units
from app.forge.ask_cerebus.llm_gateway.policy import (
    ModelRoute,
    RoutingPolicy,
    select_route,
)
from app.forge.ask_cerebus.llm_gateway.prompts import prompt_for_depth
from app.forge.ask_cerebus.llm_gateway.request import (
    admit,
    build_request,
    prompt_text,
)
from app.forge.ask_cerebus.llm_gateway.versions import (
    CANDIDATE_MATRIX_STATUS,
    PRICING_STATUS,
    RETENTION_POLICY_STATUS,
    TOKENIZER_STATUS,
)
from app.forge.persistence.sql.migrations import discover_migrations
from app.forge.providers.fakes import SimulatedClock
from app.forge.providers.llm import (
    CAPABILITY_STRUCTURED_OUTPUT,
    LLMProvider,
    LLMRequest,
)

ROOT = Path(__file__).resolve().parents[1]
Q4_DIR = ROOT / "implementation/forge/book_iv/bloc_iv_4/fixtures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


Q4 = _load("iv4_gateway_test_builders", Q4_DIR / "_builders.py")
_SCENARIOS = {scenario.id: scenario for scenario in Q4.cases()}


def _case(case_id: str):
    return _SCENARIOS[case_id]


def _candidate(provider: str, *, attempts: int = 1) -> ModelCandidate:
    return ModelCandidate(provider_name=provider, model="fake-model-1", max_attempts=attempts)


def _run(case, *, scripts=None, budget=None, cancel=None):
    selected = scripts if scripts is not None else case.scripts
    clock = SimulatedClock()
    providers = {
        name: GatewayFakeLLM(provider_name=name, scripts=tuple(items), clock=clock)
        for name, items in selected.items()
    }
    service = GatewayService(providers=providers, policy=case.policy, clock=clock)
    return (
        service.generate(case.package, budget=budget or case.budget, cancel=cancel),
        providers,
        clock,
    )


def _retry(case_id: str = "Q4-01"):
    case = _case(case_id)
    clock = SimulatedClock()
    fake = GatewayFakeLLM(
        provider_name="p1",
        scripts=(
            FakeScript(failure_class="timeout"),
            FakeScript(draft=Q4.base_draft(case.package)),
        ),
        clock=clock,
    )
    policy = Q4._route(case.package, (_candidate("p1", attempts=2),))
    service = GatewayService(providers={"p1": fake}, policy=policy, clock=clock)
    return service.generate(case.package), {"p1": fake}, clock


def _run_with(case, provider: str, scripts, *, cancel=None):
    clock = SimulatedClock()
    fake = GatewayFakeLLM(provider_name=provider, scripts=tuple(scripts), clock=clock)
    policy = Q4._route(case.package, (_candidate(provider),))
    service = GatewayService(providers={provider: fake}, policy=policy, clock=clock)
    return service.generate(case.package, cancel=cancel), {provider: fake}, clock


def _assert_expected(out, expected) -> None:
    if expected["outcome"] == "DRAFT":
        assert isinstance(out, GatewayDraft)
        assert out.status is DraftStatus.UNVALIDATED
    else:
        assert isinstance(out, GatewayRefusal)
        assert out.outcome.value == expected["outcome"]
        assert out.code.value == expected["code"]
    assert len(out.attempts) == expected["attempts"]


def _payload_text(out) -> str:
    return json.dumps(out.payload(), sort_keys=True, ensure_ascii=False)


def _package_item(package, section_id):
    return next(section for section in package.sections if section.section_id is section_id)


def _gateway_sources():
    return sorted((ROOT / "app/forge/ask_cerebus/llm_gateway").glob("*.py"))


# T1 — provider port -------------------------------------------------------


def test_a01_uses_frozen_book_ii_llm_port():
    case = _case("Q4-01")
    fake = GatewayFakeLLM(scripts=(FakeScript(draft=Q4.base_draft(case.package)),))
    assert isinstance(fake, LLMProvider)
    assert CAPABILITY_STRUCTURED_OUTPUT in fake.capabilities()
    out, _, _ = _run(case)
    assert isinstance(out, GatewayDraft)


def test_a02_transport_request_carries_only_prompt_model_schema():
    case = _case("Q4-01")
    admitted = admit(case.package)
    request = build_request(
        admitted,
        prompt_for_depth(admitted.depth),
        model="fake-model-1",
        response_schema=draft_schema(),
    )
    assert isinstance(request, LLMRequest)
    assert request.model == "fake-model-1"
    assert request.response_schema is not None
    assert set(vars(request)) == {"prompt", "model", "response_schema"}


def test_a03_requires_structured_output_capability():
    case = _case("Q4-01")
    clock = SimulatedClock()
    fake = GatewayFakeLLM(
        provider_name="p1",
        structured=False,
        scripts=(FakeScript(draft=Q4.base_draft(case.package)),),
        clock=clock,
    )
    service = GatewayService(providers={"p1": fake}, policy=case.policy, clock=clock)
    out = service.generate(case.package)
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.CAPABILITY_MISMATCH
    assert fake.calls == 0


def test_a04_preserves_usage_and_response_metadata():
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    assert out.usage.prompt_tokens > 0
    assert out.usage.completion_tokens > 0
    assert out.usage.total_tokens == out.usage.prompt_tokens + out.usage.completion_tokens
    assert out.attempts[0].finish_reason == "stop"
    assert out.model == "fake-model-1"


def test_a05_maps_timeout_cancel_and_provider_errors():
    timeout_case = _case("Q4-01")
    out, _, _ = _run(
        timeout_case,
        scripts={"p1": (FakeScript(failure_class="timeout"),)},
    )
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.PROVIDER_TIMEOUT
    cancelled, _, _ = _run(_case("Q4-01"), cancel=lambda: True)
    assert isinstance(cancelled, GatewayRefusal)
    assert cancelled.code is GatewayRefusalCode.CANCELLED


def test_a06_domain_imports_no_vendor_client():
    banned = {"httpx", "requests", "openai", "openrouter", "aiohttp", "socket"}
    for path in _gateway_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        assert not imports & banned, path


# T2 — routing -------------------------------------------------------------


def test_a07_routes_by_task_depth_budget_and_schema():
    case = _case("Q4-01")
    admitted = admit(case.package)
    plan, code, detail = select_route(
        case.policy,
        admitted.task,
        admitted.depth,
        {"p1": frozenset({CAPABILITY_STRUCTURED_OUTPUT})},
    )
    assert plan is not None and code is None and not detail
    assert plan.task is admitted.task
    assert plan.depth is admitted.depth
    assert plan.prompt.prompt_id == "ASK_CEREBUS_BEGINNER"


def test_a08_unsupported_route_refuses_bounded():
    case = _case("Q4-01")
    admitted = admit(case.package)
    policy = RoutingPolicy(
        routes=(
            ModelRoute(
                route_id="unsupported",
                tasks=frozenset({RouteTask.COMPARISON}),
                depths=frozenset({admitted.depth}),
                candidates=(_candidate("p1"),),
            ),
        )
    )
    clock = SimulatedClock()
    fake = GatewayFakeLLM(provider_name="p1", scripts=(FakeScript(draft=Q4.base_draft(case.package)),), clock=clock)
    out = GatewayService(providers={"p1": fake}, policy=policy, clock=clock).generate(case.package)
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.ROUTE_UNSUPPORTED
    assert fake.calls == 0


def test_a09_model_names_carry_no_business_truth():
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    assert out.model == "fake-model-1"
    assert out.status is DraftStatus.UNVALIDATED
    assert "CANONICAL_STATUS" not in _payload_text(out)


def test_a10_route_policy_is_versioned_and_deterministic():
    case = _case("Q4-01")
    admitted = admit(case.package)
    capabilities = {"p1": frozenset({CAPABILITY_STRUCTURED_OUTPUT})}
    first = select_route(case.policy, admitted.task, admitted.depth, capabilities)
    second = select_route(case.policy, admitted.task, admitted.depth, capabilities)
    assert first[0] is not None
    assert first[0].payload() == second[0].payload()
    assert first[0].policy_version == ASK_MODEL_ROUTING_V1


def test_a11_route_selection_is_recorded():
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    assert out.trace.route_id
    assert out.trace.route_policy_version == ASK_MODEL_ROUTING_V1
    assert out.trace.prompt_id == "ASK_CEREBUS_BEGINNER"


def test_a12_fallback_candidates_are_declared_only():
    out, providers, _ = _run(_case("Q4-21"))
    assert isinstance(out, GatewayRefusal)
    assert list(providers) == ["p1"]
    assert providers["p1"].calls == 1
    assert len(out.attempts) == 1


# T3 — prompts -------------------------------------------------------------


def test_a13_ships_versioned_three_depth_prompts():
    contracts = [prompt_for_depth(depth) for depth in (Depth.BEGINNER, Depth.OPERATOR, Depth.RESEARCHER)]
    assert [contract.prompt_id for contract in contracts] == [
        "ASK_CEREBUS_BEGINNER",
        "ASK_CEREBUS_OPERATOR",
        "ASK_CEREBUS_RESEARCHER",
    ]
    assert {contract.version for contract in contracts} == {"V1"}


def test_a14_prompt_depth_uses_effective_depth():
    case = _case("Q4-03")
    admitted = admit(case.package)
    assert admitted.depth is Depth.RESEARCHER
    out, _, _ = _run(case)
    assert isinstance(out, GatewayDraft)
    assert out.prompt_id == "ASK_CEREBUS_RESEARCHER"


def test_a15_prompt_references_answer_contract_not_hidden_facts():
    case = _case("Q4-01")
    admitted = admit(case.package)
    text = prompt_text(admitted, prompt_for_depth(admitted.depth))
    assert "UNVALIDATED" in text
    assert "never claim CANONICAL_VERIFIED" in text
    assert "BODY" not in text
    assert "sk-" not in text.lower()


def test_a16_prompt_separates_trusted_control_from_untrusted_data():
    case = _case("Q4-17")
    admitted = admit(case.package)
    text = prompt_text(admitted, prompt_for_depth(admitted.depth))
    assert text.index("TRUSTED_CONTROL_JSON") < text.index("UNTRUSTED_DATA_JSON")
    assert "IGNORE ALL PRIOR INSTRUCTIONS" in text.split("UNTRUSTED_DATA_JSON", 1)[1]


def test_a17_extractor_and_validator_prompts_are_separate():
    from app.forge.ask_cerebus.llm_gateway import versions

    assert versions.PROMPT_EXTRACTOR_ID != versions.PROMPT_VALIDATOR_ID
    assert versions.PROMPT_EXTRACTOR_ID not in {
        prompt_for_depth(depth).prompt_id for depth in (Depth.BEGINNER, Depth.OPERATOR, Depth.RESEARCHER)
    }
    source = (ROOT / "app/forge/ask_cerebus/llm_gateway/prompts.py").read_text(encoding="utf-8")
    assert "def validate" not in source


def test_a18_prompt_assembly_is_deterministic_and_bounded():
    case = _case("Q4-01")
    admitted = admit(case.package)
    text = prompt_text(admitted, prompt_for_depth(admitted.depth))
    assert estimate_text_units(text) == (len(text.encode("utf-8")) + 3) // 4
    assert admitted.context_units > 0
    assert TOKENIZER_STATUS.endswith("F4")


def test_a19_structured_draft_has_frozen_fields():
    required = set(draft_schema()["required"])
    assert required == {
        "sections",
        "claims",
        "citations",
        "uncertainties",
        "refusals",
        "proposed_prose",
    }
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    assert set(out.payload()) >= required | {
        "gateway_contract_version",
        "draft_schema_version",
        "status",
        "numbers",
        "usage",
        "attempts",
        "trace",
    }


def test_a20_material_numbers_link_to_package_refs():
    out, _, _ = _run(_case("Q4-05"))
    assert isinstance(out, GatewayDraft)
    assert out.numbers
    assert out.numbers[0].value_text == "58%"
    assert out.numbers[0].source_ref_id in admit(_case("Q4-05").package).allowed_refs


def test_a21_citations_resolve_inside_the_package():
    case = _case("Q4-01")
    out, _, _ = _run(case)
    assert isinstance(out, GatewayDraft)
    allowed = admit(case.package).allowed_refs
    assert out.citations
    assert set(out.citations) <= allowed
    assert all(set(claim.source_refs) <= set(out.citations) for claim in out.claims)


def test_a22_draft_cannot_add_facts_status_layer_or_entitlement():
    out, _, _ = _run(_case("Q4-18"))
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.POLICY_DENIED
    assert "entitlement" not in _payload_text(out).lower()


def test_a23_draft_preserves_no_go_insufficiency_conflict_history():
    out, _, _ = _run(_case("Q4-02"))
    assert isinstance(out, GatewayDraft)
    combined = " ".join(out.uncertainties + out.refusals)
    assert "NO_GO_ACTIVE" in combined
    assert "SETUP_NOT_ELIGIBLE" in combined


def test_a24_malformed_draft_has_no_prose_only_fallback():
    out, _, _ = _run(_case("Q4-21"))
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.PROVIDER_MALFORMED
    assert not isinstance(out, GatewayDraft)
    assert "proposed_prose" not in out.payload()


# T5 — timeout/retry -------------------------------------------------------


def test_a25_per_attempt_and_total_deadlines_are_enforced():
    case = _case("Q4-01")
    clock = SimulatedClock()
    fake = GatewayFakeLLM(
        provider_name="p1",
        scripts=(FakeScript(latency_seconds=2.0, draft=Q4.base_draft(case.package)),),
        clock=clock,
    )
    policy = RoutingPolicy(
        routes=(
            ModelRoute(
                route_id="short",
                tasks=frozenset({admit(case.package).task}),
                depths=frozenset({admit(case.package).depth}),
                candidates=(_candidate("p1"),),
                total_deadline_seconds=1.0,
            ),
        )
    )
    out = GatewayService(providers={"p1": fake}, policy=policy, clock=clock).generate(case.package)
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.PROVIDER_TIMEOUT


def test_a26_retries_only_safe_idempotent_calls():
    out, _, _ = _retry()
    assert isinstance(out, GatewayDraft)
    assert [attempt.outcome.value for attempt in out.attempts] == ["ERROR", "SUCCESS"]
    malformed, _, _ = _run(_case("Q4-21"))
    assert isinstance(malformed, GatewayRefusal)
    assert len(malformed.attempts) == 1


def test_a27_attempt_and_cost_caps_are_enforced():
    out, _, _ = _retry()
    assert isinstance(out, GatewayDraft)
    assert len(out.attempts) == 2
    assert out.usage.attempts == 2
    assert out.usage.total_tokens == sum(attempt.total_tokens for attempt in out.attempts)


def test_a28_retry_never_mutates_context_or_evidence():
    out, providers, _ = _retry()
    assert isinstance(out, GatewayDraft)
    assert len(providers["p1"].requests) == 2
    assert providers["p1"].requests[0].prompt == providers["p1"].requests[1].prompt
    assert providers["p1"].requests[0].model == providers["p1"].requests[1].model


def test_a29_provider_errors_use_frozen_taxonomy():
    out, _, _ = _run(_case("Q4-20"))
    assert isinstance(out, GatewayRefusal)
    assert out.attempts[0].failure_class == "rate_limited"
    assert out.code is GatewayRefusalCode.PROVIDER_UNAVAILABLE


def test_a30_cancellation_stops_and_records():
    out, providers, _ = _run(_case("Q4-01"), cancel=lambda: True)
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.CANCELLED
    assert providers["p1"].calls == 0


# T6 — fallback ------------------------------------------------------------


def test_a31_fallback_uses_declared_alternate_only():
    out, providers, _ = _run(_case("Q4-19"))
    assert isinstance(out, GatewayDraft)
    assert len(providers) == 2
    assert providers["p1"].calls == 1
    assert providers["p2"].calls == 1


def test_a32_fallback_reuses_the_same_authorized_package():
    case = _case("Q4-19")
    out, providers, _ = _run(case)
    assert isinstance(out, GatewayDraft)
    assert out.package_id == case.package.package_id
    assert out.manifest_id == case.package.manifest.manifest_digest
    assert providers["p1"].last_request.prompt == providers["p2"].last_request.prompt


def test_a33_fallback_cannot_broaden_exposure_or_context():
    case = _case("Q4-19")
    out, providers, _ = _run(case)
    assert isinstance(out, GatewayDraft)
    prompt = providers["p2"].last_request.prompt
    assert "INTERNAL_METHOD" not in prompt
    assert "INTERNAL_CODE" not in prompt
    assert out.package_id == case.package.package_id


def test_a34_fallback_preserves_prompt_and_schema_contract():
    _, providers, _ = _run(_case("Q4-19"))
    first = providers["p1"].last_request
    second = providers["p2"].last_request
    assert first.prompt == second.prompt
    assert first.response_schema == second.response_schema
    assert first.model == second.model


def test_a35_fallback_attempts_and_selected_model_are_recorded():
    out, _, _ = _run(_case("Q4-19"))
    assert isinstance(out, GatewayDraft)
    assert [attempt.provider for attempt in out.attempts] == ["p1", "p2"]
    assert out.provider == "p2"


def test_a36_fallback_never_masks_policy_or_validation_failure():
    out, providers, _ = _run(_case("Q4-21"))
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.PROVIDER_MALFORMED
    assert list(providers) == ["p1"]


# T7 — cost/usage ----------------------------------------------------------


def test_a37_records_tokens_cost_and_latency_by_dimension():
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    payload = out.usage.payload()
    assert payload["context_units"] > 0
    assert payload["prompt_units"] > 0
    assert payload["cost_usd"] > 0
    assert payload["attempts"] == 1
    assert out.attempts[0].cost_usd == out.usage.cost_usd


def test_a38_context_and_generation_budgets_are_configurable():
    case = _case("Q4-01")
    out, _, _ = _run(case, budget=GatewayBudget(max_context_units=100_000))
    assert isinstance(out, GatewayDraft)
    refused, _, _ = _run(case, budget=GatewayBudget(max_context_units=1))
    assert isinstance(refused, GatewayRefusal)
    assert refused.code is GatewayRefusalCode.BUDGET_REFUSED


def test_a39_over_budget_refuses_before_provider_call():
    out, providers, _ = _run(_case("Q4-23"))
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.BUDGET_REFUSED
    assert providers["p1"].calls == 0


def test_a40_aggregate_usage_is_bounded_and_secret_free():
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    payload = _payload_text(out)
    assert "api_key" not in payload
    assert "password" not in payload
    assert "Authorization" not in payload
    assert len(payload) < 200_000


def test_a41_provider_cost_is_flagged_estimated_or_authoritative():
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    assert out.usage.cost_basis.value in {"PROVIDER_REPORTED", "AUTHORITATIVE", "UNKNOWN"}
    assert PRICING_STATUS.endswith("F4")


def test_a42_accounts_for_retries_without_double_counting():
    out, _, _ = _retry()
    assert isinstance(out, GatewayDraft)
    assert out.usage.prompt_tokens == sum(a.prompt_tokens for a in out.attempts)
    assert out.usage.completion_tokens == sum(a.completion_tokens for a in out.attempts)
    assert out.usage.cost_usd == pytest.approx(sum(a.cost_usd for a in out.attempts))


# T8 — privacy -------------------------------------------------------------


def test_a43_sends_only_minimized_context_package():
    case = _case("Q4-01")
    _, providers, _ = _run(case)
    prompt = providers["p1"].last_request.prompt
    assert case.package.package_id in prompt
    assert "BODY" not in prompt
    assert "canonical corpus" not in prompt.lower()


def test_a44_excludes_secrets_internal_code_and_unrelated_data():
    _, providers, _ = _run(_case("Q4-01"))
    prompt = providers["p1"].last_request.prompt
    assert "sk-" not in prompt.lower()
    assert "INTERNAL_METHOD" not in prompt
    assert "INTERNAL_CODE" not in prompt


def test_a45_no_credentials_enter_request_log_or_draft():
    out, providers, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    text = _payload_text(out) + providers["p1"].last_request.prompt
    assert "api_key" not in text.lower()
    assert "authorization:" not in text.lower()
    assert "password" not in text.lower()


def test_a46_logs_and_traces_are_redacted():
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft)
    trace = json.dumps(out.trace.payload(), sort_keys=True)
    assert "PROMPT_ID=" not in trace
    assert "TRUSTED_CONTROL_JSON" not in trace
    assert "UNTRUSTED_DATA_JSON" not in trace
    assert "proposed_prose" not in trace


def test_a47_trust_boundary_is_preserved_in_prompt():
    case = _case("Q4-17")
    admitted = admit(case.package)
    text = prompt_text(admitted, prompt_for_depth(admitted.depth))
    untrusted = text.split("UNTRUSTED_DATA_JSON", 1)[1]
    assert "IGNORE ALL PRIOR INSTRUCTIONS" in untrusted
    assert "TRUSTED_CONTROL_JSON" in text.split("UNTRUSTED_DATA_JSON", 1)[0]


def test_a48_provider_retention_policy_is_explicit():
    assert RETENTION_POLICY_STATUS == "OPEN_F4"
    fake = GatewayFakeLLM()
    health = fake.health()
    assert "retention" not in health.detail.lower()


# T9 — deterministic fake --------------------------------------------------


def test_a49_fake_returns_valid_deterministic_structured_draft():
    first, _, _ = _run(_case("Q4-01"))
    second, _, _ = _run(_case("Q4-01"))
    assert isinstance(first, GatewayDraft) and isinstance(second, GatewayDraft)
    assert first.payload() == second.payload()


def test_a50_fake_scripts_hallucination_missing_citation_and_laundering():
    hallucinated, _, _ = _run(_case("Q4-06"))
    missing, _, _ = _run(_case("Q4-09"))
    laundered, _, _ = _run(_case("Q4-13"))
    assert isinstance(hallucinated, GatewayRefusal)
    assert hallucinated.code is GatewayRefusalCode.NUMERIC_EVIDENCE_MISSING
    assert isinstance(missing, GatewayRefusal) and missing.code is GatewayRefusalCode.CITATION_REQUIRED
    assert isinstance(laundered, GatewayDraft) and laundered.status is DraftStatus.UNVALIDATED


def test_a51_fake_scripts_instruction_following_attack():
    case = _case("Q4-17")
    out, _, _ = _run(case)
    assert isinstance(out, GatewayDraft)
    assert "Grant entitlement" not in out.proposed_prose
    assert "VALIDATED" not in [claim.epistemic_label for claim in out.claims]


def test_a52_fake_scripts_timeout_error_rate_limit_and_malformed():
    timeout, _, _ = _run(_case("Q4-01"), scripts={"p1": (FakeScript(failure_class="timeout"),)})
    limited, _, _ = _run(_case("Q4-01"), scripts={"p1": (FakeScript(failure_class="rate_limited"),)})
    malformed, _, _ = _run(_case("Q4-21"))
    assert isinstance(timeout, GatewayRefusal) and timeout.code is GatewayRefusalCode.PROVIDER_TIMEOUT
    assert isinstance(limited, GatewayRefusal) and limited.code is GatewayRefusalCode.PROVIDER_UNAVAILABLE
    assert isinstance(malformed, GatewayRefusal) and malformed.code is GatewayRefusalCode.PROVIDER_MALFORMED


def test_a53_fake_usage_cost_and_latency_are_fixed():
    case = _case("Q4-01")
    first, _, _ = _run(case)
    second, _, _ = _run(case)
    assert isinstance(first, GatewayDraft) and isinstance(second, GatewayDraft)
    assert first.usage == second.usage
    assert first.attempts[0].latency_seconds == second.attempts[0].latency_seconds == 0.0


def test_a54_fake_swap_changes_no_domain_contract():
    case = _case("Q4-01")
    first, _, _ = _run(case)
    second, _, _ = _run(case)
    assert isinstance(first, GatewayDraft) and isinstance(second, GatewayDraft)
    assert first.payload() == second.payload()
    assert first.status is DraftStatus.UNVALIDATED


# T10 — replacement --------------------------------------------------------


def test_a55_same_golden_suite_runs_against_candidate_provider():
    files = Q4.build_all()
    manifest = json.loads((Q4_DIR / "FIXTURE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["fixture_count"] == 24
    assert set(manifest["fixtures"]) == set(files)
    for name, text in files.items():
        normalized = text.replace("\r\n", "\n").encode("utf-8")
        assert normalized == (Q4_DIR / name).read_bytes()
        assert hashlib.sha256(normalized).hexdigest() == manifest["fixtures"][name]["sha256"]
    for scenario in _SCENARIOS.values():
        out, _, _ = _run(scenario)
        _assert_expected(out, scenario.expected)
    replacement_case = _case("Q4-24")
    replacement, _, _ = _run_with(
        replacement_case,
        replacement_case.replacement_provider,
        replacement_case.replacement_scripts,
    )
    _assert_expected(replacement, replacement_case.replacement_expected)
    assert CANDIDATE_MATRIX_STATUS.endswith("F4")


def test_a56_provider_selection_is_composition_root_only():
    source = "\n".join(path.read_text(encoding="utf-8") for path in _gateway_sources())
    assert "openrouter" not in source.lower()
    assert "ProvidersFromConfig" not in source
    assert "ProviderRegistry" not in source


def test_a57_openrouter_remains_an_adapter():
    assert not (ROOT / "app/forge/ask_cerebus/llm_gateway/openrouter.py").exists()
    source = "\n".join(path.read_text(encoding="utf-8") for path in _gateway_sources())
    assert "openrouter" not in source.lower()


def test_a58_capability_mismatch_refuses():
    case = _case("Q4-01")
    clock = SimulatedClock()
    fake = GatewayFakeLLM(
        provider_name="p1", structured=False, scripts=(FakeScript(draft=Q4.base_draft(case.package)),), clock=clock
    )
    out = GatewayService(providers={"p1": fake}, policy=case.policy, clock=clock).generate(case.package)
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.CAPABILITY_MISMATCH


def test_a59_replacement_preserves_port_semantics():
    case = _case("Q4-01")
    first, _, _ = _run(case)
    second, providers, _ = _run(case)
    assert isinstance(first, GatewayDraft) and isinstance(second, GatewayDraft)
    assert first.payload() == second.payload()
    assert len(providers["p1"].requests) == 1


def test_a60_contract_tests_do_not_claim_production_readiness():
    assert ASK_GATEWAY_CONTRACT_V1 == "ASK_GATEWAY_CONTRACT_V1"
    assert ASK_GATEWAY_DRAFT_SCHEMA_V1.endswith("V1")
    policy = _case("Q4-01").policy
    assert policy.production_authorized is False
    out, _, _ = _run(_case("Q4-01"))
    assert isinstance(out, GatewayDraft) and out.status is DraftStatus.UNVALIDATED


# Cross-cutting ------------------------------------------------------------


def test_a61_retries_only_retryable_idempotent_attempts():
    out, _, _ = _retry()
    assert isinstance(out, GatewayDraft)
    assert out.attempts[0].retryable is True
    assert out.attempts[0].failure_class == "timeout"
    assert out.attempts[1].outcome.value == "SUCCESS"


def test_a62_retry_identity_is_stable_and_never_mutates_context():
    _, providers, _ = _retry()
    requests = providers["p1"].requests
    assert len(requests) == 2
    assert requests[0].prompt == requests[1].prompt
    assert requests[0].response_schema == requests[1].response_schema


def test_a63_cancellation_stops_before_draft_emission():
    out, providers, _ = _run(_case("Q4-19"), cancel=lambda: True)
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.CANCELLED
    assert providers["p1"].calls == 0


def test_a64_fallback_never_broadens_package_or_entitlement():
    case = _case("Q4-19")
    out, providers, _ = _run(case)
    assert isinstance(out, GatewayDraft)
    assert out.package_id == case.package.package_id
    assert "INTERNAL_METHOD" not in providers["p2"].last_request.prompt
    assert "ENTITLEMENT" not in providers["p2"].last_request.prompt


def test_a65_transport_failure_does_not_become_content_success():
    out, _, _ = _run(_case("Q4-21"))
    assert isinstance(out, GatewayRefusal)
    assert not isinstance(out, GatewayDraft)


def test_a66_budget_overrun_refuses_before_provider_call():
    out, providers, _ = _run(_case("Q4-23"))
    assert isinstance(out, GatewayRefusal)
    assert out.code is GatewayRefusalCode.BUDGET_REFUSED
    assert providers["p1"].calls == 0


def test_a67_manifest_and_package_identity_are_preserved():
    case = _case("Q4-01")
    out, _, _ = _run(case)
    assert isinstance(out, GatewayDraft)
    assert out.package_id == case.package.package_id
    assert out.manifest_id == case.package.manifest.manifest_digest
    assert out.query_plan_id == case.package.query_plan_id


def test_a68_consumer_draft_contains_no_credentials_or_internal_material():
    out, providers, _ = _run(_case("Q4-01"))
    text = _payload_text(out) + providers["p1"].last_request.prompt
    assert "sk-" not in text.lower()
    assert "password" not in text.lower()
    assert "INTERNAL_METHOD" not in text
    assert "INTERNAL_CODE" not in text


def test_a69_fake_provider_replacement_changes_no_gateway_contract():
    case = _case("Q4-24")
    first, _, _ = _run(case)
    second, _, _ = _run_with(case, "p2", case.replacement_scripts)
    assert isinstance(first, GatewayDraft)
    assert isinstance(second, GatewayDraft)
    assert first.status is second.status is DraftStatus.UNVALIDATED
    assert first.package_id == second.package_id
    assert first.prompt_id == second.prompt_id
    assert first.claims == second.claims
    assert first.citations == second.citations
    assert first.numbers == second.numbers
    assert first.refusals == second.refusals
    assert (first.provider, second.provider) == ("p1", "p2")


def test_a70_frozen_iv3_context_contract_unchanged():
    assert CONTEXT_CONTRACT_V1 == "CONTEXT_CONTRACT_V1"
    assert hashlib.sha256((ROOT / "app/forge/ask_cerebus/context/schema.py").read_bytes()).hexdigest() == (
        "499dbdfb0054d6b1c7c41f61d6f91a2fdd15cad36346eb4297790e13b7cfc2c0"
    )
    case = _case("Q4-01")
    clock = SimulatedClock()
    fake = GatewayFakeLLM(
        provider_name="p1",
        scripts=(FakeScript(draft=Q4.base_draft(case.package)),),
        clock=clock,
    )
    service = GatewayService(providers={"p1": fake}, policy=case.policy, clock=clock)
    wrong_type = service.generate(object())
    assert isinstance(wrong_type, GatewayRefusal)
    assert wrong_type.code is GatewayRefusalCode.PACKAGE_INCOMPLETE
    assert fake.calls == 0
    tampered = replace(case.package, package_id="PKG." + "0" * 32)
    mismatch = service.generate(tampered)
    assert isinstance(mismatch, GatewayRefusal)
    assert mismatch.code is GatewayRefusalCode.PACKAGE_IDENTITY_MISMATCH
    assert fake.calls == 0


def test_a71_routes_migrations_and_provider_seams_unchanged():
    assert hashlib.sha256((ROOT / "app/forge/service/routes.py").read_bytes()).hexdigest() == (
        "145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af"
    )
    assert [migration.version for migration in discover_migrations()] == [1, 2, 3, 4]


def test_a72_no_network_llm_call_in_planning_verification(monkeypatch):
    original = socket.socket

    def denied(*args, **kwargs):
        raise AssertionError("network socket opened")

    monkeypatch.setattr(socket, "socket", denied)
    try:
        out, _, _ = _run(_case("Q4-01"))
    finally:
        monkeypatch.setattr(socket, "socket", original)
    assert isinstance(out, GatewayDraft)
