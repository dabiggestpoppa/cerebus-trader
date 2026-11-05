"""Bounded refusal construction and Book I card machine-validity probing."""

from __future__ import annotations

from app.forge.canonical import CanonicalId, EvidenceStatus
from app.forge.intelligence_api.contracts import UnavailableSection
from app.forge.intelligence_api.errors import RefusalError
from app.forge.intelligence_api.versions import (
    CARD_SCHEMA_INCOMPATIBLE,
    CARD_SCHEMA_MACHINE_VALID,
    CARD_SCHEMA_VERBATIM,
)


def card_machine_errors(card: object) -> tuple[str, ...]:
    """Reproduce the Book I machine-card failures without mutating anything.

    Exactly the three observed classes: `SETUP.*` identity, card lifecycle
    status vocabulary, and model-scoped parent identifiers.
    """

    errors: list[str] = []
    setup_id = getattr(card, "setup_id", "")
    try:
        CanonicalId.parse(str(setup_id))
    except Exception:
        errors.append("setup_id")
    status = getattr(card, "status", None)
    raw_status = getattr(status, "value", status)
    try:
        EvidenceStatus(str(raw_status))
    except ValueError:
        errors.append("status")
    for parent in getattr(card, "parent_model_ids", ()) or ():
        try:
            CanonicalId.parse(str(parent))
        except Exception:
            errors.append("parent_model_ids")
            break
    return tuple(errors)


def card_schema_status(card: object | None) -> str:
    if card is None:
        return "CARD_UNAVAILABLE"
    return CARD_SCHEMA_VERBATIM if card_machine_errors(card) else CARD_SCHEMA_MACHINE_VALID


def require_machine_card(card: object | None) -> None:
    if card is None:
        raise RefusalError("SETUP_UNRESOLVED", detail="card_missing")
    errors = card_machine_errors(card)
    if errors:
        raise RefusalError(CARD_SCHEMA_INCOMPATIBLE, detail="book_i_card_schema")


def unavailable(section: str, reason: str) -> UnavailableSection:
    return UnavailableSection(section=section, reason=reason)


def denial(code: str = "EXPOSURE_FORBIDDEN") -> dict[str, str]:
    """Uniform, content-free denial: no ids, no resource type, no existence."""

    return {"code": code}


def refusal_entry(code: str, *, detail: str = "") -> dict[str, str]:
    return RefusalError(code, detail=detail).to_payload()


def require_claim_for_statistic(claim_id: str | None) -> None:
    """A numerical claim without a claim identity is not served as a claim."""

    if not claim_id:
        raise RefusalError("INSUFFICIENT_EVIDENCE", detail="claim_required")


def filter_evidence(links, permitted_exposures):
    """Drop evidence whose exposure the principal may not receive."""

    kept = tuple(
        link
        for link in links
        if getattr(link, "exposure", None) is None
        or getattr(link.exposure, "value", link.exposure) in permitted_exposures
    )
    return kept, len(tuple(links)) - len(kept)


__all__ = [
    "CARD_SCHEMA_INCOMPATIBLE",
    "card_machine_errors",
    "card_schema_status",
    "require_machine_card",
    "unavailable",
    "denial",
    "refusal_entry",
    "require_claim_for_statistic",
    "filter_evidence",
]
