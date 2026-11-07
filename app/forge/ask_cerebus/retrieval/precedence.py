"""Frozen six-tier source precedence."""

from __future__ import annotations

from .enums import PrecedenceTier


def tier_for_object_type(object_type: str) -> PrecedenceTier:
    if object_type in ("MODEL", "SETUP", "TERM", "CLAIM", "EVIDENCE"):
        return PrecedenceTier.DIRECT_CANONICAL
    if object_type in ("DOCTRINE", "LINEAGE"):
        return PrecedenceTier.LINEAGE_DOCTRINE
    if object_type == "INTELLIGENCE":
        return PrecedenceTier.CURRENT_INTELLIGENCE
    return PrecedenceTier.SOURCE_DERIVED_PASSAGE


def semantic_tier() -> PrecedenceTier:
    return PrecedenceTier.SOURCE_DERIVED_PASSAGE


def ordering_key(tier: PrecedenceTier, object_id: str, generation: str = ""):
    return (int(tier), object_id, generation)


__all__ = ["tier_for_object_type", "semantic_tier", "ordering_key"]
