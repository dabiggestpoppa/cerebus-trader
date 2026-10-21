"""Version identity for the Bloc III.3 CEREBUS model runtime.

``MODEL_RUNTIME_VERSION`` is the Book III final-record field the frozen
gate requires on every model output (PLAN.md §11, ACCEPTANCE.md L7).
Redefinition of any output contract requires a new runtime version —
never an in-place change (core law: downstream may consume, never
silently redefine).
"""

from __future__ import annotations

MODEL_RUNTIME_VERSION = "MODEL_RUNTIME_V1"

__all__ = ["MODEL_RUNTIME_VERSION"]
