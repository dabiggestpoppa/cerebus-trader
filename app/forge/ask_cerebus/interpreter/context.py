"""Authenticated, already-authorized interpreter context.

Book II decides the ceiling; IV.1 only receives it. The interpreter has no
principal store, no entitlement lookup and no policy engine.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.forge.ask_cerebus.interpreter.enums import Depth
from app.forge.ask_cerebus.interpreter.versions import (
    ASK_QUERY_CONTRACT_V1,
    SUPPORTED_QUERY_CONTRACT_VERSIONS,
)

MAX_SCOPE_LENGTH = 128


@dataclass(frozen=True)
class InterpreterContext:
    principal_scope: str
    max_authorized_depth: Depth = Depth.RESEARCHER
    policy_fingerprint: str = ""
    query_contract_version: str = ASK_QUERY_CONTRACT_V1

    def __post_init__(self) -> None:
        if not isinstance(self.principal_scope, str) or not self.principal_scope:
            raise ValueError("principal_scope must be a non-empty string")
        if len(self.principal_scope) > MAX_SCOPE_LENGTH:
            raise ValueError("principal_scope is too long")
        if any(ch.isspace() for ch in self.principal_scope):
            raise ValueError("principal_scope must be an opaque bounded token")
        if not isinstance(self.max_authorized_depth, Depth):
            raise ValueError("max_authorized_depth must be a Depth")
        if self.query_contract_version not in SUPPORTED_QUERY_CONTRACT_VERSIONS:
            raise ValueError("unsupported query contract version")
        if not isinstance(self.policy_fingerprint, str):
            raise ValueError("policy_fingerprint must be a string")


__all__ = ["InterpreterContext", "MAX_SCOPE_LENGTH"]
