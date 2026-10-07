"""FORGE health / readiness service.

FORGE health/readiness at II.1 is honest:
- liveness: is the FORGE process/application alive?
- readiness: is FORGE safe to serve, given the dependencies that actually exist?

FORGE does NOT claim database/provider/corpus/market-data/Ask CEREBUS readiness.
Those belong to later Books; at II.1 they are explicitly not configured and not
required for serving, so they never block or degrade readiness.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.service.container import ForgeServiceContainer


@dataclass
class ForgeHealthService:
    """FORGE-owned health/readiness view."""

    container: ForgeServiceContainer

    def liveness(self) -> dict:
        """Lightweight liveness: process alive + service identity."""

        return {
            "service": self.container.config.service_name,
            "status": "alive",
        }

    def readiness(self) -> dict:
        """FORGE readiness with honest dependency semantics at II.1.

        Overall status is computed over REQUIRED dependencies only. Future
        dependencies are listed with the frozen non-healthy vocabulary
        (NOT_CONFIGURED / NOT_APPLICABLE / NOT_IMPLEMENTED) and required=False,
        so they are disclosed but never claimed healthy and never block.
        """

        deps = self.container.as_readiness_dependencies()
        required_ready = all(
            _dep_ready(dep) for dep in deps.values() if dep.get("required")
        )
        return {
            "service": self.container.config.service_name,
            "status": "ready" if required_ready else "not_ready",
            "dependencies": deps,
        }

    def meta(self) -> dict:
        """Deterministic non-secret FORGE build/version metadata."""

        config = self.container.config
        diagnostics = self.container.redacted_diagnostics()
        return {
            "service": config.service_name,
            "api_version": config.api_version,
            "application_version": config.application_version,
            "environment": config.environment,
            "forge_domain_version": "FORGE_DOMAIN_V1",
            "diagnostics": diagnostics,
        }


_READY_STATUSES = frozenset({"READY", "ready", "ok", "healthy"})


def _dep_ready(dep: dict) -> bool:
    return dep.get("status", "") in _READY_STATUSES
