"""Tests for ghost signal detection (webhook vs chart mismatch)."""
import pytest
from unittest.mock import patch
from pathlib import Path

from app.state_engine import StateEngine, reset_engine
from app.validator import validate


VALID_SIGNAL = {
    "symbol": "EURUSD",
    "signal_type": "IMPULSE",
    "strategy_name": "CEREBUS_IMPULSE",
    "timeframe": "M5",
    "price": 1.08542,
    "session": "LONDON",
}


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


@pytest.fixture(autouse=True)
def fresh_state(tmp_path, monkeypatch):
    reset_engine()
    engine = StateEngine(state_file=tmp_path / "state.json")
    monkeypatch.setattr("app.validator.get_engine", lambda: engine)
    monkeypatch.setattr("app.validator.SEEN_IDS_FILE", tmp_path / "seen.json")
    yield
    reset_engine()


def _signal(action, signal_id="GHOST_TEST_001", state_id=None):
    return {
        **VALID_SIGNAL,
        "signal_id": signal_id,
        "action": action,
        "state_id": state_id or signal_id,
        "timestamp": _now_iso(),
    }


def test_ghost_signal_rejected_when_chart_confirms_opposite():
    """Webhook says BUY, chart says SELL → REJECT."""
    with patch("app.validator.confirm_from_chart") as mock_vision:
        mock_vision.return_value = {
            "confirmed_side": "SELL",
            "state_id": "GHOST_TEST_001",
            "chart_confirmed": True,
            "fallback_mode": False,
        }
        result = validate(_signal("BUY", "GHOST_TEST_001"))
    assert result.result == "REJECT"
    assert "ghost_signal" in result.reason


def test_ghost_signal_rejected_sell_vs_buy():
    """Webhook says SELL, chart says BUY → REJECT."""
    with patch("app.validator.confirm_from_chart") as mock_vision:
        mock_vision.return_value = {
            "confirmed_side": "BUY",
            "state_id": "GHOST_TEST_002",
            "chart_confirmed": True,
            "fallback_mode": False,
        }
        result = validate(_signal("SELL", "GHOST_TEST_002"))
    assert result.result == "REJECT"
    assert "ghost_signal" in result.reason


def test_state_id_mismatch_rejected():
    """Webhook and chart agree on side but state_ids differ → REJECT."""
    with patch("app.validator.confirm_from_chart") as mock_vision:
        mock_vision.return_value = {
            "confirmed_side": "BUY",
            "state_id": "DIFFERENT_STATE_ID",
            "chart_confirmed": True,
            "fallback_mode": False,
        }
        result = validate(_signal("BUY", "GHOST_TEST_003", state_id="GHOST_TEST_003"))
    assert result.result == "REJECT"
    assert "state_id_mismatch" in result.reason


def test_stub_mode_skips_ghost_check():
    """In stub mode (chart_confirmed=False), ghost check is skipped → ALLOW."""
    with patch("app.validator.confirm_from_chart") as mock_vision:
        mock_vision.return_value = {
            "confirmed_side": "SELL",   # disagrees with BUY
            "state_id": "GHOST_TEST_004",
            "chart_confirmed": False,   # stub mode
            "fallback_mode": True,
        }
        result = validate(_signal("BUY", "GHOST_TEST_004"))
    # Ghost check skipped in stub mode — should ALLOW (or IGNORE if position matches)
    assert result.result in ("ALLOW", "IGNORE")


def test_matching_sides_allowed():
    """Webhook BUY + chart BUY + matching state_id → ALLOW."""
    with patch("app.validator.confirm_from_chart") as mock_vision:
        mock_vision.return_value = {
            "confirmed_side": "BUY",
            "state_id": "GHOST_TEST_005",
            "chart_confirmed": True,
            "fallback_mode": False,
        }
        result = validate(_signal("BUY", "GHOST_TEST_005", state_id="GHOST_TEST_005"))
    assert result.result == "ALLOW"
