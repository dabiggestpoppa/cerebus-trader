"""Version and identity stamps for the operator setup engine (Bloc III.5).

All stamps are frozen strings.  ``SETUP_ID_PATTERN`` encodes the
**corpus** setup identity form (``SETUP.<FAMILY>.<NAME>.<VERSION>``),
carried verbatim from the canonical cards.

Implementation-time reconciliation (disclosed as ``III.5-REC-1``):
Book I's :class:`app.forge.canonical.CanonicalId` kernel only accepts a
``SET.`` prefix, while every canonical Setup Card is named ``SETUP.*``.
Rather than mint a ``SET.*`` id (which would invent canonical identity),
the engine carries the corpus string and proves resolvability against
the frozen three-card registry — a strictly narrower admission than a
prefix match.
"""

from __future__ import annotations

SETUP_ENGINE_VERSION = "SETUP_ENGINE.V1"
SETUP_CONTRACT_VERSION = "SETUP_CONTRACT.V1"
SETUP_TRIGGER_VERSION = "SETUP_TRIGGER.V1"
SETUP_INVALIDATION_VERSION = "SETUP_INVALIDATION.V1"
SETUP_TARGET_VERSION = "SETUP_TARGET.V1"

#: The verbatim corpus identity form for a canonical Setup Card.
SETUP_ID_PATTERN = r"^SETUP\.[A-Z0-9][A-Z0-9_.-]*$"

#: The frozen chapter-to-module inventory of this Bloc (PLAN.md §7.1).
SETUP_ENGINE_MODULES: tuple[str, ...] = (
    "__init__",
    "versions",
    "errors",
    "contracts",
    "registry",
    "eligibility",
    "triggers",
    "invalidation",
    "targets",
    "xau_quarter_zone",
    "fib_rekey",
    "jpy_role_gate",
    "st_manual",
    "p90_lineage",
    "statistics",
    "invariants",
)

__all__ = [
    "SETUP_CONTRACT_VERSION",
    "SETUP_ENGINE_MODULES",
    "SETUP_ENGINE_VERSION",
    "SETUP_ID_PATTERN",
    "SETUP_INVALIDATION_VERSION",
    "SETUP_TARGET_VERSION",
    "SETUP_TRIGGER_VERSION",
]
