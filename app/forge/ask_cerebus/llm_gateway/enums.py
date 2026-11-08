"""Closed vocabularies for the IV.4 gateway."""

from __future__ import annotations

from enum import Enum


class GatewayOutcome(str, Enum):
    DRAFT = "DRAFT"
    REFUSED = "REFUSED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DraftStatus(str, Enum):
    """IV.4 can only produce an unvalidated draft."""

    UNVALIDATED = "UNVALIDATED"


class RouteTask(str, Enum):
    DEFINITION = "DEFINITION"
    CURRENT_STATE = "CURRENT_STATE"
    SETUP_CONTEXT = "SETUP_CONTEXT"
    STATISTIC_EVIDENCE = "STATISTIC_EVIDENCE"
    COMPARISON = "COMPARISON"
    HISTORICAL = "HISTORICAL"
    RESEARCH = "RESEARCH"
    GENERAL = "GENERAL"


class AttemptOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class CostBasis(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    PROVIDER_REPORTED = "PROVIDER_REPORTED"
    ESTIMATED = "ESTIMATED"
    UNKNOWN = "UNKNOWN"


class GatewayRefusalCode(str, Enum):
    CONTEXT_VERSION_REFUSED = "CONTEXT_VERSION_REFUSED"
    MANIFEST_REQUIRED = "MANIFEST_REQUIRED"
    PACKAGE_IDENTITY_MISMATCH = "PACKAGE_IDENTITY_MISMATCH"
    UPSTREAM_REFUSED = "UPSTREAM_REFUSED"
    PACKAGE_INCOMPLETE = "PACKAGE_INCOMPLETE"
    DEPTH_UNSUPPORTED = "DEPTH_UNSUPPORTED"
    ROUTE_UNSUPPORTED = "ROUTE_UNSUPPORTED"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"
    BUDGET_REFUSED = "BUDGET_REFUSED"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_MALFORMED = "PROVIDER_MALFORMED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    PROVIDER_NOT_CONFIGURED = "PROVIDER_NOT_CONFIGURED"
    CANCELLED = "CANCELLED"
    DRAFT_SCHEMA_INVALID = "DRAFT_SCHEMA_INVALID"
    CITATION_REQUIRED = "CITATION_REQUIRED"
    CITATION_OUTSIDE_PACKAGE = "CITATION_OUTSIDE_PACKAGE"
    NUMERIC_EVIDENCE_MISSING = "NUMERIC_EVIDENCE_MISSING"
    MANDATORY_RESTRICTION_MISSING = "MANDATORY_RESTRICTION_MISSING"
    POLICY_DENIED = "POLICY_DENIED"


DRAFT_FORBIDDEN_FIELDS = frozenset(
    {
        "answer",
        "recommendation",
        "order_intent",
        "position_size",
        "win_rate",
        "entitlement",
        "entitlement_grant",
        "canonical_verified",
        "current_price",
        "trade",
        "execute",
    }
)

__all__ = [
    "GatewayOutcome",
    "DraftStatus",
    "RouteTask",
    "AttemptOutcome",
    "CostBasis",
    "GatewayRefusalCode",
    "DRAFT_FORBIDDEN_FIELDS",
]
