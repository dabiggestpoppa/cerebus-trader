"""Tests for Step 4 flip logic — all 6 scenarios from the build plan."""
import pytest
from unittest.mock import patch
from pathlib import Path

from app.state_engine import StateEngine, reset_engine, get_engine
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
def fresh_engine(tmp_path, monkeypatch):
    """Each test gets an isolated state engine."""
    reset_engine()
    engine = StateEngine(state_file=tmp_path / "state.json")
    monkeypatch.setattr("app.validator.get_engine", lambda: engine)
    monkeypatch.setattr("app.state_engine._engine", engine)
    # Isolate seen_ids
    monkeypatch.setattr("app.validator.SEEN_IDS_FILE", tmp_path / "seen.json")
    yield engine
    reset_engine()


def _signal(action, signal_id, state_id=None):
    sid = state_id or signal_id
    return {**VALID_SIGNAL, "signal_id": signal_id, "action": action,
            "state_id": sid, "timestamp": _now_iso()}


# Scenario 1: FLAT + BUY → ALLOW + OPEN
def test_flat_buy_opens_long(fresh_engine):
    assert fresh_engine.get_position() == "FLAT"
    result = validate(_signal("BUY", "TEST_BUY_001"))
    assert result.result == "ALLOW"
    assert result.target_state == "LONG"
    assert result.action_required == "OPEN"
    assert result.position_after == "LONG"


# Scenario 2: FLAT + SELL → ALLOW + OPEN
def test_flat_sell_opens_short(fresh_engine):
    result = validate(_signal("SELL", "TEST_SELL_001"))
    assert result.result == "ALLOW"
    assert result.target_state == "SHORT"
    assert result.action_required == "OPEN"
    assert result.position_after == "SHORT"


# Scenario 3: LONG + BUY → IGNORE
def test_long_buy_ignored(fresh_engine):
    fresh_engine.set_position("LONG")
    result = validate(_signal("BUY", "TEST_BUY_002"))
    assert result.result == "IGNORE"
    assert result.action_required == "NONE"
    assert result.position_after == "LONG"


# Scenario 4: SHORT + SELL → IGNORE
def test_short_sell_ignored(fresh_engine):
    fresh_engine.set_position("SHORT")
    result = validate(_signal("SELL", "TEST_SELL_002"))
    assert result.result == "IGNORE"
    assert result.action_required == "NONE"
    assert result.position_after == "SHORT"


# Scenario 5: LONG + SELL → ALLOW + FLIP
def test_long_sell_flips_to_short(fresh_engine):
    fresh_engine.set_position("LONG")
    result = validate(_signal("SELL", "TEST_FLIP_001"))
    assert result.result == "ALLOW"
    assert result.target_state == "SHORT"
    assert result.action_required == "FLIP"
    assert result.position_before == "LONG"
    assert result.position_after == "SHORT"


# Scenario 6: SHORT + BUY → ALLOW + FLIP
def test_short_buy_flips_to_long(fresh_engine):
    fresh_engine.set_position("SHORT")
    result = validate(_signal("BUY", "TEST_FLIP_002"))
    assert result.result == "ALLOW"
    assert result.target_state == "LONG"
    assert result.action_required == "FLIP"
    assert result.position_before == "SHORT"
    assert result.position_after == "LONG"


# Bonus: CLOSE from LONG → FLAT
def test_close_from_long_goes_flat(fresh_engine):
    fresh_engine.set_position("LONG")
    result = validate(_signal("CLOSE", "TEST_CLOSE_001"))
    assert result.result == "ALLOW"
    assert result.target_state == "FLAT"
    assert result.action_required == "CLOSE"


# Bonus: CLOSE from FLAT → IGNORE
def test_close_when_flat_ignored(fresh_engine):
    result = validate(_signal("CLOSE", "TEST_CLOSE_002"))
    assert result.result == "IGNORE"
