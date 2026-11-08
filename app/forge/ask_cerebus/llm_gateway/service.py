"""Public IV.4 gateway entry point.

The service composes the frozen Book II LLM port. It does not retrieve, build
authorization, validate facts, or create an answer authority.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Callable, Mapping

from app.forge.ask_cerebus.llm_gateway.budget import (
    GatewayBudget,
    context_units,
    estimate_text_units,
)
from app.forge.ask_cerebus.llm_gateway.draft import (
    GatewayDraft,
    GatewayRefusal,
    build_trace,
    draft_schema,
    parse_draft,
)
from app.forge.ask_cerebus.llm_gateway.enums import (
    AttemptOutcome,
    CostBasis,
    GatewayOutcome,
    GatewayRefusalCode,
)
from app.forge.ask_cerebus.llm_gateway.policy import (
    RoutePlan,
    RoutingPolicy,
    select_route,
)
from app.forge.ask_cerebus.llm_gateway.request import (
    Admission,
    AdmissionFailure,
    admit,
    attempt_identity,
    build_request,
    prompt_text,
)
from app.forge.ask_cerebus.llm_gateway.retry import (
    is_retryable,
    refusal_for_error,
)
from app.forge.ask_cerebus.llm_gateway.trace import AttemptTrace, aggregate_usage
from app.forge.providers.errors import ProviderCancelledError, ProviderError
from app.forge.providers.fakes import SimulatedClock
from app.forge.providers.llm import CAPABILITY_STRUCTURED_OUTPUT, LLMProvider


CancelToken = Callable[[], bool]


class GatewayService:
    """Deterministic gateway over caller-supplied providers and route policy."""

    def __init__(
        self,
        *,
        providers: Mapping[str, LLMProvider],
        policy: RoutingPolicy,
        clock: SimulatedClock | None = None,
    ) -> None:
        self._providers = dict(providers)
        self._policy = policy
        self._clock = clock or SimulatedClock()

    @property
    def policy(self) -> RoutingPolicy:
        return self._policy

    def _capabilities(self) -> dict[str, frozenset[str]]:
        out: dict[str, frozenset[str]] = {}
        for name, provider in self._providers.items():
            try:
                out[name] = provider.capabilities()
            except Exception:
                out[name] = frozenset()
        return out

    @staticmethod
    def _cancelled(cancel: CancelToken | None) -> bool:
        try:
            return bool(cancel and cancel())
        except Exception:
            return True

    def _route(self, admission: Admission) -> tuple[RoutePlan | None, GatewayRefusal | None]:
        plan, code, detail = select_route(
            self._policy,
            admission.task,
            admission.depth,
            self._capabilities(),
        )
        if plan is None:
            return None, self._refusal(
                code or GatewayRefusalCode.ROUTE_UNSUPPORTED,
                detail,
                admission,
                outcome=GatewayOutcome.REFUSED,
            )
        return plan, None

    def generate(
        self,
        package: object,
        *,
        budget: GatewayBudget | None = None,
        cancel: CancelToken | None = None,
    ) -> GatewayDraft | GatewayRefusal:
        budget = budget or GatewayBudget()
        admitted = admit(package)
        if isinstance(admitted, AdmissionFailure):
            return self._admission_refusal(admitted)
        admission = admitted
        plan, refusal = self._route(admission)
        if refusal is not None or plan is None:
            return refusal or self._refusal(
                GatewayRefusalCode.ROUTE_UNSUPPORTED,
                "no declared route",
                admission,
            )

        prompt = prompt_text(admission, plan.prompt)
        prompt_units = estimate_text_units(prompt)
        admission = replace(admission, prompt_units=prompt_units)
        pre = self._precall_budget(admission, plan, budget)
        if pre is not None:
            return pre

        request = build_request(
            admission,
            plan.prompt,
            model=plan.primary.model,
            response_schema=draft_schema(),
        )
        attempts: list[AttemptTrace] = []
        started = self._clock.now()
        deadline = plan.total_deadline_seconds
        if budget.max_latency_seconds is not None:
            deadline = min(deadline, budget.max_latency_seconds)
        if deadline <= 0:
            return self._refusal(
                GatewayRefusalCode.BUDGET_REFUSED,
                "latency budget leaves no callable deadline",
                admission,
                plan,
                attempts=tuple(attempts),
            )

        last_code = GatewayRefusalCode.PROVIDER_UNAVAILABLE
        last_detail = "provider unavailable"
        global_attempt_cap = budget.max_attempts

        for candidate_index, candidate in enumerate(plan.candidates):
            provider = self._providers.get(candidate.provider_name)
            if provider is None:
                return self._refusal(
                    GatewayRefusalCode.PROVIDER_NOT_CONFIGURED,
                    "declared provider is not wired",
                    admission,
                    plan,
                    attempts=tuple(attempts),
                )
            caps = self._capabilities().get(candidate.provider_name, frozenset())
            if candidate.structured and CAPABILITY_STRUCTURED_OUTPUT not in caps:
                return self._refusal(
                    GatewayRefusalCode.CAPABILITY_MISMATCH,
                    "provider does not support structured output",
                    admission,
                    plan,
                    attempts=tuple(attempts),
                )
            if global_attempt_cap is not None:
                attempts_left = global_attempt_cap - len(attempts)
                if attempts_left <= 0:
                    break
                per_candidate_attempts = min(candidate.max_attempts, attempts_left)
            else:
                per_candidate_attempts = candidate.max_attempts

            retryable_exhausted = False
            for attempt_index in range(per_candidate_attempts):
                if self._cancelled(cancel):
                    return self._refusal(
                        GatewayRefusalCode.CANCELLED,
                        "gateway cancelled before provider call",
                        admission,
                        plan,
                        attempts=tuple(attempts),
                        outcome=GatewayOutcome.CANCELLED,
                    )
                elapsed = self._clock.now() - started
                remaining = deadline - elapsed
                if remaining <= 0:
                    return self._refusal(
                        GatewayRefusalCode.PROVIDER_TIMEOUT,
                        "total gateway deadline exceeded",
                        admission,
                        plan,
                        attempts=tuple(attempts),
                    )
                timeout = min(candidate.timeout_seconds, remaining)
                id_ = attempt_identity(
                    package_id=admission.package.package_id,
                    manifest_id=admission.package.manifest.manifest_digest,
                    policy_version=plan.policy_version,
                    route_id=plan.route_id,
                    prompt_id=plan.prompt.prompt_id,
                    prompt_version=plan.prompt.version,
                    provider=candidate.provider_name,
                    model=candidate.model,
                    attempt=len(attempts) + 1,
                )
                before = self._clock.now()
                try:
                    response = provider.generate(
                        request,
                        timeout_seconds=timeout,
                        cancel=cancel,
                    )
                except ProviderCancelledError:
                    attempts.append(
                        AttemptTrace(
                            attempt=len(attempts) + 1,
                            attempt_id=id_,
                            provider=candidate.provider_name,
                            model=candidate.model,
                            outcome=AttemptOutcome.CANCELLED,
                            timeout_seconds=timeout,
                            latency_seconds=round(self._clock.now() - before, 12),
                        )
                    )
                    return self._refusal(
                        GatewayRefusalCode.CANCELLED,
                        "provider call cancelled",
                        admission,
                        plan,
                        attempts=tuple(attempts),
                        outcome=GatewayOutcome.CANCELLED,
                    )
                except ProviderError as exc:
                    latency = round(self._clock.now() - before, 12)
                    attempts.append(
                        AttemptTrace(
                            attempt=len(attempts) + 1,
                            attempt_id=id_,
                            provider=candidate.provider_name,
                            model=candidate.model,
                            outcome=AttemptOutcome.ERROR,
                            timeout_seconds=timeout,
                            latency_seconds=latency,
                            failure_class=exc.failure_class,
                            retry_after_seconds=exc.retry_after_seconds,
                            retryable=exc.retryable,
                        )
                    )
                    last_code = refusal_for_error(exc)
                    last_detail = self._safe_error_detail(exc)
                    if is_retryable(exc):
                        retryable_exhausted = True
                        if attempt_index + 1 < per_candidate_attempts:
                            continue
                    else:
                        return self._refusal(
                            last_code,
                            last_detail,
                            admission,
                            plan,
                            attempts=tuple(attempts),
                        )
                    break
                except Exception:
                    returns = self._clock.now() - before
                    attempts.append(
                        AttemptTrace(
                            attempt=len(attempts) + 1,
                            attempt_id=id_,
                            provider=candidate.provider_name,
                            model=candidate.model,
                            outcome=AttemptOutcome.ERROR,
                            timeout_seconds=timeout,
                            latency_seconds=round(returns, 12),
                            failure_class="unknown",
                        )
                    )
                    return self._refusal(
                        GatewayRefusalCode.PROVIDER_ERROR,
                        "provider failure was not classifiable",
                        admission,
                        plan,
                        attempts=tuple(attempts),
                    )

                latency = round(self._clock.now() - before, 12)
                cost_basis = (
                    CostBasis.AUTHORITATIVE
                    if candidate.cost_authoritative
                    else CostBasis.PROVIDER_REPORTED
                )
                attempts.append(
                    AttemptTrace(
                        attempt=len(attempts) + 1,
                        attempt_id=id_,
                        provider=candidate.provider_name,
                        model=candidate.model,
                        outcome=AttemptOutcome.SUCCESS,
                        timeout_seconds=timeout,
                        latency_seconds=latency,
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens,
                        cost_usd=response.usage.cost_usd,
                        cost_basis=cost_basis,
                        finish_reason=response.finish_reason,
                    )
                )
                usage = aggregate_usage(
                    tuple(attempts),
                    context_units=admission.context_units,
                    prompt_units=prompt_units,
                )
                budget_failure = self._postcall_budget(
                    attempts, usage, admission, plan, budget, started
                )
                if budget_failure is not None:
                    return budget_failure
                parsed, failure = parse_draft(response.structured, admission)
                if failure is not None or parsed is None:
                    assert failure is not None
                    return self._refusal(
                        failure.code,
                        failure.detail,
                        admission,
                        plan,
                        attempts=tuple(attempts),
                    )
                trace = build_trace(
                    route_policy_version=plan.policy_version,
                    route_id=plan.route_id,
                    package_id=admission.package.package_id,
                    manifest_id=admission.package.manifest.manifest_digest,
                    query_plan_id=admission.package.query_plan_id,
                    prompt_id=plan.prompt.prompt_id,
                    prompt_version=plan.prompt.version,
                    provider=candidate.provider_name,
                    model=candidate.model,
                    outcome=GatewayOutcome.DRAFT,
                    attempts=tuple(attempts),
                )
                return GatewayDraft(
                    package_id=admission.package.package_id,
                    manifest_id=admission.package.manifest.manifest_digest,
                    query_plan_id=admission.package.query_plan_id,
                    route_policy_version=plan.policy_version,
                    route_id=plan.route_id,
                    prompt_id=plan.prompt.prompt_id,
                    prompt_version=plan.prompt.version,
                    depth=admission.depth.value,
                    provider=candidate.provider_name,
                    model=candidate.model,
                    sections=parsed["sections"],
                    claims=parsed["claims"],
                    citations=parsed["citations"],
                    numbers=parsed["numbers"],
                    uncertainties=parsed["uncertainties"],
                    refusals=parsed["refusals"],
                    proposed_prose=parsed["proposed_prose"],
                    usage=usage,
                    attempts=tuple(attempts),
                    trace=trace,
                )

            if retryable_exhausted and candidate_index + 1 < len(plan.candidates):
                continue
            if candidate_index + 1 < len(plan.candidates):
                # A non-retryable failure must not be hidden by fallback.
                break
        return self._refusal(
            last_code,
            last_detail,
            admission,
            plan,
            attempts=tuple(attempts),
        )

    def _precall_budget(
        self,
        admission: Admission,
        plan: RoutePlan,
        budget: GatewayBudget,
    ) -> GatewayRefusal | None:
        required = admission.context_units + admission.prompt_units
        if budget.max_context_units is not None and required > budget.max_context_units:
            return self._refusal(
                GatewayRefusalCode.BUDGET_REFUSED,
                "context budget would be exceeded before generation",
                admission,
                plan,
                prompt_units=admission.prompt_units,
            )
        cap = budget.max_cost_usd
        if cap is None:
            cap = plan.max_cost_usd
        if cap is not None:
            estimated = sum(
                candidate.estimated_cost_usd * candidate.max_attempts
                for candidate in plan.candidates
            )
            authoritative = all(c.cost_authoritative for c in plan.candidates)
            if estimated > cap:
                return self._refusal(
                    GatewayRefusalCode.BUDGET_REFUSED,
                    "declared route cost estimate exceeds the authorized cap",
                    admission,
                    plan,
                    prompt_units=admission.prompt_units,
                )
            if not authoritative and not budget.allow_estimated_cost:
                return self._refusal(
                    GatewayRefusalCode.BUDGET_REFUSED,
                    "cost cannot be authoritatively bounded; local estimate not authorized",
                    admission,
                    plan,
                    prompt_units=admission.prompt_units,
                )
        return None

    def _postcall_budget(
        self,
        attempts: list[AttemptTrace],
        usage: object,
        admission: Admission,
        plan: RoutePlan,
        budget: GatewayBudget,
        started: float,
    ) -> GatewayRefusal | None:
        usage_total = getattr(usage, "completion_tokens", 0)
        if (
            budget.max_generation_units is not None
            and usage_total > budget.max_generation_units
        ):
            return self._refusal(
                GatewayRefusalCode.BUDGET_REFUSED,
                "completion budget exceeded",
                admission,
                plan,
                attempts=tuple(attempts),
                prompt_units=admission.prompt_units,
            )
        if budget.max_cost_usd is not None:
            cost = sum(attempt.cost_usd for attempt in attempts)
            if cost > budget.max_cost_usd + 1e-12:
                return self._refusal(
                    GatewayRefusalCode.BUDGET_REFUSED,
                    "provider-reported cost exceeds the authorized cap",
                    admission,
                    plan,
                    attempts=tuple(attempts),
                    prompt_units=admission.prompt_units,
                )
        if budget.max_latency_seconds is not None:
            if self._clock.now() - started > budget.max_latency_seconds:
                return self._refusal(
                    GatewayRefusalCode.BUDGET_REFUSED,
                    "latency budget exceeded",
                    admission,
                    plan,
                    attempts=tuple(attempts),
                    prompt_units=admission.prompt_units,
                )
        return None

    def _refusal(
        self,
        code: GatewayRefusalCode,
        detail: str,
        admission: Admission,
        plan: RoutePlan | None = None,
        *,
        attempts: tuple[AttemptTrace, ...] = (),
        prompt_units: int = 0,
        outcome: GatewayOutcome = GatewayOutcome.REFUSED,
    ) -> GatewayRefusal:
        usage = aggregate_usage(
            attempts,
            context_units=admission.context_units,
            prompt_units=prompt_units,
        )
        provider = plan.primary.provider_name if plan else ""
        model = plan.primary.model if plan else ""
        route_policy_version = plan.policy_version if plan else ""
        route_id = plan.route_id if plan else ""
        prompt_id = plan.prompt.prompt_id if plan else ""
        prompt_version = plan.prompt.version if plan else ""
        trace = build_trace(
            route_policy_version=route_policy_version,
            route_id=route_id,
            package_id=admission.package.package_id,
            manifest_id=admission.package.manifest.manifest_digest,
            query_plan_id=admission.package.query_plan_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            provider=provider,
            model=model,
            outcome=outcome,
            attempts=attempts,
            refusal_code=code,
        )
        return GatewayRefusal(
            outcome=outcome,
            code=code,
            detail=detail,
            package_id=admission.package.package_id,
            manifest_id=admission.package.manifest.manifest_digest,
            query_plan_id=admission.package.query_plan_id,
            route_policy_version=route_policy_version,
            route_id=route_id,
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            depth=admission.depth.value,
            provider=provider,
            model=model,
            usage=usage,
            attempts=attempts,
            trace=trace,
        )

    def _admission_refusal(self, failure: AdmissionFailure) -> GatewayRefusal:
        usage = aggregate_usage((), context_units=0, prompt_units=0)
        trace = build_trace(
            route_policy_version="",
            route_id="",
            package_id=failure.package_id,
            manifest_id=failure.manifest_id,
            query_plan_id=failure.query_plan_id,
            prompt_id="",
            prompt_version="",
            provider="",
            model="",
            outcome=GatewayOutcome.REFUSED,
            attempts=(),
            refusal_code=failure.code,
        )
        return GatewayRefusal(
            outcome=GatewayOutcome.REFUSED,
            code=failure.code,
            detail=failure.detail,
            package_id=failure.package_id,
            manifest_id=failure.manifest_id,
            query_plan_id=failure.query_plan_id,
            route_policy_version="",
            route_id="",
            prompt_id="",
            prompt_version="",
            depth="",
            provider="",
            model="",
            usage=usage,
            attempts=(),
            trace=trace,
        )

    @staticmethod
    def _safe_error_detail(error: ProviderError) -> str:
        if error.failure_class == "timeout":
            return "provider call exceeded timeout"
        if error.failure_class == "rate_limited":
            return "provider rate limited the request"
        if error.failure_class == "unavailable":
            return "provider unavailable"
        if error.failure_class == "malformed_response":
            return "provider returned malformed output"
        return "provider call failed"


__all__ = ["GatewayService"]
