# BLOC III.4 — STATE, PATH & TRANSITION ENGINE — RATIFICATION

**Verdict: RATIFIED — PASS (CLOSED)**

**Bloc:** III.4 (State, Path & Transition Engine) · **Book:** III
**Authority:** BA-20 Rung 2 (operator-directed implementation)
**Ratifying head:** recorded by the closing CI-record commit on `forge`
**Predecessors:** Book I `RATIFIED (CLOSED)`; Book II `RATIFIED —
CONTRACTS FROZEN`; III.1 `PASS (CLOSED)`; III.2 `PASS (CLOSED)`;
III.3 `RATIFIED — PASS (CLOSED)` at `4285812`
**Planning packet:** `7ff2385` (PLAN + ACCEPTANCE, frozen; not modified)

This ratification covers the committed implementation of the state
snapshot contract, the twelve-kind transition vocabulary with
earned-transition guards, first-delivery ordering, the declared
failure/repair grammar, structural rekey, formal layer handoff,
conditional range-left, bounded stand-down states, the append-only
ordered transition history and the path invariants — nothing else.
III.5 and III.6 are **not** authorized by this record.

---

## 1. Acceptance basis

- **155/155** frozen executable test names from `ACCEPTANCE.md` are
  implemented in `tests/test_forge_state_engine.py`; **0 missing, 0
  weakened, 0 skipped, 0 xfail** (machine reconciliation: names in
  `ACCEPTANCE.md` minus names in the suite = ∅, and the relation is
  bidirectional).
- **156 tests execute**, because the frozen map references
  `test_first_delivery_order_reversal` under both T3 (C4) and T10 (J7);
  both are present and pass.
- **156 passed** focused; **1447 passed, 29 pre-existing skips** full
  repository regression (exactly +156, no regressions).
- **12 golden fixtures** plus manifest reproduce byte-identically; all
  12 manifest hashes re-derive (LF-normalized, cross-platform stable).
- Adversarial validation covered all sixteen required classes
  (EVIDENCE §4.1).
- Defect/repair history is documented root-cause in EVIDENCE §11; no
  test was weakened and no runtime rule was relaxed to obtain a pass.

## 2. Institutional-law conformity

**Observation → Measurement → Model interpretation → State transition →
Governed operator eligibility.**

- The engine **consumes** III.3 `ModelOutput` facts read-only; it never
  subclasses or re-derives `Measurement`/`ModelOutput` (T1, AST-asserted).
- `model_state` (descriptive) and `production_authorization`
  (classification) remain separate immutable fields; the engine defines
  no eligibility field and manufactures no downstream authority
  (T11).
- No probability, confidence, confluence, win-rate, expectancy,
  prediction or signal field exists anywhere — asserted by dataclass
  field-name scans, enum-value scans and payload-key scans (T11).
- A terminal outcome never erases the ordered path: both-side terminal
  reach retains its delivery sequence, reversed paths hash differently,
  and rekey closes/replaces the prior mapping with lineage (T3, T5, T10).
- A no-go is a stateful record that **locks** eligibility (T8), and no
  unearned transition succeeds (T2, T10).
- All refusals are explicit coded errors; there is no partial output, no
  silent fallback and no default version anywhere.
- Fixtures are structural validation material only
  (`SYNTHETIC_FIXTURE` / `CANONICAL_SOURCE_SLICE`); nothing in this Bloc
  is empirical performance evidence.

## 3. Interface-integrity baseline

Verified unchanged at this head (T12): Book I freeze manifest; Book II
50 contract hashes + 23 planning pins; III.1 11 modules; III.2 12
modules; III.3 13 modules; migration baseline `[1, 2, 3, 4]`;
`market_data: NOT_CONFIGURED` readiness seam.

New III.4 baseline recorded for downstream blocs — **13 modules**, full
hashes in `EVIDENCE.md` §9. Any modification of those modules requires a
new authorization and a new recorded hash set; downstream blocs must
re-verify them at their own Phase 0.

## 4. Frozen-surface conformity

No ratified file, module, manifest, container seam or migration was
modified. The III.4 planning packet (`PLAN.md`, `ACCEPTANCE.md`) is
byte-identical to its committed form at `7ff2385`. Legacy Signal Guard
(`app/state_engine.py`) was not touched, imported or reused. There is no
persistence, provider, API or execution surface in this Bloc.

## 5. Limitations carried (never silently closed)

III.4-GAP-1…12 remain open with dispositions in `EVIDENCE.md` §10,
together with the carried upstream registers (III.3-GAP-1…10,
III.2-GAP-1…6, III.1 GAP-1…5). The material blocks inherited by
downstream work:

- **Fib production transitions** stay blocked until R15 is materialized
  (GAP-1): `RANGE_ACTIVE` requires a `CANONICAL` rule.
- **JPY automation parity** stays blocked; `MANUAL_OPERATOR` stands
  (GAP-2), and any equal-vote/aggregate path is impossible by
  construction.
- **BTC weekly/monthly remapping** stays `UNRESOLVED` (GAP-8): `REKEY`
  is declared-but-unmaterialized for that family.
- **XAU promotions and band repairs** remain evidence-linked small-N
  states, never universal rules (GAP-3); 132 → 168 is a declared
  forbidden pair.
- **Durable transition-history storage** is undecided (GAP-10): only the
  logical append-only contract exists, and no migration was added.
- **ST/P90** representation remains deferred to III.5.9/III.5.10
  (GAP-11); III.4 claims neither.
- **Intrabar ordering** is bounded by supplied bar granularity (GAP-12):
  the engine refuses rather than inventing chronology.

No missing research became executable transition authority in this bloc.

## 6. Ratification gate

Per the frozen Book III gate §Evidence pack this Bloc is complete with:
`PLAN.md`, `ACCEPTANCE.md`, the implementation commit ladder, focused and
full test output, `EVIDENCE.md`, the known-gap list, and this
ratification record.

**BLOC III.4 — RATIFIED — PASS (CLOSED).**

**STOP.** III.5 and III.6 are not authorized by this record and require a
new operator handoff.
