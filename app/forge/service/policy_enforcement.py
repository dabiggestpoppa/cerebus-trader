"""FORGE policy enforcement service (Book II / Bloc II.4).

The service-layer enforcement boundary and the reusable deny-before-load
primitive for every later protected surface (I.3 corpus, III, IV Ask
CEREBUS, V, VII).

The law this module enforces:

    AUTHENTICATION (II.3) -> PRINCIPAL -> REQUESTED ACTION/RESOURCE
    -> POLICY DECISION (II.4) -> ONLY THEN protected resource load.

On DENY the protected loader is never invoked. This is the architectural
pre-retrieval / pre-LLM boundary: content may never be fetched and filtered
afterwards, and unauthorized content may never enter an LLM context.

The service reuses II.3 `ForgeAuthenticationService` for principals (never
creates a second auth implementation) and the pure II.4 kernel for
decisions. It adds: disabled-user fail-closed enforcement, structured
denials, and a bounded, content-free audit trail.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

from app.forge.canonical import ProductExposure
from app.forge.identity import ForgePrincipal
from app.forge.policy import (
    AuthorizationContext,
    DefaultDenyPolicyEngine,
    PolicyAction,
    PolicyDecision,
    PolicyEngine,
    PolicyReason,
    ResourcePolicyMetadata,
)

T = TypeVar("T")


@dataclass(frozen=True)
class GuardedAccess(Generic[T]):
    """Outcome of a guarded protected-resource access.

    `payload` is present ONLY when `allowed` — a denial exposes nothing that
    a loader might have produced.
    """

    allowed: bool
    decision: PolicyDecision
    payload: T | None = None


@dataclass(frozen=True)
class PolicyAuditRecord:
    """Content-free audit record for one policy decision.

    Safe fields only: correlation/principal/action/resource classification/
    decision/reason. Never: session token, protected body, internal code
    text, provider secrets.
    """

    correlation_id: str
    principal_id: str  # FORGE user id, or "anonymous"
    authenticated: bool
    action: str
    resource_type: str
    resource_id: str
    exposure: str
    allowed: bool
    reason_code: str
    at: str  # caller/enforcement-supplied timestamp; kernel stays clock-free


class ForgePolicyEnforcementService:
    """principal + context + action + safe resource metadata -> decision.

    The service is the only place where policy meets principals, so the
    deny-before-load ordering is enforced in exactly one reusable place.
    """

    def __init__(
        self,
        engine: PolicyEngine | None = None,
        *,
        audit_capacity: int = 256,
        now: Callable[[], str] | None = None,
    ) -> None:
        self._engine: PolicyEngine = engine or DefaultDenyPolicyEngine()
        self._audit_capacity = max(1, int(audit_capacity))
        self._audit: list[PolicyAuditRecord] = []
        self._now = now  # injectable for deterministic tests

    # -- decision -------------------------------------------------------------

    def authorize(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        action: PolicyAction | str,
        resource: ResourcePolicyMetadata,
        *,
        correlation_id: str = "",
    ) -> PolicyDecision:
        """Evaluate the policy kernel. Pure with respect to resources."""

        decision = self._engine.decide(principal, context, action, resource)
        self._record(principal, action, resource, decision, correlation_id)
        return decision

    # -- deny-before-load primitive --------------------------------------------

    def guard(
        self,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        action: PolicyAction | str,
        resource: ResourcePolicyMetadata,
        loader: Callable[..., T],
        *loader_args: Any,
        correlation_id: str = "",
        **loader_kwargs: Any,
    ) -> GuardedAccess[T]:
        """Authorize FIRST; only on ALLOW invoke the protected loader.

        This is the mandatory ordering primitive: DENY => loader never
        called; ALLOW => loader called exactly once.
        """

        decision = self.authorize(
            principal, context, action, resource, correlation_id=correlation_id
        )
        if not decision.allowed:
            return GuardedAccess(allowed=False, decision=decision, payload=None)
        payload = loader(*loader_args, **loader_kwargs)
        return GuardedAccess(allowed=True, decision=decision, payload=payload)

    # -- audit -----------------------------------------------------------------

    def _record(
        self,
        principal: ForgePrincipal,
        action: PolicyAction | str,
        resource: ResourcePolicyMetadata,
        decision: PolicyDecision,
        correlation_id: str,
    ) -> None:
        exposure = (
            resource.exposure.value
            if isinstance(resource.exposure, ProductExposure)
            else "UNSPECIFIED"
        )
        record = PolicyAuditRecord(
            correlation_id=str(correlation_id or ""),
            principal_id=principal.forge_user_id or "anonymous",
            authenticated=bool(principal.authenticated),
            action=action.value if isinstance(action, PolicyAction) else str(action),
            resource_type=resource.resource_type.value,
            resource_id=resource.resource_id,
            exposure=exposure,
            allowed=bool(decision.allowed),
            reason_code=decision.reason_code.value,
            at=self._now() if self._now else "",
        )
        self._audit.append(record)
        if len(self._audit) > self._audit_capacity:
            del self._audit[: len(self._audit) - self._audit_capacity]

    def audit_records(self) -> tuple[PolicyAuditRecord, ...]:
        """Snapshot of the bounded, content-free audit trail (tests/ops)."""

        return tuple(self._audit)


__all__ = [
    "GuardedAccess",
    "PolicyAuditRecord",
    "ForgePolicyEnforcementService",
]
