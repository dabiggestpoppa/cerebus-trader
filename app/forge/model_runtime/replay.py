"""Deterministic replay (Ch III.3.9).

Identical normalized inputs + identical model version + identical prior
state ⇒ identical output hash.  The canonical serialization is sorted
keys with compact separators over the III.2 ``encode_value`` graph
(``Decimal`` → exact string, enum → value, datetime → UTC ISO-8601,
dataclass → plain dict, LF/UTF-8 JSON), so the hash covers:

* the model key and runtime version,
* the full input-identity envelope (market-data/clock/session/
  measurement versions, clock and session ids, injected calculation
  timestamp, calibration lineage, instrument),
* the prior-state reference,
* every output field.

Replay never substitutes current rules for historical versions: an
unregistered version fails closed at resolution, and a registered
historical generation without an authorized runtime refuses explicitly
rather than being answered by the current generation.  A mismatched
prior state (version or identity drift) refuses with
``PRIOR_STATE_MISMATCH``; ordered structures (facts, levels,
sub-states) are order-sensitive by construction, so reordered
transitions produce a different state hash.
"""

from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import replace
from typing import Any, Callable, Mapping

from app.forge.market_data import DataOutcome
from app.forge.measurements import encode_value

from .contract import (
    ModelOutput,
    ModelRequest,
    WarningCode,
    iter_measurements,
    prior_ref,
    resolve_quality,
)
from .errors import (
    DataQualityBlockedError,
    InstrumentScopeMismatchError,
    ModelContractError,
    ModelVersionUnavailableError,
    NoCalculationError,
    PriorStateMismatchError,
    ReplayHashMismatchError,
)
from .registry import RegistryEntry, resolve
from .versions import MODEL_RUNTIME_VERSION

__all__ = [
    "canonical_blob",
    "canonical_payload",
    "compute_hash",
    "finalize_output",
    "run_model",
    "verify_replay",
]


# ---------------------------------------------------------------------------
# Canonical serialization + hashing
# ---------------------------------------------------------------------------


def canonical_payload(output: ModelOutput) -> dict:
    """The full output payload minus the self-referential hash field."""
    return {
        item.name: getattr(output, item.name)
        for item in output.__dataclass_fields__.values()
        if item.name != "output_hash"
    }


