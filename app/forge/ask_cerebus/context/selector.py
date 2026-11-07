"""Section selection rules for IV.3."""

from __future__ import annotations

from app.forge.ask_cerebus.context.enums import ContextSectionId, SECTION_ORDER


def section_for_object_type(object_type: str) -> ContextSectionId | None:
    value = (object_type or "").upper()
    if value in {"MODEL", "DOCTRINE", "MODEL_DOCTRINE"}:
        return ContextSectionId.CANONICAL_MODEL
    if value in {"SETUP", "SETUP_DEFINITION"}:
        return ContextSectionId.SETUP
    if value in {"CLAIM", "CLAIM_EVIDENCE"}:
        return ContextSectionId.CLAIMS
    if value in {"EVIDENCE", "EVIDENCE_RECORD"}:
        return ContextSectionId.EVIDENCE
    if value in {"TERM", "LINEAGE"}:
        return ContextSectionId.LINEAGE_TERMS
    return None


def permits_general_knowledge(intent_value: str) -> bool:
    return (intent_value or "").upper() in {
        "GENERAL_MARKET_KNOWLEDGE",
        "GENERAL_KNOWLEDGE",
        "TEACHING",
    }


def ordered_sections() -> tuple[ContextSectionId, ...]:
    return SECTION_ORDER


__all__ = [
    "section_for_object_type",
    "permits_general_knowledge",
    "ordered_sections",
]
