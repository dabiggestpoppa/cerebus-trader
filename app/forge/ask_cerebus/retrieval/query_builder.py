"""Translate a frozen IV.1 plan into deterministic resolver targets."""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.ask_cerebus.interpreter.enums import EntityKind, Intent, TimeScope


@dataclass(frozen=True)
class ResolverTargets:
    model_tokens: tuple[str, ...]
    setup_ids: tuple[str, ...]
    term_ids: tuple[str, ...]
    market: str | None
    layer: str | None
    text_terms: tuple[str, ...]
    requires_claim_evidence: bool
    requires_lineage: bool
    requires_setup_context: bool
    time_scope: TimeScope
    intent: Intent


def build_targets(plan) -> ResolverTargets:
    models: list[str] = list(plan.model_ids)
    setups: list[str] = list(plan.setup_ids)
    terms: list[str] = []
    texts: list[str] = []
    for entity in plan.entities:
        if entity.kind is EntityKind.MODEL and entity.canonical_id:
            if entity.canonical_id not in models:
                models.append(entity.canonical_id)
        elif entity.kind is EntityKind.SETUP and entity.canonical_id:
            if entity.canonical_id not in setups:
                setups.append(entity.canonical_id)
        elif entity.kind is EntityKind.TERM and entity.canonical_id:
            if entity.canonical_id not in terms:
                terms.append(entity.canonical_id)
        if entity.text:
            texts.append(entity.text)
    return ResolverTargets(
        model_tokens=tuple(models),
        setup_ids=tuple(setups),
        term_ids=tuple(terms),
        market=plan.market,
        layer=plan.layer.value if plan.layer is not None else None,
        text_terms=tuple(sorted(set(texts))),
        requires_claim_evidence=bool(
            plan.requires_evidence
            or plan.intent is Intent.STATISTIC_EVIDENCE
        ),
        requires_lineage=bool(plan.requires_lineage),
        requires_setup_context=bool(plan.requires_setup_context),
        time_scope=plan.time_scope,
        intent=plan.intent,
    )


__all__ = ["ResolverTargets", "build_targets"]
