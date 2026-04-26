import json
import pytest
from pathlib import Path
from app.state_engine import StateEngine


@pytest.fixture
def engine(tmp_path):
    return StateEngine(state_file=tmp_path / "position_state.json")


def test_initial_state_is_flat(engine):
    assert engine.get_position() == "FLAT"


def test_set_position_long(engine):
    result = engine.set_position("LONG")
    assert engine.get_position() == "LONG"
    assert result == {"from": "FLAT", "to": "LONG"}


def test_set_position_short(engine):
    engine.set_position("LONG")
    result = engine.set_position("SHORT")
    assert engine.get_position() == "SHORT"
    assert result == {"from": "LONG", "to": "SHORT"}


def test_set_position_flat(engine):
    engine.set_position("LONG")
    engine.set_position("FLAT")
    assert engine.get_position() == "FLAT"


def test_case_insensitive(engine):
    engine.set_position("long")
    assert engine.get_position() == "LONG"


def test_invalid_position_raises(engine):
    with pytest.raises(ValueError):
        engine.set_position("SIDEWAYS")


def test_persistence_across_reload(tmp_path):
    state_file = tmp_path / "position_state.json"
    e1 = StateEngine(state_file=state_file)
    e1.set_position("SHORT")
    e2 = StateEngine(state_file=state_file)
    assert e2.get_position() == "SHORT"


def test_atomic_write_produces_valid_json(engine):
    engine.set_position("LONG")
    with open(engine.state_file) as f:
        data = json.load(f)
    assert data["position"] == "LONG"
    assert isinstance(data["history"], list)


def test_history_tracks_transitions(engine):
    engine.set_position("LONG")
    engine.set_position("SHORT")
    engine.set_position("FLAT")
    history = engine.get_history()
    assert len(history) == 3
    assert history[0]["from"] == "FLAT"
    assert history[0]["to"] == "LONG"
    assert history[2]["to"] == "FLAT"


def test_history_capped_at_max(tmp_path):
    engine = StateEngine(state_file=tmp_path / "state.json")
    sides = ["LONG", "SHORT"] * 60
    for side in sides:
        engine.set_position(side)
    history = engine.get_history(n=200)
    assert len(history) <= 100


def test_corrupted_state_file_recovers(tmp_path):
    state_file = tmp_path / "position_state.json"
    state_file.write_text("not valid json")
    engine = StateEngine(state_file=state_file)
    assert engine.get_position() == "FLAT"


def test_missing_state_file_initializes_flat(tmp_path):
    engine = StateEngine(state_file=tmp_path / "nonexistent.json")
    assert engine.get_position() == "FLAT"