def canonical_blob(payload: Any) -> bytes:
    """Deterministic canonical JSON bytes (sorted keys, compact, UTF-8)."""
    encoded = encode_value(payload)
    return json.dumps(
        encoded,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def compute_hash(payload: Any) -> str:
    """sha256 over the canonical serialization."""
    return hashlib.sha256(canonical_blob(payload)).hexdigest()


def finalize_output(output: ModelOutput) -> ModelOutput:
    """Stamp the canonical replay hash onto an immutable output."""
    digest = compute_hash(canonical_payload(output))
    if output.output_hash == digest:
        return output
    return replace(output, output_hash=digest)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

#: family → evaluator module (evaluators are ``_evaluate(request, entry)``).
_EVALUATOR_MODULES: Mapping[str, str] = {
    "EUR_DAILY": "eur_daily",
    "EUR_WEEKLY": "eur_weekly",
    "EUR_HIGHER_ORDER": "eur_higher_order",
    "XAU": "xau_game",
    "BTC_TRACKER": "btc_tracker",
    "FIB_RANGE_BIRTH": "fib_range_birth",
    "JPY_CARRY": "jpy_carry",
}


def _evaluator(family: str) -> Callable[[ModelRequest, RegistryEntry], ModelOutput]:
    module_name = _EVALUATOR_MODULES.get(family)
    if module_name is None:
        # Registered but not dispatchable: the historical generations.
        # Their pinned rule at this runtime version is an explicit
        # refusal — never a silent replay under current rules.
        raise ModelVersionUnavailableError(
            f"family {family!r} is registered without an authorized runtime at "
            f"{MODEL_RUNTIME_VERSION}; refusing to substitute another "
            f"generation's rules"
        )
    module = importlib.import_module(f"app.forge.model_runtime.{module_name}")
    return getattr(module, "_evaluate")


# ---------------------------------------------------------------------------
# Request gates (uniform for every family)
# ---------------------------------------------------------------------------


def _validate_scope_and_binding(request: ModelRequest, entry: RegistryEntry) -> None:
    scope = entry.market_scope
    if scope and request.instrument_id not in scope:
        allowed = ", ".join(sorted(scope))
        raise InstrumentScopeMismatchError(
            f"{request.instrument_id} is outside the market scope of "
            f"{entry.model_key} (scope: {allowed})"
        )
    bindings = entry.calibration_bindings
    if not bindings:
        if request.calibration_key is not None:
            if request.calibration_key.model_id != request.model_id:
                raise InstrumentScopeMismatchError(
                    f"calibration {request.calibration_key} is bound to another "
                    f"model; calibration stays model-local"
                )
            raise ModelVersionUnavailableError(
                f"{entry.model_key} registers no calibration binding; got "
                f"{request.calibration_key}"
            )
        return
    if request.calibration_key is None:
        want = ", ".join(str(key) for key in bindings)
        raise ModelVersionUnavailableError(
            f"{entry.model_key} requires exactly one registered calibration "
            f"binding ({want})"
        )
    if request.calibration_key in bindings:
        return
    if request.calibration_key.model_id != request.model_id:
        raise InstrumentScopeMismatchError(
            f"calibration {request.calibration_key} belongs to another model; "
            f"cross-model calibration transfer refuses"
        )
    raise ModelVersionUnavailableError(
        f"calibration binding {request.calibration_key} does not match the "
        f"registered binding for {entry.model_key}"
    )


def _validate_measurements(request: ModelRequest) -> None:
    for measurement in iter_measurements(request.inputs):
        if measurement.instrument_id != request.instrument_id:
            raise InstrumentScopeMismatchError(
                f"measurement {measurement.definition_id} belongs to "
                f"{measurement.instrument_id}, not {request.instrument_id}"
            )
        for name in (
            "market_data_schema_version",
            "clock_registry_version",
            "session_registry_version",
            "measurement_engine_version",
        ):
            declared = getattr(request, name)
            carried = getattr(measurement, name)
            if carried != declared:
                raise ModelContractError(
                    f"identity drift: measurement {measurement.definition_id} "
                    f"carries {name}={carried!r}, request asserts {declared!r}"
                )
        carried_key = getattr(measurement, "calibration_key", None)
        if carried_key is not None and carried_key != request.calibration_key:
            if carried_key.model_id != request.model_id:
                raise InstrumentScopeMismatchError(
                    f"measurement {measurement.definition_id} carries a "
                    f"foreign calibration {carried_key}"
                )
            raise ModelVersionUnavailableError(
                f"measurement {measurement.definition_id} carries calibration "
                f"{carried_key}, request binds {request.calibration_key}"
            )
        state = measurement.quality_state
        if state is DataOutcome.DATA_QUALITY_BLOCKED:
            raise DataQualityBlockedError(
                f"input measurement {measurement.definition_id} is blocked by "
                f"its quality policy (incomplete or nonfinal source data)"
            )
        if state is DataOutcome.NO_CALCULATION:
            raise NoCalculationError(
                f"input measurement {measurement.definition_id} reports "
                f"NO_CALCULATION (clock/session could not be resolved)"
            )


def _validate_clock(request: ModelRequest, entry: RegistryEntry) -> None:
    if entry.clock_bound and request.clock_id is None:
        raise NoCalculationError(
            f"{entry.model_key} is clock-bound; an explicit clock_id is "
            f"part of model identity"
        )


def _validate_prior(request: ModelRequest) -> None:
    prior = request.prior_state
    if prior is None:
        return
    if prior.model_id != request.model_id or prior.model_version != request.model_version:
        raise PriorStateMismatchError(
            f"prior state is {prior.model_id}@{prior.model_version}, request is "
            f"{request.model_id}@{request.model_version}"
        )
    if prior.identity.instrument_id != request.instrument_id:
        raise PriorStateMismatchError(
            f"prior state instrument {prior.identity.instrument_id} drifted from "
            f"{request.instrument_id}"
        )
    if prior.identity.clock_id != request.clock_id:
        raise PriorStateMismatchError(
            "prior state clock identity drifted from the request clock"
        )
    if prior.identity.session_id != request.session_id:
        raise PriorStateMismatchError(
            "prior state session identity drifted from the request session"
        )


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def run_model(request: ModelRequest) -> ModelOutput:
    """Resolve, gate, evaluate and hash one model request.

    Fail-closed order: exact resolution → market scope + calibration
    binding → measurement coherence/quality → clock identity → prior
    state → family evaluation → canonical hash.  Every refusal is an
    explicit coded error; there is no partial output and no fallback.
    """
    if not isinstance(request, ModelRequest):
        raise ModelContractError("run_model requires a ModelRequest")
    entry = resolve(request.model_id, request.model_version)
    _validate_scope_and_binding(request, entry)
    _validate_measurements(request)
    _validate_clock(request, entry)
    _validate_prior(request)
    evaluator = _evaluator(entry.family)
    output = evaluator(request, entry)
    if (
        resolve_quality(iter_measurements(request.inputs)) is DataOutcome.DEGRADED
        and WarningCode.DEGRADED_INPUT not in output.warnings
    ):
        output = replace(
            output, warnings=output.warnings + (WarningCode.DEGRADED_INPUT,)
        )
    return finalize_output(output)


def verify_replay(request: ModelRequest, expected_hash: str) -> ModelOutput:
    """Re-run a request and refuse on any hash difference (J9)."""
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ReplayHashMismatchError(
            f"expected a 64-hex sha256 hash, got {expected_hash!r}"
        )
    output = run_model(request)
    if output.output_hash != expected_hash:
        raise ReplayHashMismatchError(
            f"replay produced {output.output_hash}, expected {expected_hash}"
        )
    return output
