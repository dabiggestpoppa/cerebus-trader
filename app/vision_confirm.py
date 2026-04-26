import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from app import config

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = Path("logs/screenshots")
MCP_DIR = Path(os.getenv("TRADINGVIEW_MCP_DIR", "C:/Users/jefe/tradingview-mcp"))
MCP_TIMEOUT = int(os.getenv("MCP_TIMEOUT_SECONDS", "8"))


def confirm_from_chart(signal: dict) -> dict:
    """
    Phase 1: stub mode — returns webhook side, chart_confirmed=False.
    Phase 2: set USE_MCP_VISION=true in .env to enable real chart confirmation.
             Requires TradingView Desktop running with CDP on localhost:9222.
             CEREBUS truth panel indicator must be visible on EURUSD M5 chart.
    """
    if config.USE_MCP_VISION:
        return _confirm_from_mcp(signal)
    return _stub_confirmation(signal)


def _stub_confirmation(signal: dict) -> dict:
    logger.warning(
        "vision_stub_mode: chart confirmation skipped for signal_id=%s",
        signal.get("signal_id"),
    )
    _log_stub_screenshot(signal)
    return {
        "confirmed_side": signal.get("action"),
        "state_id": signal.get("state_id"),
        "chart_confirmed": False,
        "fallback_mode": True,
        "reason": "vision_stub",
    }


def _confirm_from_mcp(signal: dict) -> dict:
    """
    Calls TradingView MCP CLI to read Pine truth panel from live chart.

    CLI: node src/cli/index.js data tables -f CEREBUS
    Requires: TradingView Desktop running, CDP on localhost:9222,
              CEREBUS truth panel indicator visible on EURUSD M5 chart.

    Expected table rows (space-pipe-space delimited):
      "SIDE | BUY"
      "MODEL | CEREBUS_IMPULSE"
      "STATE ID | EURUSD_0930_BUY_001"
      "VALID UNTIL | 09:35"

    Falls back to stub on any error (connection refused, TV not running, etc.)
    """
    try:
        result = subprocess.run(
            ["node", "src/cli/index.js", "data", "tables", "-f", "CEREBUS"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=MCP_TIMEOUT,
            cwd=str(MCP_DIR),
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"MCP CLI exited {result.returncode}: {result.stderr[:200]}"
            )

        data = json.loads(result.stdout)

        if not data.get("success"):
            raise ValueError(f"MCP returned failure: {data.get('error', data)}")

        studies = data.get("studies", [])
        if not studies:
            raise ValueError(
                "No studies returned — is CEREBUS truth panel visible on chart?"
            )

        rows = studies[0].get("tables", [{}])[0].get("rows", [])
        side, state_id = _parse_truth_panel(rows)

        if side is None:
            raise ValueError(
                f"SIDE not found in truth panel rows: {rows[:5]}"
            )

        _save_mcp_screenshot(signal)

        logger.info(
            "MCP vision confirmed: signal_id=%s side=%s state_id=%s",
            signal.get("signal_id"), side, state_id,
        )

        return {
            "confirmed_side": side,
            "state_id": state_id,
            "chart_confirmed": True,
            "fallback_mode": False,
            "reason": "mcp_confirmed",
        }

    except subprocess.TimeoutExpired:
        logger.warning("MCP vision timed out after %ss — falling back to stub", MCP_TIMEOUT)
        return _stub_confirmation(signal)
    except Exception as exc:
        logger.warning("MCP vision failed (%s) — falling back to stub", exc)
        return _stub_confirmation(signal)


def _parse_truth_panel(rows: list[str]) -> tuple[str | None, str | None]:
    """
    Parse rows like ["SIDE | BUY", "MODEL | CEREBUS_IMPULSE", "STATE ID | EURUSD_..."].
    Returns (side, state_id). Both may be None if rows are missing.
    """
    side = None
    state_id = None
    for row in rows:
        parts = [p.strip() for p in row.split(" | ")]
        if len(parts) < 2:
            continue
        label = parts[0].upper()
        value = parts[1]
        if label == "SIDE":
            side = value.upper()
        elif label == "STATE ID":
            state_id = value
    return side, state_id


def _save_mcp_screenshot(signal: dict) -> None:
    """Trigger chart screenshot via MCP CLI and copy to logs/screenshots/."""
    try:
        result = subprocess.run(
            ["node", "src/cli/index.js", "screenshot", "-r", "chart"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
            cwd=str(MCP_DIR),
        )
        data = json.loads(result.stdout)
        src = data.get("file_path")
        if src and Path(src).exists():
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            sid = signal.get("signal_id", "unknown")
            dest = SCREENSHOTS_DIR / f"mcp_{sid}_{ts}.png"
            shutil.copy2(src, dest)
            logger.info("Screenshot saved: %s", dest)
    except Exception as exc:
        logger.warning("Failed to save MCP screenshot: %s", exc)


def _log_stub_screenshot(signal: dict) -> None:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    sid = signal.get("signal_id", "unknown")
    placeholder = SCREENSHOTS_DIR / f"stub_{sid}_{ts}.txt"
    placeholder.write_text(
        f"vision_stub — no screenshot taken\n"
        f"signal_id: {sid}\n"
        f"action: {signal.get('action')}\n"
        f"timestamp: {ts}\n"
        f"reason: USE_MCP_VISION=false or MCP unavailable\n"
    )
