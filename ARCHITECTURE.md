# CEREBUS Signal Guard — Architecture

## Pipeline

```
TradingView Alert fires
        ↓
Webhook Receiver (FastAPI POST /webhook)
        ↓
[ STEP 1 ] Signal Integrity Check
  - duplicate ID?
  - valid fields?
  - timestamp fresh? (within 60s)
  - symbol correct?
        ↓
[ STEP 2 ] Chart Confirmation (Vision/MCP)
  - query TradingView MCP: data_get_pine_tables(study_filter="CEREBUS")
  - read Pine truth panel: SIDE / MODEL / STATE_ID
  - FALLBACK: MCP unavailable → webhook-only mode + log warning
        ↓
[ STEP 3 ] Ghost Signal Check
  - webhook_side == chart_side?
  - state_id matches?
  - IF mismatch → REJECT + log screenshot
        ↓
[ STEP 4 ] Flip Logic (State Engine)
  - current_position vs new target
  - BUY + not LONG  → LONG
  - SELL + not SHORT → SHORT
  - same direction → IGNORE
  - CLOSE → FLAT
        ↓
[ STEP 5 ] OUTPUT
  { "target_state": "LONG|SHORT|FLAT", "action": "EXECUTE|IGNORE|REJECT", "reason": "..." }
        ↓
Execution Adapter (master account) — Phase 3
        ↓
Heron (CFDs) / TradeSyncer (Futures)
        ↓
All accounts
        ↑
Hermes (monitor + reconcile + chat) — Phase 4
```

## Key Decisions

### Webhook is NOT the authority
The webhook is a trigger. It tells us to look at the chart. The Pine script truth panel on the chart is the ground truth. If the webhook says BUY but the chart shows SELL, we reject.

### State Engine is the final word
Even if chart + webhook agree, the state engine decides if the flip is needed. Already LONG + BUY = IGNORE.

### Atomic writes everywhere
All state files (position_state.json, seen_signal_ids.json) use write-to-temp + os.replace() to prevent corruption from crashes.

### Vision fallback
If TradingView MCP is unavailable, the system runs in webhook-only mode. All signals in this mode are tagged `chart_confirmed: false`. This is safe for Phase 1 but Phase 2 should require confirmed signals.

## Technology Stack
- Python 3.11
- FastAPI + Uvicorn
- Pydantic v2
- PyYAML
- Docker + docker-compose

## Ports
- 8000: FastAPI service

## Volumes
- ./data:/app/data — state persistence
- ./logs:/app/logs — signal and trade logs
- ./configs:/app/configs — strategy rules

## Phase 2 Vision Integration
TradingView MCP (C:\Users\jefe\tradingview-mcp) exposes:
- data_get_pine_tables(study_filter) → reads Pine table.new() output
- capture_screenshot() → saves chart screenshot

The truth panel Pine code must show: SIDE / MODEL / STATE_ID / VALID UNTIL
Connection: CDP localhost:9222 (TradingView Desktop must be running)
