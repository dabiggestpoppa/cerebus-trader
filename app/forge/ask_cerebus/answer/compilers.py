"""Depth compilers over one validation core.

Compilers rearrange and label validated material. They never add a fact, number,
status, layer, eligibility or entitlement that the package does not carry.
"""

from __future__ import annotations

from app.forge.ask_cerebus.answer.admission import Admission
from app.forge.ask_cerebus.answer.citations import render
from app.forge.ask_cerebus.answer.enums import (
    BEGINNER_ORDER,
    OPERATOR_ORDER,
    RESEARCHER_ORDER,
    AnswerDepth,
    SectionId,
)
from app.forge.ask_cerebus.answer.schema import AnswerClaim, AnswerSection, CitationRef
from app.forge.ask_cerebus.answer.validators import PreparedClaim, propagated_limitations
from app.forge.ask_cerebus.context.enums import ContextSectionId

_HEADINGS = {
    SectionId.WHAT_IT_MEANS: "WHAT IT MEANS",
    SectionId.WHAT_CEREBUS_SEES: "WHAT CEREBUS SEES",
    SectionId.WHAT_IT_DOES_NOT_MEAN: "WHAT IT DOES NOT MEAN",
    SectionId.NEXT_RELEVANT_STATE: "NEXT RELEVANT STATE / LEVEL",
    SectionId.MODEL_LAYER: "MODEL / LAYER",
    SectionId.CURRENT_STATE: "CURRENT STATE",
    SectionId.ELIGIBILITY: "ELIGIBILITY",
    SectionId.ACTIVE_RANGE_ANCHOR: "ACTIVE RANGE / ANCHOR",
    SectionId.CLOCK: "CLOCK",
    SectionId.PATH_RANGE_LEFT: "PATH / RANGE LEFT",
    SectionId.LEVELS: "LEVELS",
    SectionId.TRIGGER: "TRIGGER",
    SectionId.INVALIDATION: "INVALIDATION",
    SectionId.TARGETS: "TARGETS",
    SectionId.EVIDENCE_STATUS: "EVIDENCE STATUS",
    SectionId.MODEL_VERSION: "MODEL / VERSION",
    SectionId.CLAIM_EVENT: "CLAIM / EVENT",
    SectionId.POPULATION_N: "POPULATION / N",
    SectionId.PERIOD_GENERATION: "PERIOD / GENERATION",
    SectionId.METRIC_RESULT: "METRIC / RESULT",
    SectionId.OOS_REPRODUCTION: "OOS / REPRODUCTION",
    SectionId.CONTRADICTIONS_NEGATIVE: "CONTRADICTIONS / NEGATIVE EVIDENCE",
}

_BEGINNER_MEANS_SECTIONS = frozenset(
    {
        ContextSectionId.CANONICAL_MODEL,
        ContextSectionId.QUERY_CONTRACT,
        ContextSectionId.CLAIMS,
        ContextSectionId.LINEAGE_TERMS,
        ContextSectionId.GENERAL_KNOWLEDGE,
    }
)

_BEGINNER_SEES_SECTIONS = frozenset(
    {ContextSectionId.CURRENT_INTELLIGENCE, ContextSectionId.SETUP}
)

_OPERATOR_KEYS = {
    SectionId.CURRENT_STATE: ("state",),
    SectionId.ACTIVE_RANGE_ANCHOR: ("anchor", "range"),
    SectionId.CLOCK: ("clock", "as_of", "data_cutoff"),
    SectionId.PATH_RANGE_LEFT: ("path_left", "path"),
    SectionId.LEVELS: ("levels",),
    SectionId.TRIGGER: ("trigger",),
    SectionId.INVALIDATION: ("invalidation",),
    SectionId.TARGETS: ("targets",),
}

_RESEARCHER_KEYS = {
    SectionId.MODEL_VERSION: ("model", "version", "model_version"),
    SectionId.CLAIM_EVENT: ("claim_id", "event_identity", "identity"),
    SectionId.POPULATION_N: ("conditioning_population", "sample_size", "small_n_flag"),
    SectionId.PERIOD_GENERATION: ("research_period", "generation"),
    SectionId.METRIC_RESULT: ("metric", "result"),
    SectionId.OOS_REPRODUCTION: ("oos_status", "support_classification", "status"),
}

_NOT_ENCODED = "not encoded in the authorized context"


