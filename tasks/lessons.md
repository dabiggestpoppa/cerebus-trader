# Lessons Learned

## Phase 1 Build

### 2026-04-26
- TradingView MCP uses stdio transport (not HTTP) — Python must call it via subprocess CLI
- data_get_pine_tables rows are " | "-delimited strings, not structured objects
- capture_screenshot saves to tradingview-mcp/screenshots/, not our project directory
- Must copy screenshot from MCP dir to our logs/screenshots/ directory
- CLI invocation: `node src/cli/index.js data tables -f <filter>` (not direct command file)
- CDP connection is always localhost:9222, hard-coded — TradingView Desktop must be running
- Pine indicators must be VISIBLE on chart for MCP to read their graphics data
- Atomic writes: use tempfile + os.replace(), not open(file, 'w') directly
- Always UTC for timestamps — datetime.now(timezone.utc), never datetime.now()
- Dedup window is 5 seconds — stores seen signal IDs with Unix timestamps, prune after 1 hour
- Ghost check is skipped in stub/fallback mode — not an error, just a warning log
### 2026-04-26 — Phase 2 Live Test
- pine_new() fails if Pine Editor is not already open — call ui_open_panel(pine-editor) first
- pine_smart_compile() reports v5 as outdated warning (severity 4) — use //@version=6
- chart_manage_indicator() cannot add custom Pine scripts, only built-in studies
- Use ui_find_element(Add to chart) to locate the button coords, then ui_mouse_click(x, y)
- pine_get_source() confirms what is actually in editor before clicking Add to chart
- data_get_pine_tables(study_filter=name) reads table.new() output — rows are pipe-delimited strings
- MCP screenshots save to tradingview-mcp/screenshots/ — vision_confirm.py copies them to logs/screenshots/
- Running service with python -m uvicorn works fine for testing without Docker
- Windows subprocess encoding: add encoding=utf-8 or errors=ignore to avoid cp1252 decode warnings
- Ghost signal rejection end-to-end: chart SELL + webhook BUY = REJECT with chart_confirmed=true
