"""Explicit context, generation, latency and cost budgets for IV.4."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class GatewayBudget:
    """Caller-owned limits. A production USD cap is not inferred from a guess."""

    max_context_units: int | None = None
    max_generation_units: int | None = None
    max_cost_usd: float | None = None
    max_latency_seconds: float | None = None
    max_attempts: int | None = None
    allow_estimated_cost: bool = False

    def __post_init__(self) -> None:
        for name in ("max_context_units", "max_generation_units", "max_attempts"):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise ValueError(f"{name} must be >= 1")
        for name in ("max_cost_usd", "max_latency_seconds"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be >= 0")


def estimate_text_units(text: str) -> int:
    """The versioned IV.3 estimator, never a provider tokenizer claim."""

    return math.ceil(len(text.encode("utf-8")) / 4)


def context_units(package: object) -> int:
    accounting = getattr(package, "token_accounting", None)
    used = getattr(accounting, "used_units", None)
    if isinstance(used, int) and used >= 0:
        return used
    total = 0
    for section in getattr(package, "sections", ()):
        for item in getattr(section, "items", ()):
            total += int(getattr(item, "token_units", 0) or 0)
    return total


def request_units(package_units: int, prompt_text: str) -> int:
    return package_units + estimate_text_units(prompt_text)


__all__ = ["GatewayBudget", "estimate_text_units", "context_units", "request_units"]
