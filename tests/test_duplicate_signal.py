"""Tests for duplicate signal detection (5-second dedup window)."""
import time
import pytest
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


def _signal(signal_id, action="BUY"):
    return {
        **VALID_SIGNAL,
        "signal_id": signal_id,
        "action": action,
        "state_id": signal_id,
        "timestamp": _now_iso(),
    }


def test_first_signal_allowed():
    result = validate(_signal("DUP_TEST_001"))
    assert result.result == "ALLOW"


def test_immediate_duplicate_rejected():
    validate(_signal("DUP_TEST_002"))
    result = validate(_signal("DUP_TEST_002"))
    assert result.result == "REJECT"
    assert "duplicate_signal_id" in result.reason


def test_different_signal_ids_not_deduped():
    """Different signal IDs must never trigger dedup — BUY then SELL flip both go through."""
    r1 = validate(_signal("DUP_TEST_003A", "BUY"))
    r2 = validate(_signal("DUP_TEST_003B", "SELL"))
    assert r1.result == "ALLOW"
    assert r2.result == "ALLOW"
    # Neither was rejected for duplicate reason
    assert "duplicate" not in r1.reason
    assert "duplicate" not in r2.reason


def test_duplicate_does_not_change_position(tmp_path, monkeypatch):
    reset_engine()
    engine = StateEngine(state_file=tmp_path / "state2.json")
    monkeypatch.setattr("app.validator.get_engine", lambda: engine)
    monkeypatch.setattr("app.validator.SEEN_IDS_FILE", tmp_path / "seen2.json")

    validate(_signal("DUP_TEST_004"))
    assert engine.get_position() == "LONG"
    validate(_signal("DUP_TEST_004"))
    # State unchanged — duplicate was rejected, no second set_position call
    assert engine.get_position() == "LONG"
    reset_engine()
