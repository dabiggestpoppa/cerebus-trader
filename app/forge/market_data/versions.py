"""Version fields owned by Bloc III.1 (Book III final-record inputs, M5).

``MARKET_DATA_SCHEMA_VERSION`` is the market-data schema version; the
clock-registry version lives with ``ClockIdentity`` (``clocks.py``) and
the session-registry version lives with the session registry
(``sessions.py``).  All three travel with serialized derived state so a
downstream final record can cite exactly which contract produced it.
"""

from __future__ import annotations

MARKET_DATA_SCHEMA_VERSION = "MARKET_DATA_SCHEMA_V1"
