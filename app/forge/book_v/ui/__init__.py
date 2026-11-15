"""Book V deterministic UI component layer.

Pure HTML rendering components that consume the ratified
``BookVInterfaceResponse`` produced by the Book V presentation adapter.
No network calls, no routes, no production endpoints, no provider
integration. Components are deterministic functions of the presentation
model.
"""

from .components import (
    render_answer_sections,
    render_citation,
    render_citations,
    render_claim,
    render_eligibility,
    render_governed_refusal,
    render_interface_response,
    render_limitations,
    render_numbers,
    render_refusal,
    render_section,
    render_validated_answer,
)
from .versions import BOOK_V_UI_CONTRACT_V1, BOOK_V_UI_SCHEMA_V1

__all__ = [
    "BOOK_V_UI_CONTRACT_V1",
    "BOOK_V_UI_SCHEMA_V1",
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
