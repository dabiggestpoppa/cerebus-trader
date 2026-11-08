"""Book IV / Bloc IV.4 — deterministic LLM gateway (ASK_GATEWAY_CONTRACT_V1)."""

from __future__ import annotations

from app.forge.ask_cerebus.llm_gateway.budget import GatewayBudget
from app.forge.ask_cerebus.llm_gateway.draft import (
    GatewayDraft,
    GatewayRefusal,
    draft_schema,
    parse_draft,
)
from app.forge.ask_cerebus.llm_gateway.enums import (
    AttemptOutcome,
    CostBasis,
    DraftStatus,
    GatewayOutcome,
    GatewayRefusalCode,
    RouteTask,
)
from app.forge.ask_cerebus.llm_gateway.fake import FakeScript, GatewayFakeLLM
from app.forge.ask_cerebus.llm_gateway.policy import (
    ModelCandidate,
    ModelRoute,
    RoutingPolicy,
)
from app.forge.ask_cerebus.llm_gateway.prompts import prompt_for_depth
from app.forge.ask_cerebus.llm_gateway.service import GatewayService
from app.forge.ask_cerebus.llm_gateway.versions import (
    ASK_GATEWAY_CONTRACT_V1,
    ASK_GATEWAY_DRAFT_SCHEMA_V1,
    ASK_MODEL_ROUTING_V1,
    CANDIDATE_MATRIX_STATUS,
    RETENTION_POLICY_STATUS,
    TOKENIZER_STATUS,
)

__all__ = [
    "ASK_GATEWAY_CONTRACT_V1",
    "ASK_GATEWAY_DRAFT_SCHEMA_V1",
    "ASK_MODEL_ROUTING_V1",
    "CANDIDATE_MATRIX_STATUS",
    "RETENTION_POLICY_STATUS",
    "TOKENIZER_STATUS",
    "GatewayBudget",
    "GatewayDraft",
    "GatewayRefusal",
    "GatewayService",
    "GatewayFakeLLM",
    "FakeScript",
    "parse_draft",
    "draft_schema",
    "GatewayOutcome",
    "GatewayRefusalCode",
    "DraftStatus",
    "RouteTask",
    "AttemptOutcome",
    "CostBasis",
    "ModelCandidate",
    "ModelRoute",
    "RoutingPolicy",
    "prompt_for_depth",
]
