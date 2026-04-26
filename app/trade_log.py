import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.validator import ValidationResult

logger = logging.getLogger(__name__)

LOGS_DIR = Path("logs")
SIGNALS_CSV = LOGS_DIR / "signals.csv"
TRADES_CSV = LOGS_DIR / "trades.csv"

SIGNAL_HEADERS = [
    "timestamp", "signal_id", "symbol", "action", "signal_type",
    "strategy_name", "price", "session", "result", "target_state",
    "action_required", "reason", "position_before", "position_after",
    "chart_confirmed",
]

TRADE_HEADERS = [
    "timestamp", "signal_id", "symbol", "action", "target_state",
    "broker", "account_id", "order_id", "status", "notes",
]


def log_signal(signal: dict, result: ValidationResult) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _append_csv(
        SIGNALS_CSV,
        SIGNAL_HEADERS,
        {
            "timestamp": result.timestamp,
            "signal_id": result.signal_id,
            "symbol": signal.get("symbol", ""),
            "action": signal.get("action", ""),
            "signal_type": signal.get("signal_type", ""),
            "strategy_name": signal.get("strategy_name", ""),
            "price": signal.get("price", ""),
            "session": signal.get("session", ""),
            "result": result.result,
            "target_state": result.target_state,
            "action_required": result.action_required,
            "reason": result.reason,
            "position_before": result.position_before,
            "position_after": result.position_after,
            "chart_confirmed": result.chart_confirmed,
        },
    )


def log_trade(
    signal_id: str,
    symbol: str,
    action: str,
    target_state: str,
    broker: str = "",
    account_id: str = "",
    order_id: str = "",
    status: str = "",
    notes: str = "",
) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _append_csv(
        TRADES_CSV,
        TRADE_HEADERS,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signal_id": signal_id,
            "symbol": symbol,
            "action": action,
            "target_state": target_state,
            "broker": broker,
            "account_id": account_id,
            "order_id": order_id,
            "status": status,
            "notes": notes,
        },
    )


def get_recent_signals(n: int = 50) -> list[dict]:
    return _read_last_n(SIGNALS_CSV, n)


def get_recent_trades(n: int = 50) -> list[dict]:
    return _read_last_n(TRADES_CSV, n)


def _append_csv(path: Path, headers: list[str], row: dict[str, Any]) -> None:
    write_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if write_header:
            writer.writeheader()
        writer.writerow({h: row.get(h, "") for h in headers})


def _read_last_n(path: Path, n: int) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-n:]
