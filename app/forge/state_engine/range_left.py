"""Conditional range-left (Ch III.4.7).

Range-left is the *remaining* distribution conditioned on what has
already happened.  It always names the consumed events it is conditioned
on, and it is recomputed after delivery, acceptance, exhaustion,
invalidation or rekey.

An unconditional historical frequency is refused
(``UNCONDITIONAL_FREQUENCY_REFUSED``): a past base rate is not the
remaining opportunity of this path.  Where no source-supported remaining
measurement exists, the state is the explicit III.2 ``UNRESOLVED``
vocabulary — never an invented number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.forge.measurements import NativeMagnitude, RemainingState
from app.forge.model_runtime import RangeLeftField

from .errors import (
    ConsumedStateReopenedError,
    ConsumedTargetRequotedError,
    StateContractError,
    UnconditionalFrequencyRefusedError,
)

__all__ = [
    "ConditionalRangeLeft",
    "ConsumedEvent",
    "RangeLeftCondition",
    "from_historical_frequency",
    "recompute_range_left",
]

_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


class ConsumedEvent(str, Enum):
    """The consumed-event kinds range-left may be conditioned on."""

    DELIVERY = "DELIVERY"
    ACCEPTANCE = "ACCEPTANCE"
    EXHAUSTION = "EXHAUSTION"
    INVALIDATION = "INVALIDATION"
    REKEY = "REKEY"


@dataclass(frozen=True)
class RangeLeftCondition:
    """One consumed event the remaining distribution is conditioned on."""

    event: ConsumedEvent
    ref: str

    def __post_init__(self) -> None:
        if not isinstance(self.event, ConsumedEvent):
            raise StateContractError("a condition carries a bounded event kind")
        if not self.ref or not _IDENT.match(self.ref):
            raise StateContractError(
                f"a condition names its event reference: {self.ref!r}"
            )


@dataclass(frozen=True)
class ConditionalRangeLeft:
    """Remaining distribution with its explicit conditioning set."""

    state: RemainingState
    value: NativeMagnitude | None
    conditioned_on: tuple[str, ...]
    available_targets: tuple[str, ...]
    exhausted: bool
    basis_ref: str | None
    unit: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.state, RemainingState):
            raise StateContractError("range-left uses the frozen III.2 vocabulary")
        if self.state is RemainingState.UNRESOLVED and self.value is not None:
            raise StateContractError("an unresolved range-left carries no value")
        if self.state is RemainingState.MEASURED:
            if self.value is None:
                raise StateContractError("a measured range-left carries its value")
            if not self.conditioned_on:
                raise StateContractError(
                    "a measured range-left must be conditioned on consumed events"
                )
        if self.value is not None and not isinstance(self.value, NativeMagnitude):
            raise StateContractError("range-left values are asset-native magnitudes")

    def to_payload(self) -> dict:
        return {
            "state": self.state.value,
            "value": (
                {
                    "instrument_id": self.value.instrument_id,
                    "unit": self.value.unit.value,
                    "value": self.value.value,
                }
                if self.value is not None
                else None
            ),
            "conditioned_on": list(self.conditioned_on),
            "available_targets": list(self.available_targets),
            "exhausted": self.exhausted,
            "basis_ref": self.basis_ref,
            "unit": self.unit,
        }


def from_historical_frequency(**_kwargs) -> "ConditionalRangeLeft":
    """Refuse to substitute an unconditional base rate for range-left."""

    raise UnconditionalFrequencyRefusedError(
        "an unconditional historical frequency is not the conditional "
        "remaining opportunity of this path"
    )


def recompute_range_left(
    *,
    prior: RangeLeftField | ConditionalRangeLeft | None,
    conditions: tuple[RangeLeftCondition, ...],
    measurement: NativeMagnitude | None = None,
    available_targets: tuple[str, ...] = (),
    consumed_targets: tuple[str, ...] = (),
    exhausted: bool = False,
    basis_ref: str | None = None,
) -> ConditionalRangeLeft:
    """Re-condition range-left on the events that have occurred."""

    if prior is None:
        prior_conditioned: tuple[str, ...] = ()
    elif isinstance(prior, ConditionalRangeLeft):
        prior_conditioned = prior.conditioned_on
    elif isinstance(prior, RangeLeftField):
        prior_conditioned = tuple(prior.conditioned_on)
    else:
        raise StateContractError(
            "prior range-left is a III.3 field or a conditional record"
        )

    for condition in conditions:
        if not isinstance(condition, RangeLeftCondition):
            raise StateContractError("conditions are typed RangeLeftCondition items")

    refs: list[str] = list(prior_conditioned)
    for condition in conditions:
        if condition.ref not in refs:
            refs.append(condition.ref)

    if measurement is not None and not isinstance(measurement, NativeMagnitude):
        raise StateContractError("range-left measurement is a NativeMagnitude")

    # A consumed target may never be offered again as available.
    already_consumed = set(refs) | set(consumed_targets)
    requoted = sorted(already_consumed & set(available_targets))
    if requoted:
        raise ConsumedTargetRequotedError(
            f"consumed target(s) {requoted} cannot be quoted as still available"
        )

    if measurement is not None and not refs:
        raise UnconditionalFrequencyRefusedError(
            "a measured range-left requires the consumed events it is "
            "conditioned on; an unconditional figure is not accepted"
        )

    if exhausted and measurement is not None:
        raise ConsumedStateReopenedError(
            "an exhausted state cannot be silently re-opened with a new "
            "remaining value"
        )

    unit = measurement.unit.value if measurement is not None else None
    if measurement is None:
        return ConditionalRangeLeft(
            state=RemainingState.UNRESOLVED,
            value=None,
            conditioned_on=tuple(refs),
            available_targets=tuple(available_targets),
            exhausted=exhausted,
            basis_ref=basis_ref,
            unit=None,
        )

    return ConditionalRangeLeft(
        state=RemainingState.MEASURED,
        value=measurement,
        conditioned_on=tuple(refs),
        available_targets=tuple(available_targets),
        exhausted=exhausted,
        basis_ref=basis_ref,
        unit=unit,
    )
