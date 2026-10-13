"""Canonical instrument identity and asset-native units (Ch III.1.1).

Instruments are first-class frozen values: canonical id, symbol and
provider aliases, asset class, quote/base conventions, native unit with
per-instrument size, price precision, supported timeframes and clock
identities, provider symbol mappings.

Asset-native units are mandatory.  EUR pips, XAU points and BTC dollar
movements are distinct domains: there is no global pip/point constant
anywhere in this package, no implicit cross-unit arithmetic and no
silent precision conversion.  Unit sizes live only on the instrument
instance itself.  Ambiguous aliases fail closed at registry build time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping, Sequence

from .errors import (
    AmbiguousAliasError,
    ConventionViolationError,
    DuplicateRegistrationError,
    PrecisionViolationError,
    UnknownAliasError,
    UnitMismatchError,
    UnsupportedClockError,
    UnsupportedConversionError,
    UnsupportedTimeframeError,
)


class AssetClass(str, Enum):
    """Asset classes admitted by Bloc III.1."""

    FX = "FX"
    METAL = "METAL"
    CRYPTO = "CRYPTO"


class NativeUnit(str, Enum):
    """Asset-native magnitude domains.

    These enumerations are the domain boundary: a PIP price and a POINT
    price are different kinds of quantities even when their numeric step
    happens to coincide.  No conversion between members exists.
    """

    PIP = "PIP"
    POINT = "POINT"
    DOLLAR = "DOLLAR"


@dataclass(frozen=True)
class NativePrice:
    """A price magnitude tagged with its instrument and native unit."""

    instrument_id: str
    unit: NativeUnit
    value: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.value, Decimal):
            raise ConventionViolationError("native price value must be Decimal")


def add_native(first: NativePrice, second: NativePrice) -> NativePrice:
    """Add two magnitudes only when instrument and native unit both match.

    Cross-domain addition (e.g. an EURUSD pip magnitude plus an XAUUSD
    point magnitude) refuses with ``UnitMismatchError``.
    """
    if first.instrument_id != second.instrument_id or first.unit is not second.unit:
        raise UnitMismatchError(
            f"refusing {first.unit.value}/{first.instrument_id} + "
            f"{second.unit.value}/{second.instrument_id}"
        )
    return NativePrice(first.instrument_id, first.unit, first.value + second.value)


def convert_native(price: NativePrice, target_unit: NativeUnit) -> NativePrice:
    """Convert across native unit domains — always refused in III.1.

    No conversion authority exists at this layer.  A same-unit request is
    a no-op identity (not a conversion); any cross-unit request raises.
    """
    if target_unit is price.unit:
        return price
    raise UnsupportedConversionError(
        f"no conversion authority: {price.unit.value} -> {target_unit.value}"
    )


def validate_quote_base(
    instrument: Instrument, base_currency: str, quote_currency: str
) -> None:
    """Fail closed when a quote/base convention is stated differently."""
    if base_currency != instrument.base_currency or quote_currency != instrument.quote_currency:
        raise ConventionViolationError(
            f"{instrument.instrument_id} convention is "
            f"{instrument.base_currency}/{instrument.quote_currency}"
        )


@dataclass(frozen=True)
class Instrument:
    """Frozen canonical instrument record (Ch III.1.1 schema)."""

    instrument_id: str
    symbol: str
    asset_class: AssetClass
    base_currency: str
    quote_currency: str
    native_unit: NativeUnit
    price_precision: int
    supported_timeframes: frozenset[str]
    supported_clocks: frozenset[str]
    # Per-instrument native unit sizes — the only place unit sizes exist.
    pip_size: Decimal | None = None
    point_size: Decimal | None = None
    tick_size: Decimal | None = None
    provider_mappings: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.instrument_id or not self.symbol:
            raise ConventionViolationError("instrument_id and symbol are required")
        if self.price_precision < 0:
            raise ConventionViolationError("price_precision must be >= 0")
        if not self.supported_timeframes:
            raise ConventionViolationError("supported_timeframes must be declared")
        if not self.supported_clocks:
            raise ConventionViolationError("supported_clocks must be declared")
        for size_name in ("pip_size", "point_size", "tick_size"):
            size = getattr(self, size_name)
            if size is not None and not isinstance(size, Decimal):
                raise ConventionViolationError(f"{size_name} must be Decimal")
        if self.native_unit is NativeUnit.PIP and self.pip_size is None:
            raise ConventionViolationError("PIP instrument requires pip_size")
        if self.native_unit is NativeUnit.POINT and self.point_size is None:
            raise ConventionViolationError("POINT instrument requires point_size")
        object.__setattr__(
            self, "supported_timeframes", frozenset(self.supported_timeframes)
        )
        object.__setattr__(self, "supported_clocks", frozenset(self.supported_clocks))
        object.__setattr__(
            self,
            "provider_mappings",
            MappingProxyType(dict(self.provider_mappings)),
        )

    # -- declarations -------------------------------------------------
    def supports_timeframe(self, timeframe: str) -> bool:
        return timeframe in self.supported_timeframes

    def require_timeframe(self, timeframe: str) -> None:
        if not self.supports_timeframe(timeframe):
            raise UnsupportedTimeframeError(
                f"{self.instrument_id} does not support timeframe {timeframe}"
            )

    def supports_clock(self, clock_id: str) -> bool:
        return clock_id in self.supported_clocks

    def require_clock(self, clock_id: str) -> None:
        """Declared clocks only — never a silent remap (A5 / G4)."""
        if not self.supports_clock(clock_id):
            raise UnsupportedClockError(
                f"{self.instrument_id} does not declare clock {clock_id}"
            )

    # -- native magnitude handling ------------------------------------
    @property
    def native_step(self) -> Decimal:
        """Size of one native unit for this instrument (no global constant)."""
        if self.native_unit is NativeUnit.PIP:
            assert self.pip_size is not None
            return self.pip_size
        if self.native_unit is NativeUnit.POINT:
            assert self.point_size is not None
            return self.point_size
        return Decimal("1")

    def validate_price(self, value: Decimal) -> Decimal:
        """Reject prices outside declared precision — never round silently."""
        if not isinstance(value, Decimal):
            raise PrecisionViolationError("price must be Decimal")
        normalized = value.normalize()
        exponent = normalized.as_tuple().exponent
        decimals = max(0, -int(exponent))
        if decimals > self.price_precision:
            raise PrecisionViolationError(
                f"{self.instrument_id} precision {self.price_precision} "
                f"cannot hold {value}"
            )
        return value


def _normalize_alias(alias: str) -> str:
    """Fold an alias to its canonical lookup key (case/space/slash-insensitive)."""
    return "".join(ch for ch in alias.upper() if ch.isalnum())


class InstrumentRegistry:
    """Symbol + provider alias tables resolving to exactly one canonical id.

    Collisions (one alias reaching two instruments) fail closed at build
    time with ``AmbiguousAliasError`` — ambiguity is never guessed.
    """

    def __init__(
        self,
        instruments: Sequence[Instrument],
        aliases: Mapping[str, str] | None = None,
    ) -> None:
        self._instruments: dict[str, Instrument] = {}
        self._alias_map: dict[str, str] = {}
        for instrument in instruments:
            if instrument.instrument_id in self._instruments:
                raise DuplicateRegistrationError(
                    f"duplicate instrument {instrument.instrument_id}"
                )
            self._instruments[instrument.instrument_id] = instrument
            self._register_alias(instrument.instrument_id, instrument.instrument_id)
            self._register_alias(instrument.symbol, instrument.instrument_id)
            for raw_symbol in instrument.provider_mappings.values():
                self._register_alias(raw_symbol, instrument.instrument_id)
        for alias, instrument_id in (aliases or {}).items():
            self._register_alias(alias, instrument_id)

    def _register_alias(self, alias: str, instrument_id: str) -> None:
        if instrument_id not in self._instruments:
            raise UnknownAliasError(
                f"alias {alias!r} targets unknown instrument {instrument_id!r}"
            )
        key = _normalize_alias(alias)
        if not key:
            raise UnknownAliasError("empty alias")
        existing = self._alias_map.get(key)
        if existing is not None and existing != instrument_id:
            raise AmbiguousAliasError(
                f"alias {alias!r} reaches both {existing} and {instrument_id}"
            )
        self._alias_map[key] = instrument_id

    def resolve(self, alias: str) -> Instrument:
        try:
            instrument_id = self._alias_map[_normalize_alias(alias)]
        except KeyError:
            raise UnknownAliasError(f"alias {alias!r} does not resolve") from None
        return self._instruments[instrument_id]

    def resolve_provider(self, provider: str, raw_symbol: str) -> Instrument:
        """Resolve a provider's own symbol spelling to the canonical id."""
        for instrument in self._instruments.values():
            mapped = instrument.provider_mappings.get(provider)
            if mapped is not None and _normalize_alias(mapped) == _normalize_alias(
                raw_symbol
            ):
                return instrument
        raise UnknownAliasError(
            f"provider symbol {provider}:{raw_symbol!r} does not resolve"
        )

    def get(self, instrument_id: str) -> Instrument:
        try:
            return self._instruments[instrument_id]
        except KeyError:
            raise UnknownAliasError(f"unknown instrument {instrument_id!r}") from None

    @property
    def instrument_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._instruments))


