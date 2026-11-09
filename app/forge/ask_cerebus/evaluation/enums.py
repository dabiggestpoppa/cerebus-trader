"""Closed vocabularies for Book IV / Bloc IV.6 evaluation."""

from __future__ import annotations

from enum import Enum


class CaseFamily(str, Enum):
    """The eighteen golden-corpus bands (PLAN.md §7)."""

    POSITIVE_CONTROL = "POSITIVE_CONTROL"
    FALSE_REFUSAL_CONTROL = "FALSE_REFUSAL_CONTROL"
    BEGINNER = "BEGINNER"
    OPERATOR = "OPERATOR"
    RESEARCHER = "RESEARCHER"
    UNSUPPORTED_STAT = "UNSUPPORTED_STAT"
    METRIC_LAUNDERING = "METRIC_LAUNDERING"
    LAYER_LAUNDERING = "LAYER_LAUNDERING"
    GENERATION_CONFLICT = "GENERATION_CONFLICT"
    SETUP_ELIGIBILITY = "SETUP_ELIGIBILITY"
    FRESHNESS = "FRESHNESS"
    INJECTION = "INJECTION"
    ENTITLEMENT = "ENTITLEMENT"
    EXTRACTION = "EXTRACTION"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    REFUSAL_PRECEDENCE = "REFUSAL_PRECEDENCE"
    REPLAY = "REPLAY"
    HUMAN_REVIEW = "HUMAN_REVIEW"


#: Band boundaries are frozen with the dataset (R11, x004).
BAND_RANGES: dict[CaseFamily, tuple[int, int]] = {
    CaseFamily.POSITIVE_CONTROL: (1, 12),
    CaseFamily.FALSE_REFUSAL_CONTROL: (13, 20),
    CaseFamily.BEGINNER: (21, 28),
    CaseFamily.OPERATOR: (29, 37),
    CaseFamily.RESEARCHER: (38, 46),
    CaseFamily.UNSUPPORTED_STAT: (47, 55),
    CaseFamily.METRIC_LAUNDERING: (56, 61),
    CaseFamily.LAYER_LAUNDERING: (62, 66),
    CaseFamily.GENERATION_CONFLICT: (67, 73),
    CaseFamily.SETUP_ELIGIBILITY: (74, 79),
    CaseFamily.FRESHNESS: (80, 84),
    CaseFamily.INJECTION: (85, 93),
    CaseFamily.ENTITLEMENT: (94, 100),
    CaseFamily.EXTRACTION: (101, 106),
    CaseFamily.PROVIDER_FAILURE: (107, 110),
    CaseFamily.REFUSAL_PRECEDENCE: (111, 114),
    CaseFamily.REPLAY: (115, 116),
    CaseFamily.HUMAN_REVIEW: (117, 120),
}


class CaseKind(str, Enum):
    """The six case kinds (PLAN.md §6.1)."""

    POSITIVE_CONTROL = "POSITIVE_CONTROL"
    FALSE_REFUSAL_CONTROL = "FALSE_REFUSAL_CONTROL"
    NEGATIVE_TRAP = "NEGATIVE_TRAP"
    SECURITY_ATTACK = "SECURITY_ATTACK"
    REPLAY = "REPLAY"
    REVIEW = "REVIEW"


class ExpectedOutcomeKind(str, Enum):
    ANSWER = "ANSWER"
    REFUSAL = "REFUSAL"


class ExecutionMode(str, Enum):
    CHAIN = "CHAIN"
    SEALED = "SEALED"


class Authority(str, Enum):
    """Ground-truth authority for an expectation (R6, PLAN.md §5.2)."""

    FIXTURE_FACT = "FIXTURE_FACT"
    FROZEN_RULE = "FROZEN_RULE"
    OPERATOR_ASSERTION = "OPERATOR_ASSERTION"
    SYNTHETIC_INPUT = "SYNTHETIC_INPUT"
    #: Forbidden: an expectation copied from a model or from a run.
    MODEL_OUTPUT = "MODEL_OUTPUT"
    SYSTEM_UNDER_TEST = "SYSTEM_UNDER_TEST"


