"""
Phase 2 integration tests for MCP vision confirmation.

Unit tests (no TradingView required): test _parse_truth_panel logic.
Integration tests (require TradingView running): marked with @pytest.mark.integration.

Run unit tests only:    pytest tests/test_vision_mcp.py -m "not integration"
Run all incl. live MCP: pytest tests/test_vision_mcp.py --run-integration
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.vision_confirm import _parse_truth_panel, confirm_from_chart, _confirm_from_mcp


# ─── Unit tests: _parse_truth_panel ─────────────────────────────────────────

def test_parse_buy_side():
    rows = ["SIDE | BUY", "MODEL | CEREBUS_IMPULSE", "STATE ID | EURUSD_001", "VALID UNTIL | 09:35"]
    side, state_id = _parse_truth_panel(rows)
    assert side == "BUY"
    assert state_id == "EURUSD_001"


def test_parse_sell_side():
    rows = ["SIDE | SELL", "MODEL | CEREBUS_REBALANCE", "STATE ID | EURUSD_002"]
    side, state_id = _parse_truth_panel(rows)
    assert side == "SELL"
    assert state_id == "EURUSD_002"


def test_parse_case_insensitive_side():
    rows = ["SIDE | buy"]
    side, _ = _parse_truth_panel(rows)
    assert side == "BUY"


def test_parse_missing_side_returns_none():
    rows = ["MODEL | CEREBUS_IMPULSE", "STATE ID | EURUSD_001"]
    side, state_id = _parse_truth_panel(rows)
    assert side is None
    assert state_id == "EURUSD_001"


def test_parse_empty_rows():
    side, state_id = _parse_truth_panel([])
    assert side is None
    assert state_id is None


def test_parse_header_row_ignored():
    rows = ["CEREBUS TRUTH | v1.0", "SIDE | BUY", "STATE ID | EURUSD_003"]
    side, state_id = _parse_truth_panel(rows)
    assert side == "BUY"
    assert state_id == "EURUSD_003"


def test_parse_malformed_row_skipped():
    rows = ["no pipe here", "SIDE | SELL"]
    side, _ = _parse_truth_panel(rows)
    assert side == "SELL"


# ─── Unit tests: MCP path with mocked subprocess ────────────────────────────

SAMPLE_SIGNAL = {
    "signal_id": "EURUSD_20260426_0930_BUY_001",
    "symbol": "EURUSD",
    "action": "BUY",
    "state_id": "EURUSD_20260426_0930_BUY_001",
}

MCP_SUCCESS_RESPONSE = {
    "success": True,
    "study_count": 1,
    "studies": [
        {
            "name": "CEREBUS Truth Panel",
            "tables": [
                {
                    "rows": [
                        "CEREBUS TRUTH | v1.0",
                        "SIDE | BUY",
                        "MODEL | CEREBUS_IMPULSE",
                        "STATE ID | EURUSD_20260426_0930_BUY_001",
                        "VALID UNTIL | 09:35",
                    ]
                }
            ],
        }
    ],
}


def _mock_run(response: dict, returncode: int = 0):
    import json
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = json.dumps(response)
    mock.stderr = ""
    return mock


def test_mcp_confirms_matching_signal(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(MCP_SUCCESS_RESPONSE)
        result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["chart_confirmed"] is True
    assert result["confirmed_side"] == "BUY"
    assert result["state_id"] == "EURUSD_20260426_0930_BUY_001"
    assert result["reason"] == "mcp_confirmed"


def test_mcp_detects_ghost_signal(tmp_path, monkeypatch):
    """MCP says SELL, webhook says BUY — ghost signal should be caught by validator."""
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)
    sell_response = {
        **MCP_SUCCESS_RESPONSE,
        "studies": [
            {
                "name": "CEREBUS Truth Panel",
                "tables": [{"rows": ["SIDE | SELL", "STATE ID | EURUSD_20260426_0930_BUY_001"]}],
            }
        ],
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(sell_response)
        result = confirm_from_chart(SAMPLE_SIGNAL)
    # MCP confirms SELL, but signal is BUY — confirmed_side will be SELL
    assert result["chart_confirmed"] is True
    assert result["confirmed_side"] == "SELL"  # Chart says SELL


def test_mcp_timeout_falls_back_to_stub(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)
    with patch("subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("node", 8)):
        result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["chart_confirmed"] is False
    assert result["fallback_mode"] is True


def test_mcp_connection_refused_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)
    with patch("subprocess.run", side_effect=Exception("ECONNREFUSED")):
        result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["chart_confirmed"] is False
    assert result["fallback_mode"] is True


def test_mcp_no_studies_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)
    empty = {"success": True, "study_count": 0, "studies": []}
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(empty)
        result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["chart_confirmed"] is False


def test_mcp_missing_side_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)
    no_side = {
        "success": True,
        "study_count": 1,
        "studies": [{"name": "CEREBUS", "tables": [{"rows": ["MODEL | CEREBUS_IMPULSE"]}]}],
    }
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(no_side)
        result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["chart_confirmed"] is False


# ─── Ghost signal end-to-end (MCP + validator) ──────────────────────────────

def test_ghost_signal_e2e_mcp(tmp_path, monkeypatch):
    """Full pipeline: MCP says SELL, webhook says BUY → validator rejects."""
    from app.state_engine import StateEngine, reset_engine
    from app.validator import validate

    reset_engine()
    engine = StateEngine(state_file=tmp_path / "state.json")
    monkeypatch.setattr("app.validator.get_engine", lambda: engine)
    monkeypatch.setattr("app.validator.SEEN_IDS_FILE", tmp_path / "seen.json")
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)

    sell_response = {
        "success": True,
        "study_count": 1,
        "studies": [
            {"name": "CEREBUS", "tables": [{"rows": ["SIDE | SELL", "STATE ID | GHOST_001"]}]}
        ],
    }

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    signal = {
        "signal_id": "GHOST_E2E_001",
        "symbol": "EURUSD",
        "action": "BUY",
        "signal_type": "IMPULSE",
        "strategy_name": "CEREBUS_IMPULSE",
        "timestamp": now,
        "timeframe": "M5",
        "price": 1.08542,
        "session": "LONDON",
        "state_id": "GHOST_001",
    }

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = _mock_run(sell_response)
        result = validate(signal)

    assert result.result == "REJECT"
    assert "ghost_signal" in result.reason
    assert result.chart_confirmed is True
    reset_engine()
