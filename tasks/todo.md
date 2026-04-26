# CEREBUS Signal Guard — Task Tracker

## Phase 1 Status
- [x] #1  Folder structure + CLAUDE.md + state files
- [x] #2  Signal schema (strategy_rules.yaml)
- [x] #3  State engine + tests
- [x] #4  Validator steps 1,3,4,5 + tests
- [x] #5  FastAPI skeleton (all endpoints)
- [x] #6  Trade logger (CSV)
- [x] #7  Vision confirm placeholder + fallback mode
- [x] #8  TradingView MCP inspection (notes below)
- [ ] #9  Dockerfile + docker-compose.yml
- [ ] #10 Full test suite — all passing
- [ ] #11 Pine truth panel on chart (see Pine requirements)
- [ ] Docker smoke test + webhook test signals
- [ ] Git init + push

## Phase 2 Queue
- [ ] Add USE_MCP_VISION=true support (code exists, needs live test)
- [ ] Add Pine truth panel to CEREBUS indicator scripts
- [ ] Test MCP vision with live TradingView chart
- [ ] Ghost signal end-to-end test with real MCP

## Phase 3 Queue
- [ ] #12 Execution adapter — MatchTrader/TradeLocker
- [ ] #13 Heron integration test
- [ ] Live paper trade on master account

## Phase 4 Queue
- [ ] #14 Hermes supervisor container
- [ ] #15 End-to-end: TV alert → ALLOW logged → master trade

---

## TradingView MCP Integration Notes (Phase 2)

### Source: C:\Users\jefe\tradingview-mcp\

### How to call from Python (subprocess, recommended)
```python
import subprocess, json

result = subprocess.run(
    ["node", "src/cli/index.js", "data", "tables", "-f", "CEREBUS"],
    capture_output=True, text=True, timeout=8,
    cwd="C:/Users/jefe/tradingview-mcp"
)
data = json.loads(result.stdout)
# data = {success, study_count, studies:[{name, tables:[{rows:[str]}]}]}
```

### data_get_pine_tables response structure
Source file: src/core/data.js lines 404-430

```json
{
  "success": true,
  "study_count": 1,
  "studies": [
    {
      "name": "CEREBUS_IMPULSE",
      "tables": [
        {
          "rows": [
            "SIDE | BUY",
            "MODEL | CEREBUS_IMPULSE",
            "STATE ID | EURUSD_0930_BUY_001",
            "VALID UNTIL | 09:35"
          ]
        }
      ]
    }
  ]
}
```
Rows are " | "-delimited strings. Parse: `row.split(" | ")` → `[label, value]`.

### capture_screenshot response
Source file: src/core/capture.js lines 12-70

```json
{
  "success": true,
  "method": "cdp",
  "file_path": "C:/Users/jefe/tradingview-mcp/screenshots/tv_chart_2026-04-26T14-32-15.png",
  "region": "chart",
  "size_bytes": 412000
}
```
CLI: `node src/cli/index.js screenshot -r chart`

### Connection
- Always CDP localhost:9222 (hard-coded in src/connection.js)
- TradingView Desktop must be running with --remote-debugging-port=9222
- Auto-detects chart tab by querying http://localhost:9222/json/list

### Pine truth panel requirement (Phase 2 prerequisite)
The Pine indicator on the EURUSD M5 chart must render a table with these exact labels:
```pine
table.cell(truthPanel, 0, 0, "SIDE",        ...)  // row 0
table.cell(truthPanel, 0, 1, "MODEL",       ...)  // row 1
table.cell(truthPanel, 0, 2, "STATE ID",    ...)  // row 2
table.cell(truthPanel, 0, 3, "VALID UNTIL", ...)  // row 3
```
study_filter="CEREBUS" must match the indicator name.
Indicator must be VISIBLE on chart (not hidden) for MCP to read it.
