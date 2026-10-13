"""Frozen data-quality vocabulary and per-model declaration policy (Ch III.1.7).

The eight flag values are frozen exactly: ``COMPLETE``, ``GAP``,
``DUPLICATE``, ``REVISED``, ``STALE``, ``NONFINAL``, ``OUTLIER_SOURCE``,
``UNSUPPORTED_CLOCK``.  No additions, no renames, no free-text payload:
flags are bounded enumerations and every derived outcome is one of the
factual outcome enums (``OK`` / ``DEGRADED`` / ``DATA_QUALITY_BLOCKED`` /
``NO_CALCULATION``).

Models declare per (model_id, model_version) which flags *block*
calculation and which merely *warn*; the declaration must cover every
defect flag (fail closed on undeclared combinations) and may never make
``COMPLETE`` blocking.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .errors import QualityVocabularyError


class QualityFlag(str, Enum):
    """The exact frozen quality-flag vocabulary (G1)."""

    COMPLETE = "COMPLETE"
    GAP = "GAP"
    DUPLICATE = "DUPLICATE"
    REVISED = "REVISED"
    STALE = "STALE"
    NONFINAL = "NONFINAL"
    OUTLIER_SOURCE = "OUTLIER_SOURCE"
    UNSUPPORTED_CLOCK = "UNSUPPORTED_CLOCK"


FROZEN_QUALITY_FLAGS: frozenset[QualityFlag] = frozenset(QualityFlag)

_DEFECT_FLAGS: frozenset[QualityFlag] = FROZEN_QUALITY_FLAGS - {QualityFlag.COMPLETE}


class DataOutcome(str, Enum):
    """Factual outcome vocabulary for quality evaluation (G3 / L1 / L2).

    Labels are enums with plain operational meaning — no rhetorical or
    deterministic-prospect language (cross-model invariant #18).
    """

    OK = "OK"
    DEGRADED = "DEGRADED"
    DATA_QUALITY_BLOCKED = "DATA_QUALITY_BLOCKED"
    NO_CALCULATION = "NO_CALCULATION"


def parse_quality_flag(raw: str) -> QualityFlag:
    """Parse a flag from the frozen vocabulary; unknown values are rejected."""
    try:
        return QualityFlag(raw)
    except ValueError:
        raise QualityVocabularyError(f"unknown quality flag {raw!r}") from None


def coerce_flags(values: Iterable[QualityFlag | str]) -> frozenset[QualityFlag]:
    """Coerce an iterable of flags, refusing anything outside the vocabulary."""
    flags: set[QualityFlag] = set()
    for value in values:
        if isinstance(value, QualityFlag):
            flags.add(value)
        elif isinstance(value, str):
            flags.add(parse_quality_flag(value))
        else:
            raise QualityVocabularyError(f"not a quality flag: {value!r}")
    return frozenset(flags)


def normalize_flags(values: Iterable[QualityFlag | str]) -> frozenset[QualityFlag]:
    """Flags with ``COMPLETE`` dropped whenever any defect flag is present."""
    flags = set(coerce_flags(values))
    defects = flags - {QualityFlag.COMPLETE}
    if defects:
        return frozenset(defects)
    return frozenset({QualityFlag.COMPLETE})


def with_flag(
    values: Iterable[QualityFlag | str], flag: QualityFlag
) -> frozenset[QualityFlag]:
    """Add one flag, keeping the COMPLETE/defect invariant."""
    flags = set(coerce_flags(values))
    flags.add(flag)
    return normalize_flags(flags)


@dataclass(frozen=True)
class QualityPolicy:
    """Per-model blocking-vs-warning declaration (G2).

    Every defect flag must be declared exactly once (block or warn);
    declarations that overlap, that omit a flag, or that mark ``COMPLETE``
    blocking are rejected at construction — evaluation can therefore never
    encounter an undeclared flag.
    """

    model_id: str
    model_version: str
    blocking: frozenset[QualityFlag]
    warning: frozenset[QualityFlag]

    def __post_init__(self) -> None:
        blocking = coerce_flags(self.blocking)
        warning = coerce_flags(self.warning)
        object.__setattr__(self, "blocking", blocking)
        object.__setattr__(self, "warning", warning)
        if QualityFlag.COMPLETE in blocking or QualityFlag.COMPLETE in warning:
            raise QualityVocabularyError("COMPLETE must not be declared block/warn")
        overlap = blocking & warning
        if overlap:
            raise QualityVocabularyError(
                f"flags declared twice: {sorted(f.value for f in overlap)}"
            )
        undeclared = _DEFECT_FLAGS - blocking - warning
        if undeclared:
            raise QualityVocabularyError(
                f"undeclared defect flags: {sorted(f.value for f in undeclared)}"
            )

    @classmethod
    def from_strings(
        cls,
        model_id: str,
        model_version: str,
        blocking: Iterable[str],
        warning: Iterable[str],
    ) -> "QualityPolicy":
        return cls(
            model_id=model_id,
            model_version=model_version,
            blocking=frozenset(coerce_flags(blocking)),
            warning=frozenset(coerce_flags(warning)),
        )

    def evaluate(self, flags: Iterable[QualityFlag | str]) -> DataOutcome:
        """Declaring policy applied to observed flags.

        Present blocking flag -> ``DATA_QUALITY_BLOCKED``; otherwise a
        present warning flag -> ``DEGRADED`` (disclosed, not silent);
        otherwise ``OK``.  ``COMPLETE`` carries no weight.
        """
        present = normalize_flags(flags) - {QualityFlag.COMPLETE}
        if present & self.blocking:
            return DataOutcome.DATA_QUALITY_BLOCKED
        if present & self.warning:
            return DataOutcome.DEGRADED
        return DataOutcome.OK
