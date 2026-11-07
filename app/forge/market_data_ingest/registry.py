"""Additive instrument composition for ingestion (no frozen edit).

The frozen ``build_default_registry()`` declares EURUSD, XAUUSD and BTCUSD
only.  The JPYY model card requires USDJPY, AUDJPY and EURJPY as well, and real
providers need their own symbol mappings.

Editing ``instruments.py`` would be a frozen amendment, so this module composes
a new registry through the *public* ``Instrument``/``InstrumentRegistry``
constructors: base instruments are copied with ``dataclasses.replace`` to carry
provider mappings, and the three JPYY pairs are declared explicitly.

Disclosure: JPYY precision (3) and pip size (0.01) are market conventions, not
corpus claims; they are marked for operator confirmation before WP-3C.  The
production default registry is intentionally **not** changed by this module.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from app.forge.market_data.instruments import (
    AssetClass,
    Instrument,
    InstrumentRegistry,
    NativeUnit,
    build_default_registry,
)

from .symbols import PROVIDER_SYMBOLS

TIMEFRAMES: frozenset[str] = frozenset(
    {"M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"}
)
CLOCKS: frozenset[str] = frozenset({"America/New_York", "EST_NO_DST"})

JPY_BASES: dict[str, str] = {
    "USDJPY": "USD",
    "AUDJPY": "AUD",
    "EURJPY": "EUR",
}

INGEST_INSTRUMENT_IDS: tuple[str, ...] = (
    "EURUSD",
    "XAUUSD",
    "USDJPY",
    "AUDJPY",
    "EURJPY",
    "BTCUSD",
)


def _provider_mappings(instrument_id: str) -> dict[str, str]:
    mappings: dict[str, str] = {}
    for provider, table in PROVIDER_SYMBOLS.items():
        symbol = table.get(instrument_id)
        if symbol is not None:
            mappings[provider] = symbol
    return mappings


def jpy_instruments() -> tuple[Instrument, ...]:
    """The three JPYY pairs declared by the JPYY carry-game model card."""
    return tuple(
        Instrument(
            instrument_id=instrument_id,
            symbol=instrument_id,
            asset_class=AssetClass.FX,
            base_currency=base,
            quote_currency="JPY",
            native_unit=NativeUnit.PIP,
            price_precision=3,
            supported_timeframes=TIMEFRAMES,
            supported_clocks=CLOCKS,
            pip_size=Decimal("0.01"),
            tick_size=Decimal("0.001"),
            provider_mappings=_provider_mappings(instrument_id),
        )
        for instrument_id, base in JPY_BASES.items()
    )


def build_ingest_registry() -> InstrumentRegistry:
    """Compose the six-instrument ingestion registry additively.

    Base instruments come from the frozen builder, so their canonical
    conventions (pip/point/dollar sizes, precision, clocks) are reused rather
    than restated.  Only provider mappings are added.
    """
    base = build_default_registry()
    instruments: list[Instrument] = []
    for instrument_id in ("EURUSD", "XAUUSD", "BTCUSD"):
        original = base.get(instrument_id)
        instruments.append(
            replace(original, provider_mappings=_provider_mappings(instrument_id))
        )
    instruments.extend(jpy_instruments())
    return InstrumentRegistry(instruments)


__all__ = [
    "CLOCKS",
    "INGEST_INSTRUMENT_IDS",
    "JPY_BASES",
    "TIMEFRAMES",
    "build_ingest_registry",
    "jpy_instruments",
]
