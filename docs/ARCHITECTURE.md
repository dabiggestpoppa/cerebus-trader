# CEREBUS Signal Guard — Architecture Notes

See root ARCHITECTURE.md for the pipeline diagram.

## Key Design Decisions

### Why webhook-only triggers, not authority
TradingView Pine scripts can fire duplicate alerts, lag by a bar, or fire on indicator repaint.
The chart visual state is always the truth — it reflects what the strategy actually decided.

### Why atomic writes for state files
A crash during a JSON write would corrupt position_state.json. Using write-to-temp + os.replace()
guarantees the file is either the old version or the new version, never half-written.

### Why CSV for logging (not SQLite)
CSV is grep-able, diffable, and survives process crashes without corruption. Append-only CSV
with headers is the simplest audit trail. SQLite added in Phase 2+ if query patterns require it.

### Why stub vision in Phase 1
Building the full 5-step pipeline first with vision stubbed lets us test all the flip/dedup/ghost
logic end-to-end before adding the complexity of screenshot + OCR/MCP. Phase 2 drops in the real
vision layer without touching anything else.

### Why subprocess for MCP calls (not HTTP)
TradingView MCP uses stdio transport (JSON-RPC over stdin/stdout). There's no HTTP server.
The CLI wrapper (`node src/cli/index.js`) is the cleanest Python-callable interface.
