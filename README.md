# CEREBUS Signal Guard

EUR/USD M5 always-in-market flip system — TradingView signal validation and execution pipeline.

## What It Does

TradingView fires a webhook alert → Signal Guard validates it through a 5-step engine → outputs ALLOW/REJECT/IGNORE → execution adapter places order on master → copier distributes.

## Core Principle

```
Webhook     = trigger only
Chart MCP   = ground truth (visual confirmation)
State engine = final authority
Broker      = execution only
```

## Quick Start

```bash
cp .env.example .env
# fill in .env values
docker compose up --build -d
curl http://localhost:8000/health
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Signal Guard Core — integrity + state engine + logging + Docker | In Progress |
| 2 | Visual Confirmation — Pine truth panel + MCP integration | Pending |
| 3 | Execution Integration — master account adapter | Pending |
| 4 | Hermes Supervisor — persistent monitor + reconcile + chat | Pending |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /webhook | TradingView alert receiver |
| GET | /health | Uptime + current position |
| GET | /state | Position + history |
| POST | /reconcile | Force position reconcile |
| GET | /logs | Last N signals |
| GET | /screenshot | Last chart screenshot |

## Signal Schema

```json
{
  "signal_id": "EURUSD_20260426_0930_BUY_001",
  "symbol": "EURUSD",
  "action": "BUY",
  "signal_type": "IMPULSE",
  "strategy_name": "CEREBUS_IMPULSE",
  "timestamp": "2026-04-26T09:30:00Z",
  "timeframe": "M5",
  "price": 1.08542,
  "session": "LONDON",
  "state_id": "EURUSD_20260426_0930_BUY_001"
}
```

## Test Signals

See [SETUP.md](SETUP.md) for curl commands covering all 6 test scenarios.
