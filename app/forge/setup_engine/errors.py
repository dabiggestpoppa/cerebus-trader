"""Bounded refusal vocabulary and typed errors (Ch III.5, PLAN.md §11).

Every refusal the setup engine can emit is a member of one closed
enumeration.  There is no free-text reason anywhere: a caller cannot
attach prose to a refusal, and a refusal is a *result*, not an exception
that escapes the evaluation surface (Ch III.5.12 / clause L16).

The typed exceptions below exist for **construction** violations — an
immutable record being rebound, a payload carrying a float, a statistic
without a claim identity.  Those are programming errors in the caller,
not setup outcomes, and they are raised deliberately.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "AutomationNotApprovedError",
    "ClaimPopulationMismatchError",
    "SETUP_REFUSAL_CODES",
    "SetupConflictError",
    "SetupContractError",
    "SetupEngineError",
    "SetupRefusalCode",
    "SetupRegistryError",
    "TargetPromotionRefused",
    "UnsupportedStatisticError",
]


class SetupEngineError(ValueError):
    """Base class for every deliberate setup-engine refusal."""


class SetupContractError(SetupEngineError):
    """A frozen contract invariant was violated (shape, type, vocabulary)."""


class SetupRegistryError(SetupEngineError):
    """A registry request or registration violated canonical identity."""


class SetupConflictError(SetupEngineError):
    """Two supplied facts contradict each other (for example layer conflict)."""


class TargetPromotionRefused(SetupEngineError):
    """A target promotion was requested without its declared authority."""


class UnsupportedStatisticError(SetupEngineError):
    """A performance statement was attempted without a canonical claim id."""


class ClaimPopulationMismatchError(SetupEngineError):
    """A claim's population identity does not describe the quoted population."""


class AutomationNotApprovedError(SetupEngineError):
    """Automation authority was requested for a non-approved surface."""


class SetupRefusalCode(str, Enum):
    """The closed refusal vocabulary carried by every non-positive verdict."""

    SETUP_CARD_UNRESOLVED = "SETUP_CARD_UNRESOLVED"
    SETUP_NOT_CANONICAL_FOR_SURFACE = "SETUP_NOT_CANONICAL_FOR_SURFACE"
    SETUP_VERSION_DRIFT = "SETUP_VERSION_DRIFT"
    SETUP_VERSION_UNRESOLVED = "SETUP_VERSION_UNRESOLVED"
    RESEARCH_ONLY_NOT_PRODUCTION = "RESEARCH_ONLY_NOT_PRODUCTION"
    AUTOMATION_NOT_APPROVED = "AUTOMATION_NOT_APPROVED"
    AUTOMATION_PARITY_UNVERIFIED = "AUTOMATION_PARITY_UNVERIFIED"
    STAND_DOWN_LOCKED = "STAND_DOWN_LOCKED"
    PARENT_STATE_MISSING = "PARENT_STATE_MISSING"
    PARENT_STATE_UNRESOLVED = "PARENT_STATE_UNRESOLVED"
    MODEL_VERSION_UNAVAILABLE = "MODEL_VERSION_UNAVAILABLE"
    WRONG_LAYER_PARENT = "WRONG_LAYER_PARENT"
    STATE_NOT_DECLARED = "STATE_NOT_DECLARED"
    PARKED_STATE = "PARKED_STATE"
    ANCHOR_UNRESOLVED = "ANCHOR_UNRESOLVED"
    ANCHOR_INVALIDATED = "ANCHOR_INVALIDATED"
    ANCHOR_RULE_NOT_CANONICAL = "ANCHOR_RULE_NOT_CANONICAL"
    TIER_UNRESOLVED = "TIER_UNRESOLVED"
    TIER_NOT_NATIVE = "TIER_NOT_NATIVE"
    NATIVE_TIER_NO_GO = "NATIVE_TIER_NO_GO"
    CLOCK_UNRESOLVED = "CLOCK_UNRESOLVED"
    CHECKPOINT_NOT_REACHED = "CHECKPOINT_NOT_REACHED"
    HIGHER_LAYER_NO_GO = "HIGHER_LAYER_NO_GO"
    LAYER_CONFLICT = "LAYER_CONFLICT"
    DATA_QUALITY_BLOCKED = "DATA_QUALITY_BLOCKED"
    PARAMETER_UNRESOLVED = "PARAMETER_UNRESOLVED"
    PARAMETER_DECLARED_ONLY = "PARAMETER_DECLARED_ONLY"
    TRIGGER_NOT_SATISFIED = "TRIGGER_NOT_SATISFIED"
    BLIND_TOUCH_REFUSED = "BLIND_TOUCH_REFUSED"
    SETUP_INVALIDATED = "SETUP_INVALIDATED"
    INVALIDATION_UNDECLARED = "INVALIDATION_UNDECLARED"
    FORBIDDEN_PROMOTION = "FORBIDDEN_PROMOTION"
    TARGET_PROMOTION_WITHOUT_AUTHORITY = "TARGET_PROMOTION_WITHOUT_AUTHORITY"
    TARGET_NOT_DECLARED = "TARGET_NOT_DECLARED"
    UNSUPPORTED_STATISTIC = "UNSUPPORTED_STATISTIC"
    CLAIM_POPULATION_MISMATCH = "CLAIM_POPULATION_MISMATCH"


#: The closed vocabulary, as plain strings, for membership assertions.
SETUP_REFUSAL_CODES: frozenset[str] = frozenset(
    code.value for code in SetupRefusalCode
)
