"""Actionability detection. Classification only, never a decision."""

from __future__ import annotations

import re

_ACTION = re.compile(
    r"\b(should\s+i|enter|entry|buy|sell|short|long|stop|stops|target|targets|"
    r"position|position\s+size|take\s+profit|stop\s+loss|trade|execute|play|hold|"
    r"safe\s+to\s+trade)\b"
)


def is_actionable(text: str) -> bool:
    return bool(_ACTION.search(text))


__all__ = ["is_actionable"]
