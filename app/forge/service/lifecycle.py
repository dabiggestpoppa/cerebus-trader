"""FORGE startup/shutdown lifecycle hooks.

Explicit and testable. No network provider is contacted during import.
No future provider is contacted during startup.
No persistence is required at II.1.
"""

from __future__ import annotations

import logging
from typing import Any

from app.forge.config import ForgeConfig
from app.forge.service.container import ForgeServiceContainer

logger = logging.getLogger("forge")


class ForgeLifecycle:
    """Minimal FORGE lifecycle at II.1."""

    def __init__(self, container: ForgeServiceContainer) -> None:
        self._container = container
        self._started = False

    def startup(self) -> dict[str, Any]:
        """FORGE startup sequence.

        At II.1 this is intentionally lightweight:
        - load config (already provided via container)
        - initialize observability logger identity
        - note that DB/policy/providers are NOT initialized (II.1 scope)
        """

        logger.info(
            "FORGE starting: service=%s api_version=%s version=%s env=%s",
            self._container.config.service_name,
            self._container.config.api_version,
            self._container.config.application_version,
            self._container.config.environment,
        )
        self._started = True
        return {
            "service": self._container.config.service_name,
            "api_version": self._container.config.api_version,
            "version": self._container.config.application_version,
            "environment": self._container.config.environment,
            "started": True,
        }

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
