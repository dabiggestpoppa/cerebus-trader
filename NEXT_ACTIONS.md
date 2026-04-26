# Next Actions

## NOW — Phase 2 Live Test (in progress)
1. Use TradingView MCP to inject CEREBUS_TruthPanel.pine onto BTC chart
   - pine_new(type="indicator")
   - pine_set_source(source=<pine/CEREBUS_TruthPanel.pine contents>)
   - pine_smart_compile()
   - pine_save()
   - Verify panel visible on chart via capture_screenshot()
2. Read truth panel via data_get_pine_tables(study_filter="CEREBUS")
   - Verify rows: SIDE / MODEL / STATE ID / VALID UNTIL
3. Set USE_MCP_VISION=true in .env, restart container
4. Send live test webhook → verify chart_confirmed=true in response
5. Send ghost signal (BTC chart says BUY, webhook says SELL) → verify REJECT + screenshot
6. Update CURRENT_STATE.md → git push

## Phase 3 Queue (after Phase 2 live test passes)
- #12 Execution adapter — MatchTrader/TradeLocker
- #13 Heron integration test
- Live paper trade on master account

## Phase 4 Queue
- #14 Hermes supervisor container
- #15 End-to-end: TV alert → ALLOW logged → master trade

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
