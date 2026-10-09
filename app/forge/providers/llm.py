"""LLM provider port (Book II / Bloc II.5, Ch II.5.2).

Transport/provider abstraction only:

- generate
- optional structured output capability
- model identifier
- usage/cost metadata
- timeout/cancel
- normalized errors

Prompt/retrieval intelligence belongs to Book IV — this module deliberately
contains no prompt assembly, no retrieval, no conversation state.

The concrete OpenRouter adapter is Book IV scope and does NOT exist at II.5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol, runtime_checkable

from app.forge.providers.doctrine import ProviderHealth

# Caller-supplied cancellation predicate: return True to cancel. Cancellation
# raises ProviderCancelledError (control flow, outside the failure taxonomy).
CancelToken = Callable[[], bool]

# Capability vocabulary advertised by LLMProvider.capabilities().
CAPABILITY_STRUCTURED_OUTPUT = "structured_output"


@dataclass(frozen=True)
class LLMRequest:
    """Transport-only generate request. No prompt template lives here."""

    prompt: str
    model: str = "unknown"
    response_schema: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LLMUsage:
    """Usage/cost metadata (deterministic at the fake; honest at adapters)."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    usage: LLMUsage
    structured: Mapping[str, Any] | None = None
    finish_reason: str = "stop"


@runtime_checkable
class LLMProvider(Protocol):
    """The frozen II.5 LLM port."""

    def generate(
        self,
        request: LLMRequest,
        *,
        timeout_seconds: float,
        cancel: CancelToken | None = None,
    ) -> LLMResponse:
        """One completion attempt. Never retries, never swallows failures."""
        ...

    def capabilities(self) -> frozenset[str]:
        """Optional capabilities, e.g. structured_output (discovery, not guess)."""
        ...

    def health(self) -> ProviderHealth:
        """Pure health answer; never a network call by itself."""
        ...