def _claim_section(admission: Admission, prepared: PreparedClaim) -> SectionId:
    depth = admission.depth
    sections = {source.section_id for source in prepared.sources}
    labels = {source.label.value for source in prepared.sources}
    if depth is AnswerDepth.BEGINNER:
        if labels & {"NEGATIVE_EVIDENCE", "INSUFFICIENT_EVIDENCE"}:
            return SectionId.WHAT_IT_DOES_NOT_MEAN
        if sections & _BEGINNER_SEES_SECTIONS:
            return SectionId.WHAT_CEREBUS_SEES
        if sections & {ContextSectionId.LIMITATIONS_NEGATIVE}:
            return SectionId.WHAT_IT_DOES_NOT_MEAN
        if sections & _BEGINNER_MEANS_SECTIONS:
            return SectionId.WHAT_IT_MEANS
        return SectionId.WHAT_IT_MEANS
    if depth is AnswerDepth.OPERATOR:
        if sections & {ContextSectionId.SETUP}:
            return SectionId.ELIGIBILITY
        if sections & {ContextSectionId.CURRENT_INTELLIGENCE}:
            return SectionId.CURRENT_STATE
        if sections & {ContextSectionId.EVIDENCE}:
            return SectionId.EVIDENCE_STATUS
        if sections & {ContextSectionId.LIMITATIONS_NEGATIVE}:
            return SectionId.EVIDENCE_STATUS
        return SectionId.MODEL_LAYER
    if labels & {"NEGATIVE_EVIDENCE"}:
        return SectionId.CONTRADICTIONS_NEGATIVE
    if sections & {ContextSectionId.LIMITATIONS_NEGATIVE}:
        return SectionId.CONTRADICTIONS_NEGATIVE
    if sections & {ContextSectionId.EVIDENCE}:
        return SectionId.POPULATION_N
    if sections & {ContextSectionId.CLAIMS}:
        return SectionId.CLAIM_EVENT
    return SectionId.MODEL_VERSION


def _rendered_claim(item: PreparedClaim) -> str:
    """Render a claim with its trust classification visible.

    A claim quoting an untrusted passage keeps its text, its citation and its
    quotation, and gains an explicit marker naming the source that made the
    statement. CEREBUS never renders retrieved text as its own finding.
    """

    untrusted = item.untrusted_sources
    if not untrusted:
        return item.text
    return f"untrusted source {untrusted[0].ref}: {item.text}"


def _field_lines(entries, keys: tuple[str, ...]) -> list[str]:
    lines: list[str] = []
    for key in keys:
        found = ""
        for entry in entries:
            value = entry.fact_map.get(key, "")
            if value and not found:
                found = value
        lines.append(f"{key}: {found or _NOT_ENCODED}")
    return lines


def _entry_bullets(admission: Admission, claim_ids_by_ref: dict[str, str]) -> dict[SectionId, list[str]]:
    index = admission.index
    bullets: dict[SectionId, list[str]] = {}

    for section_id, keys in _OPERATOR_KEYS.items():
        entries = index.items
        bullets[section_id] = _field_lines(entries, keys)

    setup_entries = index.setup_items()
    verdicts: list[str] = []
    for entry in setup_entries:
        verdict = (
            entry.fact_map.get("setup_verdict")
            or entry.fact_map.get("verdict")
            or entry.fact_map.get("eligibility")
            or entry.item.source_status
        ).upper()
        if verdict:
            verdicts.append(f"eligibility: {verdict}")
        reason = entry.fact_map.get("reason") or entry.item.source_status
        if reason:
            verdicts.append(f"reason: {reason}")
    bullets[SectionId.ELIGIBILITY] = verdicts or ["eligibility: not encoded", f"reason: {_NOT_ENCODED}"]

    model_lines: list[str] = []
    for entry in index.items:
        if entry.ref_type in ("MODEL", "TERM", "SETUP"):
            layer = entry.layer or "CROSS_LAYER"
            model_lines.append(f"{entry.ref}: layer {layer} status {entry.item.source_status}")
    bullets[SectionId.MODEL_LAYER] = model_lines or [f"model: {_NOT_ENCODED}"]

    evidence_lines: list[str] = []
    for entry in index.items:
        if entry.ref_type == "LIMITATION":
            evidence_lines.append(f"limitation {entry.item.source_status}: preserved")
            continue
        if entry.ref_type in ("EVIDENCE", "CLAIM", "INTELLIGENCE", "NEGATIVE", "MODEL", "SETUP"):
            line = f"{entry.ref} ({entry.item.source_ref_type}): {entry.label.value}"
            if entry.item.generation:
                line += f", generation {entry.item.generation}"
            evidence_lines.append(line)
    bullets[SectionId.EVIDENCE_STATUS] = evidence_lines or [f"evidence: {_NOT_ENCODED}"]

    for section_id, keys in _RESEARCHER_KEYS.items():
        bullets[section_id] = _field_lines(index.items, keys)
    generations: list[str] = []
    for entry in index.items:
        if entry.item.generation and entry.item.generation not in generations:
            generations.append(entry.item.generation)
    bullets[SectionId.PERIOD_GENERATION] = bullets[SectionId.PERIOD_GENERATION] + [
        f"generation: {value}" for value in generations
    ]

    contradictions: list[str] = []
    for entry in index.items:
        if entry.label.value in ("NEGATIVE_EVIDENCE", "FALSIFIED"):
            contradictions.append(f"{entry.ref}: {entry.label.value}")
        elif entry.ref_type == "NEGATIVE":
            contradictions.append(f"{entry.ref}: negative evidence")
    for limitation in index.limitations():
        contradictions.append(f"limitation: {limitation}")
    bullets[SectionId.CONTRADICTIONS_NEGATIVE] = contradictions or [
        f"contradictions: {_NOT_ENCODED}"
    ]

    next_state: list[str] = []
    for entry in setup_entries:
        for key in ("next_state", "anchor", "levels", "trigger"):
            value = entry.fact_map.get(key, "")
            if value:
                next_state.append(f"{key}: {value}")
    if admission.index.as_of_values():
        next_state.append(f"as_of: {admission.index.as_of_values()[0]}")
    bullets[SectionId.NEXT_RELEVANT_STATE] = next_state or [
        f"next relevant state/level: {_NOT_ENCODED}"
    ]
    return bullets


