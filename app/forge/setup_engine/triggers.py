"""Trigger semantics (Ch III.5.3).

Exactly seven trigger types, one declared requirement per card, and a
matching rule that never promotes one type into another:

* ``TOUCH`` satisfies only ``TOUCH`` — never ``CLOSE``, ``ACCEPTANCE``
  or ``REJECTION``;
* ``CLOSE`` requires a **final** bar reference;
* ``ACCEPTANCE`` requires the declared III.4 acceptance state, not
  proximity;
* ``REJECTION`` requires an excursion **followed by** a return, or a
  declared rejection fact;
* ``SR_FLIP`` and ``OCC`` require their declared state/occurrence facts;
* a requirement is ``ALL`` (every gate literal, plus one of the declared
  alternatives) or ``ANY`` (one declared literal) — the card declares it,
  observations never infer it.

A blind touch — a touch with the required excursion absent — is an
affirmative refusal, not an armed ``WATCH``.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    TriggerCombination,
    TriggerLiteral,
    TriggerRequirement,
    TriggerType,
)
from .errors import SetupContractError

__all__ = [
    "TRIGGER_TYPES",
    "TriggerObservation",
    "TriggerSatisfaction",
    "blind_touch",
    "satisfies",
]

#: The exact seven-type vocabulary (D1).
TRIGGER_TYPES: tuple[TriggerType, ...] = (
    TriggerType.TOUCH,
    TriggerType.EXCURSION,
    TriggerType.REJECTION,
    TriggerType.ACCEPTANCE,
    TriggerType.CLOSE,
    TriggerType.SR_FLIP,
    TriggerType.OCC,
)

#: Types that require a declared state/occurrence fact, never proximity.
_DECLARED_FACT_TYPES = frozenset(
    {TriggerType.ACCEPTANCE, TriggerType.SR_FLIP, TriggerType.OCC, TriggerType.REJECTION}
)


@dataclass(frozen=True)
class TriggerObservation:
    """One governed observation of the path, supplied by the caller.

    An observation is a *fact reference*, not an inference: it names the
    trigger type, the bar that produced it, whether that bar is final,
    and — for state-bearing types — the declared state or occurrence
    reference.
    """

    trigger_type: TriggerType
    bar_ref: str
    sequence_index: int
    final_bar: bool = True
    state_ref: str | None = None
    source_ref: str = "SETUP.TRIGGER.OBSERVATION"

    def __post_init__(self) -> None:
        if not isinstance(self.trigger_type, TriggerType):
            raise SetupContractError("an observation uses the seven-type vocabulary")
        if not self.bar_ref:
            raise SetupContractError("an observation names its bar")
        if not isinstance(self.sequence_index, int) or self.sequence_index < 0:
            raise SetupContractError("an observation carries its sequence index")
        if not isinstance(self.final_bar, bool):
            raise SetupContractError("final_bar is a bool")
        if self.state_ref is not None and not self.state_ref:
            raise SetupContractError("a state reference is bounded or absent")
        if not self.source_ref:
            raise SetupContractError("an observation names its source")


@dataclass(frozen=True)
class TriggerSatisfaction:
    """The recorded outcome of matching observations to a requirement."""

    satisfied: bool
    matched: tuple[TriggerType, ...]
    unmet: tuple[TriggerType, ...]
    observed: tuple[TriggerType, ...]
    blind_touch: bool


def _has(observations: tuple[TriggerObservation, ...], kind: TriggerType) -> bool:
    return any(item.trigger_type is kind for item in observations)


def _declared(
    observations: tuple[TriggerObservation, ...], kind: TriggerType
) -> bool:
    return any(
        item.trigger_type is kind and item.state_ref is not None
        for item in observations
    )


def _rejection_sequence(observations: tuple[TriggerObservation, ...]) -> bool:
    """Excursion then return, strictly in that order on the recorded path."""

    excursions = [
        item.sequence_index
        for item in observations
        if item.trigger_type is TriggerType.EXCURSION
    ]
    returns = [
        item.sequence_index
        for item in observations
        if item.trigger_type is TriggerType.TOUCH
    ]
    return any(first < second for first in excursions for second in returns)


def _literal_satisfied(
    literal: TriggerLiteral, observations: tuple[TriggerObservation, ...]
) -> bool:
    kind = literal.trigger_type
    if kind is TriggerType.TOUCH:
        return _has(observations, TriggerType.TOUCH)
    if kind is TriggerType.EXCURSION:
        return _has(observations, TriggerType.EXCURSION)
    if kind is TriggerType.CLOSE:
        return any(
            item.trigger_type is TriggerType.CLOSE and item.final_bar
            for item in observations
        )
    if kind is TriggerType.ACCEPTANCE:
        return _declared(observations, TriggerType.ACCEPTANCE)
    if kind is TriggerType.SR_FLIP:
        return _declared(observations, TriggerType.SR_FLIP)
    if kind is TriggerType.OCC:
        return _declared(observations, TriggerType.OCC)
    if kind is TriggerType.REJECTION:
        if _declared(observations, TriggerType.REJECTION):
            return True
        return _rejection_sequence(observations)
    return False


def satisfies(
    requirement: TriggerRequirement,
    observations: tuple[TriggerObservation, ...],
) -> TriggerSatisfaction:
    """Match observations against the *declared* requirement."""

    if not isinstance(requirement, TriggerRequirement):
        raise SetupContractError("a trigger requirement is a declared object")
    observed = tuple(item.trigger_type for item in observations)
    gates = tuple(
        literal.trigger_type
        for literal in requirement.literals
        if _literal_satisfied(literal, observations)
    )
    gates_unmet = tuple(
        literal.trigger_type
        for literal in requirement.literals
        if literal.trigger_type not in gates
    )
    alternatives = tuple(
        literal.trigger_type
        for literal in requirement.any_of
        if _literal_satisfied(literal, observations)
    )
    alternatives_unmet = tuple(
        literal.trigger_type
        for literal in requirement.any_of
        if literal.trigger_type not in alternatives
    )

    if requirement.combination is TriggerCombination.ALL:
        alternative_ok = True if not requirement.any_of else bool(alternatives)
        satisfied = not gates_unmet and alternative_ok
        matched = gates + alternatives
        unmet = gates_unmet + (() if alternative_ok else alternatives_unmet)
    else:
        satisfied = bool(gates or alternatives)
        matched = gates + alternatives
        unmet = () if satisfied else gates_unmet + alternatives_unmet

    blind = (
        TriggerType.TOUCH in observed
        and TriggerType.EXCURSION not in observed
        and TriggerType.EXCURSION in requirement.declared_types
    )
    return TriggerSatisfaction(
        satisfied=satisfied,
        matched=matched,
        unmet=unmet,
        observed=observed,
        blind_touch=blind,
    )


def blind_touch(observations: tuple[TriggerObservation, ...]) -> bool:
    """A touch with no excursion at all — the forbidden entry pattern."""

    return _has(observations, TriggerType.TOUCH) and not _has(
        observations, TriggerType.EXCURSION
    )
