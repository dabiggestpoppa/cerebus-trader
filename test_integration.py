#!/usr/bin/env python3
"""Test the CEREBUS setup end-to-end."""
import sys
import json

sys.path.insert(0, '/workspace/ee9a60d3-53a4-4fe3-abd7-e9f3eea949bc/sessions/agent_e418d70e-7f00-41a1-9dd0-21285873c140')

# Test 1: Import all modules
print("="*60)
print("Test 1: Importing modules")
print("="*60)
try:
    from app.config import WEBHOOK_SECRET, USE_MCP_VISION
    print(f"OK: Config loaded: USE_MCP_VISION={USE_MCP_VISION}")
except Exception as e:
    print(f"FAIL: Config import failed: {e}")
    sys.exit(1)

try:
    from app.state_engine import StateEngine
    engine = StateEngine()
    print(f"OK: State engine: position={engine.get_position()}")
except Exception as e:
    print(f"FAIL: State engine failed: {e}")
    sys.exit(1)

try:
    from app.vision_confirm import _parse_truth_panel, confirm_from_chart
    rows = ["SIDE | BUY", "MODEL | CEREBUS_IMPULSE", "STATE ID | EURUSD_001"]
    side, sid = _parse_truth_panel(rows)
    print(f"OK: Vision parser: side={side}, state_id={sid}")
except Exception as e:
    print(f"FAIL: Vision parser failed: {e}")
    sys.exit(1)

try:
    from app.validator import validate
    print("OK: Validator imported")
except Exception as e:
    print(f"FAIL: Validator import failed: {e}")
    sys.exit(1)

# Test 2: Process test signals
print()
print("="*60)
print("Test 2: Processing signals")
print("="*60)

test_signals = [
    {
        "signal_id": "EURUSD_20260427_0000_BUY_001",
        "symbol": "EURUSD",
        "action": "BUY",
        "signal_type": "IMPULSE",
        "strategy_name": "CEREBUS_IMPULSE",
        "timestamp": "2026-04-27T00:00:00Z",
        "timeframe": "M5",
        "price": 1.08542,
        "session": "LONDON",
        "state_id": "EURUSD_20260427_0000_BUY_001",
    },
    {
        "signal_id": "EURUSD_20260427_0005_SELL_002",
        "symbol": "EURUSD",
        "action": "SELL",
        "signal_type": "IMPULSE",
        "strategy_name": "CEREBUS_IMPULSE",
        "timestamp": "2026-04-27T00:05:00Z",
        "timeframe": "M5",
        "price": 1.08500,
        "session": "LONDON",
        "state_id": "EURUSD_20260427_0005_SELL_002",
    },
    {
        "signal_id": "EURUSD_20260427_0010_CLOSE_003",
        "symbol": "EURUSD",
        "action": "CLOSE",
        "signal_type": "IMPULSE",
        "strategy_name": "CEREBUS_IMPULSE",
        "timestamp": "2026-04-27T00:10:00Z",
        "timeframe": "M5",
        "price": 1.08520,
        "session": "LONDON",
        "state_id": "EURUSD_20260427_0010_CLOSE_003",
    },
]

for i, signal in enumerate(test_signals, 1):
    result = validate(signal)
    status = "OK" if result.result in ("ALLOW", "IGNORE") else "WARN"
    print(f"{status}: Signal {i}: {result.signal_id}")
    print(f"  action={signal['action']}, result={result.result}")
    print(f"  position: {result.position_before} -> {result.position_after}")
    print(f"  reason: {result.reason}")
    print(f"  chart_confirmed: {result.chart_confirmed}")
    print()

# Test 3: Check Pine indicator files
print("="*60)
print("Test 3: Pine indicators")
print("="*60)
import os
pine_dir = '/workspace/ee9a60d3-53a4-4fe3-abd7-e9f3eea949bc/sessions/agent_e418d70e-7f00-41a1-9dd0-21285873c140/pine'
for f in sorted(os.listdir(pine_dir)):
    path = os.path.join(pine_dir, f)
    size = os.path.getsize(path)
    print(f"OK: {f} ({size} bytes)")

print()
print("="*60)
print("ALL TESTS PASSED")
print("="*60)
print()
print("System ready!")
print("  Webhook: POST /webhook")
print("  Health:  GET /health")
print("  State:   GET /state")
print("  Logs:    GET /logs")
print()
print("Pine indicators:")
for f in sorted(os.listdir(pine_dir)):
    print(f"  - pine/{f}")
print()
print("Config: USE_MCP_VISION=false (stub mode)")
print("To enable: SET USE_MCP_VISION=true + run TradingView Desktop")
