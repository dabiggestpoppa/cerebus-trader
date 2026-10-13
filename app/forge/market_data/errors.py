"""Bounded error vocabulary for Bloc III.1 market-data contracts.

Every failure in this package is an explicit, coded refusal. Nothing in
the market-data path degrades silently: cross-unit arithmetic, ambiguous
aliases, unsupported clocks/timeframes, precision violations, revisions
against the ordering contract and unknown quality flags all raise one of
these errors instead of coercing.
"""

from __future__ import annotations


class MarketDataError(Exception):
    """Base class for every Bloc III.1 market-data refusal."""

    code = "MARKET_DATA_ERROR"

    def __str__(self) -> str:  # bounded, factual message
        detail = super().__str__()
        return f"{self.code}: {detail}" if detail else self.code


class UnitMismatchError(MarketDataError):
    """Cross-instrument or cross-native-unit arithmetic was attempted."""

    code = "UNIT_MISMATCH"


class UnsupportedConversionError(MarketDataError):
    """No conversion authority exists between two native unit domains."""

    code = "UNSUPPORTED_CONVERSION"


class AmbiguousAliasError(MarketDataError):
    """An alias resolves to more than one canonical instrument (fail closed)."""

    code = "AMBIGUOUS_ALIAS"


class UnknownAliasError(MarketDataError):
    """An alias or provider symbol does not resolve to a canonical id."""

    code = "UNKNOWN_ALIAS"


class UnsupportedTimeframeError(MarketDataError):
    """Timeframe is not declared for the instrument."""

    code = "UNSUPPORTED_TIMEFRAME"


class UnsupportedClockError(MarketDataError):
    """Clock identity is unknown or not declared for the instrument."""

    code = "UNSUPPORTED_CLOCK"


class PrecisionViolationError(MarketDataError):
    """A price exceeds the instrument precision; values are never rounded."""

    code = "PRECISION_VIOLATION"


class ConventionViolationError(MarketDataError):
    """Quote/base (or other declared convention) was violated."""

    code = "CONVENTION_VIOLATION"


class DuplicateRegistrationError(MarketDataError):
    """Two definitions collide on the same registry key."""

    code = "DUPLICATE_REGISTRATION"


class RevisionViolationError(MarketDataError):
    """A revision did not satisfy the explicit revision ordering contract."""

    code = "REVISION_VIOLATION"


class NonFinalError(MarketDataError):
    """A nonfinal bar was demanded where final state is required."""

    code = "NONFINAL"


class QualityVocabularyError(MarketDataError):
    """A quality flag outside the frozen vocabulary was presented."""

    code = "QUALITY_VOCABULARY"


class ProvenanceViolationError(MarketDataError):
    """Provenance/source-reference combination is not permitted."""

    code = "PROVENANCE_VIOLATION"


class UnsupportedProviderError(MarketDataError):
    """A provider id has no scripted normalization schema in this bloc."""

    code = "UNSUPPORTED_PROVIDER"
