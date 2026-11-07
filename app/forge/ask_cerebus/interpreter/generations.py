"""Historical-generation safeguards and deterministic ambiguity findings."""

from __future__ import annotations

import re

from .entities import EntityKind, EntityRef
from .enums import AmbiguityReason, PlanConfidence, worst_confidence
from .plan import Ambiguity

_P90 = re.compile(r"\bp90\b")
_BTC_TRACKER = re.compile(r"\bbtc\s+tracker\b")
_FIB_PRODUCTION = re.compile(r"\b(production|r15)\b")
_AUTOMATION = re.compile(r"\b(automation|automated|autonomous|auto\s*trade|autotrade)\b")
_VERSION = re.compile(r"\bv(\d+)\b")
_GENERATION = re.compile(r"\bgeneration\b")
_PERCENT = re.compile(r"\d+(?:\.\d+)?\s*%")
_STAT = re.compile(r"(win\s*rate|probabilit|expectanc|correlation|hit\s*rate|results?\b)")


def classify_ambiguities(
    text: str,
    entities: tuple[EntityRef, ...],
    model_ids: tuple[str, ...],
    unknown_ids: tuple[str, ...] = (),
) -> tuple[tuple[Ambiguity, ...], PlanConfidence]:
    """Return structured ambiguity findings and the worst confidence."""

    findings: list[Ambiguity] = []
    confidence = PlanConfidence.CERTAIN

    def add(
        code: AmbiguityReason,
        *,
        material: bool,
        candidates: tuple[str, ...] = (),
        detail: str = "",
        level: PlanConfidence,
    ) -> None:
        nonlocal confidence
        findings.append(
            Ambiguity(
                code=code,
                material=material,
                candidates=candidates,
                detail=detail,
            )
        )
        confidence = worst_confidence(confidence, level)

    for unknown in unknown_ids:
        add(
            AmbiguityReason.UNSUPPORTED_IDENTITY,
            material=True,
            detail="unknown_canonical_model",
            level=PlanConfidence.UNSUPPORTED,
        )

    version = _VERSION.search(text)
    if version and _GENERATION.search(text):
        if int(version.group(1)) > 2:
            add(
                AmbiguityReason.UNAVAILABLE_GENERATION,
                material=True,
                candidates=tuple(model_ids),
                detail="generation_not_retained",
                level=PlanConfidence.UNSUPPORTED,
            )

    if "P90" in model_ids:
        if _P90.search(text) and not re.search(r"\boriginal\b", text):
            add(
                AmbiguityReason.AMBIGUOUS_GENERATION,
                material=True,
                candidates=("P90.ORIGINAL", "P90"),
                detail="current_generation_unspecified",
                level=PlanConfidence.AMBIGUOUS,
            )
        elif re.search(r"\boriginal\b", text):
            add(
                AmbiguityReason.AMBIGUOUS_GENERATION,
                material=False,
                candidates=("P90.ORIGINAL",),
                detail="original_generation_pinned",
                level=PlanConfidence.EXPLICIT_SCOPE,
            )

    if "BTC.GAME" in model_ids and "BTC.TRACKER" not in model_ids:
        add(
            AmbiguityReason.AMBIGUOUS_MODEL,
            material=False,
            candidates=("BTC.GAME",),
            detail="research_artifact_not_launch_canonical",
            level=PlanConfidence.EXPLICIT_SCOPE,
        )

    if "ST" in model_ids and _AUTOMATION.search(text):
        add(
            AmbiguityReason.AMBIGUOUS_MODEL,
            material=False,
            candidates=("ST.MANUAL",),
            detail="automation_not_approved",
            level=PlanConfidence.EXPLICIT_SCOPE,
        )

    if "FIB.RANGE_BIRTH" in model_ids and _FIB_PRODUCTION.search(text):
        add(
            AmbiguityReason.AMBIGUOUS_MODEL,
            material=True,
            candidates=("FIB.RANGE_BIRTH",),
            detail="fib_production_gated",
            level=PlanConfidence.AMBIGUOUS,
        )

    if _PERCENT.search(text) and _STAT.search(text):
        add(
            AmbiguityReason.UNSUPPORTED_STATISTIC,
            material=True,
            detail="numeric_claim_without_evidence_id",
            level=PlanConfidence.UNSUPPORTED,
        )

    if any(
        entity.kind is EntityKind.TERM
        and entity.generation == "HISTORICAL_ALIAS"
        for entity in entities
    ):
        add(
            AmbiguityReason.AMBIGUOUS_MODEL,
            material=False,
            detail="historical_alias_crosswalk",
            level=PlanConfidence.EXPLICIT_SCOPE,
        )

    return tuple(findings), confidence


__all__ = ["classify_ambiguities"]
