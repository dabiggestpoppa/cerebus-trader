"""Deterministic UI components for the Book V interface.

All functions are pure: they take presentation model data
(:class:`BookVInterfaceResponse` or its elements) and return HTML strings.
No network calls, no route access, no provider integration, no state
mutation. Components are deterministic functions of the presentation
model produced by :class:`PresentationAdapter`.

Security boundaries:

* All user-provided text is HTML-escaped before rendering.
* No internal evidence identifiers (row ids, manifest digests, object ids)
  are rendered.
* No raw :class:`GatewayDraft` provider output is accepted.
* No provider, model, latency, cost, or prompt internals are rendered.
* Refusals never render as successful answers.
* Empty ``limitations`` tuples remain valid (never synthesized).
"""

from __future__ import annotations

from typing import Any

from app.forge.book_v.presentation.model import (
    BookVCitation,
    BookVClaim,
    BookVInterfaceResponse,
    BookVNumber,
    BookVSection,
)

#: Validated answer depths per IV.5 ``AnswerDepth``.
VALID_DEPTHS = frozenset({"BEGINNER", "OPERATOR", "RESEARCHER"})

#: Valid setup eligibility verdicts per IV.5 ``SetupVerdict``.
VALID_VERDICTS = frozenset({"ELIGIBLE", "WATCH", "UNRESOLVED", "BLOCKED"})


