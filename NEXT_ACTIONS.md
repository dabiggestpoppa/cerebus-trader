# Next Actions

## Now
1. Build state_engine.py + tests/test_state_engine.py
2. Build validator.py (steps 1,3,4,5 — no vision)
3. Build main.py skeleton
4. Build trade_log.py
5. Build vision_confirm.py stub

## After Phase 1 Ships
- GitHub Issue #8: TradingView MCP inspection + integration
- GitHub Issue #11: Pine truth panel on chart
- GitHub Issue #12: Execution adapter — MatchTrader/TradeLocker
- GitHub Issue #14: Hermes supervisor container
- GitHub Issue #15: End-to-end test

## GitHub Issues (create on day 1)
- #1  Project structure + CLAUDE.md + state files
- #2  Signal schema (alert_schema.json + strategy_rules.yaml)
- #3  State engine (position_state.py + disk persistence + tests)
- #4  Validator steps 1,3,4,5 (no vision) + tests
- #5  FastAPI skeleton (all endpoints stubbed)
- #6  Trade logger (CSV)
- #7  Vision confirm placeholder + fallback mode
- #8  TradingView MCP inspection + integration
- #9  Dockerfile + docker-compose.yml
- #10 Full test suite — all passing
- #11 Pine truth panel (SIDE/MODEL/STATE_ID visible on chart)
- #12 Execution adapter — MatchTrader/TradeLocker
- #13 Heron integration test
- #14 Hermes supervisor container
- #15 End-to-end test: TV alert → ALLOW logged → master trade
