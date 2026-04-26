# CEREBUS Signal Guard — Setup

## Requirements
- Docker + docker-compose
- Python 3.11+ (for local dev/test only)

## Quick Start

```bash
git clone <repo-url>
cd trading-system
cp .env.example .env
# Edit .env — fill in TRADINGVIEW_WEBHOOK_SECRET at minimum
docker compose up --build -d
curl http://localhost:8080/health
```

## Local Dev (without Docker)

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# fill in .env
uvicorn app.main:app --reload --port 8000
```

## Run Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Expose Webhook (TradingView → local)

```bash
ngrok http 8000
# Use the HTTPS URL in TradingView alert webhook settings
```

## Test Signals

```bash
# Valid BUY → should ALLOW
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-TradingView-Secret: your_secret" \
  -d '{
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
  }'

# Wrong symbol → should REJECT
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal_id":"TEST_GBPUSD","symbol":"GBPUSD","action":"BUY","signal_type":"IMPULSE","strategy_name":"CEREBUS_IMPULSE","timestamp":"2026-04-26T09:30:00Z","timeframe":"M5","price":1.25,"session":"LONDON","state_id":"TEST_GBPUSD"}'

# Stale timestamp → should REJECT
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"signal_id":"TEST_STALE","symbol":"EURUSD","action":"BUY","signal_type":"IMPULSE","strategy_name":"CEREBUS_IMPULSE","timestamp":"2026-01-01T00:00:00Z","timeframe":"M5","price":1.08,"session":"LONDON","state_id":"TEST_STALE"}'
```

## Reconcile

```bash
curl -X POST http://localhost:8080/reconcile
```

## View Logs

```bash
curl http://localhost:8080/logs?n=20
cat logs/signals.csv
```
