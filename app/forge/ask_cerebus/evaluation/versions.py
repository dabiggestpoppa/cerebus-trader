"""Version constants for Book IV / Bloc IV.6 evaluation.

Every consumer refuses an unknown version rather than coercing it to a known
one (R15). The upstream pins are git blob ids, so ``git hash-object`` on a
checkout reproduces them exactly (see ``regression.verify_upstream_pins``).
"""

from __future__ import annotations

import re

#: Overall evaluation contract (R1).
ASK_EVALUATION_CONTRACT_V1 = "ASK_EVALUATION_CONTRACT_V1"

#: Independently versioned sub-contracts (R1, PLAN.md §4.4).
EVALUATION_DATASET_V1 = "ASK_EVALUATION_DATASET_V1"
CASE_SCHEMA_V1 = "ASK_EVALUATION_CASE_SCHEMA_V1"
ORACLE_V1 = "ASK_EVALUATION_ORACLE_V1"
SCORING_V1 = "ASK_EVALUATION_SCORING_V1"
REPORT_V1 = "ASK_EVALUATION_REPORT_V1"

SUPPORTED_DATASET_VERSIONS = (EVALUATION_DATASET_V1,)
SUPPORTED_CASE_SCHEMA_VERSIONS = (CASE_SCHEMA_V1,)

CASE_ID_PREFIX = "EV-"
CASE_ID_PATTERN = re.compile(r"^EV-(\d{3})$")
CASE_COUNT = 120
REQUIREMENT_COUNT = 102
DRIVER_COUNT = 112

#: Frozen answer refusal vocabulary, highest precedence first (R45, PLAN §1.5).
REFUSAL_CODES = (
    "ACCESS_NOT_ENTITLED",
    "AMBIGUOUS_SCOPE",
    "MODEL_VERSION_UNAVAILABLE",
    "CURRENT_DATA_UNAVAILABLE",
    "SETUP_NOT_ENCODED",
    "INSUFFICIENT_EVIDENCE",
)

#: Frozen depth vocabulary. ``Depth`` in IV.1 is the authority; the evaluator
#: keeps the same three strings so the schema never imports the system under
#: test.
DEPTHS = ("BEGINNER", "OPERATOR", "RESEARCHER")

#: Frozen eligibility vocabulary in precedence order (R26).
ELIGIBILITY_VALUES = ("BLOCKED", "UNRESOLVED", "WATCH", "ELIGIBLE")

#: Frozen injection stopping boundaries (R60).
INJECTION_BOUNDARIES = (
    "IV2_EXCLUDED",
    "IV3_CONTAINED",
    "IV4_DRAFTED",
    "IV5_REJECTED",
    "EXPOSED",
)

#: Ten pinned upstream blobs (R14, x006).
UPSTREAM_PINS = {
    "implementation/forge/book_iv/bloc_iv_5/ACCEPTANCE.md": "cd9edbeb834bb66f1e62643a3c25ef8fcd5acdac",
    "planning/forge/books/BOOK_IV_ASK_CEREBUS_PLAN_V1.md": "f5c201431530ed2200cfbe1cd9959c9e7386aca6",
    "app/forge/ask_cerebus/interpreter/plan.py": "f898665cb804af0fff5cd7ebe6dd36b721d5a421",
    "app/forge/ask_cerebus/retrieval/service.py": "cdbe615ffd18dd0fa4df096d27259a405ac98964",
    "app/forge/ask_cerebus/context/service.py": "74d66d9d33f0f90171ac0eca51e6023cdefbaac2",
    "app/forge/ask_cerebus/llm_gateway/draft.py": "a7c70c61db07136f169df2012380f956252baf35",
    "app/forge/ask_cerebus/answer/service.py": "dd6e3792b169c2b1db59cc107e580582bef31155",
    "app/forge/ask_cerebus/answer/versions.py": "28d7d9e08e247b0fdf9f437afbe058afd2eb5863",
    "app/forge/service/routes.py": "e83fa101f97b7f99a1ee9894d27f4672f0efbfda",
    "app/forge/policy.py": "11e60ea2a19eac33702b14212d8bc3fef28d0470",
}

#: Migration versions that must exist and never grow in this bloc (x010).
MIGRATION_VERSIONS = (1, 2, 3, 4)

#: Fixture directory, relative to the repository root.
FIXTURE_DIRECTORY = "implementation/forge/book_iv/bloc_iv_6/fixtures"


def known_dataset_version(version: str) -> bool:
    return version in SUPPORTED_DATASET_VERSIONS


def known_case_schema_version(version: str) -> bool:
    return version in SUPPORTED_CASE_SCHEMA_VERSIONS
