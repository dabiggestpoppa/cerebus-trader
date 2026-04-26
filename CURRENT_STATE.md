# CEREBUS Signal Guard — Current State

## Project Goal
TradingView signal → visual confirmation → state validator → execution → Heron/TradeSyncer copier.
EUR/USD M5 always-in-market flip system.

## Architecture Decisions (DO NOT CHANGE)
- Webhook = trigger only
- Chart visual/MCP = ground truth
- State validator = final authority (5-step)
- Agent does not decide trades
- Strategy decides. Validator enforces.
- CFDs: Heron. Futures: TradeSyncer. Signal layer never changes.

## Component Status
| Component | Status | Notes |
|-----------|--------|-------|
| Webhook server | [x] complete | FastAPI /webhook + all 5 endpoints live |
| Signal schema | [x] complete | strategy_rules.yaml, 5-step validator |
| State engine | [x] complete | position_state.json, atomic write, history |
| Validator (steps 1,3,4,5) | [x] complete | All 5 steps including vision stub |
| Vision confirmation | [x] stub | MCP integration ready (USE_MCP_VISION=true) |
| Trade logger | [x] complete | logs/signals.csv + logs/trades.csv |
| Docker | [x] complete | Dockerfile + compose, running on port 8080 |
| Tests | [x] complete | 34/34 passing |
| Hermes supervisor | [ ] placeholder | Phase 4 |
| Execution adapter | [ ] placeholder | Phase 3 |

## Last Completed
- Phase 1 complete: all 15 build steps done
- 34 tests passing
- Docker running on port 8080 (Docker Desktop uses 8000)
- All 6 test signals verified in signals.csv

## Next Action
- Phase 2: Add CEREBUS Pine truth panel to TradingView chart
- Set USE_MCP_VISION=true in .env and test with live chart
- See tasks/todo.md for Phase 2 queue

## Known Problems
- Docker Desktop uses port 8000 — cerebus-core binds to 8080 instead
- Vision is stub mode (chart_confirmed=false) until Phase 2 Pine panel added
- USE_MCP_VISION requires TradingView Desktop running with CDP on localhost:9222

## Last Commit
- Phase 1 stable: Signal Guard all tests passing

## Test Status
- [x] test_ghost_signal.py (5/5)
- [x] test_duplicate_signal.py (4/4)
- [x] test_flip_logic.py (8/8)
- [x] test_state_engine.py (12/12)
- [x] test_vision_confirm.py (5/5)
- Total: 34/34 passing
