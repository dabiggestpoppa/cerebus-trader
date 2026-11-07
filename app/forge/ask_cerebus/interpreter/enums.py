"""Closed vocabularies for the IV.1 query interpreter.

Nothing here carries authority: intents describe what was asked, depths
describe presentation, confidence describes interpretation completeness, and
ambiguity codes describe why a plan is not fully resolved.
"""

from __future__ import annotations

from enum import Enum


class Intent(str, Enum):
    DEFINITION = "DEFINITION"
    MODEL_DESCRIPTION = "MODEL_DESCRIPTION"
    CURRENT_STATE = "CURRENT_STATE"
    LEVEL_COORDINATE = "LEVEL_COORDINATE"
    SETUP_CONTEXT = "SETUP_CONTEXT"
    STATISTIC_EVIDENCE = "STATISTIC_EVIDENCE"
    COMPARISON = "COMPARISON"
    HISTORICAL_LINEAGE = "HISTORICAL_LINEAGE"
    METHODOLOGY_RESEARCH = "METHODOLOGY_RESEARCH"
    INDICATOR_NAVIGATION = "INDICATOR_NAVIGATION"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    GENERAL_MARKET_KNOWLEDGE = "GENERAL_MARKET_KNOWLEDGE"


class Depth(str, Enum):
    BEGINNER = "BEGINNER"
    OPERATOR = "OPERATOR"
    RESEARCHER = "RESEARCHER"

    @property
    def rank(self) -> int:
        return _DEPTH_RANK[self]


class TimeScope(str, Enum):
    CURRENT = "CURRENT"
    AS_OF = "AS_OF"
    HISTORICAL_RESEARCH = "HISTORICAL_RESEARCH"
    MODEL_VERSION = "MODEL_VERSION"
    GENERAL = "GENERAL"


class PlanConfidence(str, Enum):
    CERTAIN = "CERTAIN"
    EXPLICIT_SCOPE = "EXPLICIT_SCOPE"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"


class AmbiguityOutcome(str, Enum):
    RESOLVED = "RESOLVED"
    RESOLVED_WITH_EXPLICIT_SCOPE = "RESOLVED_WITH_EXPLICIT_SCOPE"
    MATERIAL_AMBIGUITY = "MATERIAL_AMBIGUITY"
    UNSUPPORTED_IDENTITY = "UNSUPPORTED_IDENTITY"
    UNAVAILABLE_GENERATION = "UNAVAILABLE_GENERATION"
    UNSUPPORTED_STATISTIC = "UNSUPPORTED_STATISTIC"


class AmbiguityReason(str, Enum):
    AMBIGUOUS_MODEL = "AMBIGUOUS_MODEL"
    AMBIGUOUS_INSTRUMENT = "AMBIGUOUS_INSTRUMENT"
    AMBIGUOUS_GENERATION = "AMBIGUOUS_GENERATION"
    AMBIGUOUS_LAYER = "AMBIGUOUS_LAYER"
    AMBIGUOUS_DEPTH = "AMBIGUOUS_DEPTH"
    AMBIGUOUS_TIME = "AMBIGUOUS_TIME"
    UNSUPPORTED_IDENTITY = "UNSUPPORTED_IDENTITY"
    UNAVAILABLE_GENERATION = "UNAVAILABLE_GENERATION"
    DEPTH_CAPPED = "DEPTH_CAPPED"
    UNSUPPORTED_STATISTIC = "UNSUPPORTED_STATISTIC"


class EntityKind(str, Enum):
    INSTRUMENT = "INSTRUMENT"
    MODEL = "MODEL"
    SETUP = "SETUP"
    TERM = "TERM"
    LAYER = "LAYER"
    SESSION = "SESSION"
    GENERATION = "GENERATION"


_DEPTH_RANK = {
    Depth.BEGINNER: 0,
    Depth.OPERATOR: 1,
    Depth.RESEARCHER: 2,
}

_CONFIDENCE_RANK = {
    PlanConfidence.CERTAIN: 0,
    PlanConfidence.EXPLICIT_SCOPE: 1,
    PlanConfidence.AMBIGUOUS: 2,
    PlanConfidence.UNSUPPORTED: 3,
}


def clamp_depth(requested: Depth, maximum: Depth) -> Depth:
    """Return the lower of the two depths; never grants the maximum."""

    return requested if requested.rank <= maximum.rank else maximum


def worst_confidence(*values: PlanConfidence) -> PlanConfidence:
    return max(values, key=lambda value: _CONFIDENCE_RANK[value])


__all__ = [
    "Intent",
    "Depth",
    "TimeScope",
    "PlanConfidence",
    "AmbiguityOutcome",
    "AmbiguityReason",
    "EntityKind",
    "clamp_depth",
    "worst_confidence",
]
