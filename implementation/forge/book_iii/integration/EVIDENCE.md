# BOOK III INTEGRATION — EVIDENCE

**Book:** III · **Packet:** BA-23 Rung 2 (WP-1)
**Starting head:** `9f423a490d6b1d74be4f2bd03827593152103e4c`
**Mode:** append-only, evidence-first
**Suite:** `tests/test_forge_book_iii_integration.py` — **96 names, T1–T12**

## 1. Phase 0

| Check | Result |
|---|---|
| local HEAD == `origin/forge` == `9f423a4` | PASS |
| Book I corpus/freeze manifest | PASS |
| Book II 50 frozen hashes + 23 planning pins | PASS |
| III.1–III.6 module counts 11/12/13/13/16/14 = 79 | PASS |
| III.6 `IntelligenceGateway` public interface | PASS (`read`, `read_guarded`) |
| migrations `001`–`004`, no addition | PASS |
| `market_data: NOT_CONFIGURED` | PASS |
| `app/forge/service/routes.py` frozen (`145757e0…`) | PASS |
| three integration planning artifacts | PASS |
| starting CI `42313273434` | success (`test` + `postgres`) |

## 2. Feasibility gate (pre-implementation)

`FEASIBILITY_GATE.md` was committed before the suite. It classifies all 96
requirements (63 F1 direct, 25 F2 harness, 8 F3 bounded refusal, 0 F4
infeasible) and fixes the test-versus-gate rule: a bounded refusal is a pass; a
missing A-class capability keeps the system gate OPEN even at 96/96.

## 3. Acceptance reconciliation

| Measure | Result |
|---|---|
| frozen names implemented | **96 / 96** |
| T1–T12 group counts | 10 / 9 / 9 / 8 / 9 / 7 / 8 / 8 / 8 / 7 / 7 / 6 |
| missing, renamed, skipped, xfailed | **0 / 0 / 0 / 0** |
| unmapped clauses IN-1…IN-96 | **0** |
| focused result | **96 passed** in 0.99 s |

## 4. Fixtures

Ten integration fixtures plus manifest and frozen baseline (12 files) under
`implementation/forge/book_iii/integration/fixtures/`. `generate.py --check`
reports `fixtures reproduce byte-identically (12 files)` (LF-normalized
SHA-256). Cases cover EUR lineage, XAU promotion/ceiling, BTC tracker without a
game setup, Fib unresolved anchor, JPY roles, stand-down lock, missing provider,
pinned replay, card incompatibility and restricted exposure.

## 5. What the suite proves

- **Lineage (T1):** one `SnapshotKey` traverses III.1 bar → III.2 measurement →
  III.3 output → III.4 snapshot/ledger → III.5 evaluation → III.6 snapshot;
  identity, clock and measurement provenance survive; no stage re-derives an
  upstream value.
- **Quality (T2):** missing provider, non-final bar, blocked quality, unresolved
  clock and mixed cutoff produce their frozen codes; no-go is a valid state and
  is distinct from provider failure; stale is labelled `STALE`, carries no
  invented threshold and cannot support a live claim.
- **Families (T3):** EUR L1/L2/L3 remain three owners; XAU stays cross-layer;
  BTC tracker has no setup; Fib is research-only; JPY has no vote/aggregate.
- **Path (T4):** reversed delivery order changes identity, terminal reach keeps
  its path, intrabar ambiguity refuses, first-delivery timestamps survive,
  rekey requires a structural decision, range-left reconditions consumption.
- **Setup/no-go (T5):** stand-down forces `BLOCKED`; model state alone yields an
  `UNAVAILABLE` setup section; XAU caps below `ELIGIBLE`; Fib production is
  `BLOCKED`; JPY automation is false; no order/size/brokerage field exists;
  eligibility is carried verbatim.
- **Policy (T6):** denial precedes composition with a spy loader proving zero
  calls; denial is exactly `{"code": "EXPOSURE_FORBIDDEN"}`; anonymous and
  research reads are denied; a broken policy engine fails closed; every decision
  is audited.
- **Determinism (T7):** identical inputs give identical id/bytes; cutoff, model
  version and clock each change identity; decimals stay text; no float appears;
  component hashes are unique and ordered.
- **History (T8):** retained replay reproduces the hash; version drift refuses;
  missing inputs are `HISTORICAL_UNAVAILABLE`; the historical view is labelled
  and evidence status is preserved; no durability is claimed.
- **Cards (T9):** all three cards fail with exactly three machine errors; IDs are
  verbatim, statuses unpromoted, no `SET.*` minted, strict projection refuses
  `SCHEMA_INCOMPATIBLE`.
- **Consumer (T10):** the DTO is frozen, complete and non-authoritative; no
  recalculated value differs from the model output.
- **Security (T11):** cache hits re-authorize, principals do not share response
  entries, exposure change invalidates, refusals carry no payload, no module or
  network disclosure, responses are bounded.
- **Integrity (T12):** Book II 50-hash manifest, 79 module files, migration set,
  provider seam and no-production-claim all hold.

## 6. Integrity

No Book I, Book II, III.1–III.6, migration, route, provider-seam or frozen
planning file was modified. Git status before commit showed only the three new
integration artifacts, the fixture directory and the new test file; `.bu_tmp/`
is preserved.

## 7. Regression

| Check | Result |
|---|---|
| `pytest tests/test_forge_book_iii_integration.py -q` | **96 passed** |
| `pytest -q` | **1963 passed, 29 skipped**, exit 0 |
| `fixtures/generate.py --check` | 12/12 byte-identical |
| Book II freeze/manifest guards | 10 passed, 0 mismatches |

The 29 skips are pre-existing provider/environment skips from earlier blocs.

## 8. Defects found and repaired during this rung

| Defect | Root cause | Repair |
|---|---|---|
| harness could not load III.6 builders | wrong relative depth for `bloc_iii_6` | `parents[2]` |
| fixture script failed outside pytest | repo root absent from `sys.path` | explicit root insert |
| III.1 bar rejected at construction | `open_time == close_time` | open five minutes earlier |
| stand-down fixture crashed | `Classifications` has no `status` | emit `manual_only`/`automation_permitted` |
| section assertions failed | `payload()` returns dataclass sections | project through canonical JSON |
| identity helpers missing | not exported by the harness | aliased `snapshot_id`, `level` |
| live-claim assertion inverted | base fixture is provider-configured | assert the missing-provider facts |
| stale expected as refusal | no versioned policy exists | assert label + no invented threshold |
| false "order" disclosure | substring matched `ordered` fields | narrow execution-authority tokens |
| integrity count 50 | manifest contains one extra hash | require ≥50 and the route hash |
| suite-count guard 0 | earlier suites use test classes | count `def test_` anywhere |

No frozen test was weakened, renamed, skipped or converted to xfail.

## 9. Verdict and gate

**Integration verdict: PASS — synthetic/contract integration verified.**
**Book III end-to-end release gate: OPEN (PARTIAL).**

The suite proves the six blocs exchange valid, deterministic, policy-gated
facts. It does not prove live data, durability, exposure or production
readiness:

| A-class gap | Effect on the gate |
|---|---|
| III.4-GAP-10 / III.5-GAP-6 / III.6-GAP-1 durability | in-memory replay only; no cross-session history |
| III.5-GAP-4 trigger observation source | no `ELIGIBLE` positive path end to end |
| III.5-DEFECT-1 card schema | strict machine operations remain refused |
| III.6-GAP-2 provider | no current-live snapshot |

B/C/D/E gaps remain as classified in `DEPENDENCY_GATE_MATRIX.md`. No production
GO is claimed.
