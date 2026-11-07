"""Provider symbol tables (data only).

Resolution still belongs to the frozen III.1 ``InstrumentRegistry``; this module
only records what each vendor calls the instrument.  Spellings are documented
from vendor symbol references and must be revisited whenever a vendor renames an
instrument — a rename is a mapping change, not code logic.
"""

from __future__ import annotations

from typing import Mapping

from app.forge.market_data.errors import UnknownAliasError

PROVIDER_SYMBOLS: Mapping[str, Mapping[str, str]] = {
    # Twelve Data: slash-separated FX/metals/crypto symbols.
    "twelvedata": {
        "EURUSD": "EUR/USD",
        "XAUUSD": "XAU/USD",
        "USDJPY": "USD/JPY",
        "AUDJPY": "AUD/JPY",
        "EURJPY": "EUR/JPY",
        "BTCUSD": "BTC/USD",
    },
    # Polygon currencies use the C: prefix for FX and metals.
    "polygon": {
        "EURUSD": "C:EURUSD",
        "XAUUSD": "C:XAUUSD",
        "USDJPY": "C:USDJPY",
        "AUDJPY": "C:AUDJPY",
        "EURJPY": "C:EURJPY",
        "BTCUSD": "C:BTCUSD",
    },
    # Kraken: true USD crypto pair (legacy XBT spelling still resolves).
    "kraken": {
        "BTCUSD": "BTC/USD",
    },
}

KRAKEN_LEGACY_ALIASES: Mapping[str, str] = {"XXBTZUSD": "BTC/USD"}


def source_symbol(provider: str, instrument_id: str) -> str:
    """Provider spelling for one instrument, or a bounded refusal."""
    table = PROVIDER_SYMBOLS.get(provider)
    if table is None:
        raise UnknownAliasError(f"unknown provider {provider!r}")
    symbol = table.get(instrument_id)
    if symbol is None:
        raise UnknownAliasError(
            f"{provider} does not cover instrument {instrument_id!r}"
        )
    return symbol


def instrument_for_source_symbol(provider: str, symbol: str) -> str:
    """Reverse lookup with Kraken's legacy alias honoured."""
    normalized = symbol.upper().replace(" ", "")
    if provider == "kraken":
        normalized = KRAKEN_LEGACY_ALIASES.get(normalized, normalized)
    for instrument_id, mapped in PROVIDER_SYMBOLS.get(provider, {}).items():
        if mapped.upper().replace(" ", "") == normalized:
            return instrument_id
    # Case-insensitive fallback for vendors that mix prefix casing.
    for instrument_id, mapped in PROVIDER_SYMBOLS.get(provider, {}).items():
        if mapped.lower() == symbol.lower():
            return instrument_id
    raise UnknownAliasError(f"{provider}:{symbol!r} does not resolve")


__all__ = [
    "KRAKEN_LEGACY_ALIASES",
    "PROVIDER_SYMBOLS",
    "instrument_for_source_symbol",
    "source_symbol",
]
