"""Additive market-data ingestion boundary (WP-3B).

This package adapts external market-data providers into the frozen Bloc III.1
contracts.  It owns **provider communication and raw-event adaptation only**:
canonical normalization, clarity of finality, dedupe, gaps, clocks, sessions and
research-day ownership remain owned by ``app.forge.market_data``.

No module here performs network I/O, reads credentials from the environment at
import time, or mutates a frozen III.1 module.  Providers are driven through an
injected transport so the entire package is deterministic offline.
"""

from __future__ import annotations

from .canonical import CanonicalOutcome, IngestRefusal, canonicalize
from .capture import CaptureMetadata, source_window_digest
from .config import MarketDataIngestConfig
from .contract import (
    CandlePage,
    CandleRequest,
    MarketDataProvider,
    ProviderCapabilities,
    RawCandle,
)
from .registry import (
    INGEST_INSTRUMENT_IDS,
    build_ingest_registry,
    jpy_instruments,
)
from .symbols import PROVIDER_SYMBOLS, source_symbol

__all__ = [
    "CanonicalOutcome",
    "IngestRefusal",
    "canonicalize",
    "CaptureMetadata",
    "source_window_digest",
    "MarketDataIngestConfig",
    "CandlePage",
    "CandleRequest",
    "MarketDataProvider",
    "ProviderCapabilities",
    "RawCandle",
    "INGEST_INSTRUMENT_IDS",
    "build_ingest_registry",
    "jpy_instruments",
    "PROVIDER_SYMBOLS",
    "source_symbol",
]
