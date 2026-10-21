"""Model registry / dispatch resolution (Ch III.3.8).

Explicit ``(model_id, model_version)`` resolution for the seven launch
families plus the historical JPY DT generation recorded by the frozen
III.2 coordinate registry.  Resolution is exact-match only:

* unknown id or unknown version ⇒ ``MODEL_VERSION_UNAVAILABLE`` — fail
  closed, no partial output, no fallback;
* there is **no** ``latest()`` API, no default version parameter and no
  implicit upgrade anywhere in this package;
* retired/historical generations stay registered, so a pinned
  historical request resolves to *its own* registered entry — it is
  never silently answered by a later generation.

Each entry binds the runtime version, declared layer, market scope
(cross-asset family ⇒ empty scope, calibration stays instrument-bound),
the exact III.2 calibration bindings and coordinate-set keys of the
family (PLAN.md §5.2), its canonical source refs, and whether the
family is stateful (prior-state aware) or clock-bound.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from app.forge.measurements import CalibrationKey

from .contract import Layer
from .errors import ModelVersionUnavailableError
from .versions import MODEL_RUNTIME_VERSION

__all__ = [
    "MODEL_REGISTRY",
    "ModelKey",
    "RegistryEntry",
    "resolve",
]


@dataclass(frozen=True)
class ModelKey:
    """The exact dispatch key: model id + explicit version."""

    model_id: str
    model_version: str

    def __post_init__(self) -> None:
        if not self.model_id or not self.model_version:
            raise ValueError("a model key requires an id and an explicit version")

    def __str__(self) -> str:
        return f"{self.model_id}@{self.model_version}"


@dataclass(frozen=True)
class RegistryEntry:
    """One registered model generation."""

    model_key: ModelKey
    family: str
    runtime_version: str
    layer: Layer
    market_scope: frozenset[str]
    calibration_bindings: tuple[CalibrationKey, ...]
    coordinate_set_keys: tuple[tuple[str, str], ...]
    canonical_source_refs: tuple[str, ...]
    stateful: bool
    clock_bound: bool

    def __post_init__(self) -> None:
        if not self.family:
            raise ValueError("a registry entry declares its family")
        if self.runtime_version != MODEL_RUNTIME_VERSION:
            raise ValueError(
                f"every entry is pinned to {MODEL_RUNTIME_VERSION}; "
                f"got {self.runtime_version!r}"
            )
        if not isinstance(self.layer, Layer):
            raise ValueError("an entry declares a bounded layer")
        if not isinstance(self.market_scope, frozenset):
            raise ValueError("market_scope is an immutable frozenset")
        for item in self.market_scope:
            if not isinstance(item, str) or not item:
                raise ValueError("market_scope holds instrument ids")
        for key in self.calibration_bindings:
            if not isinstance(key, CalibrationKey):
                raise ValueError("calibration bindings are III.2 CalibrationKeys")
        for pair in self.coordinate_set_keys:
            if not (isinstance(pair, tuple) and len(pair) == 2 and all(pair)):
                raise ValueError("coordinate set keys are (model_id, version) pairs")
        if not self.canonical_source_refs:
            raise ValueError("an entry cites at least its canonical model card")
        if not isinstance(self.stateful, bool) or not isinstance(self.clock_bound, bool):
            raise ValueError("stateful/clock_bound are booleans")


def _key(model_id: str, model_version: str) -> ModelKey:
    return ModelKey(model_id=model_id, model_version=model_version)


def _binding(
    model_id: str, model_version: str, calibration_id: str, calibration_version: str
) -> CalibrationKey:
    return CalibrationKey(
        model_id=model_id,
        model_version=model_version,
        calibration_id=calibration_id,
        calibration_version=calibration_version,
    )


# --- canonical source refs (read-only citations) --------------------------

_CARD_EUR_DAILY = "corpus/canonical/models/EUR_DAILY_NEWS_REKEY_MODEL_CARD_V1.md"
_CARD_EUR_WEEKLY = "corpus/canonical/models/EUR_WEEKLY_ENGINE_MODEL_CARD_V1.md"
_CARD_EUR_HO = "corpus/canonical/models/EUR_HIGHER_ORDER_MODEL_CARD_V1.md"
_CARD_XAU = "corpus/canonical/models/XAU_GAME_L1_L2_L3_MODEL_CARD_V1.md"
_CARD_BTC = "corpus/canonical/models/BTC_DAILY_WEEKLY_MONTHLY_TRACKER_MODEL_CARD_V1.md"
_CARD_FIB = "corpus/canonical/models/FIB_RANGE_BIRTH_MODEL_CARD_V1.md"
_CARD_JPY = "corpus/canonical/models/JPY_CARRY_GAME_MODEL_CARD_V1.md"
_EV_EUR_TIER = "corpus/canonical/evidence/EUR_DAILY_PHASE1_CALIBRATION_EVIDENCE_V1.md"
_EV_EUR_WEEKLY = "corpus/canonical/evidence/EUR_WEEKLY_TIER_RANGE_EVIDENCE_V1.md"

_JPY_PAIRS = frozenset({"USDJPY", "AUDJPY", "EURJPY"})


# --- the seven launch families --------------------------------------------

EUR_DAILY_KEY = _key("EUR.DAILY.NEWS_REKEY.V1", "PHASE1")
EUR_WEEKLY_KEY = _key("EUR.WEEKLY.V1_1", "V1_1")
EUR_HIGHER_ORDER_KEY = _key("EUR.HIGHER_ORDER.V1", "V1")
XAU_KEY = _key("XAU.GAME.L1_L2_L3.V1", "V1")
BTC_TRACKER_KEY = _key("BTC.TRACKER.DWM.V1", "V1")
FIB_KEY = _key("CROSSASSET.FIB.RANGE_BIRTH.V1", "R15")
JPY_KEY = _key("JPY.CARRY_GAME.L1_L3.V1", "V1")
#: The historical DT geometry generation of the JPY model, recorded by
#: the frozen III.2 coordinate registry and fixture as a model version.
#: Registered so a pinned historical request resolves to its own entry;
#: no DT runtime is authorized by the frozen III.3 chapters, so its
#: dispatch fails closed rather than substituting the current rules.
JPY_DT_HISTORICAL_KEY = _key("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM")


_ENTRIES: tuple[RegistryEntry, ...] = (
    RegistryEntry(
        model_key=EUR_DAILY_KEY,
        family="EUR_DAILY",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.L1,
        market_scope=frozenset({"EURUSD"}),
        calibration_bindings=(
            _binding("EUR.DAILY.NEWS_REKEY.V1", "PHASE1", "EUR_DAILY_PHASE1_TIERS", "V1"),
        ),
        coordinate_set_keys=(("EUR.DAILY.NEWS_REKEY.V1", "PHASE1"),),
        canonical_source_refs=(_CARD_EUR_DAILY, _EV_EUR_TIER),
        stateful=True,
        clock_bound=True,
    ),
    RegistryEntry(
        model_key=EUR_WEEKLY_KEY,
        family="EUR_WEEKLY",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.L2,
        market_scope=frozenset({"EURUSD"}),
        calibration_bindings=(
            _binding("EUR.WEEKLY.V1_1", "V1_1", "EUR_WEEKLY_TIER_RANGE", "V1"),
        ),
        coordinate_set_keys=(),
        canonical_source_refs=(_CARD_EUR_WEEKLY, _EV_EUR_WEEKLY),
        stateful=True,
        clock_bound=False,
    ),
    RegistryEntry(
        model_key=EUR_HIGHER_ORDER_KEY,
        family="EUR_HIGHER_ORDER",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.L3,
        market_scope=frozenset({"EURUSD"}),
        calibration_bindings=(),
        coordinate_set_keys=(),
        canonical_source_refs=(_CARD_EUR_HO,),
        stateful=True,
        clock_bound=False,
    ),
    RegistryEntry(
        model_key=XAU_KEY,
        family="XAU",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.CROSS_LAYER,
        market_scope=frozenset({"XAUUSD"}),
        calibration_bindings=(
            _binding("XAU.GAME.L1_L2_L3.V1", "V1", "XAU_SPATIAL_BANDS", "V1"),
        ),
        coordinate_set_keys=(("XAU.GAME.L1_L2_L3.V1", "V1"),),
        canonical_source_refs=(_CARD_XAU,),
        stateful=True,
        clock_bound=False,
    ),
    RegistryEntry(
        model_key=BTC_TRACKER_KEY,
        family="BTC_TRACKER",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.CROSS_LAYER,
        market_scope=frozenset({"BTCUSD"}),
        calibration_bindings=(
            _binding("BTC.TRACKER.DWM.V1", "V1", "BTC_TRACKER_DWM_TIERS", "V1"),
        ),
        coordinate_set_keys=(),
        canonical_source_refs=(_CARD_BTC,),
        stateful=True,
        clock_bound=False,
    ),
    RegistryEntry(
        model_key=FIB_KEY,
        family="FIB_RANGE_BIRTH",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.CROSS_LAYER,
        market_scope=frozenset(),  # cross-asset by design; calibration stays local
        calibration_bindings=(),
        coordinate_set_keys=(("CROSSASSET.FIB.RANGE_BIRTH.V1", "R15"),),
        canonical_source_refs=(_CARD_FIB,),
        stateful=True,
        clock_bound=False,
    ),
    RegistryEntry(
        model_key=JPY_KEY,
        family="JPY_CARRY",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.CROSS_LAYER,
        market_scope=_JPY_PAIRS,
        calibration_bindings=(),
        coordinate_set_keys=(("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM"),),
        canonical_source_refs=(_CARD_JPY,),
        stateful=False,  # stateless per call; a prior state is optional
        clock_bound=False,
    ),
    # Historical generation: registered, resolvable, never dispatched.
    RegistryEntry(
        model_key=JPY_DT_HISTORICAL_KEY,
        family="JPY_DT_HISTORICAL",
        runtime_version=MODEL_RUNTIME_VERSION,
        layer=Layer.CROSS_LAYER,
        market_scope=_JPY_PAIRS,
        calibration_bindings=(),
        coordinate_set_keys=(("JPY.CARRY_GAME.L1_L3.V1", "DT_12_4PM"),),
        canonical_source_refs=(_CARD_JPY,),
        stateful=False,
        clock_bound=False,
    ),
)


#: The immutable registry: exact ``(model_id, model_version)`` keys only.
MODEL_REGISTRY: Mapping[ModelKey, RegistryEntry] = MappingProxyType(
    {entry.model_key: entry for entry in _ENTRIES}
)


def resolve(model_id: str, model_version: str) -> RegistryEntry:
    """Resolve one exact model key.  Unknown ⇒ fail closed.

    There is never a fallback to another version, another generation or
    a "latest" default: a request that is not registered raises
    ``MODEL_VERSION_UNAVAILABLE`` and produces no partial output.
    """
    if not isinstance(model_id, str) or not model_id:
        raise ModelVersionUnavailableError("a model_id is required")
    if not isinstance(model_version, str) or not model_version:
        raise ModelVersionUnavailableError(
            f"an explicit model version is required for {model_id!r}"
        )
    entry = MODEL_REGISTRY.get(ModelKey(model_id, model_version))
    if entry is None:
        known_versions = sorted(
            key.model_version for key in MODEL_REGISTRY if key.model_id == model_id
        )
        if known_versions:
            raise ModelVersionUnavailableError(
                f"model version {model_version!r} is not registered for "
                f"{model_id!r}; registered versions: {', '.join(known_versions)}"
            )
        raise ModelVersionUnavailableError(
            f"model id {model_id!r} is not registered"
        )
    return entry
