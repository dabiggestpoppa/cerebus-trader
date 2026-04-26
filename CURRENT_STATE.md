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
| Vision confirmation | [x] Phase 2 code ready | MCP path wired, awaiting live chart test |
| Trade logger | [x] complete | logs/signals.csv + logs/trades.csv |
| Docker | [x] complete | Dockerfile + compose, running on port 8080 |
| Tests | [x] complete | 48/48 passing (incl. Phase 2 MCP tests) |
| Pine truth panel | [ ] needs chart setup | pine/CEREBUS_TruthPanel.pine written, add to TV |
| Hermes supervisor | [ ] placeholder | Phase 4 |
| Execution adapter | [ ] placeholder | Phase 3 |

## Last Completed
- Phase 2 code complete: vision_confirm.py MCP path + _parse_truth_panel
- Pine truth panel script written: pine/CEREBUS_TruthPanel.pine
- 14 new Phase 2 tests (48/48 total)
- Ghost signal e2e test with real MCP mocked — passing
- GitHub repo live: https://github.com/dabiggestpoppa/cerebus-trader
- All 15 issues created, #1-10 closed

## Next Action
1. Open TradingView Desktop on EURUSD M5
2. Add CEREBUS_TruthPanel.pine as indicator (Pine Editor → New → paste → Add to chart)
3. Verify panel shows SIDE/MODEL/STATE ID/VALID UNTIL in top-right
4. Set USE_MCP_VISION=true in .env
5. Send test webhook → verify chart_confirmed=true in response
6. Send ghost signal → verify REJECT with chart screenshot saved

## Known Problems
- Docker Desktop uses port 8000 — cerebus-core binds to 8080 instead
- Vision MCP path not yet live-tested (needs TradingView Desktop running)
- CEREBUS_TruthPanel.pine uses EMA crossover as placeholder bias logic
  Replace with real CEREBUS signal logic before Phase 3

## Last Commit
- Phase 2: MCP vision + Pine truth panel + 14 new tests

## Test Status
- [x] test_ghost_signal.py (5/5)
- [x] test_duplicate_signal.py (4/4)
- [x] test_flip_logic.py (8/8)
- [x] test_state_engine.py (12/12)
- [x] test_vision_confirm.py (5/5)
- [x] test_vision_mcp.py (14/14)
- Total: 48/48 passing