def build_default_registry() -> InstrumentRegistry:
    """Canonical III.1 instrument set for this repository.

    Convention disclosures (market convention, not corpus claims): the
    EURUSD pip is 0.0001 with 5-decimal price precision; XAUUSD points
    are price dollars (point size 1.00, 2-decimal precision — corpus
    XAU bands such as 25-50/68/100-132 read as dollar magnitudes); BTC
    moves are dollars (2-decimal precision).  The three native-unit
    domains remain distinct enumerations regardless of numeric size and
    are never convertible across each other.
    """
    eurusd = Instrument(
        instrument_id="EURUSD",
        symbol="EURUSD",
        asset_class=AssetClass.FX,
        base_currency="EUR",
        quote_currency="USD",
        native_unit=NativeUnit.PIP,
        price_precision=5,
        supported_timeframes=frozenset({"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}),
        supported_clocks=frozenset({"America/New_York", "EST_NO_DST"}),
        pip_size=Decimal("0.0001"),
        tick_size=Decimal("0.00001"),
        provider_mappings={"fake_alpha": "EUR/USD", "fake_beta": "EUR-USD"},
    )
    xauusd = Instrument(
        instrument_id="XAUUSD",
        symbol="XAUUSD",
        asset_class=AssetClass.METAL,
        base_currency="XAU",
        quote_currency="USD",
        native_unit=NativeUnit.POINT,
        price_precision=2,
        supported_timeframes=frozenset({"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}),
        supported_clocks=frozenset({"America/New_York", "EST_NO_DST"}),
        point_size=Decimal("1.00"),
        tick_size=Decimal("0.01"),
        provider_mappings={"fake_alpha": "XAU/USD", "fake_beta": "XAU-USD"},
    )
    btcusd = Instrument(
        instrument_id="BTCUSD",
        symbol="BTCUSD",
        asset_class=AssetClass.CRYPTO,
        base_currency="BTC",
        quote_currency="USD",
        native_unit=NativeUnit.DOLLAR,
        price_precision=2,
        supported_timeframes=frozenset({"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}),
        supported_clocks=frozenset({"America/New_York", "EST_NO_DST"}),
        point_size=Decimal("1.00"),
        tick_size=Decimal("0.01"),
        provider_mappings={"fake_alpha": "BTC/USD", "fake_beta": "BTC-USD"},
    )
    instruments: Iterable[Instrument] = (eurusd, xauusd, btcusd)
    aliases = {
        "EUR/USD": "EURUSD",
        "EUR-USD": "EURUSD",
        "XAU/USD": "XAUUSD",
        "XAU-USD": "XAUUSD",
        "BTC/USD": "BTCUSD",
        "BTC-USD": "BTCUSD",
    }
    return InstrumentRegistry(list(instruments), aliases)
