"""Bounded refusal vocabulary for the Bloc III.3 model runtime.

Every failure in this package is an explicit, coded refusal.  Nothing
degrades silently: an unregistered model version, a cross-asset
calibration, a blocking quality state, an unresolvable clock, a missing
measurement, an incompatible prior state, an unmaterialized rule and a
replay hash mismatch each raise exactly one of these errors instead of
coercing to a default or falling back to a later version.

The codes mirror the frozen Book III failure-behaviour vocabulary
(PLAN.md §9).  The measurement-layer refusal *codes* of Bloc III.2
(``DATA_QUALITY_BLOCKED``, ``NO_CALCULATION``,
``MODEL_VERSION_UNAVAILABLE`` …) are mirrored as strings so a caller can
handle either layer uniformly; the III.2 enums and refusal codes
themselves are imported from III.2 where they travel with measurements,
never redefined here.
"""

from __future__ import annotations


class ModelRuntimeError(Exception):
    """Base class for every Bloc III.3 model-runtime refusal."""

    code = "MODEL_RUNTIME_ERROR"

    def __str__(self) -> str:  # bounded, factual message
        detail = super().__str__()
        return f"{self.code}: {detail}" if detail else self.code


class ModelContractError(ModelRuntimeError):
    """A model request was constructed with inconsistent fields."""

    code = "MODEL_CONTRACT"


class ModelVersionUnavailableError(ModelRuntimeError):
    """The requested model_id / model_version is not registered.

    Fail closed: no partial output, no fallback, no "latest".
    """

    code = "MODEL_VERSION_UNAVAILABLE"


class DataQualityBlockedError(ModelRuntimeError):
    """Input data is incomplete, nonfinal or defective for this model."""

    code = "DATA_QUALITY_BLOCKED"


class NoCalculationError(ModelRuntimeError):
    """A clock, session or required identity could not be resolved."""

    code = "NO_CALCULATION"


class InstrumentScopeMismatchError(ModelRuntimeError):
    """Instrument or calibration outside the family's declared scope."""

    code = "INSTRUMENT_SCOPE_MISMATCH"


class PriorStateMismatchError(ModelRuntimeError):
    """The supplied prior state belongs to another version/identity."""

    code = "PRIOR_STATE_MISMATCH"


class InputMeasurementMissingError(ModelRuntimeError):
    """A required measurement is absent — never synthesized from nothing."""

    code = "INPUT_MEASUREMENT_MISSING"


class RuleNotMaterializedError(ModelRuntimeError):
    """An eligibility-bearing rule (R15 Range Birth) is not materialized."""

    code = "RULE_NOT_MATERIALIZED"


class ReplayHashMismatchError(ModelRuntimeError):
    """Replay verification found a different output hash.

    Replay never substitutes current rules for historical versions.
    """

    code = "REPLAY_HASH_MISMATCH"


#: The complete bounded refusal-code vocabulary of this package.
MODEL_RUNTIME_CODES: tuple[str, ...] = (
    ModelContractError.code,
    ModelVersionUnavailableError.code,
    DataQualityBlockedError.code,
    NoCalculationError.code,
    InstrumentScopeMismatchError.code,
    PriorStateMismatchError.code,
    InputMeasurementMissingError.code,
    RuleNotMaterializedError.code,
    ReplayHashMismatchError.code,
)

__all__ = [
    "MODEL_RUNTIME_CODES",
    "DataQualityBlockedError",
    "InstrumentScopeMismatchError",
    "InputMeasurementMissingError",
    "ModelContractError",
    "ModelRuntimeError",
    "ModelVersionUnavailableError",
    "NoCalculationError",
    "PriorStateMismatchError",
    "ReplayHashMismatchError",
    "RuleNotMaterializedError",
]
