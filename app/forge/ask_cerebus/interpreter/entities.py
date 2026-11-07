"""Deterministic canonical entity resolution.

Only exact, source-backed vocabulary resolves. There is no fuzzy matching,
no embedding similarity and no invented identifier. Unknown phrases stay
unresolved and are reported by the ambiguity classifier.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.forge.model_runtime.contract import Layer
from app.forge.retrieval.aliases import HISTORICAL_ALIASES

from .enums import EntityKind


@dataclass(frozen=True)
class EntityRef:
    kind: EntityKind
    text: str
    canonical_id: str | None = None
    generation: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EntityKind):
            raise ValueError("kind must be an EntityKind")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("entity text must be non-empty")
        if self.canonical_id is not None:
            if not isinstance(self.canonical_id, str) or not self.canonical_id:
                raise ValueError("canonical_id must be a non-empty string")
            if any(ch.isspace() for ch in self.canonical_id):
                raise ValueError("canonical_id must not contain whitespace")
        if self.generation is not None and (
            not isinstance(self.generation, str) or not self.generation
        ):
            raise ValueError("generation must be a non-empty string")

    def payload(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "text": self.text,
            "canonical_id": self.canonical_id,
            "generation": self.generation,
        }


def _pattern(phrase: str) -> re.Pattern[str]:
    return re.compile(
        r"(?<![\w])" + re.escape(phrase) + r"(?![\w])", re.IGNORECASE
    )


_INSTRUMENTS: tuple[tuple[str, str], ...] = (
    ("eurusd", "EURUSD"),
    ("eurjpy", "EURJPY"),
    ("usdjpy", "USDJPY"),
    ("audjpy", "AUDJPY"),
    ("btcusd", "BTCUSD"),
    ("xauusd", "XAUUSD"),
    ("eur", "EURUSD"),
    ("xau", "XAUUSD"),
    ("gold", "XAUUSD"),
    ("btc", "BTCUSD"),
    ("bitcoin", "BTCUSD"),
)

_MODELS: tuple[tuple[str, str], ...] = (
    ("gold game", "XAU.GAME"),
    ("xau game", "XAU.GAME"),
    ("btc game", "BTC.GAME"),
    ("btc tracker", "BTC.TRACKER"),
    ("btc daily", "BTC.TRACKER"),
    ("btc weekly", "BTC.TRACKER"),
    ("btc monthly", "BTC.TRACKER"),
    ("eur daily", "EUR.DAILY.REKEY"),
    ("eur rekey", "EUR.DAILY.REKEY"),
    ("daily rekey", "EUR.DAILY.REKEY"),
    ("eur weekly", "EUR.WEEKLY"),
    ("weekly state", "EUR.WEEKLY"),
    ("eur higher order", "EUR.HIGHER_ORDER"),
    ("higher order", "EUR.HIGHER_ORDER"),
    ("jpy carry", "JPY.CARRY"),
    ("jpy", "JPY.CARRY"),
    ("p90p", "P90P"),
    ("p90", "P90"),
    ("symmetry trap", "ST"),
    ("st", "ST"),
    ("base80", "BASE80"),
    ("range birth", "FIB.RANGE_BIRTH"),
    ("fib", "FIB.RANGE_BIRTH"),
    ("r15", "FIB.RANGE_BIRTH"),
    ("markov", "MARKOV"),
    ("phi", "PHI"),
    ("oil", "OIL"),
)

_INSTRUMENT_IDS = frozenset(canonical for _, canonical in _INSTRUMENTS)
_MODEL_IDS = frozenset(canonical for _, canonical in _MODELS)

_SESSIONS: tuple[tuple[str, str], ...] = (
    ("daily", "D1"),
    ("d1", "D1"),
    ("weekly", "W1"),
    ("w1", "W1"),
    ("monthly", "MN1"),
    ("mn1", "MN1"),
    ("hourly", "H1"),
    ("h1", "H1"),
    ("m5", "M5"),
    ("5m", "M5"),
    ("asian", "SESSION.ASIAN"),
    ("london", "SESSION.LONDON"),
    ("new york", "SESSION.NEW_YORK"),
)

_KNOWN_SETUP = re.compile(r"\bSET\.[A-Z0-9][A-Z0-9_.-]*", re.IGNORECASE)
_VERSION = re.compile(r"\bv(\d+)\b")

_INSTRUMENT_PATTERNS = tuple((_pattern(phrase), canonical) for phrase, canonical in _INSTRUMENTS)
_MODEL_PATTERNS = tuple((_pattern(phrase), canonical) for phrase, canonical in _MODELS)
_SESSION_PATTERNS = tuple((_pattern(phrase), canonical) for phrase, canonical in _SESSIONS)
_TERM_PATTERNS = tuple((_pattern(entry.historical), entry.historical) for entry in HISTORICAL_ALIASES)


def _slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def _generation(model_id: str, text: str) -> str | None:
    version = _VERSION.search(text)
    if model_id == "P90":
        if version:
            return f"P90.v{version.group(1)}"
        return "P90.ORIGINAL" if _pattern("original").search(text) else "P90"
    if model_id == "P90P":
        return "P90P"
    if model_id == "ST":
        return "ST.MANUAL"
    if model_id == "BASE80":
        return "BASE80"
    if model_id == "MARKOV":
        return "MARKOV.LEGACY"
    if model_id == "FIB.RANGE_BIRTH":
        return "FIB.R15" if _pattern("r15").search(text) else "FIB"
    if model_id == "BTC.GAME":
        return "RESEARCH_ARTIFACT"
    if model_id == "XAU.GAME":
        return "XAU.GAME"
    return f"v{version.group(1)}" if version else None


def known_model_ids() -> tuple[str, ...]:
    return tuple(sorted(_MODEL_IDS))


def resolve_entities(text: str) -> tuple[EntityRef, ...]:
    """Resolve the fixed, source-backed vocabulary in a stable order."""

    found: list[EntityRef] = []
    seen: set[tuple[str, str]] = set()

    def add(entity: EntityRef) -> None:
        key = (entity.kind.value, entity.canonical_id or entity.text)
        if key in seen:
            return
        seen.add(key)
        found.append(entity)

    for pattern, canonical in _INSTRUMENT_PATTERNS:
        match = pattern.search(text)
        if match:
            add(EntityRef(EntityKind.INSTRUMENT, match.group(0), canonical))

    for pattern, canonical in _MODEL_PATTERNS:
        match = pattern.search(text)
        if match:
            add(
                EntityRef(
                    EntityKind.MODEL,
                    match.group(0),
                    canonical,
                    _generation(canonical, text),
                )
            )

    for pattern, historical in _TERM_PATTERNS:
        match = pattern.search(text)
        if match:
            add(
                EntityRef(
                    EntityKind.TERM,
                    match.group(0),
                    "TERM." + _slug(historical),
                    "HISTORICAL_ALIAS",
                )
            )

    layer_match = re.search(r"\bl([123])\b", text)
    if layer_match:
        add(EntityRef(EntityKind.LAYER, layer_match.group(0), "L" + layer_match.group(1)))
    elif _pattern("higher order").search(text):
        add(EntityRef(EntityKind.LAYER, "higher order", Layer.L3.value))

    for setup_match in _KNOWN_SETUP.finditer(text):
        value = setup_match.group(0).upper()
        add(EntityRef(EntityKind.SETUP, value, value))

    for pattern, canonical in _SESSION_PATTERNS:
        match = pattern.search(text)
        if match:
            add(EntityRef(EntityKind.SESSION, match.group(0), canonical))

    if _pattern("wednesday generation").search(text):
        add(EntityRef(EntityKind.GENERATION, "wednesday generation", "WEDNESDAY"))
    if _pattern("afternoon generation").search(text):
        add(EntityRef(EntityKind.GENERATION, "afternoon generation", "AFTERNOON"))

    return tuple(found)


def model_ids(entities: tuple[EntityRef, ...]) -> tuple[str, ...]:
    return tuple(
        entity.canonical_id
        for entity in entities
        if entity.kind is EntityKind.MODEL and entity.canonical_id
    )


def setup_ids(entities: tuple[EntityRef, ...]) -> tuple[str, ...]:
    return tuple(
        entity.canonical_id
        for entity in entities
        if entity.kind is EntityKind.SETUP and entity.canonical_id
    )


def market(entities: tuple[EntityRef, ...]) -> str | None:
    for entity in entities:
        if entity.kind is EntityKind.INSTRUMENT and entity.canonical_id:
            return entity.canonical_id
    return None


def layer(entities: tuple[EntityRef, ...]) -> Layer | None:
    for entity in entities:
        if entity.kind is EntityKind.LAYER and entity.canonical_id:
            try:
                return Layer(entity.canonical_id)
            except ValueError:
                return None
    return None


def term_ids(entities: tuple[EntityRef, ...]) -> tuple[str, ...]:
    return tuple(
        entity.canonical_id
        for entity in entities
        if entity.kind is EntityKind.TERM and entity.canonical_id
    )


def unknown_model_ids(text: str) -> tuple[str, ...]:
    """Explicit `MOD.*` identifiers that do not exist in the frozen family map."""

    unknown: list[str] = []
    for match in re.finditer(
        r"\bMOD\.[A-Z0-9][A-Z0-9_.-]*", text, re.IGNORECASE
    ):
        value = match.group(0).upper()
        if value not in _MODEL_IDS and value not in unknown:
            unknown.append(value)
    return tuple(unknown)


__all__ = [
    "EntityRef",
    "resolve_entities",
    "model_ids",
    "setup_ids",
    "market",
    "layer",
    "term_ids",
    "unknown_model_ids",
    "known_model_ids",
]
