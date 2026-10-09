"""FORGE service container / dependency boundary.

This is the explicit composition seam for the FORGE service layer.

It exists so later Books/Blocs can provide:
- canonical registry access
- provenance access
- persistence (II.2: injected PersistenceGateway implementations)
- policy (II.4: injected PolicyEngine)
- providers (II.5: injected ProviderRegistry — config-selected at the
  composition root, deterministic fakes until Book IV/VI adapters arrive)

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
from app.forge.providers.doctrine import HEALTH_STATUSES, PORTS
from app.forge.providers.registry import ProviderRegistry
from app.forge.service.authentication import ForgeAuthenticationService
from app.forge.policy import PolicyEngine


@dataclass
class ForgeServiceContainer:
    """Minimal FORGE composition root.

    Replacements/fakes are acceptable in tests.
    """

    config: ForgeConfig
    # Reserved seams for later Blocs. Persistence is an II.2-owned injected
    # implementation of the PersistenceGateway port; policy is the II.4-owned
    # PolicyEngine; providers is the II.5-owned ProviderRegistry.
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
    # exist.
    policy: PolicyEngine | None = field(default=None, repr=False)
    # II.5: typed provider port bindings (deterministic fakes at II.5).
    # Default None keeps composition explicit — no hidden singleton; the
    # application composition root passes providers_from_config(config).
    providers: ProviderRegistry | None = field(default=None, repr=False)
    observability: Any = field(default=None, repr=False)

    _persistence_healthy: bool = field(default=False, repr=False, init=False)
    _migration_status: str = field(default="NOT_CHECKED", repr=False, init=False)

    def __post_init__(self) -> None:
        # Persistence must implement the port (explicit injection, never a
        # hidden module-level singleton).
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
        # II.5 owns the provider seam: an injected registry must be a real
        # ProviderRegistry (typed port bindings, frozen after composition).
        # This supersedes the II.1-era RuntimeError guard exactly as II.2 and
        # II.4 superseded theirs: ownership moved, fail-closed principle kept.
        if self.providers is not None and not isinstance(
            self.providers, ProviderRegistry
        ):
            raise TypeError("providers must be a ProviderRegistry")

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

    def _provider_dependency(self, port: str) -> dict[str, Any]:
        """Honest per-port provider readiness entry (II.5 semantics).

        Not wired => NOT_CONFIGURED (never claimed healthy). Wired => live
        health() probe mapped to the service vocabulary; probe exceptions are
        absorbed as UNAVAILABLE with the exception class name only (no
        payloads, no credentials). required stays False at II.5 because no
        serving path consumes providers yet; the consuming Bloc flips it.
        """

        if self.providers is None:
            return {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": f"{port} port not wired at the composition root",
            }
        try:
            impl = self.providers.get(port)
            name = self.providers.name(port)
        except Exception:  # ProviderConfigurationError: port unbound
            return {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": f"{port} port not bound in the provider registry",
            }
        try:
            health = impl.health()
        except BaseException as exc:  # NOSONAR: normalized; detail never logged
            return {
                "status": "UNAVAILABLE",
                "required": False,
                "note": f"{port} health probe raised {type(exc).__name__}",
            }
        if health.status == "healthy":
            status = "READY"
        elif health.status in HEALTH_STATUSES:
            status = "UNAVAILABLE" if health.status == "unavailable" else "DEGRADED"
        else:
            status = "UNAVAILABLE"
        return {
            "status": status,
            "required": False,
            "note": (
                f"{port} port wired ({name}); required=False until a serving "
                "path consumes it"
            ),
        }

    def redacted_diagnostics(self) -> dict[str, Any]:
        """Safe diagnostic snapshot for health/meta endpoints."""

        return {
            "config": self.config.redacted_diagnostics(),
            "persistence_enabled": self.persistence is not None,
            "persistence_healthy": self._persistence_healthy,
            "policy_wired": self.policy is not None,
            "providers_wired": self.providers is not None,
            "provider_bindings": (
                self.providers.bound_names() if self.providers is not None else {}
            ),
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
        the dependency is actually wired. II.5 wires the four neutral provider
        ports (llm/commerce/notification/storage) with live health probes;
        concrete vendor adapters (openrouter/whop) remain NOT_CONFIGURED
        until Book IV/VI.
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
            # The four II.5 neutral ports (PORTS is the authority; tested).
            **{port: self._provider_dependency(port) for port in PORTS},
            "openrouter": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": (
                    "concrete OpenRouter adapter belongs to Book IV; II.5 "
                    "wires the neutral llm port"
                ),
            },
            "whop": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": (
                    "concrete Whop adapter belongs to Book VI; II.5 wires "
                    "the neutral commerce port"
                ),
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
