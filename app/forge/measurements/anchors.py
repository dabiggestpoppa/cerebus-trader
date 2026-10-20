"""Range Birth / anchor interface (Ch III.2.4).

An *anchor* is the earned structural reference from which coordinates
may be projected.  Its state vocabulary is frozen and exactly five
valued::

    UNRESOLVED | ELIGIBLE | ACTIVE | INVALIDATED | REKEYED

This module implements the **interface**, not the anchor *rule*.  The
canonical Fib R15 Range Birth eligibility rule is **not** materialized
in the frozen corpus (the model card states it "must be materialized
from R15 before autonomous signal generation"), so:

* there is **no anchor generator** in this package — no function turns
  bars or pivots into an anchor.  The R11 generic-pivot fallback is
  absent by construction, not merely unused;
* an anchor record is a *declared input* that a model runtime (III.3)
  or a governed fixture supplies; the engine validates its internal
  consistency and reports it;
* eligibility is a first-class output (``AnchorEligibility``) carrying
  the state, the earned-range reference, the rule identity and the
  refusal code;
* ``automation_ready`` is **always** ``False`` at this layer: III.2
  measures, III.5 governs automation approval, and the R15 rule is an
  open gap (III.2-GAP-1).

REKEYED is a *remapping transition* (invariant #9): the prior anchor is
never destroyed, mutated or silently replaced — the successor carries
the lineage of the anchor it remaps.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .contracts import (
    Measurement,
    Provenance,
    envelope,
)
from .errors import (
    InvalidAnchorStateError,
    MeasurementContractError,
)
from .ranges import RangeMeasurement

__all__ = [
    "ANCHOR_RULE_REGISTRY",
    "AnchorEligibility",
    "AnchorRecord",
    "AnchorRefusalCode",
    "AnchorRule",
    "AnchorStatus",
    "RuleMaterialization",
    "evaluate_anchor",
    "rekey_anchor",
]


class AnchorStatus(str, Enum):
    """The exact five-state anchor vocabulary (D1)."""

    UNRESOLVED = "UNRESOLVED"
    ELIGIBLE = "ELIGIBLE"
    ACTIVE = "ACTIVE"
    INVALIDATED = "INVALIDATED"
    REKEYED = "REKEYED"


#: States from which a coordinate may not be projected (C2 / D4).
PROJECTION_BLOCKING_STATES: frozenset[AnchorStatus] = frozenset(
    {AnchorStatus.UNRESOLVED, AnchorStatus.INVALIDATED, AnchorStatus.REKEYED}
)

#: States that require an earned range and a declared rule.
EARNED_STATES: frozenset[AnchorStatus] = frozenset(
    {AnchorStatus.ELIGIBLE, AnchorStatus.ACTIVE}
)


class RuleMaterialization(str, Enum):
    """How far the anchor's eligibility rule is materialized.

    ``CANONICAL`` — a frozen canonical source states the rule.
    ``DECLARED`` — the rule is declared by the caller; no canonical
    source materializes it (the R15 situation today).
    ``NOT_MATERIALIZED`` — the rule is known to be missing; the anchor
    can never become eligible.
    """

    CANONICAL = "CANONICAL"
    DECLARED = "DECLARED"
    NOT_MATERIALIZED = "NOT_MATERIALIZED"


class AnchorRefusalCode(str, Enum):
    """Bounded refusal codes carried by an eligibility output."""

    NONE = "NONE"
    EARNED_RANGE_MISSING = "EARNED_RANGE_MISSING"
    RULE_NOT_MATERIALIZED = "RULE_NOT_MATERIALIZED"
    ANCHOR_UNRESOLVED = "ANCHOR_UNRESOLVED"
    ANCHOR_INVALIDATED = "ANCHOR_INVALIDATED"
    ANCHOR_REKEYED = "ANCHOR_REKEYED"
    INVALIDATION_REASON_MISSING = "INVALIDATION_REASON_MISSING"


@dataclass(frozen=True)
class AnchorRule:
    """The identity of the rule that declared (or failed to declare) an anchor.

    ``materialization`` states whether a frozen canonical source
    materializes the rule.  The canonical R15 Range Birth rule is
    **not** materialized, so no registry entry in this package carries
    ``CANONICAL`` for that rule.
    """

    rule_id: str
    rule_version: str
    materialization: RuleMaterialization
    source_ref: str

    def __post_init__(self) -> None:
        if not self.rule_id or not self.rule_version:
            raise MeasurementContractError(
                "anchor rule requires an id and a version"
            )
        if not self.source_ref:
            raise MeasurementContractError("anchor rule requires a source ref")

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "materialization": self.materialization.value,
            "source_ref": self.source_ref,
        }


#: The registered anchor rules.
#:
#: The registry holds **no** production Range Birth rule: the canonical
#: R15 eligibility rule is not materialized in the corpus (III.2-GAP-1)
#: and the R11 generic-pivot fallback is forbidden.  A lookup of an
#: unknown rule refuses instead of falling back to anything.
ANCHOR_RULE_REGISTRY: Mapping[str, AnchorRule] = {}


@dataclass(frozen=True)
class AnchorRecord:
    """A declared anchor — an input to the measurement layer.

    The record is *not* produced by this package.  It is supplied by a
    model runtime or a governed fixture; the engine validates that an
    ELIGIBLE/ACTIVE anchor names an earned range and a rule, and that
    an INVALIDATED anchor states why.
    """

    anchor_id: str
    model_id: str
    model_version: str
    status: AnchorStatus
    rule: AnchorRule
    earned_range: RangeMeasurement | None = None
    invalidation_reason: str | None = None
    rekey_source_anchor_id: str | None = None
    rekey_mapping: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.anchor_id:
            raise MeasurementContractError("anchor requires an id")
        if not self.model_id or not self.model_version:
            raise MeasurementContractError(
                "anchor requires a model id and a model version"
            )
        if not isinstance(self.status, AnchorStatus):
            raise InvalidAnchorStateError(
                f"unknown anchor state {self.status!r}"
            )
        if self.status in EARNED_STATES:
            if self.earned_range is None:
                raise MeasurementContractError(
                    f"{self.status.value} anchor requires an earned range"
                )
            if self.rule.materialization is RuleMaterialization.NOT_MATERIALIZED:
                raise MeasurementContractError(
                    "an anchor cannot be earned under a rule that is not materialized"
                )
        if self.status is AnchorStatus.INVALIDATED and not self.invalidation_reason:
            raise MeasurementContractError(
                "an invalidated anchor must state its invalidation reason"
            )
        if self.status is AnchorStatus.REKEYED:
            if not self.rekey_source_anchor_id:
                raise MeasurementContractError(
                    "a rekeyed anchor must name the anchor it remaps"
                )
        object.__setattr__(
            self,
            "rekey_mapping",
            dict(self.rekey_mapping) if self.rekey_mapping is not None else None,
        )

    def to_dict(self) -> dict:
        return {
            "anchor_id": self.anchor_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "status": self.status.value,
            "rule": self.rule.to_dict(),
            "earned_range_reference": (
                self.earned_range.source_window.input_digest
                if self.earned_range is not None
                else None
            ),
            "invalidation_reason": self.invalidation_reason,
            "rekey_source_anchor_id": self.rekey_source_anchor_id,
            "rekey_mapping": (
                dict(self.rekey_mapping)
                if self.rekey_mapping is not None
                else None
            ),
        }


@dataclass(frozen=True)
class AnchorEligibility(Measurement):
    """The first-class anchor eligibility output (D2)."""

    anchor_id: str
    model_id: str
    model_version: str
    status: AnchorStatus
    earned_range_reference: str | None
    rule_id: str
    rule_version: str
    rule_materialization: RuleMaterialization
    refusal_code: AnchorRefusalCode
    automation_ready: bool
    rekey_source_anchor_id: str | None

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def evaluate_anchor(
    anchor: AnchorRecord,
    *,
    provenance: Provenance,
    source_window=None,
    definition_version: str = "V1",
) -> AnchorEligibility:
    """Report the eligibility of one declared anchor.

    The output is a *report*, never a promotion: the anchor's status is
    carried through unchanged, the refusal code names exactly why a
    projection would be blocked, and ``automation_ready`` is always
    ``False`` at the measurement layer.
    """
    from .contracts import source_window_from_bars

    if source_window is None:
        if anchor.earned_range is None:
            raise MeasurementContractError(
                "an anchor without an earned range needs an explicit source window"
            )
        source_window = anchor.earned_range.source_window
    assert source_window is not None

    refusal = AnchorRefusalCode.NONE
    if anchor.status is AnchorStatus.UNRESOLVED:
        refusal = AnchorRefusalCode.ANCHOR_UNRESOLVED
    elif anchor.status is AnchorStatus.INVALIDATED:
        refusal = AnchorRefusalCode.ANCHOR_INVALIDATED
    elif anchor.status is AnchorStatus.REKEYED:
        refusal = AnchorRefusalCode.ANCHOR_REKEYED
    elif anchor.earned_range is None:
        refusal = AnchorRefusalCode.EARNED_RANGE_MISSING
    elif anchor.rule.materialization is RuleMaterialization.NOT_MATERIALIZED:
        refusal = AnchorRefusalCode.RULE_NOT_MATERIALIZED

    context = provenance.context(source_window)
    return AnchorEligibility(
        **envelope(
            context,
            "ANCHOR_ELIGIBILITY",
            definition_version=definition_version,
            native_unit=(
                anchor.earned_range.native_unit
                if anchor.earned_range is not None
                else None
            ),
        ),
        anchor_id=anchor.anchor_id,
        model_id=anchor.model_id,
        model_version=anchor.model_version,
        status=anchor.status,
        earned_range_reference=(
            anchor.earned_range.source_window.input_digest
            if anchor.earned_range is not None
            else None
        ),
        rule_id=anchor.rule.rule_id,
        rule_version=anchor.rule.rule_version,
        rule_materialization=anchor.rule.materialization,
        refusal_code=refusal,
        automation_ready=False,
        rekey_source_anchor_id=anchor.rekey_source_anchor_id,
    )


@dataclass(frozen=True)
class AnchorRekey(Measurement):
    """A rekey transition: a remapping, never a destruction (D3)."""

    anchor_id: str
    successor_anchor_id: str
    model_id: str
    model_version: str
    rule_id: str
    rule_version: str
    mapping: tuple[tuple[str, str], ...]
    prior_status: AnchorStatus

    def to_dict(self) -> dict:
        from .contracts import encode_value

        return encode_value(self)


def rekey_anchor(
    prior: AnchorRecord,
    successor_anchor_id: str,
    *,
    mapping: Mapping[str, str],
    provenance: Provenance,
    definition_version: str = "V1",
) -> AnchorRekey:
    """Emit the remapping transition from a prior anchor to a successor.

    The prior anchor is returned untouched: the transition is *recorded*,
    never applied destructively.  The successor anchor is constructed by
    the caller (III.3), which is the only layer allowed to declare a
    new earned range.
    """
    if prior.status is AnchorStatus.UNRESOLVED:
        raise MeasurementContractError(
            "an unresolved anchor cannot be rekeyed"
        )
    if prior.status is AnchorStatus.INVALIDATED:
        raise MeasurementContractError(
            "an invalidated anchor cannot be rekeyed"
        )
    if not successor_anchor_id:
        raise MeasurementContractError("a rekey needs a successor anchor id")
    if not mapping:
        raise MeasurementContractError("a rekey needs an explicit mapping")
    if prior.earned_range is None:
        raise MeasurementContractError("a rekey needs an earned range")

    context = provenance.context(prior.earned_range.source_window)
    return AnchorRekey(
        **envelope(
            context,
            "ANCHOR_REKEY",
            definition_version=definition_version,
            native_unit=prior.earned_range.native_unit,
        ),
        anchor_id=prior.anchor_id,
        successor_anchor_id=successor_anchor_id,
        model_id=prior.model_id,
        model_version=prior.model_version,
        rule_id=prior.rule.rule_id,
        rule_version=prior.rule.rule_version,
        mapping=tuple(sorted(mapping.items())),
        prior_status=prior.status,
    )
