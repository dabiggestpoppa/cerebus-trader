# Bloc III.3 — Deterministic Golden Fixtures

`BLOC_III_3.*.V1` — committed contract-test inputs for the CEREBUS Model
Runtime acceptance suite (`tests/test_forge_model_runtime.py`, clauses
T1–T12 of the frozen `ACCEPTANCE.md`).

## Inventory

| File | Fixture id | Contents |
|------|-----------|----------|
| `eur_daily_states.json` | `BLOC_III_3.EUR_DAILY_STATES.V1` | EUR Daily seed/tier states, the >45p source no-go boundary (45/46/52), the 100/125/132/168/185 ladder states, touch-only anchor refusal, event conditioning over one synthetic labeled event, slot in/out range-left |
| `eur_weekly_states.json` | `BLOC_III_3.EUR_WEEKLY_STATES.V1` | EUR Weekly route/promoted/inner-node/frozen states, frozen chaining through the prior-state field, explicit unresolved hour×tier timing |
| `eur_higher_order_states.json` | `BLOC_III_3.EUR_HIGHER_ORDER_STATES.V1` | Quarter seed → D3 prior (declared/none), evidence-bound parameter degradation, unfinished-side conditional completion, M3 checkpoint resolution, layer-conflict facts, DEGRADED input propagation |
| `xau_promotion_states.json` | `BLOC_III_3.XAU_PROMOTION_STATES.V1` | 68+8h→80 (VALIDATED_SMALL_N), 68+7h pending, 120+8h→132 (RESEARCH_FLAG_SMALL_N), the 132 boundary with no automatic 168, parked-stays-parked, blind-touch never confirming, L3 authority isolation, active coordinates |
| `btc_tracker_states.json` | `BLOC_III_3.BTC_TRACKER_STATES.V1` | Native tier edges 749/750/3000/3001, the >$3,000 Asian-range no-go, slot-conditioned range-left, unresolved weekly/monthly horizons, AU/threshold/density facts, BTC-GAME alias, foreign instrument/calibration refusals |
| `fib_range_birth_states.json` | `BLOC_III_3.FIB_RANGE_BIRTH_STATES.V1` | R15-gated declared-rule chains, RULE_NOT_MATERIALIZED refusals, structural rekey remapping, no-pivot-fallback behavior, coordinates-without-anchor rejection |
| `jpy_carry_states.json` | `BLOC_III_3.JPY_CARRY_STATES.V1` | Agree+confirm, confirm-absent, veto, master/expression conflict, per-pair no-go, explicit DT reference only, equal-vote refusal, cross-pair contamination, role-map reassignment refusal |
| `registry_dispatch_cases.json` | `BLOC_III_3.REGISTRY_DISPATCH_CASES.V1` | The eight registered `(model_id, version)` entries with bindings and scope, plus fail-closed refusals (unknown version, unknown model id, empty id) |
| `replay_hashes.json` | `BLOC_III_3.REPLAY_HASHES.V1` | sha256 over the sorted-key compact JSON of each golden `ModelOutput` payload (identity envelope + prior-state reference included) |
| `FIXTURE_MANIFEST.json` | — | sha256 of every JSON fixture except the manifest itself |

## Provenance honesty

Every fixture is labeled and stays inside its class:

* **`SYNTHETIC_FIXTURE`** — all bar rows, session/period instants and
  event records are deterministic generated values or reused committed
  III.2 synthetic slices. They are *structural validation material
  only*: never empirical market evidence and never citable for a
  performance claim (PLAN.md §10 GAP-4/5/6; ACCEPTANCE O3/O4).
* **`CANONICAL_SOURCE_SLICE`** — tier tables, spatial bands, promotion
  sample sizes, weekly outer nodes and evidence ids enter only through
  the ratified III.2 registries and frozen evidence cards, quoted
  verbatim with their source refs.
* **`replay_hashes.json`** — reproduction of these hashes is
  *determinism evidence* (contract clause T12), never empirical
  performance evidence.

## Determinism and regeneration

`generate_fixtures.py` is the single source of truth for both the
fixture documents and the `ModelRequest` reconstruction used by the
focused suite (`build_request`), so the generator and the tests can
never drift apart.

```
python generate_fixtures.py           # regenerate all fixture files
python generate_fixtures.py --check   # byte-identical reproduction + hash reproduction
```

The generator reads the committed III.1/III.2 fixture slices
**read-only**, uses no wall clock, no randomness and no network, and
writes sorted-key, LF-terminated JSON — so regeneration is
byte-identical on any platform. `FIXTURE_MANIFEST.json` records hashes
over LF-normalized content, so the manifest verifies identically on
Windows (CRLF worktrees) and Linux CI (LF checkouts).

The generator imports `app.forge.model_runtime`; from the
model-runtime commit onward it always reproduces the committed bytes
and the recorded replay hashes.
