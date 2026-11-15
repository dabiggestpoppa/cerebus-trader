"""Frozen versions for the Book V UI component contract.

The UI contract renders ``BookVInterfaceResponse`` (produced by the
presentation adapter) into HTML. It does not introduce
``ASK_ANSWER_CONTRACT_V2`` or a consolidated ``refusal_limitations``
field without separate authorization.
"""

BOOK_V_UI_CONTRACT_V1 = "BOOK_V_UI_CONTRACT_V1"
BOOK_V_UI_SCHEMA_V1 = "BOOK_V_UI_SCHEMA_V1"

__all__ = [
    "BOOK_V_UI_CONTRACT_V1",
    "BOOK_V_UI_SCHEMA_V1",
]
