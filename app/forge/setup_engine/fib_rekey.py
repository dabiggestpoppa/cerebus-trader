"""Fib Rekey operator (Ch III.5.7) — ``RESEARCH_ONLY``, end to end.

The card's requirements are carried exactly:

* a valid active A–B Range Birth is mandatory; the canonical R15 anchor
  eligibility rule is **not** materialised, so the anchor gate yields
  ``UNRESOLVED`` and never a research promotion;
* 132% is the primary rekey location, 168% is historical dual-entry
  research, 185% is the extension;
* 50–72% is a **separate** retracement family and is never conflated with
  rekey entry;
* the R11 generic-pivot fallback does not exist in this package — there is
  no anchor generator and no pivot-to-anchor path;
* R11 frequency/hit-rate is never transferred into R15;
* a production/operator request is blocked by the registry, not by a
  caller's good intentions.
"""

from __future__ import annotations

from decimal import Decimal

from .contracts import EvidenceReference
from .eligibility import SetupEvaluation, SetupEvaluationRequest, evaluate_setup
from .errors import SetupContractError
from .registry import CanonicalSetupCard, SetupRegistry

__all__ = [
    "AUTOMATION_PERMITTED",
    "GENERIC_PIVOT_FALLBACK_AVAILABLE",
    "HISTORICAL_DUAL_ENTRY",
    "PRIMARY_REKEY",
    "R11_FREQUENCY_TRANSFER_ALLOWED",
    "RETRACE_FAMILY",
    "SETUP_ID",
    "card",
    "evidence_refs",
    "evaluate_fib",
    "lineage_facts",
    "rekey_levels",
]

SETUP_ID = "SETUP.FIB.REKEY.V1"

#: 132% primary rekey, 168% historical dual entry, 185% extension.
PRIMARY_REKEY = Decimal("132")
HISTORICAL_DUAL_ENTRY = Decimal("168")
EXTENSION = Decimal("185")

#: A separate retracement family — never a rekey entry level.
RETRACE_FAMILY: tuple[str, ...] = ("RETRACE_50", "RETRACE_61", "RETRACE_72")

#: Structural absences: no fallback, no frequency transfer, no approval.
GENERIC_PIVOT_FALLBACK_AVAILABLE = False
R11_FREQUENCY_TRANSFER_ALLOWED = False
AUTOMATION_PERMITTED = False


def card(registry: SetupRegistry | None = None) -> CanonicalSetupCard:
    return (SetupRegistry() if registry is None else registry).card(SETUP_ID)


def evidence_refs(registry: SetupRegistry | None = None) -> tuple[EvidenceReference, ...]:
    return card(registry).evidence_refs


def rekey_levels() -> tuple[tuple[str, Decimal], ...]:
    return (
        ("SETUP.FIB.TARGET.REKEY_132", PRIMARY_REKEY),
        ("SETUP.FIB.TARGET.DUAL_ENTRY_168", HISTORICAL_DUAL_ENTRY),
        ("SETUP.FIB.TARGET.EXTENSION_185", EXTENSION),
    )


def lineage_facts():
    """The 132 → 168 → 185 lineage as bounded, prose-free facts."""

    from app.forge.model_runtime.contract import make_fact

    return (
        make_fact(
            "SETUP.FIB.LINEAGE",
            "SETUP.FIB.REKEY.LINEAGE",
            SETUP_ID,
            (
                ("primary", format(PRIMARY_REKEY, "f")),
                ("dual_entry", format(HISTORICAL_DUAL_ENTRY, "f")),
                ("extension", format(EXTENSION, "f")),
            ),
        ),
        make_fact(
            "SETUP.FIB.SEPARATION",
            "SETUP.FIB.RETRACE.SEPARATE",
            SETUP_ID,
            (
                ("retrace_family", ",".join(RETRACE_FAMILY)),
                ("conflated", "NO"),
            ),
        ),
        make_fact(
            "SETUP.FIB.R15",
            "SETUP.FIB.ANCHOR.R15",
            SETUP_ID,
            (
                ("rule_materialized", "NO"),
                ("fallback_available", "NO"),
                ("r11_frequency_transferred", "NO"),
            ),
        ),
    )


def evaluate_fib(
    request: SetupEvaluationRequest, *, registry: SetupRegistry | None = None
) -> SetupEvaluation:
    """Evaluate the Fib rekey operator (research surface only)."""

    if request.setup_id != SETUP_ID:
        raise SetupContractError(
            f"the Fib operator evaluates {SETUP_ID}, not {request.setup_id}"
        )
    return evaluate_setup(request, registry=registry)