def compile_answer(
    admission: Admission,
    prepared: tuple[PreparedClaim, ...],
    citations: tuple[CitationRef, ...],
) -> tuple[tuple[AnswerSection, ...], tuple[AnswerClaim, ...]]:
    citation_by_ref = {citation.source_ref_id: citation.source_ref_id for citation in citations}
    rendered_refs: set[str] = set(citation_by_ref)

    answer_claims: list[AnswerClaim] = []
    for item in prepared:
        section_id = _claim_section(admission, item)
        citation_ids: list[str] = []
        for source in item.sources:
            citation = render(source)
            if citation is not None and citation.source_ref_id in rendered_refs:
                if citation.source_ref_id not in citation_ids:
                    citation_ids.append(citation.source_ref_id)
        answer_claims.append(
            AnswerClaim(
                claim_id=item.claim_id,
                text=item.text,
                section_id=section_id,
                epistemic_label=item.draft.epistemic_label,
                layer=item.draft.layer,
                generation=item.draft.generation,
                source_refs=tuple(item.draft.source_refs),
                citation_ids=tuple(citation_ids),
            )
        )

    prepared_by_id = {item.claim_id: item for item in prepared}
    field_bullets = _entry_bullets(admission, {})
    order = {
        AnswerDepth.BEGINNER: BEGINNER_ORDER,
        AnswerDepth.OPERATOR: OPERATOR_ORDER,
        AnswerDepth.RESEARCHER: RESEARCHER_ORDER,
    }[admission.depth]

    sections: list[AnswerSection] = []
    for section_id in order:
        claims = [claim for claim in answer_claims if claim.section_id is section_id]
        bullets: list[str] = []
        rendered = {
            claim.claim_id: _rendered_claim(prepared_by_id[claim.claim_id]) for claim in claims
        }
        if section_id is SectionId.WHAT_IT_MEANS:
            bullets = [rendered[claim.claim_id] for claim in claims] or [f"meaning: {_NOT_ENCODED}"]
        elif section_id is SectionId.WHAT_CEREBUS_SEES:
            bullets = [rendered[claim.claim_id] for claim in claims] or [
                f"authorized state: {_NOT_ENCODED}"
            ]
        elif section_id is SectionId.WHAT_IT_DOES_NOT_MEAN:
            bullets = [rendered[claim.claim_id] for claim in claims]
            bullets.extend(f"limitation: {value}" for value in admission.index.limitations())
            bullets.extend(
                f"unresolved: {value}" for value in propagated_limitations(admission)
            )
            bullets = bullets or [f"limitations: {_NOT_ENCODED}"]
        elif section_id is SectionId.CONTRADICTIONS_NEGATIVE:
            bullets = [rendered[claim.claim_id] for claim in claims] + field_bullets[section_id]
        else:
            bullets = field_bullets[section_id] + [rendered[claim.claim_id] for claim in claims]
        deduped: list[str] = []
        for bullet in bullets:
            if bullet not in deduped:
                deduped.append(bullet)
        sections.append(
            AnswerSection(
                section_id=section_id,
                heading=_HEADINGS[section_id],
                bullets=tuple(deduped),
                claim_ids=tuple(claim.claim_id for claim in claims),
            )
        )
    return tuple(sections), tuple(answer_claims)


def answer_limitations(admission: Admission) -> tuple[str, ...]:
    out: list[str] = list(admission.index.limitations())
    for value in propagated_limitations(admission):
        if value not in out:
            out.append(value)
    return tuple(out)


__all__ = ["compile_answer", "answer_limitations"]
