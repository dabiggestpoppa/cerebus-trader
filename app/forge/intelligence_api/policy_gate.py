"""Policy-first gateway: authorize before composition, cache only after allow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from app.forge.canonical import ProductExposure
from app.forge.identity import ForgePrincipal
from app.forge.intelligence_api.cache import (
    ResponseKey,
    SnapshotCache,
    policy_fingerprint,
    principal_scope,
)
from app.forge.intelligence_api.contracts import Snapshot
from app.forge.intelligence_api.identity import snapshot_id
from app.forge.policy import (
    AuthorizationContext,
    PolicyAction,
    PolicyResourceType,
    ResourcePolicyMetadata,
)
from app.forge.service.policy_enforcement import (
    ForgePolicyEnforcementService,
    GuardedAccess,
)


@dataclass(frozen=True)
class GuardedRead:
    """Outcome of one guarded intelligence read. Denials carry no content."""

    allowed: bool
    snapshot: Snapshot | None = None
    reason_code: str | None = None
    cached: bool = False
    refusal: dict[str, str] | None = None

    def denial(self) -> dict[str, str]:
        return self.refusal or {"code": "EXPOSURE_FORBIDDEN"}


class IntelligenceGateway:
    """Single policy seam for every III.6 surface."""

    def __init__(
        self,
        *,
        enforcement: ForgePolicyEnforcementService | None = None,
        cache: SnapshotCache | None = None,
        resource_type: PolicyResourceType = PolicyResourceType.SERVICE_ENDPOINT,
    ) -> None:
        self._enforcement = enforcement or ForgePolicyEnforcementService()
        self._cache = cache or SnapshotCache()
        self._resource_type = resource_type

    @property
    def cache(self) -> SnapshotCache:
        return self._cache

    @property
    def enforcement(self) -> ForgePolicyEnforcementService:
        return self._enforcement

    def read(
        self,
        *,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        key: Any,
        exposure: ProductExposure | None,
        loader: Callable[[], Snapshot],
        action: PolicyAction = PolicyAction.VIEW,
        correlation_id: str = "",
    ) -> GuardedRead:
        resource = ResourcePolicyMetadata(
            resource_type=self._resource_type,
            resource_id=key.model_id,
            exposure=exposure,
        )
        try:
            decision = self._enforcement.authorize(
                principal, context, action, resource, correlation_id=correlation_id
            )
        except Exception:
            # Fail closed: a policy-engine failure denies, never allows.
            return GuardedRead(allowed=False, refusal={"code": "EXPOSURE_FORBIDDEN"})

        if not decision.allowed:
            return GuardedRead(
                allowed=False,
                reason_code=decision.reason_code.value,
                refusal={"code": "EXPOSURE_FORBIDDEN"},
            )

        exposure_text = exposure.value if exposure is not None else "UNSPECIFIED"
        response_key = ResponseKey(
            snapshot_id=snapshot_id(key),
            exposure=exposure_text,
            policy_fingerprint=policy_fingerprint(
                allowed=True,
                reason_code=decision.reason_code.value,
                exposure=exposure_text,
            ),
            principal_scope=principal_scope(
                authenticated=principal.authenticated,
                user_id=principal.forge_user_id,
            ),
        )
        hit = self._cache.get_response(response_key)
        if hit is not None:
            return GuardedRead(allowed=True, snapshot=hit, cached=True)

        snapshot = loader()
        self._cache.put_composition(snapshot)
        self._cache.put_response(response_key, snapshot)
        return GuardedRead(allowed=True, snapshot=snapshot, cached=False)

    def read_guarded(
        self,
        *,
        principal: ForgePrincipal,
        context: AuthorizationContext,
        key: Any,
        exposure: ProductExposure | None,
        loader: Callable[[], Snapshot],
        correlation_id: str = "",
    ) -> GuardedAccess[Snapshot]:
        """Deny-before-load variant built on the service primitive itself."""

        resource = ResourcePolicyMetadata(
            resource_type=self._resource_type,
            resource_id=key.model_id,
            exposure=exposure,
        )
        return self._enforcement.guard(
            principal,
            context,
            PolicyAction.VIEW,
            resource,
            loader,
            correlation_id=correlation_id,
        )

    def audit_records(self) -> tuple[Any, ...]:
        return self._enforcement.audit_records()


__all__ = ["GuardedRead", "IntelligenceGateway"]