def _escape(text: str) -> str:
    """Escape HTML special characters in user-provided text."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _attr(name: str, value: str) -> str:
    """Render a single HTML attribute with an escaped value."""
    return f'{name}="{_escape(value)}"'


def render_depth_badge(depth: str) -> str:
    """Render a depth badge (BEGINNER/OPERATOR/RESEARCHER).

    Implements BV-F1-06: display answer depth. The depth label is
    preserved verbatim from the presentation model; no semantic
    reinterpretation is performed.
    """
    if depth not in VALID_DEPTHS:
        raise ValueError(f"Invalid answer depth: {depth!r}")
    return (
        f'<span class="depth-badge depth-{depth.lower()}" '
        f'{_attr("aria-label", f"Depth: {depth}")} '
        f'aria-hidden="true">{_escape(depth)}</span>'
    )


def render_citation(citation: BookVCitation) -> str:
    """Render a single citation with safe provenance fields.

    Implements BV-F1-04: preserve model generation in citations. The
    ``source_ref_id`` is an authorized package reference, never an
    internal row or object id. All fields are escaped before rendering.
    """
    return (
        f'<div class="citation" {_attr("data-ref-id", citation.source_ref_id)}>'
        f'<span class="citation-ref-id">{_escape(citation.source_ref_id)}</span>'
        f'<span class="citation-type">{_escape(citation.source_ref_type)}</span>'
        f'<span class="citation-status">{_escape(citation.source_status)}</span>'
        f'<span class="citation-generation">{_escape(citation.generation)}</span>'
        f"</div>"
    )


def render_citations(citations: tuple[BookVCitation, ...]) -> str:
    """Render all citations as a bounded, attributed list."""
    if not citations:
        return '<div class="citations" aria-label="No citations"></div>'
    items = "".join(render_citation(c) for c in citations)
    return f'<div class="citations">{items}</div>'


def render_numbers(numbers: tuple[BookVNumber, ...]) -> str:
    """Render numeric values that resolve to authorized package evidence.

    Implements BV-F1-08: refuse unsupported statistics. Numbers are only
    rendered when they appear in the presentation model (i.e. they have
    already been validated by IV.5). No number is invented or
    recalculated here.
    """
    if not numbers:
        return '<div class="numbers" aria-label="No numbers"></div>'
    items = "".join(
        f'<div class="number">'
        f'<span class="number-value">{_escape(n.value_text)}</span>'
        f'<span class="number-unit">{_escape(n.unit)}</span>'
        f'<span class="number-source">{_escape(n.source_ref_id)}</span>'
        f"</div>"
        for n in numbers
    )
    return f'<div class="numbers">{items}</div>'


def render_claim(claim: BookVClaim) -> str:
    """Render a single claim preserving epistemic status and generation.

    Implements BV-F1-01 and BV-F1-05: render claims and preserve
    epistemic labels. The label is copied verbatim from the presentation
    model; it is never upgraded or reinterpreted.
    """
    return (
        f'<div class="claim" {_attr("data-claim-id", claim.claim_id)} '
        f'{_attr("aria-label", f"Claim {claim.claim_id}")}>'
        f'<span class="claim-epistemic-label">{_escape(claim.epistemic_label)}</span>'
        f'<span class="claim-layer">{_escape(claim.layer)}</span>'
        f'<span class="claim-generation">{_escape(claim.generation)}</span>'
        f'<span class="claim-text">{_escape(claim.text)}</span>'
        f"</div>"
    )


def render_section(section: BookVSection) -> str:
    """Render a single answer section preserving ratified depth order.

    Implements BV-F1-01 and BV-F2-03: render sections and preserve
    section order. Sections are rendered in the order supplied by the
    presentation model, which reflects IV.5 ``SECTION_ORDER`` for the
    answer depth.
    """
    bullets = "".join(f"<li>{_escape(b)}</li>" for b in section.bullets)
    return (
        f'<section class="answer-section" '
        f'{_attr("data-section-id", section.section_id)} '
        f'{_attr("aria-label", f"Section {section.heading}")}>'
        f"<h3>{_escape(section.heading)}</h3>"
        f"<ul>{bullets}</ul>"
        f"</section>"
    )


def render_answer_sections(
    sections: tuple[BookVSection, ...],
) -> str:
    """Render answer sections in ratified depth order.

    Implements BV-F2-03: depth-aware answer layout. Sections preserve
    their IV.5 ``SECTION_ORDER`` for the answer depth; no section is
    dropped, added, or reordered.
    """
    if not sections:
        return '<div class="sections" aria-label="No sections"></div>'
    items = "".join(render_section(s) for s in sections)
    return f'<div class="sections">{items}</div>'


def render_limitations(limitations: tuple[str, ...]) -> str:
    """Render inherited context limitations.

    Implements BV-F1-09: preserve limitations as inherited restrictions.
    An empty tuple is legal and is rendered as "(no inherited
    limitations)" — it is never treated as evidence that a refusal has
    no reason, and no limitation is synthesized.
    """
    if not limitations:
        return (
            '<div class="limitations empty" aria-label="No inherited limitations">'
            "<span>(no inherited limitations)</span></div>"
        )
    items = "".join(f"<li>{_escape(l)}</li>" for l in limitations)
    return f'<div class="limitations"><ul>{items}</ul></div>'


def render_eligibility(verdict: str) -> str:
    """Render setup eligibility verdict.

    Implements BV-F1-07: display setup eligibility verdict. The verdict
    is preserved verbatim from the presentation model; no eligibility
    change is performed here.
    """
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"Invalid setup verdict: {verdict!r}")
    return (
        f'<span class="eligibility verdict-{verdict.lower()}" '
        f'{_attr("aria-label", f"Setup eligibility: {verdict}")} '
        f'aria-hidden="true">{_escape(verdict)}</span>'
    )


def render_refusal(
    code: str,
    detail: str,
    findings: tuple[str, ...],
    limitations: tuple[str, ...],
) -> str:
    """Render a governed refusal per F-07a Option C.

    Implements BV-F1-02 and BV-F2-01: render refusal code/detail/findings
    per Option C. ``code`` is the primary refusal reason; ``findings`` are
    supporting validation findings; ``detail`` is consumer-safe
    explanatory prose; ``limitations`` are inherited context restrictions
    shown alongside, never merged into the reason. An empty ``limitations``
    tuple is legal and never suppresses the refusal.
    """
    findings_html = "".join(f"<li>{_escape(f)}</li>" for f in findings)
    if limitations:
        limitations_html = "".join(f"<li>{_escape(l)}</li>" for l in limitations)
    else:
        limitations_html = '<li class="none">(no inherited limitations)</li>'
    return (
        f'<div class="refusal" {_attr("data-refusal-code", code)} '
        f'{_attr("aria-label", f"Refusal: {code}")} '
        f'role="alert" aria-live="polite">'
        f'<div class="refusal-code">{_escape(code)}</div>'
        f'<div class="refusal-detail">{_escape(detail)}</div>'
        f'<div class="refusal-findings"><ul>{findings_html}</ul></div>'
        f'<div class="refusal-limitations"><ul>{limitations_html}</ul></div>'
        f"</div>"
    )


def render_validated_answer(response: BookVInterfaceResponse) -> str:
    """Render a validated answer as HTML.

    Implements BV-F1-01 through BV-F1-10: render sections, claims,
    citations, answer_id, depth, model generation, epistemic labels,
    setup eligibility, limitations, and refusal of unsupported
    statistics. No number is rendered unless it resolves to authorized
    package evidence.
    """
    sections_html = render_answer_sections(response.sections)
    claims_html = "".join(render_claim(c) for c in response.claims)
    citations_html = render_citations(response.citations)
    numbers_html = render_numbers(response.numbers)
    limitations_html = render_limitations(response.limitations)
    depth_html = render_depth_badge(response.depth)
    return (
        f'<div class="validated-answer" '
        f'{_attr("data-outcome", "VALIDATED_ANSWER")} '
        f'{_attr("data-answer-id", response.answer_id)} '
        f'{_attr("aria-label", "Validated answer")} '
        f'aria-live="polite">'
        f'{depth_html}'
        f'{sections_html}'
        f'<div class="claims">{claims_html}</div>'
        f'{citations_html}'
        f'{numbers_html}'
        f'{limitations_html}'
        f"</div>"
    )


def render_governed_refusal(response: BookVInterfaceResponse) -> str:
    """Render a governed refusal as HTML.

    Implements BV-F1-02 and BV-F2-01: render refusal code/detail/findings
    per F-07a Option C. A refusal never renders as a successful answer:
    no sections, claims, citations, or numbers are rendered.
    """
    depth_html = render_depth_badge(response.depth)
    refusal_html = render_refusal(
        response.code, response.detail, response.findings, response.limitations
    )
    return (
        f'<div class="governed-refusal" '
        f'{_attr("data-outcome", "GOVERNED_REFUSAL")} '
        f'{_attr("data-answer-id", response.answer_id)} '
        f'{_attr("aria-label", "Governed refusal")} '
        f'role="alert" aria-live="polite">'
        f'{depth_html}'
        f'{refusal_html}'
        f"</div>"
    )


def render_interface_response(response: BookVInterfaceResponse) -> str:
    """Main renderer - dispatches based on outcome.

    Accepts only :class:`BookVInterfaceResponse` (produced by the
    presentation adapter). Raises :class:`ValueError` for any input that
    is not a :class:`BookVInterfaceResponse` or for any outcome other
    than ``VALIDATED_ANSWER`` or ``GOVERNED_REFUSAL``.
    """
    if not isinstance(response, BookVInterfaceResponse):
        raise ValueError(
            "Book V UI rendering accepts only BookVInterfaceResponse; "
            f"got {type(response).__name__!r}"
        )
    if response.is_answer():
        return render_validated_answer(response)
    if response.is_refusal():
        return render_governed_refusal(response)
    raise ValueError(f"Unknown interface response outcome: {response.outcome!r}")


__all__ = [
    "VALID_DEPTHS",
    "VALID_VERDICTS",
    "render_answer_sections",
    "render_citation",
    "render_citations",
    "render_claim",
    "render_eligibility",
    "render_governed_refusal",
    "render_interface_response",
    "render_limitations",
    "render_numbers",
    "render_refusal",
    "render_section",
    "render_validated_answer",
]
