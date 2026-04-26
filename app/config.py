import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

_RULES_FILE = Path("configs/strategy_rules.yaml")
_config_cache: dict[str, Any] | None = None


def load_rules() -> dict[str, Any]:
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if _RULES_FILE.exists():
        with open(_RULES_FILE) as f:
            _config_cache = yaml.safe_load(f) or {}
    else:
        _config_cache = {}
    return _config_cache


def reset_config() -> None:
    global _config_cache
    _config_cache = None


def get(key: str, default: Any = None) -> Any:
    return load_rules().get(key, default)


WEBHOOK_SECRET: str = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
USE_MCP_VISION: bool = os.getenv("USE_MCP_VISION", "false").lower() == "true"
TRADINGVIEW_MCP_DIR: str = os.getenv("TRADINGVIEW_MCP_DIR", "C:/Users/jefe/tradingview-mcp")
MCP_TIMEOUT_SECONDS: int = int(os.getenv("MCP_TIMEOUT_SECONDS", "8"))
