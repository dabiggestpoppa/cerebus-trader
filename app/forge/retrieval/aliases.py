"""Alias / generation routing for GLX FORGE Book I / Bloc I.4 (Ch I.4.4).

Historical CEREBUS vocabulary maps to the frozen modern vocabulary through the
ONTOLOGY_CROSSWALK_V1 table, which lives here as bounded, verbatim data (the
crosswalk is a governance contract: rules-read, never indexed as canonical
evidence — I.3 limitation B).

Two routing behaviors, both non-authoritative:

- **Query expansion** — a historical query term adds its modern interpretation
  so historical questions reach modern records. Expansion ADDS search tokens
  only: it never changes status, exposure, claim population, evidence class,
  or record identity (the crosswalk translation rule: never move statistics
  across aliases without evidence that populations are equivalent).
- **Record aliases** — a record carries the historical terms actually present
  in its own governed text, so its historical vocabulary is discoverable and
  the object's own wording is never rewritten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.forge.backfill.mappings import NOT_SPECIFIED


@dataclass(frozen=True)
class AliasEntry:
    """One verbatim ONTOLOGY_CROSSWALK_V1 row."""

    historical: str
    intermediate: str
    canonical_kind: str
    modern: str


# Verbatim rows of corpus/canonical/ONTOLOGY_CROSSWALK_V1.md (test-asserted
# equal to the markdown table; do not edit without a governance amendment).
HISTORICAL_ALIASES: tuple[AliasEntry, ...] = (
    AliasEntry(
        "Constraint Deficit",
        "unresolved available movement",
        "STATE / MEASUREMENT",
        "remaining distribution / unresolved side",
    ),
    AliasEntry(
        "Resolution Output",
        "delivered movement",
        "EVENT / TRANSITION",
        "delivery / excursion",
    ),
    AliasEntry(
        "Available Resolution Pathway",
        "possible route",
        "PATH",
        "conditional path",
    ),
    AliasEntry(
        "Partial Rebalancing",
        "counter-move within active structure",
        "TRANSITION",
        "repair/rebalance",
    ),
    AliasEntry(
        "Constraint Violation",
        "structural breach",
        "EVENT",
        "violation / rekey candidate",
    ),
    AliasEntry(
        "Resolution Stall",
        "incomplete delivery",
        "STATE",
        "stall/persistence state",
    ),
    AliasEntry(
        "Constraint Boundary",
        "normalized boundary",
        "SCALE/COORDINATE",
        "node/extension",
    ),
    AliasEntry(
        "Activation Signal",
        "pathway activation",
        "EVENT",
        "P90/OCC/acceptance family",
    ),
    AliasEntry("AU", "native atomic distance", "SCALE", "centroid-derived asset scale"),
    AliasEntry("Tier", "range regime bucket", "STATE/SCALE", "calibrated magnitude state"),
    AliasEntry(
        "Density Zone",
        "AU/threshold overlap",
        "LOCATION/STATE",
        "local decision zone",
    ),
    AliasEntry("P90", "kinetic activation", "EVENT", "momentum/activation evidence"),
    AliasEntry(
        "Cascade",
        "repeated activation",
        "TRANSITION/PATH",
        "repeated same-direction evidence",
    ),
    AliasEntry(
        "EWS",
        "exhaustion warning",
        "EVENT",
        "exit/exhaustion, not automatic reversal",
    ),
    AliasEntry(
        "Base80",
        "initial P90 path",
        "SETUP/HISTORICAL",
        "first activation/delivery lineage",
    ),
    AliasEntry(
        "132 Kill",
        "pathway invalidation",
        "EVENT",
        "rekey/violation transition",
    ),
    AliasEntry("Float", "unresolved persistence", "STATE", "survival/persistence"),
    AliasEntry(
        "Failure Repair",
        "failed acceptance then repair",
        "PATH",
        "transition sequence",
    ),
    AliasEntry(
        "Midpoint Repair",
        "first post-failure destination",
        "EVENT/PATH",
        "first-delivery repair node",
    ),
    AliasEntry(
        "Second Acceptance",
        "new accepted path",
        "TRANSITION",
        "confirmed state reassignment",
    ),
    AliasEntry(
        "Recursive Shift",
        "proportional new pathway",
        "TRANSITION",
        "path-state shift/new range",
    ),
    AliasEntry(
        "Blind Structural Chain",
        "impulse/rebalance/continuation",
        "PATH",
        "local geometry observation",
    ),
    AliasEntry(
        "Recursive/Fractal Resolution",
        "repeated grammar across scales",
        "MODEL/DOCTRINE",
        "nested conditional distributions",
    ),
    AliasEntry(
        "P90P",
        "weighted distribution tracker",
        "MODEL/HISTORICAL",
        "ancestor of range-left/checkpoints",
    ),
    AliasEntry(
        "PHI",
        "hand-built confidence scalar",
        "MODEL/HISTORICAL",
        "superseded by measured conditional features",
    ),
    AliasEntry(
        "Single RESOLUTION CONSTRUCTION state",
        "ontological process claim",
        "DOCTRINE/HISTORICAL",
        "explanatory ontology, not statistical state vocabulary",
    ),
    AliasEntry(
        "Markov states",
        "discrete event states",
        "STATE/TRANSITION",
        "historical statistical vocabulary; old fitted model not established",
    ),
    AliasEntry(
        "State age",
        "dwell time",
        "CLOCK/STATE",
        "semi-Markov hazard/survival feature",
    ),
    AliasEntry(
        "Health state",
        "recovery quality",
        "STATE",
        "structural health beyond price recovery",
    ),
    AliasEntry(
        "Breadth/dispersion",
        "field participation",
        "STATE/MEASUREMENT",
        "global constraint context",
    ),
    AliasEntry(
        "Peer/basket effect",
        "cross-market context",
        "MODEL/STATE",
        "conditional peer field",
    ),
    AliasEntry(
        "First delivery",
        "earliest realized destination",
        "EVENT/PATH",
        "path-dependent outcome",
    ),
    AliasEntry(
        "Range-left",
        "remaining expected movement",
        "MEASUREMENT/MODEL",
        "conditional remaining distribution",
    ),
    AliasEntry(
        "Range Birth",
        "earned A-B anchor",
        "RANGE/ANCHOR EVENT",
        "prerequisite for Fib coordinates",
    ),
    AliasEntry(
        "Alpha/Beta/Gamma/Delta",
        "nested fib sequence families",
        "PATH/STATE",
        "local structural sequence",
    ),
    AliasEntry(
        "Rekey",
        "remapping after structural excursion",
        "EVENT/TRANSITION",
        "state/range reassignment candidate",
    ),
    AliasEntry(
        "L1/L2/L3",
        "execution/path/destination",
        "LAYER",
        "canonical layer separation",
    ),
)


def _pattern(term: str) -> re.Pattern[str]:
    return re.compile(
        r"(?<![\w])" + re.escape(term.lower()) + r"(?![\w])", re.IGNORECASE
    )


_PATTERNS: dict[str, re.Pattern[str]] = {
    entry.historical: _pattern(entry.historical) for entry in HISTORICAL_ALIASES
}


def historical_terms() -> tuple[str, ...]:
    return tuple(entry.historical for entry in HISTORICAL_ALIASES)


def lookup_alias(term: str) -> AliasEntry | None:
    """Exact (case-insensitive) historical-term lookup. No fuzzy matching."""

    if not isinstance(term, str):
        return None
    for entry in HISTORICAL_ALIASES:
        if entry.historical.lower() == term.strip().lower():
            return entry
    return None


def expand_query_text(text: str) -> tuple[str, ...]:
    """Historical query vocabulary → modern interpretation tokens.

    Returns ADDITIONAL search tokens (never a replacement for the query) —
    identity, status and population are untouched by expansion.
    """

    if not text:
        return ()
    additions: list[str] = []
    for entry in HISTORICAL_ALIASES:
        if _PATTERNS[entry.historical].search(text):
            additions.extend(_split_terms(entry.modern))
    seen: dict[str, None] = {}
    for token in additions:
        seen.setdefault(token, None)
    return tuple(seen)


def aliases_present(text: str) -> tuple[str, ...]:
    """Historical aliases whose historical term literally appears in `text`.

    Sorted and deduplicated; used for the record's `structured.aliases` facet
    so a record's own historical wording is preserved, never rewritten.
    """

    if not text:
        return ()
    found = [
        entry.historical
        for entry in HISTORICAL_ALIASES
        if _PATTERNS[entry.historical].search(text)
    ]
    return tuple(sorted(set(found)))


def _split_terms(value: str) -> list[str]:
    """Split a modern interpretation into searchable lowercase tokens."""

    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def is_not_specified(value: object) -> bool:
    """True for absent / empty / the frozen NOT_SPECIFIED_IN_SOURCE marker."""

    if value is None:
        return True
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return stripped == "" or stripped == NOT_SPECIFIED


__all__ = [
    "AliasEntry",
    "HISTORICAL_ALIASES",
    "historical_terms",
    "lookup_alias",
    "expand_query_text",
    "aliases_present",
    "is_not_specified",
]
