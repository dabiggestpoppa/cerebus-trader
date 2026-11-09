"""Book IV / Bloc IV.5 — answer compiler, validators and citations."""

from app.forge.ask_cerebus.answer.admission import Admission, AnswerPolicy, admit
from app.forge.ask_cerebus.answer.enums import (
    AnswerDepth,
    AnswerOutcome,
    AnswerRefusalCode,
    REFUSAL_PRECEDENCE,
    SectionId,
    ValidationCode,
)
from app.forge.ask_cerebus.answer.schema import (
    AnswerClaim,
    AnswerNumber,
    AnswerSection,
    CitationRef,
    FinalResponseRecord,
    GovernedAnswerRefusal,
    ValidatedAnswer,
)
from app.forge.ask_cerebus.answer.service import validate_answer
from app.forge.ask_cerebus.answer.versions import (
    ANSWER_RECORD_V1,
    ANSWER_SECTION_SCHEMA_V1,
    ASK_ANSWER_CONTRACT_V1,
    VALIDATOR_SET_V1,
    VALIDATOR_ORDER,
)

__all__ = [
    "Admission",
    "AnswerPolicy",
    "admit",
    "AnswerDepth",
    "AnswerOutcome",
    "AnswerRefusalCode",
    "REFUSAL_PRECEDENCE",
    "SectionId",
    "ValidationCode",
    "AnswerClaim",
    "AnswerNumber",
    "AnswerSection",
    "CitationRef",
    "FinalResponseRecord",
    "GovernedAnswerRefusal",
    "ValidatedAnswer",
    "validate_answer",
    "ANSWER_RECORD_V1",
    "ANSWER_SECTION_SCHEMA_V1",
    "ASK_ANSWER_CONTRACT_V1",
    "VALIDATOR_SET_V1",
    "VALIDATOR_ORDER",
]