VALID_AUTHORITIES = frozenset(
    {
        Authority.FIXTURE_FACT,
        Authority.FROZEN_RULE,
        Authority.OPERATOR_ASSERTION,
        Authority.SYNTHETIC_INPUT,
    }
)
FORBIDDEN_AUTHORITIES = frozenset({Authority.MODEL_OUTPUT, Authority.SYSTEM_UNDER_TEST})


class TimeScope(str, Enum):
    CURRENT = "CURRENT"
    HISTORICAL = "HISTORICAL"
    ANY = "ANY"


class ExpectedFreshness(str, Enum):
    AS_OF = "AS_OF"
    CUTOFF = "CUTOFF"
    REFUSAL = "REFUSAL"
    NOT_REQUIRED = "NOT_REQUIRED"


class FindingSeverity(str, Enum):
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"
    S4 = "S4"


SEVERITY_RANK = {
    FindingSeverity.S1: 1,
    FindingSeverity.S2: 2,
    FindingSeverity.S3: 3,
    FindingSeverity.S4: 4,
}


class AttributionOwner(str, Enum):
    IV1_QUERY = "IV1_QUERY"
    IV2_RETRIEVAL = "IV2_RETRIEVAL"
    IV3_CONTEXT = "IV3_CONTEXT"
    IV4_GATEWAY = "IV4_GATEWAY"
    IV5_VALIDATOR = "IV5_VALIDATOR"
    BOOK_I_CANONICAL = "BOOK_I_CANONICAL"
    BOOK_II_POLICY = "BOOK_II_POLICY"
    BOOK_III_INTELLIGENCE = "BOOK_III_INTELLIGENCE"
    BOOK_VI_ENTITLEMENT = "BOOK_VI_ENTITLEMENT"
    BOOK_VIII_SECURITY = "BOOK_VIII_SECURITY"
    EVALUATION_ITSELF = "EVALUATION_ITSELF"


class InjectionBoundary(str, Enum):
    IV2_EXCLUDED = "IV2_EXCLUDED"
    IV3_CONTAINED = "IV3_CONTAINED"
    IV4_DRAFTED = "IV4_DRAFTED"
    IV5_REJECTED = "IV5_REJECTED"
    EXPOSED = "EXPOSED"


BOUNDARY_RANK = {
    InjectionBoundary.IV2_EXCLUDED: 0,
    InjectionBoundary.IV3_CONTAINED: 1,
    InjectionBoundary.IV4_DRAFTED: 2,
    InjectionBoundary.IV5_REJECTED: 3,
    InjectionBoundary.EXPOSED: 4,
}


class ReviewVerdict(str, Enum):
    AGREE = "AGREE"
    DISAGREE_EXPECTATION = "DISAGREE_EXPECTATION"
    DISAGREE_SYSTEM = "DISAGREE_SYSTEM"
    NEEDS_MORE_EVIDENCE = "NEEDS_MORE_EVIDENCE"


class DisagreementDisposition(str, Enum):
    NONE = "NONE"
    OPEN_FINDING = "OPEN_FINDING"
    DATASET_CHANGE_PROPOSAL = "DATASET_CHANGE_PROPOSAL"
    WITHHELD_PENDING_EVIDENCE = "WITHHELD_PENDING_EVIDENCE"


class ScoreStatus(str, Enum):
    MEASURED = "MEASURED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    BLOCKED = "BLOCKED"


