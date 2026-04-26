# CEREBUS Signal Guard — Claude Instructions

## Rules (never violate)
- Plan mode for any 3+ step task (Shift+Tab)
- After every correction update tasks/lessons.md
- Never mark task done without passing test
- Commit to GitHub after every working module
- Update CURRENT_STATE.md before every push
- Atomic writes for all state files (temp → os.replace)
- Screenshot every signal — pass or fail

## Architecture (never change)
- Webhook = trigger only
- Chart visual/MCP = ground truth
- State engine = final authority
- Agent does not decide trades
- Strategy decides. Validator enforces.
- CFDs: Heron. Futures: TradeSyncer. Signal layer never changes.

## Hierarchy
Strategy → decides
Webhook → triggers inspection
Chart Visual → confirms truth
State Engine → final authority
Validator → enforces rules
Executor → places order (master only)
Copier → distributes (Heron / TradeSyncer)
Hermes → monitors + corrects
GitHub → project brain + handoff memory
Logs → audit trail
Claude Code → builds + improves

## File Locations
- Position state: data/position_state.json
- Seen signals: data/seen_signal_ids.json
- Signal log: logs/signals.csv
- Trade log: logs/trades.csv
- Screenshots: logs/screenshots/
- Config: configs/strategy_rules.yaml
- Accounts: configs/accounts.yaml

## Session Start Checklist
1. Read CURRENT_STATE.md
2. Read NEXT_ACTIONS.md
3. Read tasks/todo.md
4. Read tasks/lessons.md
5. Check open GitHub issues
6. Run tests before touching anything
