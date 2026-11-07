"""Pure interpreter entry point: text + authorized context -> typed plan."""

from __future__ import annotations

import re

from .actionability import is_actionable
from .context import InterpreterContext
from .depth import requested_depth
from .entities import (
    EntityKind,
    EntityRef,
    layer,
    market,
    model_ids,
    resolve_entities,
    setup_ids,
    unknown_model_ids,
)
from .enums import AmbiguityReason, Depth, Intent, PlanConfidence, TimeScope, worst_confidence
from .generations import classify_ambiguities
from .intent import classify_intent
from .numerical import is_deterministic_measurement, requires_evidence
from .plan import Ambiguity, AskCerebusQueryPlan
from .temporal import classify_time_scope

_FIELD_CUES: tuple[tuple[str, str], ...] = (
    ("state", "state"),
    ("setup", "setup"),
    ("setupcard", "setup"),
    ("level", "levels"),
    ("levels", "levels"),
    ("anchor", "levels"),
    ("coordinate", "levels"),
    ("evidence", "evidence"),
    ("claim", "evidence"),
    ("winrate", "evidence"),
    ("invalidation", "invalidation"),
    ("stop", "invalidation"),
    ("target", "targets"),
    ("path", "path"),
    ("clock", "clock"),
    ("session", "session"),
)


def _normalize(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("query text must be a string")
    normalized = " ".join(text.strip().lower().split())
    if not normalized:
        raise ValueError("query text must not be empty")
    return normalized


def _requested_fields(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for cue, field in _FIELD_CUES:
        if cue in text and field not in found:
            found.append(field)
    return tuple(found)


def interpret(
    text: str,
    context: InterpreterContext | None = None,
) -> AskCerebusQueryPlan:
    """Interpret a question without answering, retrieving or authorizing it."""

    normalized = _normalize(text)
    context = context or InterpreterContext(principal_scope="anonymous")

    intent = classify_intent(normalized)
    scope = classify_time_scope(normalized)

    entities = list(resolve_entities(normalized))
    unknown = unknown_model_ids(normalized)
    for raw in unknown:
        entities.append(EntityRef(kind=EntityKind.MODEL, text=raw, canonical_id=None))

    resolved_models = model_ids(tuple(entities))
    resolved_setups = setup_ids(tuple(entities))
    ambiguities, confidence = classify_ambiguities(
        normalized, tuple(entities), resolved_models, unknown
    )

    requested, effective = requested_depth(
        normalized, intent, scope, context.max_authorized_depth
    )
    findings = list(ambiguities)
    if effective is not requested:
        findings.append(
            Ambiguity(
                code=AmbiguityReason.DEPTH_CAPPED,
                material=False,
                candidates=(requested.value,),
                detail="authorized_depth_ceiling",
            )
        )
        confidence = worst_confidence(confidence, PlanConfidence.EXPLICIT_SCOPE)

    evidence_required = requires_evidence(normalized) or is_deterministic_measurement(
        normalized
    )
    # A statistic question may contain the word "target" without asking for an
    # action; the frozen intent taxonomy keeps those separate.
    actionable = is_actionable(normalized) and intent is not Intent.STATISTIC_EVIDENCE
    setup_required = actionable or intent is Intent.SETUP_CONTEXT
    historical_generations = {
        "P90",
        "P90.ORIGINAL",
        "P90P",
        "ST.MANUAL",
        "BASE80",
        "MARKOV.LEGACY",
        "FIB",
        "FIB.R15",
    }
    lineage_required = scope in (
        TimeScope.AS_OF,
        TimeScope.HISTORICAL_RESEARCH,
        TimeScope.MODEL_VERSION,
    ) or any(entity.generation in historical_generations for entity in entities)

    plan = AskCerebusQueryPlan(
        intent=intent,
        entities=tuple(entities),
        model_ids=resolved_models,
        setup_ids=resolved_setups,
        market=market(tuple(entities)),
        layer=layer(tuple(entities)),
        time_scope=scope,
        requested_depth=requested,
        effective_depth=effective,
        requires_live_intelligence=scope is TimeScope.CURRENT,
        requires_evidence=evidence_required,
        requires_lineage=lineage_required,
        requires_setup_context=setup_required,
        actionable=actionable,
        requested_fields=_requested_fields(normalized),
        confidence=confidence,
        ambiguities=tuple(findings),
    )
    return plan.finalized()


__all__ = ["interpret"]
