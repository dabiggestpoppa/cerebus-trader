"""FORGE service container / dependency boundary.

This is the smallest explicit composition seam FORGE needs at II.1.

It exists so later Books/Blocs can provide:
- canonical registry access
- provenance access
- persistence
- policy
- provider adapters

...without converting FORGE domain modules into global mutable singletons used
by the HTTP layer.

At II.1, FORGE routes do NOT depend on unimplemented persistence/policy/provider
services. This container is mostly a marker boundary plus a real object that can
be replaced/faked in tests.

Domain modules remain free of service-layer singletons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.forge.config import ForgeConfig


@dataclass
class ForgeServiceContainer:
    """Minimal FORGE composition root.

    Replacements/fakes are acceptable in tests.
    """

    config: ForgeConfig
    # Reserved seams for later Blocs. Empty/placeholder at II.1.
    canonical: Any = field(default=None, repr=False)
    provenance: Any = field(default=None, repr=False)
    persistence: Any = field(default=None, repr=False)
    policy: Any = field(default=None, repr=False)
    providers: Any = field(default=None, repr=False)
    observability: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # Explicit marker: II.1 does not wire real persistence/policy/providers.
        if self.persistence is not None:
            raise RuntimeError(
                "FORGE persistence is not wired at II.1; II.2 owns that boundary"
            )
        if self.policy is not None:
            raise RuntimeError(
                "FORGE policy engine is not wired at II.1; II.4 owns that boundary"
            )
        if self.providers is not None:
            raise RuntimeError(
                "FORGE provider adapters are not wired at II.1; II.5 owns that boundary"
            )

    def redacted_diagnostics(self) -> dict[str, Any]:
        """Safe diagnostic snapshot for health/meta endpoints."""

        return {
            "config": self.config.redacted_diagnostics(),
            "persistence_wired": self.persistence is not None,
            "policy_wired": self.policy is not None,
            "providers_wired": self.providers is not None,
            "observability_wired": self.observability is not None,
        }

    def as_readiness_dependencies(self) -> dict[str, Any]:
        """Honest FORGE dependency view at II.1.

        Future dependencies that do not exist yet are represented with the
        frozen non-healthy vocabulary NOT_CONFIGURED / NOT_APPLICABLE /
        NOT_IMPLEMENTED, never HEALTHY. They are marked required=False because
        II.1 serving does not depend on them; II.2+ flips the flag when the
        dependency is actually wired.
        """

        return {
            "forge": {
                "status": "READY",
                "required": True,
                "note": "FORGE service skeleton has no external dependency at II.1",
            },
            "postgresql": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": "persistence belongs to II.2; not wired at II.1",
            },
            "pgvector": {
                "status": "NOT_APPLICABLE",
                "required": False,
                "note": "pgvector is a II.2/II.4 retrieval concern, not II.1",
            },
            "openrouter": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": "LLM provider belongs to II.5 / IV; not wired at II.1",
            },
            "whop": {
                "status": "NOT_CONFIGURED",
                "required": False,
                "note": "commerce provider belongs to II.5 / VI; not wired at II.1",
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
