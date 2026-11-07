"""Deterministic context budgeting for IV.3."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from typing import Protocol, runtime_checkable

from app.forge.ask_cerebus.context.enums import ContextSectionId, SECTION_RANK
from app.forge.ask_cerebus.context.schema import ContextItem
from app.forge.ask_cerebus.context.versions import (
    DEFAULT_MAX_UNITS,
    DEFAULT_SAFETY_RESERVE_UNITS,
    ESTIMATOR_VERSION,
    MAX_EXCERPT_CHARS,
    MAX_ITEMS_PER_SECTION,
)


@dataclass(frozen=True)
class ContextBudget:
    max_units: int = DEFAULT_MAX_UNITS
    reserve_units: int = DEFAULT_SAFETY_RESERVE_UNITS
    max_excerpt_chars: int = MAX_EXCERPT_CHARS
    max_items_per_section: int = MAX_ITEMS_PER_SECTION

    def __post_init__(self) -> None:
        if self.max_units <= 0 or self.reserve_units < 0:
            raise ValueError("budget must be positive")
        if self.max_units <= self.reserve_units:
            raise ValueError("max_units must exceed reserve_units")
        if self.max_items_per_section <= 0:
            raise ValueError("max_items_per_section must be positive")

    @property
    def available_units(self) -> int:
        return self.max_units - self.reserve_units


def estimate_item(item: ContextItem) -> int:
    control = json.dumps(
        item.control_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    text = item.text or ""
    return (
        math.ceil(len(control.encode("utf-8")) / 4)
        + math.ceil(len(text.encode("utf-8")) / 4)
        + 8
    )


def estimate_items(items: tuple[ContextItem, ...]) -> int:
    return sum(estimate_item(item) for item in items)


def estimate_section(items: tuple[ContextItem, ...]) -> int:
    return 16 + estimate_items(items) if items else 0


@runtime_checkable
class TokenizerPort(Protocol):
    """Replaceable estimator seam; this is not a provider tokenizer."""

    version: str

    def estimate_item(self, item: ContextItem) -> int: ...


class Utf8QuarterTokenizer:
    """Versioned deterministic estimator used by CONTEXT_CONTRACT_V1."""

    version = ESTIMATOR_VERSION

    def estimate_item(self, item: ContextItem) -> int:
        return estimate_item(item)


def with_token_units(item: ContextItem) -> ContextItem:
    return replace(item, token_units=estimate_item(item))


def _drop_order(item: ContextItem) -> tuple[int, str, str, str]:
    # Drop semantic first, then lineage, negative, setup, model, claims and
    # current. Mandatory items are never candidates.
    return (-item.priority, item.source_ref_type, item.source_ref_id, item.item_id)


def select_within_budget(
    grouped: dict[ContextSectionId, list[ContextItem]],
    budget: ContextBudget,
) -> tuple[
    dict[ContextSectionId, list[ContextItem]],
    list[tuple[ContextSectionId, ContextItem]],
    int,
]:
    """Return kept items, trimmed items and total mandatory units.

    Mandatory overflow is represented by ``mandatory_units > available`` so the
    service can return a bounded refusal rather than a partial context.
    """

    all_items = [item for items in grouped.values() for item in items]
    mandatory_units = sum(
        estimate_item(item) for item in all_items if item.mandatory
    )
    kept = {section: list(items) for section, items in grouped.items()}
    if mandatory_units > budget.available_units:
        return kept, [], mandatory_units

    # Trim by priority; stable ordering prevents nondeterministic output.
    candidates = sorted(
        [item for item in all_items if not item.mandatory],
        key=_drop_order,
    )
    trimmed: list[tuple[ContextSectionId, ContextItem]] = []
    used = sum(estimate_item(item) for items in kept.values() for item in items)
    counts = {section: len(items) for section, items in kept.items()}

    for item in candidates:
        section = _section_for_item(kept, item)
        if section is None:
            continue
        if used <= budget.available_units and counts[section] <= budget.max_items_per_section:
            continue
        kept[section] = [candidate for candidate in kept[section] if candidate is not item]
        counts[section] -= 1
        used -= estimate_item(item)
        trimmed.append((section, item))

    return kept, trimmed, mandatory_units


def _section_for_item(
    grouped: dict[ContextSectionId, list[ContextItem]], item: ContextItem
) -> ContextSectionId | None:
    for section, items in grouped.items():
        if any(candidate is item for candidate in items):
            return section
    return None


__all__ = [
    "ContextBudget",
    "TokenizerPort",
    "Utf8QuarterTokenizer",
    "estimate_item",
    "estimate_items",
    "estimate_section",
    "with_token_units",
    "select_within_budget",
]
