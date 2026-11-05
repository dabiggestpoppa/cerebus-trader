"""Typed, frozen request families. Clients select no authority."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Iterable, Mapping

from app.forge.intelligence_api.errors import RefusalError
from app.forge.model_runtime.contract import Layer

FORBIDDEN_REQUEST_KEYS = frozenset(
    {
        "verdict",
        "eligibility",
        "eligible",
        "exposure",
        "execution_class",
        "automation_permitted",
        "authorization",
        "authorized",
        "score",
        "confidence",
        "probability",
        "hit_rate",
        "expectancy",
        "order",
        "size",
        "position_size",
        "entry_price",
        "stop",
        "flatten",
        "average",
        "net_bias",
        "as_current",
        "force_current",
        "snapshot_id",
        "snapshot_hash",
        "principal",
        "user_id",
    }
)

VERSION_TOKENS = frozenset({"latest", "current", "newest", "*", "any"})


def _check_mapping(cls: type, mapping: Mapping[str, Any]) -> dict[str, Any]:
    allowed = {field.name for field in fields(cls)}
    unknown = set(mapping) - allowed
    forbidden = unknown & FORBIDDEN_REQUEST_KEYS
    if forbidden:
        raise RefusalError("MALFORMED_REQUEST", detail="forbidden_field")
    if unknown:
        raise RefusalError("MALFORMED_REQUEST", detail="unknown_field")
    return dict(mapping)


def _require(mapping: Mapping[str, Any], *names: str) -> None:
    missing = [name for name in names if mapping.get(name) in (None, "")]
    if missing:
        raise RefusalError("MALFORMED_REQUEST", detail="missing_field")


def _version(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if str(value).strip().lower() in VERSION_TOKENS:
        raise RefusalError("UNKNOWN_VERSION", detail="version_token")
    return value


def _immutable(value: Iterable[Any]) -> tuple[Any, ...]:
    return tuple(value)


@dataclass(frozen=True)
class SnapshotRequest:
    instrument_id: str
    model_id: str
    model_version: str
    layer: Layer
    as_of: str
    data_cutoff: str
    calculation_version: str
    clock_id: str | None = None
    session_id: str | None = None
    surface: str = "CURRENT"

    def __post_init__(self) -> None:
        _require(
            {
                "instrument_id": self.instrument_id,
                "model_id": self.model_id,
                "model_version": self.model_version,
                "as_of": self.as_of,
                "data_cutoff": self.data_cutoff,
                "calculation_version": self.calculation_version,
            },
            "instrument_id",
            "model_id",
            "model_version",
            "as_of",
            "data_cutoff",
            "calculation_version",
        )
        _version(self.model_version, "model_version")
        _version(self.calculation_version, "calculation_version")
        if not isinstance(self.layer, Layer):
            raise RefusalError("MALFORMED_REQUEST", detail="layer_required")
        if self.surface not in ("CURRENT", "OPERATOR", "RESEARCH"):
            raise RefusalError("MALFORMED_REQUEST", detail="surface_unknown")

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "SnapshotRequest":
        data = _check_mapping(cls, mapping)
        _require(data, "instrument_id", "model_id", "model_version", "layer", "as_of", "data_cutoff", "calculation_version")
        return cls(**data)


@dataclass(frozen=True)
class HistoricalRequest:
    instrument_id: str
    model_id: str
    model_version: str
    layer: Layer
    as_of: str
    data_cutoff: str
    calculation_version: str
    clock_id: str | None = None
    session_id: str | None = None
    retention_acknowledged: bool = False

    def __post_init__(self) -> None:
        _require(
            {
                "instrument_id": self.instrument_id,
                "model_id": self.model_id,
                "model_version": self.model_version,
                "as_of": self.as_of,
                "data_cutoff": self.data_cutoff,
                "calculation_version": self.calculation_version,
            },
            "instrument_id",
            "model_id",
            "model_version",
            "as_of",
            "data_cutoff",
            "calculation_version",
        )
        _version(self.model_version, "model_version")
        _version(self.calculation_version, "calculation_version")
        if not isinstance(self.layer, Layer):
            raise RefusalError("MALFORMED_REQUEST", detail="layer_required")

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "HistoricalRequest":
        data = _check_mapping(cls, mapping)
        _require(data, "instrument_id", "model_id", "model_version", "layer", "as_of", "data_cutoff", "calculation_version")
        return cls(**data)


@dataclass(frozen=True)
class InstrumentViewRequest:
    instrument_id: str
    layers: tuple[Layer, ...] = (Layer.L3, Layer.L2, Layer.L1)
    model_versions: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _require({"instrument_id": self.instrument_id}, "instrument_id")
        for layer in self.layers:
            if not isinstance(layer, Layer):
                raise RefusalError("MALFORMED_REQUEST", detail="layer_unknown")
            if layer is Layer.CROSS_LAYER:
                raise RefusalError("MALFORMED_REQUEST", detail="layer_unknown")
        if not self.layers:
            raise RefusalError("MALFORMED_REQUEST", detail="layers_empty")

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "InstrumentViewRequest":
        data = _check_mapping(cls, mapping)
        if "layers" in data:
            data["layers"] = tuple(data["layers"])
        return cls(**data)


@dataclass(frozen=True)
class BasketRequest:
    basket_id: str = "JPY"
    pairs: tuple[str, ...] = ("USDJPY", "AUDJPY", "EURJPY")

    def __post_init__(self) -> None:
        if self.basket_id != "JPY":
            raise RefusalError("MALFORMED_REQUEST", detail="basket_unknown")
        if not self.pairs:
            raise RefusalError("MALFORMED_REQUEST", detail="pairs_empty")

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "BasketRequest":
        data = _check_mapping(cls, mapping)
        if "pairs" in data:
            data["pairs"] = tuple(data["pairs"])
        return cls(**data)


@dataclass(frozen=True)
class SetupContextRequest:
    setup_id: str
    setup_version: str | None = None
    surface: str = "OPERATOR"
    require_machine_valid_card: bool = False

    def __post_init__(self) -> None:
        _require({"setup_id": self.setup_id}, "setup_id")
        if self.surface not in ("PRODUCTION", "OPERATOR", "RESEARCH", "AUTOMATION"):
            raise RefusalError("MALFORMED_REQUEST", detail="surface_unknown")
        if self.surface == "AUTOMATION":
            # Eligibility can be read on the automation surface; permission is
            # still registry-wide false and cannot be requested.
            pass

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "SetupContextRequest":
        data = _check_mapping(cls, mapping)
        _require(data, "setup_id")
        return cls(**data)


def parse_request(kind: str, mapping: Mapping[str, Any]) -> Any:
    table = {
        "snapshot": SnapshotRequest,
        "historical": HistoricalRequest,
        "instrument_view": InstrumentViewRequest,
        "basket": BasketRequest,
        "setup_context": SetupContextRequest,
    }
    if kind not in table:
        raise RefusalError("MALFORMED_REQUEST", detail="request_kind_unknown")
    return table[kind].from_mapping(mapping)


__all__ = [
    "FORBIDDEN_REQUEST_KEYS",
    "VERSION_TOKENS",
    "SnapshotRequest",
    "HistoricalRequest",
    "InstrumentViewRequest",
    "BasketRequest",
    "SetupContextRequest",
    "parse_request",
]
