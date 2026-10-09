"""Cost/usage ledger (Book II / Bloc II.6, Ch II.6.9).

Ch II.6.9: record LLM/provider usage enough for later cost controls —
request, provider/model, input/output usage IF SUPPLIED, normalized cost IF
KNOWN, latency, success.

Laws:

- Partial data stays partial: unsupplied usage/cost fields are None, never
  fabricated. No financial accounting claims (totals, balances, invoices)
  exist here — provider data only supports what it actually supports.
- Records are ids-and-numbers only; no prompts, no completions, no payloads.
- Bounded append-only trail (oldest evicted, order preserved).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.forge.observability.audit import BoundedAuditTrail, DEFAULT_AUDIT_CAPACITY

MAX_REASONABLE_TOKENS = 100_000_000
MAX_NORMALIZED_COST = 1_000_000.0


@dataclass(frozen=True)
class UsageRecord:
    """One provider/LLM usage observation (Ch II.6.9 field set)."""

    request_id: str
    provider_type: str
    provider_name: str
    model_id: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    normalized_cost: float | None = None
    latency_ms: float | None = None
    success: bool = True
    at: str = ""

    def __post_init__(self) -> None:
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, int) or value < 0:
                    raise ValueError(f"{name} must be a non-negative int")
                if value > MAX_REASONABLE_TOKENS:
                    raise ValueError(f"{name} exceeds sanity bound")
        if self.normalized_cost is not None:
            if self.normalized_cost < 0:
                raise ValueError("normalized_cost must be >= 0")
            if self.normalized_cost > MAX_NORMALIZED_COST:
                raise ValueError("normalized_cost exceeds sanity bound")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "usage",
            "request_id": self.request_id,
            "provider_type": self.provider_type,
            "provider_name": self.provider_name,
            "model_id": self.model_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "normalized_cost": self.normalized_cost,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "at": self.at,
        }


class UsageLedger:
    """Bounded append-only usage ledger."""

    def __init__(self, capacity: int = DEFAULT_AUDIT_CAPACITY) -> None:
        self._trail: BoundedAuditTrail = BoundedAuditTrail(capacity)

    def append(self, record: UsageRecord) -> None:
        self._trail.append(record)

    def records(self) -> tuple[UsageRecord, ...]:
        return tuple(self._trail.records())

    def __len__(self) -> int:
        return len(self._trail)


__all__ = [
    "MAX_NORMALIZED_COST",
    "MAX_REASONABLE_TOKENS",
    "UsageLedger",
    "UsageRecord",
]
