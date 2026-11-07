"""Canonical compression helpers for IV.3."""

from __future__ import annotations

from app.forge.ask_cerebus.context.enums import EpistemicLabel, TrustClass
from app.forge.ask_cerebus.context.schema import ContextFact, ContextItem
from app.forge.ask_cerebus.context.trust import fact_key_allowed, normalise_excerpt


def facts(*pairs: tuple[str, object, str]) -> tuple[ContextFact, ...]:
    out: list[ContextFact] = []
    for key, value, unit in pairs:
        if not fact_key_allowed(key):
            raise ValueError(f"fact key is not allowlisted: {key}")
        if value is None:
            continue
        text = str(value)
        if not text:
            continue
        out.append(ContextFact(key=key, value_text=text, unit=unit))
    return tuple(out)


def item(
    *,
    section: str,
    source_ref_id: str,
    source_ref_type: str,
    source_status: str,
    label: EpistemicLabel,
    layer: str = "",
    exposure: str = "",
    generation: str = "",
    trust_class: TrustClass = TrustClass.TRUSTED_CONTROL,
    facts: tuple[ContextFact, ...] = (),
    text: str | None = None,
    quote_scope: str = "NONE",
    provenance_refs: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    priority: int = 3,
    mandatory: bool = False,
) -> ContextItem:
    del section  # section membership is assigned by the selector
    return ContextItem(
        item_id="",
        source_ref_id=source_ref_id,
        source_ref_type=source_ref_type,
        source_status=source_status,
        epistemic_label=label,
        layer=layer,
        exposure=exposure,
        generation=generation,
        trust_class=trust_class,
        facts=facts,
        text=text,
        quote_scope=quote_scope,
        provenance_refs=provenance_refs,
        evidence_refs=evidence_refs,
        priority=priority,
        mandatory=mandatory,
    )


def excerpt(text: str, *, max_chars: int) -> str | None:
    value = normalise_excerpt(text, max_chars=max_chars)
    return value or None


__all__ = ["facts", "item", "excerpt"]
