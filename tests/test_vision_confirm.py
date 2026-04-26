"""Tests for vision_confirm.py — stub/fallback mode."""
import pytest
from pathlib import Path
from unittest.mock import patch

from app.vision_confirm import confirm_from_chart, _stub_confirmation


SAMPLE_SIGNAL = {
    "signal_id": "EURUSD_20260426_0930_BUY_001",
    "symbol": "EURUSD",
    "action": "BUY",
    "state_id": "EURUSD_20260426_0930_BUY_001",
}


def test_stub_mode_returns_webhook_side(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", False)
    result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["confirmed_side"] == "BUY"
    assert result["chart_confirmed"] is False
    assert result["fallback_mode"] is True
    assert result["reason"] == "vision_stub"


def test_stub_mode_state_id_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", False)
    result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["state_id"] == SAMPLE_SIGNAL["state_id"]


def test_stub_creates_placeholder_screenshot(tmp_path, monkeypatch):
    screenshots_dir = tmp_path / "screenshots"
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", screenshots_dir)
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", False)
    confirm_from_chart(SAMPLE_SIGNAL)
    files = list(screenshots_dir.glob("stub_*.txt"))
    assert len(files) == 1


def test_stub_works_for_sell_signal(tmp_path, monkeypatch):
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", False)
    sell_signal = {**SAMPLE_SIGNAL, "action": "SELL", "signal_id": "SELL_001"}
    result = confirm_from_chart(sell_signal)
    assert result["confirmed_side"] == "SELL"
    assert result["chart_confirmed"] is False


def test_mcp_fallback_on_failure(tmp_path, monkeypatch):
    """If MCP call fails, should fall back to stub result."""
    monkeypatch.setattr("app.vision_confirm.SCREENSHOTS_DIR", tmp_path / "screenshots")
    monkeypatch.setattr("app.vision_confirm.config.USE_MCP_VISION", True)
    with patch("subprocess.run", side_effect=Exception("MCP unavailable")):
        result = confirm_from_chart(SAMPLE_SIGNAL)
    assert result["chart_confirmed"] is False
    assert result["fallback_mode"] is True
