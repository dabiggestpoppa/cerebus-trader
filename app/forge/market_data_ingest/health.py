"""Provider health and readiness evidence (WP-3B).

Health is honest and bounded.  A configured adapter that has never completed a
verified window is not ``READY``; only the ten readiness gates in
``ACCEPTANCE.md`` can move it there, and this module cannot flip the Book II
seam regardless of its verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.forge.providers.doctrine import ProviderHealth


class IngestState(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class ReadinessEvidence:
    """The ten gates; each must be explicitly observed, never assumed."""

    r1_authorized_provider: bool = False
    r2_credentials_injected: bool = False
    r3_bounded_requests_succeeded: bool = False
    r4_clock_session_verified: bool = False
    r5_final_bar_checks: bool = False
    r6_parity_verified: bool = False
    r7_replay_reproduced: bool = False
    r8_source_health_observed: bool = False
    r9_recovery_drill: bool = False
    r10_book_ii_amendment: bool = False

    def missing(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, value in (
                ("R1", self.r1_authorized_provider),
                ("R2", self.r2_credentials_injected),
                ("R3", self.r3_bounded_requests_succeeded),
                ("R4", self.r4_clock_session_verified),
                ("R5", self.r5_final_bar_checks),
                ("R6", self.r6_parity_verified),
                ("R7", self.r7_replay_reproduced),
                ("R8", self.r8_source_health_observed),
                ("R9", self.r9_recovery_drill),
                ("R10", self.r10_book_ii_amendment),
            )
            if not value
        )

    @property
    def satisfied(self) -> bool:
        return not self.missing()


@dataclass(frozen=True)
class IngestHealth:
    provider_id: str
    state: IngestState
    detail: str
    consecutive_failures: int = 0

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("provider_id is required")
        if self.consecutive_failures < 0:
            raise ValueError("consecutive_failures must be >= 0")

    def as_provider_health(self) -> ProviderHealth:
        mapping = {
            IngestState.READY: "healthy",
            IngestState.DEGRADED: "degraded",
            IngestState.UNAVAILABLE: "unavailable",
            IngestState.NOT_CONFIGURED: "unavailable",
        }
        return ProviderHealth(
            provider_type="market_data",
            provider_name=self.provider_id,
            status=mapping[self.state],
            detail=self.detail,
        )


class HealthMonitor:
    """Tracks observed source behaviour; never invents a positive state."""

    def __init__(self, provider_id: str, *, configured: bool = False) -> None:
        self.provider_id = provider_id
        self._configured = configured
        self._consecutive_failures = 0
        self._degraded_reason: str | None = None
        self._observed_success = False

    def record_success(self) -> None:
        self._consecutive_failures = 0
        self._degraded_reason = None
        self._observed_success = True

    def record_failure(self, *, retryable: bool = True) -> None:
        if retryable:
            self._consecutive_failures += 1

    def record_degraded(self, reason: str) -> None:
        if not reason or any(ch.isspace() for ch in reason):
            raise ValueError("degraded reason must be a bounded code")
        self._degraded_reason = reason

    def snapshot(self) -> IngestHealth:
        if not self._configured:
            return IngestHealth(
                provider_id=self.provider_id,
                state=IngestState.NOT_CONFIGURED,
                detail="provider_not_configured",
            )
        if self._degraded_reason is not None:
            return IngestHealth(
                provider_id=self.provider_id,
                state=IngestState.DEGRADED,
                detail=self._degraded_reason,
                consecutive_failures=self._consecutive_failures,
            )
        if self._consecutive_failures > 0 or not self._observed_success:
            return IngestHealth(
                provider_id=self.provider_id,
                state=IngestState.UNAVAILABLE,
                detail="no_verified_window",
                consecutive_failures=self._consecutive_failures,
            )
        return IngestHealth(
            provider_id=self.provider_id,
            state=IngestState.DEGRADED,
            detail="awaiting_readiness_evidence",
        )

    def readiness(self, evidence: ReadinessEvidence) -> IngestHealth:
        """Only a fully evidenced provider may be READY."""
        if not self._configured:
            return self.snapshot()
        if not evidence.satisfied:
            return IngestHealth(
                provider_id=self.provider_id,
                state=IngestState.DEGRADED,
                detail="readiness_gates_incomplete",
            )
        return IngestHealth(
            provider_id=self.provider_id,
            state=IngestState.READY,
            detail="readiness_evidence_complete",
        )


__all__ = ["HealthMonitor", "IngestHealth", "IngestState", "ReadinessEvidence"]
