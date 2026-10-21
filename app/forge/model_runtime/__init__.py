"""CEREBUS Model Runtime (Book III / Bloc III.3).

A bounded, deterministic runtime that interprets III.2 measurements
under canonical model rules and emits immutable versioned model
states.  It invents no evidence, no probabilities, no trade setups and
no automation authority: model state ≠ trade eligibility, and
``production_authorization`` is a classification fact, never a grant.

Public surface (bounded on purpose): the common contract, the bounded
error vocabulary, the exact ``(model_id, version)`` registry, the
deterministic replay pipeline, the runtime version, and the seven
launch family input/state types.
"""

from __future__ import annotations

from .contract import (
    AnchorStateRef,
    DirectionBias,
    DirectionSide,
    ExplanationFact,
    InputIdentity,
    Layer,
    LevelKind,
    ModelOutput,
    ModelRequest,
    NoGoReason,
    ProductionAuthorization,
    RangeLeftField,
    SubState,
    TypedLevel,
    WarningCode,
    make_fact,
)
from .errors import (
    MODEL_RUNTIME_CODES,
    DataQualityBlockedError,
    InstrumentScopeMismatchError,
    InputMeasurementMissingError,
    ModelContractError,
    ModelRuntimeError,
    ModelVersionUnavailableError,
    NoCalculationError,
    PriorStateMismatchError,
    ReplayHashMismatchError,
    RuleNotMaterializedError,
)
from .registry import MODEL_REGISTRY, ModelKey, RegistryEntry, resolve
from .replay import (
    canonical_blob,
    canonical_payload,
    compute_hash,
    finalize_output,
    run_model,
    verify_replay,
)
from .versions import MODEL_RUNTIME_VERSION
from .btc_tracker import BtcTrackerInputs, BtcTrackerState
from .eur_daily import EurDailyInputs, EurDailyState, LADDER_STATES as EUR_DAILY_LADDER_STATES
from .eur_higher_order import EurHigherOrderInputs, EurHigherOrderState
from .eur_weekly import EurWeeklyInputs, EurWeeklyState
from .fib_range_birth import FibRangeBirthInputs, FibState
from .jpy_carry import (
    ROLE_MAP as JPY_ROLE_MAP,
    JpyBasketState,
    JpyCarryInputs,
    JpyPairInput,
    JpyRole,
)
from .xau_game import XauGameInputs, XauState

__all__ = [
    "MODEL_REGISTRY",
    "MODEL_RUNTIME_CODES",
    "MODEL_RUNTIME_VERSION",
    "AnchorStateRef",
    "BtcTrackerInputs",
    "BtcTrackerState",
    "DataQualityBlockedError",
    "DirectionBias",
    "DirectionSide",
    "EUR_DAILY_LADDER_STATES",
    "EurDailyInputs",
    "EurDailyState",
    "EurHigherOrderInputs",
    "EurHigherOrderState",
    "EurWeeklyInputs",
    "EurWeeklyState",
    "ExplanationFact",
    "FibRangeBirthInputs",
    "FibState",
    "InputIdentity",
    "InputMeasurementMissingError",
    "InstrumentScopeMismatchError",
    "JPY_ROLE_MAP",
    "JpyBasketState",
    "JpyCarryInputs",
    "JpyPairInput",
    "JpyRole",
    "Layer",
    "LevelKind",
    "ModelContractError",
    "ModelKey",
    "ModelOutput",
    "ModelRequest",
    "ModelRuntimeError",
    "ModelVersionUnavailableError",
    "NoCalculationError",
    "NoGoReason",
    "PriorStateMismatchError",
    "ProductionAuthorization",
    "RangeLeftField",
    "RegistryEntry",
    "ReplayHashMismatchError",
    "RuleNotMaterializedError",
    "SubState",
    "TypedLevel",
    "WarningCode",
    "XauGameInputs",
    "XauState",
    "canonical_blob",
    "canonical_payload",
    "compute_hash",
    "finalize_output",
    "make_fact",
    "resolve",
    "run_model",
    "verify_replay",
]
