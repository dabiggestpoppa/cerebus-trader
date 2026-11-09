"""Deterministic harness for the five-stage public chain.

``CHAIN`` runs interpreter → retrieval → context → gateway → validate.
``SEALED`` supplies a frozen package and a scripted draft straight to
``validate_answer``. Both modes use only fixture-backed fakes: no network, no
provider, no market, no wall clock.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.forge.ask_cerebus.evaluation import enums
from app.forge.ask_cerebus.evaluation.schema import (
    EvaluationCase,
    EvaluationDataset,
    EvaluationExecution,
    canonical_json,
    digest_of,
)

ROOT = Path(__file__).resolve().parents[4]
FIXTURES = ROOT / "implementation/forge/book_iv/bloc_iv_6/fixtures"


def _load(name: str, path: Path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixtures():
    return _load("iv6_fixture_builders", FIXTURES / "_builders.py")


def _draft_script(draft: Any) -> dict[str, Any]:
    return {
        "sections": [section.payload() for section in draft.sections],
        "claims": [claim.payload() for claim in draft.claims],
        "citations": list(draft.citations),
        "numbers": [number.payload() for number in draft.numbers],
        "uncertainties": list(draft.uncertainties),
        "refusals": list(draft.refusals),
        "proposed_prose": draft.proposed_prose,
    }


@dataclass(frozen=True)
class StageArtifacts:
    plan: Any = None
    bundle: Any = None
    package: Any = None
    draft: Any = None
    answer: Any = None
    gateway: Any = None
    error: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "has_plan": self.plan is not None,
            "has_bundle": self.bundle is not None,
            "has_package": self.package is not None,
            "has_draft": self.draft is not None,
            "has_answer": self.answer is not None,
            "gateway_outcome": _gateway_outcome(self.gateway),
            "error": self.error,
        }


def _gateway_outcome(gateway: Any) -> str:
    outcome = getattr(gateway, "outcome", None)
    if outcome is None:
        return ""
    return str(getattr(outcome, "value", outcome))


def _identity(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "payload"):
        return digest_of(value.payload())
    return digest_of(str(value))


def _package_id(package: Any) -> str:
    return getattr(package, "package_id", "")


def _manifest_id(package: Any) -> str:
    manifest = getattr(package, "manifest", None)
    return getattr(manifest, "manifest_digest", "")


def _answer_identity(answer: Any) -> str:
    payload = answer.payload() if hasattr(answer, "payload") else {}
    return str(payload.get("answer_id") or payload.get("record", {}).get("answer_id", ""))


def _run_sealed(case: EvaluationCase) -> StageArtifacts:
    F = fixtures()
    bundle = F.build_sealed(
        case.fixture_source, case.case_id, case.draft_variant, case.depth, case.payload_marker
    )
    from app.forge.ask_cerebus.answer.service import validate_answer

    answer = validate_answer(bundle.draft, bundle.package)
    return StageArtifacts(package=bundle.package, draft=bundle.draft, answer=answer)


def _chain_gateway(package: Any, draft: Any, *, fail: bool):
    from app.forge.ask_cerebus.llm_gateway.fake import FakeScript, GatewayFakeLLM
    from app.forge.ask_cerebus.llm_gateway.policy import ModelCandidate, ModelRoute, RoutingPolicy
    from app.forge.ask_cerebus.llm_gateway.request import admit
    from app.forge.ask_cerebus.llm_gateway.service import GatewayService
    from app.forge.providers.fakes import SimulatedClock

    admitted = admit(package)
    if not hasattr(admitted, "task"):
        return None
    policy = RoutingPolicy(
        routes=(
            ModelRoute(
                route_id=f"EV6-{admitted.task.value}-{admitted.depth.value}",
                tasks=frozenset({admitted.task}),
                depths=frozenset({admitted.depth}),
                candidates=(ModelCandidate(provider_name="p1", model="fake-model-1"),),
                local_test_mode=True,
            ),
        )
    )
    clock = SimulatedClock()
    script = FakeScript(failure_class="timeout") if fail else FakeScript(draft=_draft_script(draft))
    provider = GatewayFakeLLM(provider_name="p1", scripts=(script,), clock=clock)
    service = GatewayService(providers={"p1": provider}, policy=policy, clock=clock)
    return service.generate(package)


def _run_chain(case: EvaluationCase) -> StageArtifacts:
    F = fixtures()
    from app.forge.ask_cerebus.answer.service import validate_answer
    from app.forge.ask_cerebus.context.service import ContextPackager
    from app.forge.ask_cerebus.interpreter.interpret import interpret

    query = case.query_text
    principal, context = F.chain_credentials()
    service = F.chain_service()
    plan = interpret(query)
    bundle = service.retrieve(plan, principal, context)
    package = ContextPackager().pack(plan, bundle)
    draft = F.chain_draft(package, case.depth)
    gateway = _chain_gateway(package, draft, fail=case.draft_variant == "gateway_fail")
    if gateway is not None and not hasattr(gateway, "claims"):
        return StageArtifacts(plan=plan, bundle=bundle, package=package, gateway=gateway)
    answer = validate_answer(gateway, package)
    return StageArtifacts(
        plan=plan, bundle=bundle, package=package, draft=gateway, answer=answer, gateway=gateway
    )


def run_case(case: EvaluationCase) -> EvaluationExecution:
    try:
        artifacts = (
            _run_chain(case)
            if case.execution_mode is enums.ExecutionMode.CHAIN
            else _run_sealed(case)
        )
        error = ""
    except Exception as exc:  # failure isolation: never abort the run
        artifacts = StageArtifacts(error=f"{type(exc).__name__}: {exc}")
        error = artifacts.error

    answer = artifacts.answer
    payload = answer.payload() if hasattr(answer, "payload") else {}
    raw_outcome = payload.get("outcome")
    outcome = str(getattr(raw_outcome, "value", raw_outcome) or "ERROR")
    raw_code = payload.get("answer_refusal_code")
    refusal_code = getattr(raw_code, "value", raw_code)
    validation_codes = tuple(str(getattr(code, "value", code)) for code in payload.get("findings", ()))

    return EvaluationExecution(
        case_id=case.case_id,
        mode=case.execution_mode.value,
        plan_digest=_identity(artifacts.plan),
        bundle_digest=_identity(artifacts.bundle),
        trace_digest=_identity(getattr(artifacts.bundle, "trace", None)),
        package_id=_package_id(artifacts.package),
        manifest_id=_manifest_id(artifacts.package),
        draft_digest=_identity(artifacts.draft),
        answer_id=_answer_identity(answer),
        outcome=outcome,
        validation_codes=validation_codes,
        refusal_code=refusal_code,
        latency_ms=0.0,
        artifacts={
            "plan": artifacts.plan,
            "bundle": artifacts.bundle,
            "package": artifacts.package,
            "draft": artifacts.draft,
            "gateway": artifacts.gateway,
            "answer": answer,
            "error": error,
            "stage": artifacts.payload(),
        },
    )


def run_dataset(dataset: EvaluationDataset) -> tuple[EvaluationExecution, ...]:
    return tuple(run_case(case) for case in dataset.cases)


def run_case_twice(case: EvaluationCase) -> tuple[EvaluationExecution, EvaluationExecution]:
    """Replay support: two independent executions of one case."""

    return run_case(case), run_case(case)


def replay_equal(first: EvaluationExecution, second: EvaluationExecution) -> bool:
    return (
        first.payload() == second.payload()
        and first.answer_text() == second.answer_text()
    )


def execution_index(executions: Iterable[EvaluationExecution]) -> dict[str, EvaluationExecution]:
    return {execution.case_id: execution for execution in executions}


def assert_no_network_receipt(executions: Iterable[EvaluationExecution]) -> bool:
    """The harness holds no credentials and composes no network client."""

    for execution in executions:
        gateway = execution.artifacts.get("gateway")
        if gateway is None:
            continue
        module = type(gateway).__module__
        if "llm_gateway.fake" not in module and "llm_gateway.draft" not in module:
            return False
        if getattr(gateway, "credentials", None) not in (None, (), {}):
            return False
    return True


def corpus_script() -> str:
    """Canonical, order-stable description of every case binding."""

    module = _load("iv6_cases", FIXTURES / "cases.py")
    return canonical_json([case.payload() for case in module.cases()])


def build_fixture_dataset() -> EvaluationDataset:
    module = _load("iv6_cases", FIXTURES / "cases.py")
    return EvaluationDataset.build(module.cases())
