"""Declared-alternate selection. This is not a retrieval or policy engine."""

from __future__ import annotations

from app.forge.ask_cerebus.llm_gateway.policy import ModelCandidate, RoutePlan


def alternates_after(plan: RoutePlan, index: int) -> tuple[ModelCandidate, ...]:
    if index < 0:
        return ()
    return plan.candidates[index + 1 :]


def has_declared_alternate(plan: RoutePlan, index: int) -> bool:
    return bool(alternates_after(plan, index))


__all__ = ["alternates_after", "has_declared_alternate"]
