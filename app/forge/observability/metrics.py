"""Foundation metrics (Book II / Bloc II.6, Ch II.6.4).

Ch II.6.4 freezes the foundation metric list:
request rate/errors/latency, DB latency/pool, policy allow/deny counts, auth
failures, retrieval counts, provider latency/error/rate-limit, LLM
token/cost metadata, commerce event processing, job lag/failure.

This module is a deterministic in-process registry — no vendor, no push, no
network. Metrics are counters, gauges and bounded latency samples; a
`snapshot()` is a plain sorted dict, safe for diagnostics.

Metrics describe what happened. They grant nothing, mutate nothing and are
never an input to policy or canonical writes.
"""

from __future__ import annotations

from typing import Any

# Frozen metric names (Ch II.6.4), test-enforced.
COUNTER_METRICS: tuple[str, ...] = (
    "requests_total",
    "request_errors_total",
    "policy_allow_total",
    "policy_deny_total",
    "auth_failures_total",
    "retrieval_objects_total",
    "provider_errors_total",
    "provider_rate_limited_total",
    "commerce_events_total",
    "job_failures_total",
)
GAUGE_METRICS: tuple[str, ...] = (
    "db_pool_in_use",
)
HISTOGRAM_METRICS: tuple[str, ...] = (
    "request_latency_ms",
    "db_latency_ms",
    "provider_latency_ms",
    "job_lag_ms",
)
# LLM token/cost metadata (Ch II.6.9 feeds these).
LLM_TOKEN_METRICS: tuple[str, ...] = (
    "llm_input_tokens_total",
    "llm_output_tokens_total",
)
LLM_COST_METRIC = "llm_cost_normalized_total"

ALL_COUNTERS: tuple[str, ...] = COUNTER_METRICS + LLM_TOKEN_METRICS
ALL_GAUGES: tuple[str, ...] = GAUGE_METRICS
ALL_HISTOGRAMS: tuple[str, ...] = HISTOGRAM_METRICS

# Bounded latency sample memory (deterministic ring).
MAX_HISTOGRAM_SAMPLES = 256


class MetricsRegistry:
    """Deterministic in-process metric registry (fail-closed on unknowns)."""

    def __init__(self) -> None:
        self._counters: dict[str, float] = {name: 0.0 for name in ALL_COUNTERS}
        self._counters[LLM_COST_METRIC] = 0.0
        self._gauges: dict[str, float] = {name: 0.0 for name in ALL_GAUGES}
        self._histograms: dict[str, list[float]] = {
            name: [] for name in ALL_HISTOGRAMS
        }

    def increment(self, name: str, value: float = 1.0) -> None:
        if name not in self._counters:
            raise ValueError(f"unknown counter metric {name!r}")
        if value < 0:
            raise ValueError("counter increments must be >= 0")
        self._counters[name] += float(value)

    def set_gauge(self, name: str, value: float) -> None:
        if name not in self._gauges:
            raise ValueError(f"unknown gauge metric {name!r}")
        if value < 0:
            raise ValueError("gauge values must be >= 0")
        self._gauges[name] = float(value)

    def observe(self, name: str, value: float) -> None:
        """Record one latency/duration sample (bounded ring memory)."""

        if name not in self._histograms:
            raise ValueError(f"unknown histogram metric {name!r}")
        if value < 0:
            raise ValueError("histogram samples must be >= 0")
        samples = self._histograms[name]
        samples.append(float(value))
        if len(samples) > MAX_HISTOGRAM_SAMPLES:
            del samples[: len(samples) - MAX_HISTOGRAM_SAMPLES]

    def add_llm_usage(
        self,
        *,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        normalized_cost: float | None = None,
    ) -> None:
        """Record LLM usage/cost metadata when supplied (never fabricated)."""

        if input_tokens is not None:
            if input_tokens < 0:
                raise ValueError("input_tokens must be >= 0")
            self.increment("llm_input_tokens_total", float(input_tokens))
        if output_tokens is not None:
            if output_tokens < 0:
                raise ValueError("output_tokens must be >= 0")
            self.increment("llm_output_tokens_total", float(output_tokens))
        if normalized_cost is not None:
            if normalized_cost < 0:
                raise ValueError("normalized_cost must be >= 0")
            self._counters[LLM_COST_METRIC] += float(normalized_cost)

    def counter(self, name: str) -> float:
        if name not in self._counters:
            raise ValueError(f"unknown counter metric {name!r}")
        return self._counters[name]

    def snapshot(self) -> dict[str, Any]:
        """Deterministic sorted snapshot (safe for diagnostics/health)."""

        histograms: dict[str, dict[str, float | int]] = {}
        for name in sorted(self._histograms):
            samples = self._histograms[name]
            if samples:
                histograms[name] = {
                    "count": len(samples),
                    "sum": round(sum(samples), 6),
                    "min": min(samples),
                    "max": max(samples),
                }
            else:
                histograms[name] = {"count": 0, "sum": 0.0, "min": 0.0, "max": 0.0}
        return {
            "counters": {name: self._counters[name] for name in sorted(self._counters)},
            "gauges": {name: self._gauges[name] for name in sorted(self._gauges)},
            "histograms": histograms,
        }


__all__ = [
    "ALL_COUNTERS",
    "ALL_GAUGES",
    "ALL_HISTOGRAMS",
    "COUNTER_METRICS",
    "GAUGE_METRICS",
    "HISTOGRAM_METRICS",
    "LLM_COST_METRIC",
    "LLM_TOKEN_METRICS",
    "MAX_HISTOGRAM_SAMPLES",
    "MetricsRegistry",
]
