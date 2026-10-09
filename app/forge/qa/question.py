"""I.5 deterministic question classification (PLAN §3).

Pure token/grammar logic — no model, no randomness. Reuses I.4 query
tokenization and frozen Ontology Crosswalk alias expansion; expansion adds
tokens only and never rewrites status, identity or evidence class.

Class precedence (frozen): ACTIONABLE > EMPIRICAL > COMPARATIVE >
DESCRIPTIVE (safe fallback: descriptive can never assert a number).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.forge.retrieval import RetrievalQuery, normalize_query

CANONICAL_ID_RE = re.compile(r"\b(?:MOD|CL|EV|SET)\.[A-Z0-9][A-Z0-9_.]*\b")

VERSION_TOKEN_RE = re.compile(r"\bV\d+(?:[._]\d+)*\b")
LAYER_TOKEN_RE = re.compile(r"\bL[123]\b")
# P-numbered tokens (P90 …) are indicator-lineage names, never numerical
# claims (frozen Q6: P90 stays lineage vocabulary, never a statistic).
P_TOKEN_RE = re.compile(r"\bP\d+\b")
DIGIT_RE = re.compile(r"\d")

ACTIONABLE_WORDS = frozenset(
    {
        "entry",
        "enter",
        "trigger",
        "target",
        "targets",
        "no-go",
        "nogo",
        "setup",
        "setups",
        "should",
        "signal",
        "signals",
        "buy",
        "sell",
        "stop",
        "trade",
        "trading",
        "position",
        "order",
        "automation",
        "automate",
        "automated",
        "parity",
        "activate",
        "activation",
    }
)

EMPIRICAL_WORDS = frozenset(
    {
        "accuracy",
        "correlation",
        "probability",
        "win",
        "wins",
        "rate",
        "rates",
        "percent",
        "percentage",
        "backtest",
        "backtested",
        "auc",
        "often",
        "frequency",
        "multiplier",
        "multipliers",
        "statistic",
        "statistics",
        "performance",
        "drawdown",
        "sample",
        "samples",
        "measured",
        "measure",
        "finding",
        "findings",
        "evidence",
        "claim",
        "claims",
        "validated",
        "validation",
    }
)

COMPARATIVE_WORDS = frozenset(
    {
        "vs",
        "versus",
        "verses",
        "compare",
        "comparison",
        "difference",
        "different",
        "distinguish",
        "distinct",
        "separate",
        "collapse",
        "same",
        "equal",
    }
)

MARKETS = ("EURUSD", "XAUUSD", "BTCUSD", "USDJPY", "AUDJPY", "EURJPY")

_MARKET_ALIASES = {
    "GOLD": "XAUUSD",
    "BITCOIN": "BTCUSD",
}

_FAMILY_BY_MARKET = {
    "EURUSD": "EUR",
    "XAUUSD": "XAU",
    "BTCUSD": "BTC",
    "USDJPY": "JPY",
    "AUDJPY": "JPY",
    "EURJPY": "JPY",
}

FAMILIES = ("EUR", "XAU", "BTC", "JPY")


class QuestionClass(str, Enum):
    DESCRIPTIVE = "DESCRIPTIVE"
    EMPIRICAL = "EMPIRICAL"
    ACTIONABLE = "ACTIONABLE"
    COMPARATIVE = "COMPARATIVE"


@dataclass(frozen=True)
class ClassifiedQuestion:
    text: str
    question_class: QuestionClass
    canonical_id: str | None
    canonical_ids: tuple[str, ...]
    market: str | None
    model_family: str | None
    empirical_signal: bool
    tokens: tuple[str, ...]


def _scope(text: str) -> tuple[str | None, str | None]:
    """Exact market else family scope from raw text (frozen token table)."""
    compact = re.sub(r"[^A-Za-z0-9]", "", text).upper()
    for market in MARKETS:
        if market in compact:
            return market, _FAMILY_BY_MARKET[market]
    for alias, market in sorted(_MARKET_ALIASES.items()):
        if alias in compact:
            return market, _FAMILY_BY_MARKET[market]
    normalized = normalize_query(RetrievalQuery(text=text))
    for token in sorted(normalized.all_tokens):
        if token.upper() in FAMILIES:
            return None, token.upper()
    return None, None


def classify_question(text: str) -> ClassifiedQuestion:
    """Frozen classification procedure (PLAN §3), applied in order."""
    raw = text or ""
    id_matches = tuple(CANONICAL_ID_RE.findall(raw))
    canonical_ids = id_matches[:3]
    canonical_id = canonical_ids[0] if canonical_ids else None

    normalized = normalize_query(RetrievalQuery(text=raw))
    tokens = tuple(sorted(normalized.all_tokens))

    market, family = _scope(raw)

    lowered = set(tokens)
    # empirical signal: empirical vocabulary, or a digit that is not part of
    # a version/layer/lineage/canonical-id token ("V1.1", "L3", "P90",
    # "CL.FIB.R11…" are names, never numerical claims).
    empirical_words = EMPIRICAL_WORDS & lowered
    stripped = CANONICAL_ID_RE.sub(" ", raw)
    stripped = VERSION_TOKEN_RE.sub(" ", stripped)
    stripped = LAYER_TOKEN_RE.sub(" ", stripped)
    stripped = P_TOKEN_RE.sub(" ", stripped)
    empirical_signal = bool(empirical_words) or bool(DIGIT_RE.search(stripped))

    if ACTIONABLE_WORDS & lowered:
        question_class = QuestionClass.ACTIONABLE
    elif empirical_signal:
        question_class = QuestionClass.EMPIRICAL
    elif COMPARATIVE_WORDS & lowered:
        question_class = QuestionClass.COMPARATIVE
    else:
        question_class = QuestionClass.DESCRIPTIVE

    return ClassifiedQuestion(
        text=raw,
        question_class=question_class,
        canonical_id=canonical_id,
        canonical_ids=canonical_ids,
        market=market,
        model_family=family,
        empirical_signal=empirical_signal,
        tokens=tokens,
    )
