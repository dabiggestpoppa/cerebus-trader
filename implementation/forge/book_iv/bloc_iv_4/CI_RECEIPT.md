# BOOK IV / BLOC IV.4 — CI RECEIPT

**Contract:** `ASK_GATEWAY_CONTRACT_V1`
**Code/documentation head:** `413b9f34716793844edf709b9571ba46b5e87560`
**Workflow:** FORGE Tests
**Run:** `42530782457`
**URL:** https://github.com/dabiggestpoppa/cerebus-trader/actions/runs/42530782457

---

## 1. RESULT

| Job | Result | Duration | pytest summary |
|---|---|---|---|
| `test` | **SUCCESS** | 30s | **2,374 passed, 30 skipped** |
| `postgres` | **SUCCESS** | 1m9s | **2,403 passed, 1 skipped** |

PostgreSQL evidence steps also passed:

- `tests/test_forge_postgres_integration.py` — **19 passed**
- II.3 identity/session selection — **7 passed, 12 deselected**

---

## 2. COUNT RECONCILIATION

Local final tree: **2,375 passed, 29 skipped**.

CI `test`: **2,374 passed, 30 skipped**.

The one-test difference is:

`tests/test_forge_market_data.py::...::test_planning_pins_unchanged`

The CI checkout is shallow. The test skips with:

`planning-pin commit objects unavailable (shallow clone)`

This is the same single pass-to-skip classification identified in the starting
baseline (`2,303/29` local versus `2,302/30` CI). It is not coverage drift.
No frozen test was changed to normalize the count.

The `postgres` job has a different collection profile because its live database
environment executes the PostgreSQL/pgvector gates that are skipped locally.

---

## 3. BOUNDARY

The run used only the deterministic fake provider. No OpenRouter request,
credential, adapter, route or migration was introduced. CI success does not
close F3/F4 and does not mean IV.5 validated model output.

The final documentation-head run is recorded in the BA-29 final report after
this receipt is pushed.
