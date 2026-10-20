"""Bounded refusal vocabulary for Bloc III.2 measurement contracts.

Every failure in this package is an explicit, coded refusal.  Nothing in
the measurement path degrades silently: an unresolvable range, an
unresolvable clock/session, a missing model/calibration version, an
unearned anchor, an out-of-band magnitude and a cross-asset calibration
transfer each raise one of these errors instead of coercing to a default.

The codes mirror the frozen Book III failure-behaviour vocabulary:
``DATA_QUALITY_BLOCKED``, ``NO_CALCULATION``, ``MODEL_VERSION_UNAVAILABLE``
and the anchor/tier refusals the acceptance map names explicitly.
"""

from __future__ import annotations


class MeasurementError(Exception):
    """Base class for every Bloc III.2 measurement refusal."""

    code = "MEASUREMENT_ERROR"

    def __str__(self) -> str:  # bounded, factual message
        detail = super().__str__()
        return f"{self.code}: {detail}" if detail else self.code


class MeasurementContractError(MeasurementError):
    """A measurement contract was constructed with inconsistent fields."""

    code = "MEASUREMENT_CONTRACT"


class DataQualityBlockedError(MeasurementError):
    """Input data is incomplete or defective for the declared model policy."""

    code = "DATA_QUALITY_BLOCKED"


class NoCalculationError(MeasurementError):
    """A clock, session or other required identity could not be resolved."""

    code = "NO_CALCULATION"


class ModelVersionUnavailableError(MeasurementError):
    """A model / calibration version was requested that is not registered."""

    code = "MODEL_VERSION_UNAVAILABLE"


class UnclassifiedValueError(MeasurementError):
    """A value falls outside every declared band and was not classified."""

    code = "UNCLASSIFIED_VALUE"


class CalibrationTransferRefusedError(MeasurementError):
    """A calibration was asked to classify a foreign asset or unit."""

    code = "CALIBRATION_TRANSFER_REFUSED"


class AnchorNotEarnedError(MeasurementError):
    """A coordinate projection was attempted without an earned anchor."""

    code = "ANCHOR_NOT_EARNED"


class CoordinateFamilyNotEarnedError(MeasurementError):
    """A coordinate family was not declared for the anchor's model."""

    code = "COORDINATE_FAMILY_NOT_EARNED"


class UnknownCoordinateFamilyError(MeasurementError):
    """A coordinate family outside the canonical / declared-extension set."""

    code = "UNKNOWN_COORDINATE_FAMILY"


class UnknownDefinitionError(MeasurementError):
    """A measurement definition id or version is not registered."""

    code = "UNKNOWN_DEFINITION"


class UnitDomainError(MeasurementError):
    """Arithmetic was attempted across two asset-native unit domains."""

    code = "UNIT_DOMAIN"


class RangeNotResolvableError(MeasurementError):
    """A range could not be resolved from the supplied finalized bars."""

    code = "RANGE_NOT_RESOLVABLE"


class PathNotResolvableError(MeasurementError):
    """A path measurement could not be resolved from the supplied bars."""

    code = "PATH_NOT_RESOLVABLE"


class InvalidAnchorStateError(MeasurementError):
    """An anchor record was constructed with an impossible state."""

    code = "INVALID_ANCHOR_STATE"


class EventBudgetError(MeasurementError):
    """An event budget could not be computed from the declared fields."""

    code = "EVENT_BUDGET"
