"""Deterministic fake LLM for IV.4 tests. No network, no randomness."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from app.forge.ask_cerebus.llm_gateway.enums import CostBasis
from app.forge.providers.doctrine import ProviderHealth
from app.forge.providers.errors import (
    ERROR_BY_CLASS,
    ProviderCancelledError,
    ProviderInvalidRequestError,
    ProviderTimeoutError,
)
from app.forge.providers.fakes import SimulatedClock
from app.forge.providers.llm import (
    CAPABILITY_STRUCTURED_OUTPUT,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)


@dataclass(frozen=True)
class FakeScript:
    draft: Mapping[str, Any] | None = None
    failure_class: str | None = None
    latency_seconds: float = 0.0
    malformed: bool = False
    cancel: bool = False
    rate_limit_retry_after: float = 1.0
    cost_usd: float | None = None
    finish_reason: str = "stop"


class GatewayFakeLLM:
    """Scripted provider that satisfies the frozen Book II LLMProvider port."""

    provider_type = "llm"

    def __init__(
        self,
        *,
        provider_name: str = "fake-primary",
        model: str = "fake-model-1",
        scripts: tuple[FakeScript, ...] = (),
        structured: bool = True,
        clock: SimulatedClock | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.model = model
        self._scripts = tuple(scripts) or (FakeScript(draft={}),)
        self._structured = structured
        self.clock = clock or SimulatedClock()
        self.calls = 0
        self.requests: list[LLMRequest] = []
        self.last_request: LLMRequest | None = None

    def capabilities(self) -> frozenset[str]:
        return (
            frozenset({CAPABILITY_STRUCTURED_OUTPUT})
            if self._structured
            else frozenset()
        )

    def health(self) -> ProviderHealth:
        scripted = self._scripts[min(self.calls, len(self._scripts) - 1)]
        return ProviderHealth(
            provider_type=self.provider_type,
            provider_name=self.provider_name,
            status="unavailable" if scripted.failure_class else "healthy",
            detail="deterministic scripted fake",
        )

    def _script(self) -> FakeScript:
        index = min(max(self.calls - 1, 0), len(self._scripts) - 1)
        return self._scripts[index]

    def generate(
        self,
        request: LLMRequest,
        *,
        timeout_seconds: float,
        cancel: Any = None,
    ) -> LLMResponse:
        self.calls += 1
        self.requests.append(request)
        self.last_request = request
        if timeout_seconds <= 0:
            raise ProviderInvalidRequestError(
                "timeout_seconds must be > 0",
                provider_type=self.provider_type,
                provider_name=self.provider_name,
            )
        if self._script().cancel or (cancel is not None and cancel()):
            raise ProviderCancelledError(
                "call cancelled by caller",
                provider_type=self.provider_type,
                provider_name=self.provider_name,
            )
        script = self._script()
        if script.latency_seconds:
            self.clock.advance(script.latency_seconds)
            if script.latency_seconds > timeout_seconds:
                raise ProviderTimeoutError(
                    "provider call exceeded timeout",
                    provider_type=self.provider_type,
                    provider_name=self.provider_name,
                )
        if script.failure_class:
            error_cls = ERROR_BY_CLASS[script.failure_class]
            kwargs: dict[str, Any] = {}
            if script.failure_class == "rate_limited":
                kwargs["retry_after_seconds"] = script.rate_limit_retry_after
            raise error_cls(
                "provider unavailable"
                if script.failure_class in {"unavailable", "rate_limited"}
                else "provider call failed",
                provider_type=self.provider_type,
                provider_name=self.provider_name,
                **kwargs,
            )
        if script.malformed:
            text = "not-a-structured-draft"
            structured = None
        else:
            value = copy.deepcopy(dict(script.draft or {}))
            text = json.dumps(value, sort_keys=True, separators=(",", ":"))
            structured = value
        prompt_tokens = max(1, len(request.prompt.encode("utf-8")) // 4)
        completion_tokens = max(1, len(text.encode("utf-8")) // 4)
        total_tokens = prompt_tokens + completion_tokens
        cost = (
            script.cost_usd
            if script.cost_usd is not None
            else round(total_tokens * 0.002 / 1000.0, 8)
        )
        return LLMResponse(
            text=text,
            model=request.model,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_usd=cost,
            ),
            structured=structured,
            finish_reason=script.finish_reason,
        )


def script_digest(script: FakeScript) -> str:
    value = {
        "draft": script.draft,
        "failure_class": script.failure_class,
        "latency_seconds": script.latency_seconds,
        "malformed": script.malformed,
        "cancel": script.cancel,
        "rate_limit_retry_after": script.rate_limit_retry_after,
        "cost_usd": script.cost_usd,
        "finish_reason": script.finish_reason,
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
    ).hexdigest()


__all__ = ["FakeScript", "GatewayFakeLLM", "script_digest", "CostBasis"]
