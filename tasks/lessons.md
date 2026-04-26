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
