# CEREBUS Signal Guard — Claude Code Master Prompt

Paste this entire block as your first message in a new session.

---

You are building CEREBUS Signal Guard — a production-grade trading signal validation and execution system.

FIRST — read these files before writing a single line of code:
1. README.md
2. CURRENT_STATE.md
3. ARCHITECTURE.md
4. NEXT_ACTIONS.md
5. tasks/todo.md
6. tasks/lessons.md

RULES:
- Do NOT redesign the system
- Do NOT change architecture decisions listed in CURRENT_STATE.md
- Continue the next incomplete task only
- Implement one issue at a time
- Run tests before marking anything done
- Update CURRENT_STATE.md after every completed step
- Commit after every working module

ARCHITECTURE (never change):
- Webhook = trigger only
- Chart visual/MCP = ground truth
- State engine = final authority
- No AI trade decisions

If anything is unclear, write your assumptions in CURRENT_STATE.md before changing code.
Ask before any decision that affects architecture.

Priority order:
1. Keep existing architecture intact
2. Make code run
3. Add tests
4. Commit with clear message referencing issue number
