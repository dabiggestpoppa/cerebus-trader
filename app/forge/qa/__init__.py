"""Book I / Bloc I.5 — QA & Answer Contract.

Deterministic answer quality over the ratified I.4 retrieval boundary:
question classification → governed intake → claim/evidence/source binding →
answerability decision → validated structured answer. No LLM, no provider,
no route — an in-process kernel only.
"""
from __future__ import annotations

from app.forge.qa.contract import (
    Answer,
    AnswerClass,
    AnswerOutcome,
    AnswerValidationError,
    Assertion,
    AssertionVerdict,
    Citation,
    ConflictKind,
    ConflictNote,
    ConflictResolution,
    DenialEntry,
    FollowUp,
    Gap,
    GapCode,
    Ladder,
    Qualification,
    QualificationCode,
    label_for_status,
    validate_answer,
)
from app.forge.qa.kernel import IDENTITY_DIMENSIONS, QAService
from app.forge.qa.question import (
    ClassifiedQuestion,
    QuestionClass,
    classify_question,
)

__all__ = [
    "Answer",
    "AnswerClass",
    "AnswerOutcome",
    "AnswerValidationError",
    "Assertion",
    "AssertionVerdict",
    "Citation",
    "ClassifiedQuestion",
    "ConflictKind",
    "ConflictNote",
    "ConflictResolution",
    "DenialEntry",
    "FollowUp",
    "Gap",
    "GapCode",
    "IDENTITY_DIMENSIONS",
    "Ladder",
    "Qualification",
    "QualificationCode",
    "QAService",
    "QuestionClass",
    "classify_question",
    "label_for_status",
    "validate_answer",
]