class MetricId(str, Enum):
    """Every metric declares a numerator, a denominator and a population."""

    # truth and evidence (PLAN.md §9.1)
    NUMERICAL_EXACT_MATCH_RATE = "numerical_exact_match_rate"
    UNSUPPORTED_NUMERICAL_CLAIM_RATE = "unsupported_numerical_claim_rate"
    CITATION_RESOLUTION_ACCURACY = "citation_resolution_accuracy"
    CITATION_SUPPORT_ACCURACY = "citation_support_accuracy"
    EPISTEMIC_STATUS_CORRECTNESS = "epistemic_status_correctness"
    LAYER_CORRECTNESS = "layer_correctness"
    HISTORICAL_GENERATION_CORRECTNESS = "historical_generation_correctness"
    SETUP_GATING_CORRECTNESS = "setup_gating_correctness"
    FRESHNESS_CORRECTNESS = "freshness_correctness"
    # security (§9.2)
    PROTECTED_EXPOSURE_VIOLATION_RATE = "protected_exposure_violation_rate"
    INJECTION_ATTACK_SUCCESS_RATE = "injection_attack_success_rate"
    ENTITLEMENT_BYPASS_RATE = "entitlement_bypass_rate"
    CORPUS_EXTRACTION_LEAKAGE_RATE = "corpus_extraction_leakage_rate"
    # usefulness (§9.3)
    VALID_ANSWER_COMPLETION_RATE = "valid_answer_completion_rate"
    CORRECT_REFUSAL_RATE = "correct_refusal_rate"
    FALSE_REFUSAL_RATE = "false_refusal_rate"
    BEGINNER_EXPLANATION_COMPLETENESS = "beginner_explanation_completeness"
    OPERATOR_FIELD_COMPLETENESS = "operator_field_completeness"
    RESEARCHER_METADATA_COMPLETENESS = "researcher_metadata_completeness"
    HUMAN_REVIEW_AGREEMENT = "human_review_agreement"


class FindingCode(str, Enum):
    """Finding classes used by drivers (ACCEPTANCE.md §3)."""

    UNSUPPORTED_NUMBER = "UNSUPPORTED_NUMBER"
    NUMBER_MISMATCH = "NUMBER_MISMATCH"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    METRIC_LAUNDERED = "METRIC_LAUNDERED"
    EVIDENCE_CLASS_LAUNDERED = "EVIDENCE_CLASS_LAUNDERED"
    STATISTIC_INCOMPLETE = "STATISTIC_INCOMPLETE"
    CITATION_MISSING = "CITATION_MISSING"
    CITATION_UNRESOLVED = "CITATION_UNRESOLVED"
    LAYER_LAUNDERED = "LAYER_LAUNDERED"
    LAYER_AUTHORITY = "LAYER_AUTHORITY"
    SETUP_GATE_WRONG = "SETUP_GATE_WRONG"
    ADVICE_EMITTED = "ADVICE_EMITTED"
    STATUS_LAUNDERED = "STATUS_LAUNDERED"
    GENERATION_LAUNDERED = "GENERATION_LAUNDERED"
    GENERATION_SUBSTITUTED = "GENERATION_SUBSTITUTED"
    STALE_AS_LIVE = "STALE_AS_LIVE"
    FRESHNESS_MISSING = "FRESHNESS_MISSING"
    LEAK_INTERNAL = "LEAK_INTERNAL"
    LEAK_CORPUS = "LEAK_CORPUS"
    LEAK_ENUMERATION = "LEAK_ENUMERATION"
    LEAK_SYSTEM = "LEAK_SYSTEM"
    UNTRUSTED_INSTRUCTION = "UNTRUSTED_INSTRUCTION"
    FALSE_REFUSAL = "FALSE_REFUSAL"
    LIMITATION_DROPPED = "LIMITATION_DROPPED"
    FIELD_INCOMPLETE = "FIELD_INCOMPLETE"
    PROTECTED_EXPOSURE = "PROTECTED_EXPOSURE"
    ENTITLEMENT_BYPASS = "ENTITLEMENT_BYPASS"
    INJECTION_EXPOSED = "INJECTION_EXPOSED"
    REVIEW_MISSING = "REVIEW_MISSING"
    HUMAN_DISAGREEMENT = "HUMAN_DISAGREEMENT"
    METADATA_NOTE = "METADATA_NOTE"


class GateVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    OPEN = "OPEN"
