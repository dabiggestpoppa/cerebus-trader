import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

VALID_POSITIONS = {"LONG", "SHORT", "FLAT"}
STATE_FILE = Path("data/position_state.json")
MAX_HISTORY = 100


class StateEngine:
    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.state_file.exists():
            self._write({"position": "FLAT", "history": []})

    def get_position(self) -> str:
        return self._read()["position"]

    def set_position(self, side: str) -> dict:
        side = side.upper()
        if side not in VALID_POSITIONS:
            raise ValueError(f"Invalid position: {side}. Must be one of {VALID_POSITIONS}")
        state = self._read()
        prev = state["position"]
        state["position"] = side
        state["history"].append({
            "from": prev,
            "to": side,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if len(state["history"]) > MAX_HISTORY:
            state["history"] = state["history"][-MAX_HISTORY:]
        self._write(state)
        return {"from": prev, "to": side}

    def get_history(self, n: int = 20) -> list:
        return self._read()["history"][-n:]

    def _read(self) -> dict:
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
            if data.get("position") not in VALID_POSITIONS:
                data["position"] = "FLAT"
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"position": "FLAT", "history": []}

    def _write(self, data: dict) -> None:
        dir_ = self.state_file.parent
        with tempfile.NamedTemporaryFile(
            mode="w", dir=dir_, delete=False, suffix=".tmp"
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, self.state_file)


_engine: StateEngine | None = None


def get_engine(state_file: Path = STATE_FILE) -> StateEngine:
    global _engine
    if _engine is None:
        _engine = StateEngine(state_file)
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None
