"""Deterministic, declared model routing.

No default production provider exists here. A route is usable only when the
caller supplies an explicit policy and the selected provider advertises the
required capability. F3 policy ownership is intentionally not claimed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.forge.ask_cerebus.interpreter.enums import Depth
from app.forge.ask_cerebus.llm_gateway.enums import GatewayRefusalCode, RouteTask
from app.forge.ask_cerebus.llm_gateway.prompts import PromptContract, prompt_for_depth
from app.forge.ask_cerebus.llm_gateway.versions import ASK_MODEL_ROUTING_V1


@dataclass(frozen=True)
class ModelCandidate:
    provider_name: str
    model: str
    structured: bool = True
    timeout_seconds: float = 10.0
    max_attempts: int = 1
    estimated_cost_usd: float = 0.0
    cost_authoritative: bool = False

    def __post_init__(self) -> None:
        if not self.provider_name or not self.model:
            raise ValueError("provider_name and model are required")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.estimated_cost_usd < 0:
            raise ValueError("estimated_cost_usd must be >= 0")


@dataclass(frozen=True)
class ModelRoute:
    route_id: str
    tasks: frozenset[RouteTask]
    depths: frozenset[Depth]
    candidates: tuple[ModelCandidate, ...]
    total_deadline_seconds: float = 30.0
    max_cost_usd: float | None = None
    local_test_mode: bool = True

    def __post_init__(self) -> None:
        if not self.route_id or not self.candidates:
            raise ValueError("route_id and at least one candidate are required")
        if self.total_deadline_seconds <= 0:
            raise ValueError("total_deadline_seconds must be > 0")
        if self.max_cost_usd is not None and self.max_cost_usd < 0:
            raise ValueError("max_cost_usd must be >= 0")


@dataclass(frozen=True)
class RoutingPolicy:
    routes: tuple[ModelRoute, ...]
    policy_version: str = ASK_MODEL_ROUTING_V1
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.routes:
            raise ValueError("a routing policy requires at least one declared route")
        ids = [route.route_id for route in self.routes]
        if len(ids) != len(set(ids)):
            raise ValueError("route ids must be unique")


@dataclass(frozen=True)
class RoutePlan:
    policy_version: str
    route_id: str
    task: RouteTask
    depth: Depth
    prompt: PromptContract
    candidates: tuple[ModelCandidate, ...]
    total_deadline_seconds: float
    max_cost_usd: float | None
    local_test_mode: bool
    production_authorized: bool

    @property
    def primary(self) -> ModelCandidate:
        return self.candidates[0]

    @property
    def alternates(self) -> tuple[ModelCandidate, ...]:
        return self.candidates[1:]

    def payload(self) -> dict[str, object]:
        return {
            "policy_version": self.policy_version,
            "route_id": self.route_id,
            "task": self.task.value,
            "depth": self.depth.value,
            "prompt_id": self.prompt.prompt_id,
            "prompt_version": self.prompt.version,
            "candidates": [
                {
                    "provider": c.provider_name,
                    "model": c.model,
                    "structured": c.structured,
                    "timeout_seconds": c.timeout_seconds,
                    "max_attempts": c.max_attempts,
                    "estimated_cost_usd": c.estimated_cost_usd,
                    "cost_authoritative": c.cost_authoritative,
                }
                for c in self.candidates
            ],
            "total_deadline_seconds": self.total_deadline_seconds,
            "max_cost_usd": self.max_cost_usd,
            "local_test_mode": self.local_test_mode,
            "production_authorized": self.production_authorized,
        }


def select_route(
    policy: RoutingPolicy,
    task: RouteTask,
    depth: Depth,
    capabilities: Mapping[str, frozenset[str]],
) -> tuple[RoutePlan | None, GatewayRefusalCode | None, str]:
    if policy.policy_version != ASK_MODEL_ROUTING_V1:
        return None, GatewayRefusalCode.ROUTE_UNSUPPORTED, "unknown routing policy version"
    for route in policy.routes:
        if task not in route.tasks or depth not in route.depths:
            continue
        if not route.local_test_mode and not policy.production_authorized:
            return (
                None,
                GatewayRefusalCode.ROUTE_UNSUPPORTED,
                "production route is not authorized",
            )
        primary = route.candidates[0]
        capabilities_for_primary = capabilities.get(primary.provider_name, frozenset())
        if primary.structured and "structured_output" not in capabilities_for_primary:
            return (
                None,
                GatewayRefusalCode.CAPABILITY_MISMATCH,
                "selected provider lacks structured-output capability",
            )
        return (
            RoutePlan(
                policy_version=policy.policy_version,
                route_id=route.route_id,
                task=task,
                depth=depth,
                prompt=prompt_for_depth(depth),
                candidates=route.candidates,
                total_deadline_seconds=route.total_deadline_seconds,
                max_cost_usd=route.max_cost_usd,
                local_test_mode=route.local_test_mode,
                production_authorized=policy.production_authorized,
            ),
            None,
            "",
        )
    return None, GatewayRefusalCode.ROUTE_UNSUPPORTED, "no declared route for task/depth"


def task_from_intent(intent: str) -> RouteTask | None:
    value = (intent or "").upper()
    return {
        "DEFINITION": RouteTask.DEFINITION,
        "MODEL_DESCRIPTION": RouteTask.DEFINITION,
        "METHODOLOGY_RESEARCH": RouteTask.RESEARCH,
        "TROUBLESHOOTING": RouteTask.DEFINITION,
        "CURRENT_STATE": RouteTask.CURRENT_STATE,
        "LEVEL_COORDINATE": RouteTask.CURRENT_STATE,
        "SETUP_CONTEXT": RouteTask.SETUP_CONTEXT,
        "STATISTIC_EVIDENCE": RouteTask.STATISTIC_EVIDENCE,
        "COMPARISON": RouteTask.COMPARISON,
        "HISTORICAL_LINEAGE": RouteTask.HISTORICAL,
        "GENERAL_MARKET_KNOWLEDGE": RouteTask.GENERAL,
    }.get(value)


__all__ = [
    "ModelCandidate",
    "ModelRoute",
    "RoutingPolicy",
    "RoutePlan",
    "select_route",
    "task_from_intent",
]
