import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app import config
from app.state_engine import get_engine
from app.vision_confirm import confirm_from_chart

logger = logging.getLogger(__name__)

SEEN_IDS_FILE = Path("data/seen_signal_ids.json")
VALID_ACTIONS = {"BUY", "SELL", "CLOSE"}


@dataclass
class ValidationResult:
    signal_id: str
    result: str          # ALLOW | REJECT | IGNORE
    target_state: str    # LONG | SHORT | FLAT
    action_required: str # FLIP | OPEN | CLOSE | NONE
    reason: str
    position_before: str
    position_after: str
    chart_confirmed: bool
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


def validate(signal: dict) -> ValidationResult:
    now_ts = datetime.now(timezone.utc).isoformat()
    engine = get_engine()

    # Step 1 — Signal Integrity
    integrity = _check_integrity(signal)
    if integrity:
        return ValidationResult(
            signal_id=signal.get("signal_id", "unknown"),
            result="REJECT",
            target_state="NONE",
            action_required="NONE",
            reason=integrity,
            position_before=engine.get_position(),
            position_after=engine.get_position(),
            chart_confirmed=False,
            timestamp=now_ts,
        )

    # Step 2 — Chart Confirmation (stub in Phase 1)
    vision = confirm_from_chart(signal)

    # Step 3 — Ghost Signal Check
    ghost = _check_ghost(signal, vision)
    if ghost:
        return ValidationResult(
            signal_id=signal["signal_id"],
            result="REJECT",
            target_state="NONE",
            action_required="NONE",
            reason=ghost,
            position_before=engine.get_position(),
            position_after=engine.get_position(),
            chart_confirmed=vision.get("chart_confirmed", False),
            timestamp=now_ts,
        )

    # Step 4 — Flip Logic
    position_before = engine.get_position()
    action = signal["action"].upper()
    target_state, action_required, result = _flip_logic(action, position_before)

    if result == "ALLOW":
        engine.set_position(target_state)
        _mark_seen(signal["signal_id"])

    return ValidationResult(
        signal_id=signal["signal_id"],
        result=result,
        target_state=target_state,
        action_required=action_required,
        reason=_reason(result, action, position_before),
        position_before=position_before,
        position_after=engine.get_position(),
        chart_confirmed=vision.get("chart_confirmed", False),
        timestamp=now_ts,
    )


def _check_integrity(signal: dict) -> str | None:
    rules = config.load_rules()
    sid = signal.get("signal_id", "")
    symbol = signal.get("symbol", "").upper()
    action = signal.get("action", "").upper()
    strategy = signal.get("strategy_name", "")
    raw_ts = signal.get("timestamp", "")

    if not sid:
        return "missing_signal_id"
    if symbol not in [s.upper() for s in rules.get("allowed_symbols", [])]:
        return f"symbol_not_allowed:{symbol}"
    if action not in VALID_ACTIONS:
        return f"invalid_action:{action}"
    if strategy not in rules.get("allowed_strategies", []):
        return f"strategy_not_allowed:{strategy}"

    # Duplicate check
    window = rules.get("duplicate_window_seconds", 5)
    if _is_duplicate(sid, window):
        return f"duplicate_signal_id:{sid}"

    # Timestamp freshness
    max_age = rules.get("max_signal_age_seconds", 60)
    try:
        signal_dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - signal_dt).total_seconds()
        if age > max_age:
            return f"stale_timestamp:age={int(age)}s"
        if age < -10:
            return f"future_timestamp:age={int(age)}s"
    except (ValueError, TypeError):
        return f"invalid_timestamp:{raw_ts}"

    return None


def _check_ghost(signal: dict, vision: dict) -> str | None:
    webhook_action = signal.get("action", "").upper()
    confirmed_side = (vision.get("confirmed_side") or "").upper()
    vision_state_id = vision.get("state_id") or ""
    signal_state_id = signal.get("state_id", "")

    if not vision.get("chart_confirmed"):
        # Stub/fallback mode — skip ghost check, log warning
        logger.warning(
            "ghost_check_skipped: chart not confirmed for signal_id=%s",
            signal.get("signal_id"),
        )
        return None

    if webhook_action != confirmed_side:
        return f"ghost_signal:webhook={webhook_action},chart={confirmed_side}"
    if signal_state_id and vision_state_id and signal_state_id != vision_state_id:
        return f"state_id_mismatch:webhook={signal_state_id},chart={vision_state_id}"

    return None


def _flip_logic(action: str, position: str) -> tuple[str, str, str]:
    if action == "CLOSE":
        if position == "FLAT":
            return "FLAT", "NONE", "IGNORE"
        return "FLAT", "CLOSE", "ALLOW"
    if action == "BUY":
        if position == "LONG":
            return "LONG", "NONE", "IGNORE"
        return "LONG", "FLIP" if position == "SHORT" else "OPEN", "ALLOW"
    if action == "SELL":
        if position == "SHORT":
            return "SHORT", "NONE", "IGNORE"
        return "SHORT", "FLIP" if position == "LONG" else "OPEN", "ALLOW"
    return "NONE", "NONE", "REJECT"


def _reason(result: str, action: str, position: str) -> str:
    if result == "IGNORE":
        return f"already_{position}:action={action}"
    if result == "ALLOW":
        return f"valid_signal:action={action},from={position}"
    return "unknown"


def _is_duplicate(signal_id: str, window_seconds: int) -> bool:
    data = _load_seen()
    now = datetime.now(timezone.utc).timestamp()
    if signal_id in data:
        seen_at = data[signal_id]
        if now - seen_at < window_seconds:
            return True
    return False


def _mark_seen(signal_id: str) -> None:
    data = _load_seen()
    now = datetime.now(timezone.utc).timestamp()
    data[signal_id] = now
    # Prune entries older than 1 hour
    data = {k: v for k, v in data.items() if now - v < 3600}
    _write_seen(data)


def _load_seen() -> dict:
    try:
        SEEN_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if SEEN_IDS_FILE.exists():
            with open(SEEN_IDS_FILE) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _write_seen(data: dict) -> None:
    import os, tempfile
    SEEN_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=SEEN_IDS_FILE.parent, delete=False, suffix=".tmp"
    ) as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name
    os.replace(tmp_path, SEEN_IDS_FILE)
