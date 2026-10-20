"""Version fields owned by Bloc III.2 (Book III final-record fields, M5).

``MEASUREMENT_ENGINE_VERSION`` is the measurement-engine version carried
by every emitted measurement.  It travels beside the III.1 contract
versions (``MARKET_DATA_SCHEMA_VERSION``, ``CLOCK_REGISTRY_VERSION``,
``SESSION_REGISTRY_VERSION``) so a downstream final record can cite
exactly which contracts produced it.
"""

from __future__ import annotations

MEASUREMENT_ENGINE_VERSION = "MEASUREMENT_ENGINE_V1"
