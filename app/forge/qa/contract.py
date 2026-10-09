"""Book I / Bloc I.5 — structured answer contract (frozen vocabulary).

The contract defines the *answer* representation and its validation law. It
introduces NO new evidence-status enum and NO new ontology value:

- ``EvidenceStatus`` stays the frozen I.1 enum (carried verbatim on every
  assertion);
- epistemic labels are the frozen ``ANSWER_CONTRACT_V1`` vocabulary with the
  PLAN §2.2 status→label table;
- answerability outcomes (PLAN §2.3) are I.5's own frozen answer vocabulary —
  they describe *answerability*, never epistemic status.

Laws enforced by :func:`validate_answer` (fail closed, never repairs):

- ladder monotonicity: ``assertable ⇒ supported ⇒ retrieved``,
  ``explainable ⇒ assertable``;
- outcome consistency (e.g. ``ANSWERABLE`` ⇒ no gaps, full citations;
  ``OUT_OF_CORPUS``/``RESTRICTED`` ⇒ zero corpus content);
- referential integrity: citations point at claims/evidence the answer
  actually references;
- no internal marker text on any content surface;
- bounded structure (assertions, citations, follow-ups);
- deterministic identity: sorted-key JSON, ``content_hash()``, no clock.
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.forge.canonical import ClaimIdentity, EvidenceStatus

# Bounded answer structure (PLAN §10): an answer is never an unbounded dump.
MAX_ASSERTIONS = 3
MAX_CITATIONS = 6
MAX_FOLLOW_UPS = 3
MAX_QUALIFICATIONS = 16
MAX_GAPS = 16
MAX_CONFLICTS = 4


class AnswerOutcome(str, Enum):
    """The seven frozen answerability outcomes (PLAN §2.3).

    These are answerability outcomes, NOT evidence statuses. ``UNSUPPORTED``
    is the contract's ``INSUFFICIENT_EVIDENCE`` case.
    """

    ANSWERABLE = "ANSWERABLE"
    ANSWERABLE_QUALIFIED = "ANSWERABLE_QUALIFIED"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    OUT_OF_CORPUS = "OUT_OF_CORPUS"
    RESTRICTED = "RESTRICTED"


class AnswerClass(str, Enum):
    """Frozen question/answer class (PLAN §3): descriptive answers are an
    explicit class that makes no empirical claim."""

    DESCRIPTIVE = "DESCRIPTIVE"
    EMPIRICAL = "EMPIRICAL"
    ACTIONABLE = "ACTIONABLE"
    COMPARATIVE = "COMPARATIVE"


class AssertionVerdict(str, Enum):
    ASSERT = "ASSERT"      # status authority + identity + chain all satisfied
    QUALIFY = "QUALIFY"    # assertable only with a mandatory qualification
    GAP = "GAP"            # cannot be asserted; disclosed as a gap


class QualificationCode(str, Enum):
    """Mandatory qualification vocabulary (frozen; PLAN §4)."""

    SMALL_N = "SMALL_N"
    RESEARCH_SAMPLE = "RESEARCH_SAMPLE"
    RELATIONSHIP_STATISTIC = "RELATIONSHIP_STATISTIC"
    FORWARD_OOS = "FORWARD_OOS"
    CANDIDATE_STATUS = "CANDIDATE_STATUS"
    RESEARCH_FLAG = "RESEARCH_FLAG"
    HISTORICAL_GENERATION = "HISTORICAL_GENERATION"
    SUPERSEDED = "SUPERSEDED"
    PARKED = "PARKED"
    NEGATIVE_EVIDENCE = "NEGATIVE_EVIDENCE"
    NO_CONTRACT_LABEL = "NO_CONTRACT_LABEL"
    ACTION_GAP = "ACTION_GAP"
    IDENTITY_UNSPECIFIED = "IDENTITY_UNSPECIFIED"


class GapCode(str, Enum):
    """Why an assertion or answer could not be produced (frozen)."""

    NOT_IN_INDEX = "NOT_IN_INDEX"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NO_EVIDENCE_REFERENCE = "NO_EVIDENCE_REFERENCE"
    NO_SOURCE_ARTIFACT = "NO_SOURCE_ARTIFACT"
    NO_CLAIM_ROUTE = "NO_CLAIM_ROUTE"
    IDENTITY_INCOMPLETE = "IDENTITY_INCOMPLETE"
    DENIED = "DENIED"
    NO_SETUP_CARD = "NO_SETUP_CARD"
    CONFLICT_UNRESOLVED = "CONFLICT_UNRESOLVED"


class ConflictKind(str, Enum):
    MATCHED_IDENTITY_DIVERGENCE = "MATCHED_IDENTITY_DIVERGENCE"
    DECLARED_CONTRADICTS = "DECLARED_CONTRADICTS"


class ConflictResolution(str, Enum):
    DOWNGRADE_AND_EXPOSE_BOTH = "DOWNGRADE_AND_EXPOSE_BOTH"
    SEPARATE_POPULATIONS = "SEPARATE_POPULATIONS"


# Frozen epistemic-label vocabulary (ANSWER_CONTRACT_V1) and the PLAN §2.2
# status → label table. ``None`` means the frozen contract defines no label
# for that status: a qualification is then mandatory and the assertion can
# never be a plain ANSWERABLE.
_EPISTEMIC_LABELS = frozenset(
    {
        "CANONICAL",
        "VALIDATED",
        "FORWARD_OOS",
        "CANDIDATE",
        "RESEARCH_FLAG",
        "HISTORICAL",
        "NEGATIVE_EVIDENCE",
        "PARKED",
        "SUPERSEDED",
        "INFERENCE",
        "GENERAL_KNOWLEDGE",
        "INSUFFICIENT_EVIDENCE",
    }
)

_STATUS_TO_LABEL: dict[str, str] = {
    EvidenceStatus.VALIDATED.value: "VALIDATED",
    EvidenceStatus.FORWARD_OOS.value: "FORWARD_OOS",
    EvidenceStatus.CANDIDATE.value: "CANDIDATE",
    EvidenceStatus.RESEARCH_FLAG.value: "RESEARCH_FLAG",
    EvidenceStatus.HISTORICAL.value: "HISTORICAL",
    EvidenceStatus.PARKED.value: "PARKED",
    EvidenceStatus.SUPERSEDED.value: "SUPERSEDED",
    EvidenceStatus.FALSIFIED.value: "NEGATIVE_EVIDENCE",
    EvidenceStatus.DESCRIPTIVE.value: "CANONICAL",
    # OBSERVED, NO_GO, REPRODUCTION_REQUIRED, INTERNAL_CONTRADICTION,
    # IMPLEMENTATION_NOT_PARITY_SAFE: no frozen contract label ⇒ None.
}


def label_for_status(status: str | EvidenceStatus) -> str | None:
    """PLAN §2.2 frozen status → epistemic label table."""
    value = status.value if isinstance(status, EvidenceStatus) else status
    return _STATUS_TO_LABEL.get(value)


def is_known_epistemic_label(label: str) -> bool:
    return label in _EPISTEMIC_LABELS


# Internal-marker text that must never appear on any answer content surface.
_INTERNAL_MARKERS = ("INTERNAL_METHOD", "INTERNAL_CODE")


class Ladder(BaseModel):
    """The four-state ladder (PLAN §2.5). Monotonic by validation law."""

    model_config = ConfigDict(frozen=True)

    retrieved: bool = False
    supported: bool = False
    assertable: bool = False
    explainable: bool = False

    @model_validator(mode="after")
    def _monotonic(self) -> "Ladder":
        if self.explainable and not self.assertable:
            raise ValueError("explainable requires assertable")
        if self.assertable and not self.supported:
            raise ValueError("assertable requires supported")
        if self.supported and not self.retrieved:
            raise ValueError("supported requires retrieved")
        return self

    def to_dict(self) -> dict:
        return {
            "retrieved": self.retrieved,
            "supported": self.supported,
            "assertable": self.assertable,
            "explainable": self.explainable,
        }


class Assertion(BaseModel):
    """A bounded answer statement: governed ``retrieval_text`` only."""

    model_config = ConfigDict(frozen=True)

    object_id: str
    object_type: str
    layer: str = ""
    market_scope: tuple[str, ...] = ()
    status: str                      # frozen EvidenceStatus, verbatim
    epistemic_label: str | None      # PLAN §2.2 table; None ⇒ qualification
    text: str                        # governed retrieval_text, never a body
    numerical: bool
    verdict: AssertionVerdict
    verdict_reason: str = ""         # machine code (QualificationCode/GapCode)
    claim_identity: ClaimIdentity | None = None
    supported: bool = False
    support_classification: str = "NO_SOURCE"
    evidence_ids: tuple[str, ...] = ()
    sample_n: int | None = None
    qualifiers: tuple[str, ...] = ()
    generation: int = 0
    index_generation: int = 0

    @model_validator(mode="after")
    def _numerical_identity(self) -> "Assertion":
        if self.numerical and self.object_type == "CLAIM":
            if self.claim_identity is None:
                raise ValueError(
                    "numerical claim assertion requires all eight identity "
                    "dimensions"
                )
        if self.status not in {s.value for s in EvidenceStatus}:
            raise ValueError(f"unknown evidence status: {self.status!r}")
        if self.epistemic_label is not None and not is_known_epistemic_label(
            self.epistemic_label
        ):
            raise ValueError(f"unknown epistemic label: {self.epistemic_label!r}")
        return self


class Citation(BaseModel):
    """Assertion → claim → evidence → source artifact routing facts (no body)."""

    model_config = ConfigDict(frozen=True)

    claim_id: str
    evidence_id: str
    artifact_id: str
    relation: str
    source_class: str
    source_state: str
    content_identity: str
    locator: str

    @model_validator(mode="after")
    def _complete(self) -> "Citation":
        required = (
            "claim_id",
            "artifact_id",
            "relation",
            "content_identity",
            "locator",
        )
        for field_name in required:
            if not getattr(self, field_name):
                raise ValueError(f"citation field {field_name} must be non-empty")
        if not self.evidence_id and self.relation != "DEFINES":
            raise ValueError(
                "only a DEFINES (doctrine) citation may omit the evidence id"
            )
        if not self.content_identity.startswith("sha256:"):
            raise ValueError("citation content_identity must be a sha256 identity")
        return self


class Qualification(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: QualificationCode
    text: str
    object_id: str = ""


class ConflictNote(BaseModel):
    """Bounded, auditable conflict record (PLAN §7)."""

    model_config = ConfigDict(frozen=True)

    kind: ConflictKind
    basis: str                        # "SAME_POPULATION" | "contradicts_ids"
    claim_ids: tuple[str, ...]
    statuses: tuple[str, ...]
    generations: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()
    resolution: ConflictResolution
    matched_dimensions: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _parallel(self) -> "ConflictNote":
        if len(self.claim_ids) < 2:
            raise ValueError("a conflict needs at least two claims")
        if len(self.statuses) != len(self.claim_ids):
            raise ValueError("statuses must parallel claim_ids")
        if self.resolution is ConflictResolution.SEPARATE_POPULATIONS and (
            self.basis == "SAME_POPULATION"
        ):
            raise ValueError(
                "matched populations must be downgraded and exposed, never "
                "separated"
            )
        return self


class Gap(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: GapCode
    detail: str
    object_id: str = ""


class DenialEntry(BaseModel):
    """Content-free denial (identical fields to the I.4 denial contract)."""

    model_config = ConfigDict(frozen=True)

    object_id: str
    exposure: str
    reason_code: str


class FollowUp(BaseModel):
    """Suggested next question — built only from authorized result titles."""

    model_config = ConfigDict(frozen=True)

    object_id: str
    text: str


class Answer(BaseModel):
    """The frozen machine-readable answer representation (PLAN §10)."""

    model_config = ConfigDict(frozen=True)

    outcome: AnswerOutcome
    answer_class: AnswerClass
    ladder: Ladder
    epistemic_label: str | None = None
    scope: tuple[str, ...] = ()
    assertions: tuple[Assertion, ...] = ()
    claim_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    citations: tuple[Citation, ...] = ()
    qualifications: tuple[Qualification, ...] = ()
    conflicts: tuple[ConflictNote, ...] = ()
    gaps: tuple[Gap, ...] = ()
    limitations: tuple[str, ...] = ()
    denials: tuple[DenialEntry, ...] = ()
    follow_ups: tuple[FollowUp, ...] = ()
    generation: int = 0
    index_hash: str = ""

    # -- deterministic identity --------------------------------------------

    def payload_dict(self) -> dict:
        payload = self.model_dump(mode="json")
        # canonical ordering: sorted collections, sorted keys at dump time
        for key in (
            "scope",
            "claim_refs",
            "evidence_refs",
            "limitations",
        ):
            payload[key] = sorted(payload[key])
        payload["assertions"] = sorted(
            payload["assertions"], key=lambda item: item["object_id"]
        )
        payload["citations"] = sorted(
            payload["citations"],
            key=lambda item: (
                item["claim_id"],
                item["evidence_id"],
                item["artifact_id"],
            ),
        )
        payload["qualifications"] = sorted(
            payload["qualifications"], key=lambda item: (item["code"], item["object_id"])
        )
        payload["conflicts"] = sorted(
            payload["conflicts"], key=lambda item: tuple(item["claim_ids"])
        )
        payload["gaps"] = sorted(
            payload["gaps"], key=lambda item: (item["code"], item["object_id"])
        )
        payload["denials"] = sorted(
            payload["denials"], key=lambda item: item["object_id"]
        )
        payload["follow_ups"] = sorted(
            payload["follow_ups"], key=lambda item: item["object_id"]
        )
        return payload

    def to_json(self) -> str:
        return json.dumps(
            self.payload_dict(), sort_keys=True, separators=(",", ":")
        )

    def content_hash(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()


class AnswerValidationError(ValueError):
    """An invalid answer is rejected, never silently repaired (N5)."""


def _scan_for_internal_markers(answer: Answer) -> None:
    surfaces = {
        "assertion.text": [a.text for a in answer.assertions],
        "qualification.text": [q.text for q in answer.qualifications],
        "gap.detail": [g.detail for g in answer.gaps],
        "conflict.basis": [c.basis for c in answer.conflicts],
        "conflict.resolution": [c.resolution.value for c in answer.conflicts],
        "follow_up.text": [f.text for f in answer.follow_ups],
        "limitations": list(answer.limitations),
        "citation.locator": [c.locator for c in answer.citations],
    }
    for surface, values in surfaces.items():
        for value in values:
            for marker in _INTERNAL_MARKERS:
                if marker in value:
                    raise AnswerValidationError(
                        f"internal marker {marker!r} on surface {surface}"
                    )


def validate_answer(answer: Answer) -> Answer:
    """Fail-closed validation of the frozen answer contract (N1/N5)."""
    o = answer.outcome
    emp = answer.answer_class is AnswerClass.EMPIRICAL
    gaps = [a for a in answer.assertions if a.verdict is AssertionVerdict.GAP]
    has_gap = bool(gaps) or bool(answer.gaps)

    # -- bounds ------------------------------------------------------------
    if len(answer.assertions) > MAX_ASSERTIONS:
        raise AnswerValidationError("answer exceeds MAX_ASSERTIONS")
    if len(answer.citations) > MAX_CITATIONS:
        raise AnswerValidationError("answer exceeds MAX_CITATIONS")
    if len(answer.follow_ups) > MAX_FOLLOW_UPS:
        raise AnswerValidationError("answer exceeds MAX_FOLLOW_UPS")
    if len(answer.qualifications) > MAX_QUALIFICATIONS:
        raise AnswerValidationError("answer exceeds MAX_QUALIFICATIONS")
    if len(answer.gaps) > MAX_GAPS:
        raise AnswerValidationError("answer exceeds MAX_GAPS")
    if len(answer.conflicts) > MAX_CONFLICTS:
        raise AnswerValidationError("answer exceeds MAX_CONFLICTS")

    # -- outcome consistency ----------------------------------------------
    if o in (AnswerOutcome.OUT_OF_CORPUS, AnswerOutcome.RESTRICTED):
        if (
            answer.assertions
            or answer.citations
            or answer.qualifications
            or answer.conflicts
            or answer.claim_refs
            or answer.evidence_refs
            or answer.follow_ups
        ):
            raise AnswerValidationError(f"{o.value} must carry no corpus content")
        if any(
            (
                answer.ladder.retrieved,
                answer.ladder.supported,
                answer.ladder.assertable,
                answer.ladder.explainable,
            )
        ):
            raise AnswerValidationError(f"{o.value} ladder must be all false")
        if o is AnswerOutcome.RESTRICTED and not answer.denials:
            raise AnswerValidationError("RESTRICTED requires denial entries")

    if o is AnswerOutcome.UNSUPPORTED:
        if answer.epistemic_label != "INSUFFICIENT_EVIDENCE":
            raise AnswerValidationError(
                "UNSUPPORTED must carry INSUFFICIENT_EVIDENCE"
            )
        if answer.ladder.supported:
            raise AnswerValidationError("UNSUPPORTED cannot be supported")
        if answer.assertions and any(
            a.verdict is not AssertionVerdict.GAP for a in answer.assertions
        ):
            raise AnswerValidationError("UNSUPPORTED assertions must be gaps")

    if o is AnswerOutcome.CONTRADICTED and not answer.conflicts:
        raise AnswerValidationError("CONTRADICTED requires a conflict note")

    if o is AnswerOutcome.ANSWERABLE:
        if has_gap:
            raise AnswerValidationError("ANSWERABLE cannot contain gaps")
        if answer.qualifications:
            raise AnswerValidationError(
                "ANSWERABLE cannot carry mandatory qualifications "
                "(use ANSWERABLE_QUALIFIED)"
            )
        if answer.conflicts:
            raise AnswerValidationError("ANSWERABLE cannot contain conflicts")
        if not answer.assertions:
            raise AnswerValidationError("ANSWERABLE requires assertions")
        if any(a.verdict is AssertionVerdict.GAP for a in answer.assertions):
            raise AnswerValidationError("ANSWERABLE cannot contain GAP verdicts")
        if emp:
            for assertion in answer.assertions:
                if assertion.verdict is AssertionVerdict.ASSERT and not any(
                    c.claim_id == assertion.object_id for c in answer.citations
                ):
                    raise AnswerValidationError(
                        f"empirical assertion {assertion.object_id} lacks a "
                        "citation chain"
                    )

    if o is AnswerOutcome.ANSWERABLE_QUALIFIED:
        if has_gap:
            raise AnswerValidationError("qualified answer cannot contain gaps")
        if not answer.qualifications and not answer.conflicts:
            raise AnswerValidationError(
                "ANSWERABLE_QUALIFIED requires at least one qualification"
            )

    if o is AnswerOutcome.PARTIAL:
        if not has_gap:
            raise AnswerValidationError("PARTIAL requires at least one gap")
        if not any(
            a.verdict is not AssertionVerdict.GAP for a in answer.assertions
        ) and not answer.qualifications:
            raise AnswerValidationError("PARTIAL requires an assertable part")

    # -- ladder vs outcome --------------------------------------------------
    if o in (AnswerOutcome.ANSWERABLE, AnswerOutcome.ANSWERABLE_QUALIFIED):
        if not (answer.ladder.retrieved and answer.ladder.supported):
            raise AnswerValidationError("asserting outcomes require retrieved+supported")
        if o is AnswerOutcome.ANSWERABLE and not answer.ladder.assertable:
            raise AnswerValidationError("ANSWERABLE requires assertable")
        if answer.ladder.explainable and not answer.citations and emp:
            raise AnswerValidationError("explainable empirical answers cite")

    # -- referential integrity (F6) ----------------------------------------
    claim_refs = set(answer.claim_refs)
    evidence_refs = set(answer.evidence_refs)
    assertion_ids = {a.object_id for a in answer.assertions}
    if not claim_refs <= assertion_ids:
        raise AnswerValidationError("claim_refs must reference assertions")
    for citation in answer.citations:
        if citation.claim_id not in claim_refs:
            raise AnswerValidationError(
                f"citation claim {citation.claim_id} not referenced by answer"
            )
        if citation.evidence_id and citation.evidence_id not in evidence_refs:
            raise AnswerValidationError(
                f"citation evidence {citation.evidence_id} not referenced"
            )

    # -- numerical safety ---------------------------------------------------
    for assertion in answer.assertions:
        if assertion.numerical:
            if assertion.verdict is AssertionVerdict.ASSERT and assertion.object_type == "CLAIM":
                if assertion.support_classification not in (
                    "EMPIRICAL",
                    "VISUAL_ONLY",
                    "CONVERSATION_DERIVED",
                    "NO_SOURCE",
                ):
                    raise AnswerValidationError("unexpected support classification")
            if assertion.verdict is AssertionVerdict.ASSERT and not assertion.supported:
                raise AnswerValidationError(
                    "an unqualified numerical assertion must be supported"
                )
            if assertion.object_type == "CLAIM" and assertion.claim_identity is None:
                raise AnswerValidationError("numerical claim missing identity")

    # -- internal markers ---------------------------------------------------
    _scan_for_internal_markers(answer)

    # -- outcome label law --------------------------------------------------
    if o is AnswerOutcome.UNSUPPORTED and answer.epistemic_label is not None:
        if answer.epistemic_label != "INSUFFICIENT_EVIDENCE":
            raise AnswerValidationError("unsupported answers expose no other label")

    return answer
