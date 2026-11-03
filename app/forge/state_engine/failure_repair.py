"""Failure / repair grammar (Ch III.4.4).

The grammar is **declared per family and generation**.  A family that does
not declare it can never express ``FAIL``/``REPAIR``/``COMPRESS``/
``RELEASE`` — the absence is authority, not an implementation gap to fill.

The declared canonical chain is:

    valid acceptance -> failure -> midpoint repair ->
    compression / reacceptance / opposite acceptance

with failure, attempted repair, confirmed repair and a *new* acceptance
kept as four distinct states.  Historical P90 behaviour is declared only
for the EUR Daily generation that carries it and is never generalized to
another model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from app.forge.measurements import RuleMaterialization

from .errors import (
    CompressionWithoutFailureError,
    EvidenceRequiredError,
    FailureGrammarNotDeclaredError,
    FailureWithoutAcceptanceError,
    ReleaseWithoutCompressionError,
    RepairWithoutFailureError,
    StateContractError,
    TransitionAuthorityMismatchError,
)
from .vocabulary import TransitionKind, TransitionRule

__all__ = [
    "FAILURE_GRAMMARS",
    "FailureGrammar",
    "FailureRecord",
    "FailureState",
    "advance_failure",
    "failure_grammar_for",
]

_IDENT = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


class FailureState(str, Enum):
    """The distinct failure/repair states (attempt ≠ confirmation)."""

    NONE = "NONE"
    ACCEPTED = "ACCEPTED"
    FAILED = "FAILED"
    REPAIR_ATTEMPTED = "REPAIR_ATTEMPTED"
    REPAIR_CONFIRMED = "REPAIR_CONFIRMED"
    COMPRESSED = "COMPRESSED"
    REACCEPTED = "REACCEPTED"
    OPPOSITE_ACCEPTED = "OPPOSITE_ACCEPTED"


@dataclass(frozen=True)
class FailureGrammar:
    """A declared failure/repair grammar for one model generation."""

    model_id: str
    model_version: str
    family: str
    rule: TransitionRule
    midpoint_rule_ref: str
    requires_evidence: bool = False

    def __post_init__(self) -> None:
        if not self.model_id or not self.model_version or not self.family:
            raise StateContractError("a failure grammar declares its model key")
        if not isinstance(self.rule, TransitionRule):
            raise StateContractError("a failure grammar carries its canonical rule")
        if not self.midpoint_rule_ref:
            raise StateContractError("a failure grammar declares its midpoint rule")


@dataclass(frozen=True)
class FailureRecord:
    """One step in a failure/repair chain, with its acceptance lineage."""

    model_id: str
    model_version: str
    rule_id: str
    state: FailureState
    acceptance_ref: str | None
    event_time: datetime
    evidence_refs: tuple[str, ...] = ()
    steps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.state, FailureState):
            raise StateContractError("a failure record carries a bounded state")
        if self.state in (FailureState.ACCEPTED, FailureState.REACCEPTED) and not (
            self.acceptance_ref
        ):
            raise StateContractError("an acceptance state names its acceptance")
        if self.event_time.tzinfo is None:
            raise StateContractError("failure event times are timezone-aware")

    @property
    def is_new_acceptance(self) -> bool:
        """A confirmed repair is never a new acceptance (D6)."""

        return self.state in (FailureState.REACCEPTED, FailureState.OPPOSITE_ACCEPTED)


_FAILURE_GRAMMARS: tuple[FailureGrammar, ...] = (
    FailureGrammar(
        model_id="EUR.DAILY.NEWS_REKEY.V1",
        model_version="PHASE1",
        family="EUR_DAILY",
        rule=TransitionRule(
            rule_id="EUR_DAILY_P90_FAILURE_REPAIR",
            rule_version="V1",
            materialization=RuleMaterialization.DECLARED,
            source_ref="EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md",
        ),
        midpoint_rule_ref="EUR_DAILY_MIDPOINT_REPAIR",
    ),
    FailureGrammar(
        model_id="XAU.GAME.L1_L2_L3.V1",
        model_version="V1",
        family="XAU",
        rule=TransitionRule(
            rule_id="XAU_FAILURE_REPAIR_BANDS",
            rule_version="V1",
            materialization=RuleMaterialization.DECLARED,
            source_ref="XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md",
        ),
        midpoint_rule_ref="XAU_MIDPOINT_REPAIR",
        requires_evidence=True,
    ),
)

FAILURE_GRAMMARS: Mapping[tuple[str, str], FailureGrammar] = MappingProxyType(
    {(grammar.model_id, grammar.model_version): grammar for grammar in _FAILURE_GRAMMARS}
)


def failure_grammar_for(model_id: str, model_version: str) -> FailureGrammar:
    """Resolve the declared grammar; undeclared ⇒ explicit refusal."""

    try:
        return FAILURE_GRAMMARS[(model_id, model_version)]
    except KeyError:
        raise FailureGrammarNotDeclaredError(
            f"{model_id}@{model_version} declares no failure/repair grammar; "
            "historical failure behaviour is never generalized to a model that "
            "does not declare it"
        ) from None


_ALLOWED_KINDS: frozenset[TransitionKind] = frozenset(
    {
        TransitionKind.ACCEPT,
        TransitionKind.FAIL,
        TransitionKind.REPAIR,
        TransitionKind.COMPRESS,
        TransitionKind.RELEASE,
    }
)


def advance_failure(
    prior: FailureRecord,
    kind: TransitionKind,
    *,
    grammar: FailureGrammar,
    event_time: datetime,
    acceptance_ref: str | None = None,
    confirmed: bool = False,
    reaccepted: bool = False,
    evidence_refs: tuple[str, ...] = (),
) -> FailureRecord:
    """Advance a failure/repair chain by one declared step."""

    if not isinstance(prior, FailureRecord):
        raise StateContractError("advance_failure requires a FailureRecord")
    if not isinstance(kind, TransitionKind):
        raise StateContractError("advance_failure requires a vocabulary kind")
    if not isinstance(grammar, FailureGrammar):
        raise StateContractError("advance_failure requires a declared grammar")
    if kind not in _ALLOWED_KINDS:
        raise StateContractError(
            f"{kind.value} is not part of the failure/repair grammar"
        )
    if grammar.model_id != prior.model_id or grammar.model_version != prior.model_version:
        raise TransitionAuthorityMismatchError(
            f"grammar {grammar.model_id}@{grammar.model_version} does not own "
            f"{prior.model_id}@{prior.model_version}"
        )
    if event_time.tzinfo is None:
        raise StateContractError("event_time must be timezone-aware (injected)")
    if event_time < prior.event_time:
        raise StateContractError("event_time precedes the prior failure record")

    refs = tuple(evidence_refs) or prior.evidence_refs
    if grammar.requires_evidence and kind in (
        TransitionKind.FAIL,
        TransitionKind.REPAIR,
    ) and not refs:
        raise EvidenceRequiredError(
            f"{grammar.model_id} band transitions are evidence-linked; "
            f"{kind.value} requires evidence references"
        )

    steps = prior.steps + (kind.value,)

    def build(state: FailureState, acceptance: str | None) -> FailureRecord:
        return FailureRecord(
            model_id=prior.model_id,
            model_version=prior.model_version,
            rule_id=grammar.rule.rule_id,
            state=state,
            acceptance_ref=acceptance,
            event_time=event_time,
            evidence_refs=refs,
            steps=steps,
        )

    if kind is TransitionKind.ACCEPT:
        if prior.state not in (
            FailureState.NONE,
            FailureState.REACCEPTED,
            FailureState.OPPOSITE_ACCEPTED,
        ):
            raise StateContractError(
                f"cannot accept from {prior.state.value}"
            )
        if not acceptance_ref:
            raise StateContractError("ACCEPT requires an acceptance reference")
        return build(FailureState.ACCEPTED, acceptance_ref)

    if kind is TransitionKind.FAIL:
        if prior.state is not FailureState.ACCEPTED:
            raise FailureWithoutAcceptanceError(
                "failure requires a prior valid acceptance"
            )
        return build(FailureState.FAILED, prior.acceptance_ref)

    if kind is TransitionKind.REPAIR:
        if prior.state is not FailureState.FAILED:
            raise RepairWithoutFailureError(
                "repair requires a prior failure"
            )
        return build(
            FailureState.REPAIR_CONFIRMED if confirmed else FailureState.REPAIR_ATTEMPTED,
            # A confirmed repair does not create a new acceptance (D6).
            prior.acceptance_ref,
        )

    if kind is TransitionKind.COMPRESS:
        if prior.state not in (FailureState.FAILED, FailureState.REPAIR_ATTEMPTED):
            raise CompressionWithoutFailureError(
                "compression requires a prior failure or attempted repair"
            )
        return build(FailureState.COMPRESSED, prior.acceptance_ref)

    # RELEASE
    if prior.state is not FailureState.COMPRESSED:
        raise ReleaseWithoutCompressionError(
            "release requires a prior compression"
        )
    if reaccepted:
        if not acceptance_ref:
            raise StateContractError(
                "a reacceptance release requires its new acceptance reference"
            )
        return build(FailureState.REACCEPTED, acceptance_ref)
    return build(FailureState.OPPOSITE_ACCEPTED, acceptance_ref or prior.acceptance_ref)


def start_failure_chain(
    model_id: str, model_version: str, *, event_time: datetime
) -> FailureRecord:
    """Open a chain at ``NONE`` for a model that declares a grammar."""

    grammar = failure_grammar_for(model_id, model_version)
    if event_time.tzinfo is None:
        raise StateContractError("event_time must be timezone-aware (injected)")
    return FailureRecord(
        model_id=model_id,
        model_version=model_version,
        rule_id=grammar.rule.rule_id,
        state=FailureState.NONE,
        acceptance_ref=None,
        event_time=event_time,
        steps=(),
    )
