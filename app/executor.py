"""Execution adapter — Phase 3 placeholder."""
import logging

logger = logging.getLogger(__name__)


def execute(signal_id: str, symbol: str, action: str, target_state: str) -> dict:
    logger.warning(
        "Executor called but Phase 3 not implemented. signal_id=%s action=%s",
        signal_id,
        action,
    )
    return {
        "status": "not_implemented",
        "signal_id": signal_id,
        "note": "Execution adapter is a Phase 3 placeholder.",
    }
