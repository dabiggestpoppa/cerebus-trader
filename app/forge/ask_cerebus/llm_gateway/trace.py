"""Deterministic, exposure-safe attempt and gateway traces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.forge.ask_cerebus.llm_gateway.enums import AttemptOutcome, CostBasis
from app.forge.ask_cerebus.llm_gateway.versions import ASK_GATEWAY_CONTRACT_V1


@dataclass(frozen=True)
class AttemptTrace:
    attempt: int
    attempt_id: str
    provider: str
    model: str
    outcome: AttemptOutcome
    timeout_seconds: float
    latency_seconds: float = 0.0
    failure_class: str | None = None
    retry_after_seconds: float | None = None
    retryable: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    cost_basis: CostBasis = CostBasis.UNKNOWN
    finish_reason: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "attempt_id": self.attempt_id,
            "provider": self.provider,
            "model": self.model,
            "outcome": self.outcome.value,
            "timeout_seconds": self.timeout_seconds,
            "latency_seconds": self.latency_seconds,
            "failure_class": self.failure_class,
            "retry_after_seconds": self.retry_after_seconds,
            "retryable": self.retryable,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "cost_basis": self.cost_basis.value,
            "finish_reason": self.finish_reason,
        }


@dataclass(frozen=True)
class UsageAccounting:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    cost_basis: CostBasis = CostBasis.UNKNOWN
    context_units: int = 0
    prompt_units: int = 0
    latency_seconds: float = 0.0
    attempts: int = 0

    def payload(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "cost_basis": self.cost_basis.value,
            "context_units": self.context_units,
            "prompt_units": self.prompt_units,
            "latency_seconds": self.latency_seconds,
            "attempts": self.attempts,
        }


@dataclass(frozen=True)
class GatewayTrace:
    contract_version: str
    route_policy_version: str
    route_id: str
    package_id: str
    manifest_id: str
    query_plan_id: str
    prompt_id: str
    prompt_version: str
    provider: str
    model: str
    outcome: str
    attempts: tuple[AttemptTrace, ...] = ()
    refusal_code: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version or ASK_GATEWAY_CONTRACT_V1,
            "route_policy_version": self.route_policy_version,
            "route_id": self.route_id,
            "package_id": self.package_id,
            "manifest_id": self.manifest_id,
            "query_plan_id": self.query_plan_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "provider": self.provider,
            "model": self.model,
            "outcome": self.outcome,
            "attempts": [attempt.payload() for attempt in self.attempts],
            "refusal_code": self.refusal_code,
        }


def aggregate_usage(attempts: tuple[AttemptTrace, ...], *, context_units: int, prompt_units: int) -> UsageAccounting:
    prompt_tokens = sum(a.prompt_tokens for a in attempts)
    completion_tokens = sum(a.completion_tokens for a in attempts)
    total_tokens = sum(a.total_tokens for a in attempts)
    cost = round(sum(a.cost_usd for a in attempts), 12)
    bases = {a.cost_basis for a in attempts if a.outcome is AttemptOutcome.SUCCESS}
    if not bases:
        basis = CostBasis.UNKNOWN
    elif len(bases) == 1:
        basis = next(iter(bases))
    else:
        basis = CostBasis.PROVIDER_REPORTED
    return UsageAccounting(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_usd=cost,
        cost_basis=basis,
        context_units=context_units,
        prompt_units=prompt_units,
        latency_seconds=round(sum(a.latency_seconds for a in attempts), 12),
        attempts=len(attempts),
    )


__all__ = [
    "AttemptTrace",
    "UsageAccounting",
    "GatewayTrace",
    "aggregate_usage",
]
