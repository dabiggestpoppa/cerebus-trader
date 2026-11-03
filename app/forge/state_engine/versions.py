"""Version identity for the Bloc III.4 state/path engine.

``STATE_ENGINE_VERSION`` is the Book III final-record field this Bloc
contributes (transition-layer identity).  Every snapshot and every
transition event is stamped with it, so a replay can never mix two
engine generations silently.  Redefinition of any III.4 contract
requires a new version — never an in-place change.
"""

from __future__ import annotations

STATE_ENGINE_VERSION = "STATE_ENGINE_V1"

__all__ = ["STATE_ENGINE_VERSION"]
