"""FORGE startup/shutdown lifecycle hooks.

Explicit and testable. No network provider is contacted during import.
No future provider is contacted during startup.

II.2: when a persistence gateway is injected, startup pings the backend and
checks migration compatibility BEFORE readiness. A required-persistence
failure flips container health state so readiness reports honestly
(not READY). No credentials, URLs or raw DB errors are logged.

II.5: provider registries are built by the composition root (never here);
startup probes each bound port's health() and logs the exception class name
only — never payloads, credentials, or provider internals.
"""

from __future__ import annotations

import logging
from typing import Any

from app.forge.config import ForgeConfig
from app.forge.persistence.port import MigrationOutcome
from app.forge.service.container import ForgeServiceContainer

logger = logging.getLogger("forge")


class ForgeLifecycle:
    """FORGE lifecycle (II.2-aware)."""

    def __init__(self, container: ForgeServiceContainer) -> None:
        self._container = container
        self._started = False

    def startup(self) -> dict[str, Any]:
        """FORGE startup sequence.

        - load config (already provided via container)
        - initialize observability logger identity
        - ping persistence when wired; record migration compatibility
        - probe provider health when wired (II.5); log class names only
        - policy is NOT initialized here (pure kernel needs no wiring)
        """

        startup_context = {
            "service": self._container.config.service_name,
            "api_version": self._container.config.api_version,
            "version": self._container.config.application_version,
            "environment": self._container.config.environment,
            "started": True,
        }

        persistence = self._container.persistence
        if persistence is not None:
            try:
                persistence.ping()
            except BaseException as exc:  # NOSONAR: normalized; detail never logged
                logger.error(
                    "FORGE persistence ping failed: %s", type(exc).__name__
                )
                self._container.mark_persistence_health(False)
            else:
                self._container.mark_persistence_health(True)
                try:
                    outcome = persistence.apply_migrations()
                    compatibility = persistence.check_compatibility()
                except BaseException as exc:  # NOSONAR: normalized; detail never logged
                    logger.error(
                        "FORGE migration check failed: %s", type(exc).__name__
                    )
                    self._container.set_migration_status("INCOMPATIBLE")
                else:
                    logger.info(
                        "FORGE migrations outcome=%s compatibility=%s",
                        outcome,
                        compatibility,
                    )
                    self._container.set_migration_status(compatibility)
        else:
            self._container.set_migration_status("NOT_CONFIGURED")

        providers = self._container.providers
        if providers is not None:
            for port in providers.ports():
                try:
                    health = providers.get(port).health()
                except BaseException as exc:  # NOSONAR: normalized; detail never logged
                    logger.error(
                        "FORGE provider health failed: port=%s error=%s",
                        port,
                        type(exc).__name__,
                    )
                else:
                    logger.info(
                        "FORGE provider wired: port=%s name=%s status=%s",
                        port,
                        providers.name(port),
                        health.status,
                    )

        logger.info(
            "FORGE starting: service=%s api_version=%s version=%s env=%s persistence=%s",
            self._container.config.service_name,
            self._container.config.api_version,
            self._container.config.application_version,
            self._container.config.environment,
            "enabled" if persistence is not None else "disabled",
        )
        self._started = True
        return startup_context

    def shutdown(self) -> dict[str, Any]:
        """FORGE shutdown/drain sequence."""

        if not self._started:
            return {"started": False, "shutdown": True}
        logger.info(
            "FORGE shutting down: service=%s env=%s",
            self._container.config.service_name,
            self._container.config.environment,
        )
        self._started = False
        return {"service": self._container.config.service_name, "shutdown": True}

    @property
    def started(self) -> bool:
        return self._started
