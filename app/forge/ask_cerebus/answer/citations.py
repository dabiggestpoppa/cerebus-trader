"""Citation resolution and user-facing provenance rendering.

A citation must support the exact claim, not merely exist somewhere in the
package. Rendering exposes only user-facing provenance fields; internal object
identifiers are never emitted.
"""

from __future__ import annotations

import re

from app.forge.ask_cerebus.answer.resolution import PackageIndex, ResolvedItem
from app.forge.ask_cerebus.answer.schema import CitationRef

_INTERNAL_REF_PATTERNS = (
    re.compile(r"^PKG\.", re.IGNORECASE),
    re.compile(r"^MFD\.", re.IGNORECASE),
    re.compile(r"^CTX\.", re.IGNORECASE),
    re.compile(r"^ROW\.", re.IGNORECASE),
    re.compile(r"^ITEM[._:]", re.IGNORECASE),
    re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-", re.IGNORECASE),
)


def is_internal_ref(ref: str) -> bool:
    """True when a reference names an internal object rather than provenance."""

    value = (ref or "").strip()
    if not value:
        return True
    if any(pattern.search(value) for pattern in _INTERNAL_REF_PATTERNS):
        return True
    lowered = value.lower()
    return any(
        token in lowered
        for token in (
            "object_id",
            "item_id",
            "row_id",
            "table:",
            "sql:",
            "traceback",
            "../",
            "\\",
        )
    )


def resolve(index: PackageIndex, ref: str) -> ResolvedItem | None:
    return index.resolve(ref)


def render(entry: ResolvedItem) -> CitationRef | None:
    """Build a safe provenance reference, or None when none can be rendered."""

    source_ref_id = entry.item.source_ref_id
    if not source_ref_id or is_internal_ref(source_ref_id):
        return None
    return CitationRef(
        source_ref_id=source_ref_id,
        source_ref_type=entry.item.source_ref_type,
        source_status=entry.item.source_status,
        provenance_refs=tuple(entry.item.provenance_refs),
        evidence_refs=tuple(entry.item.evidence_refs),
        generation=entry.item.generation,
    )


def collect(
    index: PackageIndex, refs: tuple[str, ...]
) -> tuple[tuple[CitationRef, ...], tuple[str, ...]]:
    """Resolve refs in first-seen order, de-duplicated by rendered identity.

    Returns the rendered citations and the refs that could not be resolved.
    """

    seen: set[str] = set()
    rendered: list[CitationRef] = []
    unresolved: list[str] = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        entry = resolve(index, ref)
        if entry is None:
            unresolved.append(ref)
            continue
        citation = render(entry)
        if citation is None:
            unresolved.append(ref)
            continue
        if citation.source_ref_id in {item.source_ref_id for item in rendered}:
            continue
        rendered.append(citation)
    return tuple(rendered), tuple(unresolved)


def claim_sources(index: PackageIndex, refs: tuple[str, ...]) -> tuple[ResolvedItem, ...]:
    out: list[ResolvedItem] = []
    for ref in refs:
        entry = resolve(index, ref)
        if entry is not None and entry not in out:
            out.append(entry)
    return tuple(out)


def same_source(left: ResolvedItem | None, right: ResolvedItem | None) -> bool:
    if left is None or right is None:
        return False
    return left.ref == right.ref


__all__ = [
    "is_internal_ref",
    "resolve",
    "render",
    "collect",
    "claim_sources",
    "same_source",
]
