"""FORGE service container / dependency boundary.

This is the explicit composition seam for the FORGE service layer.

It exists so later Books/Blocs can provide:
- canonical registry access
- provenance access
- persistence (II.2: injected PersistenceGateway implementations)
- policy
- provider adapters

...without converting FORGE domain modules into global mutable singletons used
by the HTTP layer.

Persistence is explicitly injected via the port; there is no hidden
module-level database singleton. Domain modules remain free of service-layer
singletons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.forge.config import ForgeConfig
from app.forge.persistence.port import PersistenceGateway
from app.forge.service.authentication import ForgeAuthenticationService
from app.forge.policy import PolicyEngine


@dataclass
class ForgeServiceContainer:
    """Minimal FORGE composition root.

    Replacements/fakes are acceptable in tests.
    """

    config: ForgeConfig
    # Reserved seams for later Blocs. Persistence is an II.2-owned injected
    # implementation of the PersistenceGateway port; policy/providers stay
    # forbidden until their Blocs own those boundaries.
    canonical: Any = field(default=None, repr=False)
    provenance: Any = field(default=None, repr=False)
    persistence: PersistenceGateway | None = field(default=None, repr=False)
    # II.3: the runtime authentication boundary (credential -> principal).
    # Injected explicitly like persistence; built lazily from the persistence
    # gateway when not supplied.
    authentication: ForgeAuthenticationService | None = field(
        default=None, repr=False
    )
    # II.4: the central policy authority (pure PolicyEngine). Injected
    # explicitly; default None because the pure kernel needs no wiring to
    # exist. Providers remain forbidden until II.5 owns that boundary.
    policy: PolicyEngine | None = field(default=None, repr=False)
    providers: Any = field(default=None, repr=False)
    observability: Any = field(default=None, repr=False)

    _persistence_healthy: bool = field(default=False, repr=False, init=False)
    _migration_status: str = field(default="NOT_CHECKED", repr=False, init=False)

    def __post_init__(self) -> None:
        # Persistence must implement the port (explicit injection, never a
        # hidden module-level singleton). Policy/providers remain prohibited
        # until II.4/II.5 own those boundaries.
        if self.persistence is not None and not isinstance(
            self.persistence, PersistenceGateway
        ):  # runtime_checkable protocol: structural check
            raise TypeError(
                "persistence must implement the PersistenceGateway port"
            )
        # II.3: an explicitly injected authentication service must be of the
        # FORGE-owned boundary type; the default is derived from persistence.
        if self.authentication is None and self.persistence is not None:
            self.authentication = ForgeAuthenticationService(self.persistence)
        elif self.authentication is not None and not isinstance(
            self.authentication, ForgeAuthenticationService
        ):
            raise TypeError(
                "authentication must be a ForgeAuthenticationService"
            )
        # II.4 owns the policy seam: an injected engine must implement the
        # pure PolicyEngine port (structural check).
        if self.policy is not None and not isinstance(self.policy, PolicyEngine):
            raise TypeError("policy must implement the PolicyEngine port")
        if self.providers is not None:
            raise RuntimeError(
                "FORGE provider adapters are not wired at II.2; II.5 owns that boundary"
            )

    def _postgresql_dependency(self) -> dict[str, Any]:
        """Honest postgresql readiness entry (II.2 semantics).

        Persistence is only a readiness blocker when it is enabled AND the
        deployment treats migration compatibility as required. Otherwise it is
        disclosed without claiming health.
        """

        if self.persistence is None:
            return {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": "persistence not enabled; FORGE serves with in-memory only",
            }
        if not self._persistence_healthy:
            return {
                "status": "UNAVAILABLE",
                "required": True,
                "note": "persistence enabled but backend did not answer ping",
            }
        if self._migration_status in {"BEHIND", "INCOMPATIBLE"}:
            return {
                "status": f"SCHEMA_{self._migration_status}",
                "required": True,
                "note": "migration compatibility check failed at startup",
            }
        return {
            "status": "READY",
            "required": True,
            "note": "persistence enabled, backend answering, migration check passed",
        }

    def redacted_diagnostics(self) -> dict[str, Any]:
        """Safe diagnostic snapshot for health/meta endpoints."""

        return {
            "config": self.config.redacted_diagnostics(),
            "persistence_enabled": self.persistence is not None,
            "persistence_healthy": self._persistence_healthy,
            "policy_wired": self.policy is not None,
            "providers_wired": self.providers is not None,
            "observability_wired": self.observability is not None,
        }

    def mark_persistence_health(self, healthy: bool) -> None:
        """Record lifecycle ping outcome (called by ForgeLifecycle at startup)."""

        self._persistence_healthy = healthy

    def set_migration_status(self, status: str) -> None:
        """Record migration compatibility identity from lifecycle startup."""

        self._migration_status = status

    @property
    def migration_status(self) -> str:
        return self._migration_status

    def as_readiness_dependencies(self) -> dict[str, Any]:
        """Honest FORGE dependency view.

        Future dependencies that do not exist yet are represented with the
        frozen non-healthy vocabulary NOT_CONFIGURED / NOT_APPLICABLE /
        NOT_IMPLEMENTED, never HEALTHY. They are marked required=False because
        serving does not depend on them; the owning Bloc flips the flag when
        the dependency is actually wired.
        """

        return {
            "forge": {
                "status": "READY",
                "required": True,
                "note": "FORGE service composition root is live",
            },
            "postgresql": self._postgresql_dependency(),
            "pgvector": {
                "status": "NOT_APPLICABLE",
                "required": False,
                "note": "pgvector/semantic storage belongs to a later retrieval bloc",
            },
            "openrouter": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": "LLM provider belongs to II.5 / IV; not wired at II.1",
            },
            "whop": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": "commerce provider belongs to II.5 / VI; not wired at II.2",
            },
            "market_data": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": "market-data providers belong to Book III; not wired at II.1",
            },
            "ask_cerebus": {
                "status": "NOT_APPLICABLE",
                "required": False,
                "note": "Ask CEREBUS is a later Book IV service, not II.1",
            },
        }
