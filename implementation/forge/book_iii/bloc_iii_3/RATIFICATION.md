# BLOC III.3 — CEREBUS MODEL RUNTIME — RATIFICATION

**Verdict: RATIFIED — PASS (CLOSED)**

**Bloc:** III.3 (CEREBUS Model Runtime) · **Book:** III
**Authority:** BA-19 Rung 2 (operator-directed implementation)
**Ratifying head:** recorded by the rung-5 evidence commit on `forge`
**Predecessors:** Book I I.5 `RATIFIED (CLOSED)` at `2aafef9`·`a49426e`-era freeze; Book II `RATIFIED — CONTRACTS FROZEN`; III.1 `PASS (CLOSED)` at `2aafef9`; III.2 `PASS (CLOSED)` at `f9dce4f`
**Planning packet:** `37924ae` (PLAN + ACCEPTANCE, frozen; not modified)

This ratification covers the committed implementation of the common
model contract, the seven canonical runtime families
(III.3.1–III.3.7), the explicit `(model_id, version)`
registry/dispatch and deterministic replay — nothing else. III.4,
III.5 and III.6 are **not** authorized by this record.

---

## 1. Acceptance basis

- **123/123** frozen executable test names (T1–T12) implemented in
  `tests/test_forge_model_runtime.py`; **0 missing, 0 weakened, 0
  skipped, 0 xfail** (name-extraction cross-check against the frozen
  ACCEPTANCE recorded in `EVIDENCE.md` §4).
- **69 golden cases** (57 outputs + 12 exact-code refusals) reproduce
  byte-identically; committed replay hashes all re-verify.
- Full repository regression: **1291 passed, 29 pre-existing
  Postgres-gated skips** — no regressions.
- Adversarial validation covered all twelve required classes (wrong
  model/version/calibration, cross-asset contamination, nonfinal and
  low-quality data, missing evidence, R15 unresolved, XAU
  unsupported/parked promotions, BTC Tracker/Game contamination, JPY
  equal-vote, L3/L2/L1 leakage, historical-generation drift, incorrect
  rekey promotion, nondeterministic replay).
- Defect/repair history is documented root-cause in `EVIDENCE.md` §9;
  no test was ever weakened and no runtime rule was relaxed to obtain
  a pass.

## 2. Institutional-law conformity

**Observation → Measurement → Canonical interpretation → State
transition → Operator eligibility.**

- The runtime **interprets** III.1/III.2 measurement facts verbatim;
  it never re-measures, never subclasses `Measurement`, never
  redefines a canonical formula (asserted structurally, T12).
- Model state and `production_authorization` are separate immutable
  fields; the highest authorization any III.3 state can reach is
  `RESEARCH_ONLY` or `MANUAL_OPERATOR`. No component manufactures the
  authority of the next layer: no probability, confidence, win-rate,
  expectancy, prediction, signal, entry, position or execution field
  exists anywhere in the runtime or its serialized payloads (asserted
  by identifier, enum-value, field-name and payload-key scans).
- All refusals are explicit coded errors; there is no partial output,
  no silent fallback and no default version anywhere.
- Fixtures are structural validation material only
  (`SYNTHETIC_FIXTURE` / `CANONICAL_SOURCE_SLICE`); nothing in this
  bloc is empirical performance evidence.

## 3. Interface-integrity baseline (13 modules, LF-normalized sha256)

Recorded for future blocs as the III.3 module-hash baseline (same
method as III.1/III.2 §6 baselines):

`__init__.py 4d742dea…8311a` · `btc_tracker.py 60340930…f45a5` ·
`contract.py d0dc91f7…f9056` · `errors.py 9a29936d…a6f1e` ·
`eur_daily.py 4cb0fb57…da606` · `eur_higher_order.py 19621c53…038fe` ·
`eur_weekly.py f532d263…2f62d` · `fib_range_birth.py c64ebf90…54d2d` ·
`jpy_carry.py bde7aa38…f9c16` · `registry.py 3ce67bf4…67ca9` ·
`replay.py c6a14aca…3b611` · `versions.py 87823a05…9ea81` ·
`xau_game.py 3255d6d1…baa0c`

Any modification of these ratified modules requires a new authorization
and a new recorded hash set; downstream blocs must re-verify them at
their own Phase 0.

## 4. Frozen-surface conformity

Verified unchanged at this head and after the suite runs (T12):
Book I freeze manifest + clean corpus; Book II 50 contract hashes +
23 planning pins; III.1 11-module hashes; III.2 12-module hashes;
migration baseline `[1, 2, 3, 4]`; `market_data: NOT_CONFIGURED`
readiness seam; no network, no credentials, no corpus write, no
composition-root import.

## 5. Limitations carried (never silently closed)

III.3-GAP-1…10 remain open with dispositions in `EVIDENCE.md` §10,
together with the carried upstream registers (III.1 GAP-1…5,
III.2-GAP-1…6). The material blocks inherited by downstream work:

- **Fib production classification** stays blocked until R15 is
  materialized (GAP-1).
- **JPY automation parity** stays blocked; `MANUAL_OPERATOR` stands
  until canonical per-pair tables + parity approval (GAP-2).
- **BTC weekly/monthly classification** stays blocked until canonical
  anchor/rekey definitions exist (GAP-8); BTC Tracker ≠ BTC Game is
  enforced structurally.
- **XAU promotions** remain evidence-linked small-N states, never
  universal rules (GAP-3), and setup/confirmation doctrine remains
  III.5's (GAP-9).
- **ST/P90** golden representation is deferred to III.5.9/III.5.10
  (GAP-10); III.3 claims neither.

No missing research became executable model authority in this bloc.

## 6. III.4 stance

**Do not authorize III.4 merely because III.3 is green.** The
recommended preconditions are listed in `EVIDENCE.md` §11 (operator
review of emitted state vocabularies; governance decisions on GAP-1
and GAP-2; III.4 planning consumes the §3 interfaces read-only; fresh
Phase-0 verification including this bloc's module-hash baseline).

---

*BA-19 Rung 2 — Bloc III.3 closed as PASS on the evidence recorded in
this directory. Next authorization (III.4 planning) requires a
separate operator-directed rung.*
