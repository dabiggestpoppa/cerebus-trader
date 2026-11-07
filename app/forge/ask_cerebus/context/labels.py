"""Epistemic mapping and numerical-admission rules for IV.3."""

from __future__ import annotations

from app.forge.ask_cerebus.context.enums import EpistemicLabel, SmallNFlag

_NEGATIVE = {
    "FALSIFIED",
    "NO_GO",
    "INTERNAL_CONTRADICTION",
    "IMPLEMENTATION_NOT_PARITY_SAFE",
}

_DIRECT = {
    "CANONICAL",
    "VALIDATED",
    "FORWARD_OOS",
    "CANDIDATE",
    "RESEARCH_FLAG",
    "HISTORICAL",
    "NEGATIVE_EVIDENCE",
    "PARKED",
    "SUPERSEDED",
    "GENERAL_KNOWLEDGE",
    "INSUFFICIENT_EVIDENCE",
}

_ALLOWED_NUMBER_LABELS = {
    EpistemicLabel.VALIDATED,
    EpistemicLabel.FORWARD_OOS,
    EpistemicLabel.CANDIDATE,
    EpistemicLabel.RESEARCH_FLAG,
    EpistemicLabel.HISTORICAL,
}


def map_status(status: str, *, direct: bool = False) -> EpistemicLabel:
    """Map an upstream status without promoting it."""

    if direct:
        return EpistemicLabel.CANONICAL
    value = (status or "").upper()
    if value in _DIRECT:
        # INFERENCE is reserved for the later answer layer and must never be
        # introduced by a source-status mapping.
        if value == EpistemicLabel.INFERENCE.value:
            return EpistemicLabel.INSUFFICIENT_EVIDENCE
        return EpistemicLabel(value)
    if value in _NEGATIVE:
        return EpistemicLabel.NEGATIVE_EVIDENCE
    return EpistemicLabel.INSUFFICIENT_EVIDENCE


def number_is_admissible(label: EpistemicLabel, join_status: str) -> bool:
    return (
        (join_status or "").upper() in {"VERIFIED", "SUPPORTED"}
        and label in _ALLOWED_NUMBER_LABELS
    )


def small_n_state(
    sample_size: int | None,
    flag: SmallNFlag,
    threshold_ref: str,
) -> SmallNFlag:
    if sample_size is None or not threshold_ref:
        return SmallNFlag.UNRESOLVED
    return flag


__all__ = ["map_status", "number_is_admissible", "small_n_state"]
