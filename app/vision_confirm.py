import logging
from datetime import datetime, timezone
from pathlib import Path

from app import config

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = Path("logs/screenshots")


def confirm_from_chart(signal: dict) -> dict:
    """
    Phase 1 stub — returns webhook side as confirmed, marks chart_confirmed=False.
    Phase 2 will call TradingView MCP data_get_pine_tables(study_filter="CEREBUS")
    to read the Pine truth panel (SIDE / MODEL / STATE_ID / VALID UNTIL).
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
    Phase 2 — calls TradingView MCP CLI to read Pine truth panel.
    CLI: node src/cli/index.js data tables -f CEREBUS
    Requires: TradingView Desktop running with CDP on localhost:9222.

    Response rows are " | "-delimited strings, e.g.:
      "SIDE | BUY"
      "MODEL | CEREBUS_IMPULSE"
      "STATE ID | EURUSD_0930_BUY_001"
      "VALID UNTIL | 09:35"

    Falls back to stub if MCP is unavailable or TradingView not running.
    """
    import subprocess
    import json as _json

    MCP_DIR = "C:/Users/jefe/tradingview-mcp"

    try:
        result = subprocess.run(
            ["node", "src/cli/index.js", "data", "tables", "-f", "CEREBUS"],
            capture_output=True,
            text=True,
            timeout=8,
            cwd=MCP_DIR,
        )
        data = _json.loads(result.stdout)
        if not data.get("success"):
            raise ValueError(f"MCP returned failure: {data}")

        studies = data.get("studies", [])
        if not studies:
            raise ValueError("No studies returned from MCP")

        rows = studies[0].get("tables", [{}])[0].get("rows", [])
        side = None
        state_id = None
        for row in rows:
            parts = [p.strip() for p in row.split(" | ")]
            if len(parts) >= 2:
                label = parts[0].upper()
                value = parts[1]
                if label == "SIDE":
                    side = value.upper()
                elif label == "STATE ID":
                    state_id = value

        if side is None:
            raise ValueError(f"SIDE not found in Pine truth panel rows: {rows}")

        _save_mcp_screenshot(signal, MCP_DIR)

        return {
            "confirmed_side": side,
            "state_id": state_id,
            "chart_confirmed": True,
            "fallback_mode": False,
            "reason": "mcp_confirmed",
        }
    except Exception as exc:
        logger.warning("MCP vision failed (%s), falling back to stub", exc)
        return _stub_confirmation(signal)


def _save_mcp_screenshot(signal: dict, mcp_dir: str) -> None:
    """Trigger a screenshot via MCP CLI and copy to our logs/screenshots/."""
    import subprocess
    try:
        result = subprocess.run(
            ["node", "src/cli/index.js", "screenshot", "-r", "chart"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=mcp_dir,
        )
        import json as _json
        data = _json.loads(result.stdout)
        src = data.get("file_path")
        if src:
            import shutil
            SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            dest = SCREENSHOTS_DIR / f"mcp_{signal.get('signal_id', 'unknown')}_{ts}.png"
            shutil.copy2(src, dest)
    except Exception as exc:
        logger.warning("Failed to save MCP screenshot: %s", exc)


def _log_stub_screenshot(signal: dict) -> None:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    placeholder = SCREENSHOTS_DIR / f"stub_{signal.get('signal_id', 'unknown')}_{ts}.txt"
    placeholder.write_text(
        f"vision_stub — no screenshot taken\nsignal_id: {signal.get('signal_id')}\n"
        f"action: {signal.get('action')}\ntimestamp: {ts}\n"
    )
