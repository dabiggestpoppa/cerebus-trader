# BLOC III.3 — CEREBUS MODEL RUNTIME — EVIDENCE

**Book:** III (CEREBUS Market Intelligence) · **Bloc:** III.3
**Authority:** BA-19 Rung 2 — operator-directed implementation
**Branch:** `forge` · **Starting head:** `37924ae2349cb33cd29caf3c7d444e2566b496b8`
**Scope:** Bloc III.3 only (common model contract, seven canonical
runtime families, model registry/dispatch, deterministic replay).
III.4/III.5/III.6 were not implemented.

Green tests alone do not constitute ratification; this document is the
evidence pack required by the frozen Book III gate. Ratification verdict
is in `RATIFICATION.md`.

---

## 1. Commit ladder (append-only, fast-forward)

| Rung | Commit | Contents |
|------|--------|----------|
| 1 — fixtures | `6e67cb2` | 10 fixture documents + deterministic generator + LF-normalized manifest + provenance README |
| 2 — modules | `c2f8ccd` | `app/forge/model_runtime/` — 13 modules (contract, errors, versions, registry, replay, 7 family evaluators) |
| 3 — tests | `25c748e` | `tests/test_forge_model_runtime.py` — 123 binding tests (T1–T12) |
| 4 — repairs | folded into rung 2 (see §9) | no post-test repair commits were required; every repair was root-cause and pre-commit |
| 5 — evidence | this document + `RATIFICATION.md` | evidence pack + verdict |
| 6 — CI record | follows after final-head push | final-head CI run id + result |

No amend, squash, rebase, reset or force-push was used. Tracked-tree
files outside `implementation/forge/book_iii/bloc_iii_3/`,
`app/forge/model_runtime/` and `tests/test_forge_model_runtime.py`
are untouched; the pre-existing untracked `.bu_tmp/` is preserved.

## 2. Foundation verification (Phase 0, this head)

- Local HEAD == `origin/forge` == the expected starting SHA at phase 0;
  fast-forward ancestry confirmed; tracked tree clean except the
  pre-existing untracked `.bu_tmp/`.
- Book I ratification intact; corpus freeze manifest matches HEAD;
  `git status corpus/` clean (asserted inside the suite, T12).
- Book II 50 frozen-file hashes and 23 planning pins re-verified
  (T12 `test_frozen_manifests_unchanged`).
- III.1 PASS/CLOSED; its 11 module hashes re-verify (T12
  `test_iii1_interfaces_unchanged`, baselines from III.3 PLAN §6).
- III.2 PASS/CLOSED; its 12 module hashes re-verify (T12
  `test_iii2_interfaces_unchanged`, same baselines).
- III.3 PLAN/ACCEPTANCE present at `37924ae` with a complete
  clause-to-test mapping; not modified.
- Migration baseline `[1, 2, 3, 4]` unchanged; no `005_*.sql` (T12
  `test_discover_migrations_unchanged`).
- `market_data: NOT_CONFIGURED` readiness seam byte-identical (T12
  `test_market_data_readiness_seam_unchanged`).
- Actual III.1/III.2 APIs inspected at source before implementation;
  the consumed-primitive list in PLAN §6 matched the checked-out APIs.
  No upstream interface discrepancy was found; no stop was required.

## 3. Source and module inventory

New package `app/forge/model_runtime/` (touches no ratified file):

| Module | Role |
|--------|------|
| `contract.py` | `ModelRequest`/`ModelOutput`, `DirectionBias`, `TypedLevel`, `AnchorStateRef`, `RangeLeftField`, `SubState`, `ExplanationFact`, `InputIdentity`, bounded `Layer`/`LevelKind`/`NoGoReason`/`WarningCode`/`ProductionAuthorization` vocabularies, quality aggregation, evidence union, canonical payload/hash helpers |
| `errors.py` | `MODEL_RUNTIME_CODES` — the closed refusal vocabulary (`MODEL_CONTRACT`, `MODEL_VERSION_UNAVAILABLE`, `INSTRUMENT_SCOPE_MISMATCH`, `INPUT_MEASUREMENT_MISSING`, `NO_CALCULATION`, `PRIOR_STATE_MISMATCH`, `RULE_NOT_MATERIALIZED`, `REPLAY_HASH_MISMATCH`, `DATA_QUALITY_BLOCKED`) |
| `registry.py` | eight explicit `(model_id, version)` entries (7 launch families + the pinned historical `DT_12_4PM` generation), exact-key dispatch, fail-closed resolution |
| `replay.py` | `run_model` (resolve → scope/binding → measurement coherence/quality → clock identity → prior state → evaluate → canonical hash), `verify_replay`, `compute_hash`, `canonical_payload`/`canonical_blob` |
| `eur_daily.py` | III.3.1 — seed → tier → distance/asymmetry → consumed states → news conditioning → rekey ladder → remaining distribution |
| `eur_weekly.py` | III.3.2 — Monday seed → tier → route → outer-node state → hour×tier timing → freeze → distribution |
| `eur_higher_order.py` | III.3.3 — quarter seed → D3 prior → M1 scale → M2 shaping → M3 resolution → local handoff; layer-conflict facts |
| `xau_game.py` | III.3.4 — L3/L2/L1 sub-states, promotion rules 68+8h→80 and 120+8h→132, 132 boundary, parked states, blind-touch separation |
| `btc_tracker.py` | III.3.5 — 19:00–03:00 source frame → native tier/AU/threshold/density → 03:00–19:00 slot × tier/range-left; weekly/monthly `UNRESOLVED` |
| `fib_range_birth.py` | III.3.6 — R15 gate → born range → A/B range → sequence → coordinates → path → structural rekey; R11 negative-evidence fact |
| `jpy_carry.py` | III.3.7 — per-pair role states, master/expression agreement, confirmation/veto, per-pair no-go, explicit DT reference |
| `versions.py` | `MODEL_RUNTIME_VERSION` |

Consumed read-only: III.1 `market_data` contracts and III.2
`measurements` contracts/registries (PLAN §6 primitive list). The
runtime never re-measures, never subclasses `Measurement` (T12
`test_no_measurement_redefinition`), never imports Book I/II authority
modules or the composition root (T12 `test_no_book1_authority_imports`).

## 4. Clause-to-test traceability (ACCEPTANCE T1–T12)

The frozen ACCEPTANCE contains **123 distinct executable test names**;
the rung brief's "124" counts the same set including the suite-file
token `test_forge_model_runtime` (the file itself). All 123 executable
names are implemented in `tests/test_forge_model_runtime.py` — the
committed name-extraction cross-check reports **0 missing, 0 weakened,
0 skipped, 0 xfail**.

| Group | Tests | Result |
|-------|-------|--------|
| T1 common contract | 20 | PASS |
| T2 registry/dispatch | 6 | PASS |
| T3 EUR Daily | 8 | PASS |
| T4 EUR Weekly | 7 | PASS |
| T5 EUR Higher Order | 8 | PASS |
| T6 XAU | 10 | PASS |
| T7 BTC Tracker | 10 | PASS |
| T8 Fib Range Birth | 9 | PASS |
| T9 JPY Carry | 10 | PASS |
| T10 replay/fixtures | 10 | PASS |
| T11 adversarial discipline | 13 | PASS |
| T12 boundaries | 12 | PASS |
| **Total** | **123** | **123 passed, 0 failed, 0 skipped, 0 xfail** |

## 5. Family-by-family acceptance results (golden cases)

69 deterministic golden cases: 57 produce outputs, 12 refuse with the
exact authored refusal code (validated bidirectionally by the
generator: an unexpected refusal or a missing refusal fails
generation).

| Family group | Cases | Refusals | Key acceptance evidence |
|--------------|-------|----------|-------------------------|
| `eur_daily_states` | 18 | 3 | seed T1/T2/T3 chain; >45p no-go at 46/52 with 45 still T3; five distinct ladder states (pairwise-distinct hashes); touch-only anchor refuses (`MODEL_CONTRACT`); event conditioning changes only conditional facts (shared geometry payloads byte-identical); subtractive budget 22−10=12; slot in/out range-left; clock-bound refusal `NO_CALCULATION` |
| `eur_weekly_states` | 6 | 0 | outer-node promotion only (inner node stays `ROUTE_OPEN`); frozen-after-completion stable across re-evaluation; prior-linked freeze carries the prior hash in identity; `destination_evidence = NOT_THIS_LAYER` as the only destination-shaped field; `RESEARCH` status travels with `EV.EUR.WEEKLY.TIER_RANGE.V1`; explicit `TIMING_UNRESOLVED` |
| `eur_higher_order_states` | 7 | 0 | declared D3 prior with evidence id; missing M1 ⇒ `UNRESOLVED` + parameter fact + no EV_M1 reference; unfinished side ⇒ `COMPLETION_CONDITIONAL`; two M3 checkpoints resolved; layer-conflict fact carries no score field; DEGRADED input propagates with `DEGRADED_INPUT` warning |
| `xau_promotion_states` | 9 | 0 | 68+8h ⇒ `PROMOTION_ELIGIBLE`/`ELIGIBLE_80` with `VALIDATED_SMALL_N` (N=48, EV linked); 68+7h ⇒ pending; 120+8h ⇒ `RESEARCH_PROMOTED_132` with `SMALL_N_RESEARCH_FLAG` (N=25, EV linked); 132 never yields 168 (fact + absence scan across all XAU outputs); parked stays parked with `PROMOTION_PARKED` and inactive coordinates; blind touch measures a route but confirmation stays `ABSENT`; rich L1/L2 leaves L3 `UNRESOLVED` (authority isolation); coordinates active without creating eligibility |
| `btc_tracker_states` | 11 | 3 | tier edges 749→T1, 750→T2, 3000→T3, 3001⇒ `ASIAN_RANGE_NO_GO`; AU/threshold/density facts and three active threshold levels; slot-conditioned range-left (measured in checkpoint, unresolved outside); weekly/monthly `UNRESOLVED`/`NOT_MATERIALIZED`; `BTC.GAME.L1_V1` request ⇒ `MODEL_VERSION_UNAVAILABLE`; foreign instrument and foreign calibration ⇒ `INSTRUMENT_SCOPE_MISMATCH`; no XAU/JPY module import (static scan) |
| `fib_range_birth_states` | 9 | 3 | declared-rule chains ALPHA/BETA/GAMMA/DELTA with active coordinates; `RULE_NOT_MATERIALIZED` refusal for unresolved R15 and for coordinates without a materialized rule; no-anchor case ⇒ `NOT_AUTHORIZED` + `RULE_NOT_MATERIALIZED` no-go and no invented anchor; coordinates-without-anchor ⇒ inactive levels; structural rekey with prior→successor mapping payload; FIB_132 coordinate touch is never a rekey; pivot origin refuses (`MODEL_CONTRACT`) and no pivot rule exists on the rule surface; R11 stance `NEGATIVE` in every Fib state |
| `jpy_carry_states` | 9 | 3 | three role states returned separately with role-map payloads; agree+confirm ⇒ `BASKET_AGREE_CONFIRM`; confirm absent ⇒ `BASKET_CONFIRM_ABSENT` (absence is never a veto); EURJPY disagreement ⇒ `BASKET_VETO`; master/expression conflict ⇒ `BASKET_CONFLICT`; per-pair `NATIVE_TIER_NO_GO`; DT levels present only when explicitly referenced and never active; equal-vote request ⇒ `MODEL_CONTRACT`; cross-pair path ⇒ `INSTRUMENT_SCOPE_MISMATCH`; role-map reassignment ⇒ `MODEL_CONTRACT`; authorization `MANUAL_OPERATOR` under every state |

Registry file: 8 registered entries resolve exactly (family, layer,
statefulness, clock-boundness, scope, calibration bindings, coordinate
set keys — all asserted against the frozen PLAN §5.2 matrix); 4
fail-closed refusal cases (`V2` versions, unknown model id, empty id).

## 6. Golden-fixture reproduction and provenance

- `python generate_fixtures.py --check` → **"OK 10 fixture files
  reproduce byte-identically (inputs, expectations and replay
  hashes)"** on this head. The generator reads the committed III.1/III.2
  fixture slices read-only; no wall clock, no randomness, no network.
- `FIXTURE_MANIFEST.json` records sha256 over LF-normalized content, so
  the manifest verifies identically on the CRLF worktree and the LF CI
  checkout (T12 `test_fixture_manifest_hashes_recorded` recomputes it).
- Provenance honesty: all bar rows/session instants/event records are
  `SYNTHETIC_FIXTURE` (deterministic structural-validation material,
  never empirical evidence); canonical constants enter only through the
  ratified III.2 registries and are labeled `CANONICAL_SOURCE_SLICE`
  where quoted (T12 `test_fixtures_labeled_historical`). The synthetic
  event record used by the EUR Daily conditioning case is explicitly
  labeled `SYNTHETIC_FIXTURE` at creation (III.2 GAP-4 discipline).

## 7. Registry/dispatch and replay determinism

- Dispatch is exact-key only. Unknown id, unknown version and empty
  version all raise `MODEL_VERSION_UNAVAILABLE`; there is no `latest`
  parameter, no default version and no silent fallback (T2 asserts the
  signature, the explicit-key registry and the behavior).
- The pinned historical generation `JPY.CARRY_GAME.L1_L3.V1 @
  DT_12_4PM` resolves to its own registered entry and **refuses
  dispatch** (`MODEL_VERSION_UNAVAILABLE`) because no authorized
  runtime exists for it — it never silently upgrades to `V1`.
- Replay: for every one of the 57 outputs, re-running the identical
  request reproduces the identical 64-hex hash, and every hash equals
  the committed value in `replay_hashes.json`. `compute_hash
  (canonical_payload(output))` recomputes each `output_hash`.
- Identity participates in the hash: changed calculation timestamp,
  changed clock identity, or a prior-state link each change the hash
  (T10 asserts all three).
- Order sensitivity: fact order preserves the state chain, and a
  frozen state reached through the prior-state field hashes
  differently from the same state computed fresh.
- Prior-state law: a prior from another model or version refuses with
  `PRIOR_STATE_MISMATCH`; a matching prior links with
  `PRIOR_STATE.LINKED` and its hash recorded in identity.
- Nondeterministic-replay attempts (mutated timestamp) are detected by
  `verify_replay` as `REPLAY_HASH_MISMATCH`.
- Cross-model isolation: instrument scope, calibration locality and
  per-pair path ownership each refuse with explicit codes; no family
  imports another family's module (static import discipline asserted).

## 8. Regression, integrity and CI

- Focused suite: **123 passed** (0 failed / 0 skipped / 0 xfail).
- Full repository regression: **1291 passed, 29 skipped** — the 29 are
  the pre-existing Postgres-gated skips recorded in the III.2 evidence
  (baseline 1168 + 123 = 1291; no regression, no new skip).
- Frozen integrity is asserted *inside* the suite (T12): Book I freeze
  manifest vs HEAD, corpus clean, Book II 50 hashes + 23 planning pins,
  III.1 11-module and III.2 12-module hash baselines — all unchanged
  after the suite runs.
- Final-head CI (post-push, head `4285812fa22ff813c4d103baf078eb5f34510cdb`):
  FORGE Tests run [`39523352791`](https://github.com/dabiggestpoppa/cerebus-trader/actions/runs/39523352791)
  **completed — success**; both workflow jobs green: `test` (Linux,
  LF checkout — fixture manifest + replay hashes verify identically)
  and `postgres` (live pgvector). No new skip; the Linux run re-checks
  the EOL-normalized manifest mechanism cross-platform.

## 9. Defect and repair history (root cause, no test weakened)

| # | Defect | Root cause | Repair |
|---|--------|-----------|--------|
| R1 | Any coordinate-bearing XAU/Fib case refused `MODEL_CONTRACT: level prices are Decimal, never float` | `TypedLevel(price=projection.projected_price)` passed a III.2 `NativePrice` where the contract requires a `Decimal` (two call sites: `fib_range_birth.py`, `xau_game.py`) | pass `projection.projected_price.value`; found by golden-case execution before rung 2 commit |
| R2 | Generator prior-dependency loop reported all cases pending | `break` left the stale `pending` list referenced | reassign before break |
| R3 | Generator decoded family inputs as raw dicts | `get_origin(X \| None)` returns `types.UnionType` but the branch tested `isinstance(origin, UnionType)` (an *instance* check) | `origin is UnionType` |
| R4 | Synthetic ramp bars fell outside the observation cutoff | `timedelta(step_minutes * index)` passed *days*, not minutes | `timedelta(minutes=…)` |
| R5 | Golden expectations mismatched implemented behavior in six places (weekly tier evidence refs, qualified coordinate ids, per-layer sub-state layers, presence of the `FIB.AB_RANGE` fact, measured range-left on the bound Fib path, `DEGRADED_INPUT` warning) | hand-authored expectations pre-dating the final implementations | expectations corrected to the canonically-correct implemented behavior; **no runtime logic was weakened to make a test pass** |
| R6 | `HO_NO_CALCULATION` fixture case unconstructible | III.2 refuses blocked measurements at construction ("a blocked measurement is refused, not emitted") | replaced with a DEGRADED-input propagation case; the blocked-at-construction law is asserted directly in T11 `test_nonfinal_source_data_blocks` |

Every repair was applied before its containing rung commit; no
post-commit repair commit was needed (rung 4 is therefore folded into
rung 2 and this record).

## 10. Carried gap dispositions (III.3-GAP-1…10 + upstream)

For each gap: what the runtime **permits**, what it **blocks**, what
**closes** it, and whether it **affects III.3 ratification**.

| Gap | Runtime permits | Runtime blocks | Closes when | Affects III.3 ratification? |
|-----|-----------------|----------------|-------------|------------------------------|
| III.3-GAP-1 (R15 not materialized; carries III.2-GAP-1) | research/explanation states behind the gate; structural rekey; coordinate facts | every eligibility-bearing request ⇒ `RULE_NOT_MATERIALIZED`; production setup generation; anchor invention; pivot fallback | governance materializes the exact R15 rule with canonical source + evidence and registers the anchor rule | **No** — the frozen plan allows explanation/research states meanwhile; blocks Fib production classification and downstream automation |
| III.3-GAP-2 (JPY parity; carries III.2-GAP-2) | role-aware basket states, agreement/conflict/veto facts, per-pair no-go | per-pair tier interpretation beyond canonical; parity claims | canonical per-pair tier/AU tables **and** operator parity approval | **No** — `MANUAL_OPERATOR` stands; blocks JPY automation parity claims |
| III.3-GAP-3 (XAU calibration shape; carries III.2-GAP-3) | evidence-linked promotion states preserving small-N flags and sample sizes | presenting promotions as universal rules/guarantees | a canonical frozen XAU tier table (if ever) is ratified | **No** — blocks universal-rule presentation only |
| III.3-GAP-4 (no event calendar; carries III.2-GAP-4) | event-conditioning states over synthetic labeled events; budget arithmetic | real-history news conditioning claims | operator supplies canonical EUR event-history slices | **No** — contract tests only |
| III.3-GAP-5 (HO statistics evidence-bound; carries III.2-GAP-6) | hierarchy/structure; statistics referenced by evidence ID only | emitting D3/unfinished/completion statistics as values; researcher-mode display | exact definitions + evidence attachments materialized | **No** — blocks Book IV numerical display |
| III.3-GAP-6 (no real bars; carries III.1 GAP-1 / III.2-GAP-5) | deterministic synthetic-labeled golden states | any empirical/performance claim from fixtures | operator supplies canonical bar slices | **No** — blocks performance claims by design |
| III.3-GAP-7 (sessions/live parity; carries III.1 GAP-2…5) | canonical sessions/periods; explicit `NO_CALCULATION` degradation | live-feed behavior claims | the same upstream operator decisions as III.1 | **No** |
| III.3-GAP-8 (BTC weekly/monthly anchors, new) | daily lineage fully; explicit `UNRESOLVED`/`NOT_MATERIALIZED` weekly/monthly interfaces | invented weekly/monthly anchors; any BTC-Game import | canonical weekly/monthly anchor/rekey definitions + evidence ratified | **No** — blocks BTC weekly/monthly classification |
| III.3-GAP-9 (XAU parked/quarter-zone doctrine, new) | bounded parked flag + L1 context states the runtime respects and never clears | setup eligibility emission (out of scope anyway) | III.5 materializes the setup-card implementation | **No** |
| III.3-GAP-10 (ST/P90 disclosure; re-states III.2 J8) | re-disclosure only | runtime representation of ST/P90 (no canonical MODEL objects exist) | III.5.9/III.5.10 | **No** — neither III.2 nor III.3 claims them |

Upstream carried registers (III.1 GAP-1…5, III.2-GAP-1…6) are folded
into the rows above where they lineage-match; none is a prerequisite
for III.3 ratification and none was silently closed. **No missing
research became executable model authority anywhere in this bloc.**

## 11. III.4 prerequisite-readiness recommendation

III.3 is ratifiable as implemented (see `RATIFICATION.md`), but III.4
must **not** be authorized merely because III.3 is green. Recommended
preconditions for an III.4 authorization decision:

1. Operator review of the family state vocabularies actually emitted
   (this evidence §5) versus the operator mental model — especially
   `BASKET_CONFIRM_ABSENT` vs veto semantics and the XAU research
   promotion standing labels.
2. Governance decision on GAP-1 (R15 materialization) and GAP-2 (JPY
   parity), since III.4/III.5 automation surfaces would otherwise
   inherit their blocks.
3. Confirmation that the III.4 planning packet (to be written under
   its own rung) consumes the committed interfaces in §3 without
   requiring changes to any III.3-ratified module.
4. A fresh Phase-0 foundation verification at the then-current head
   (freeze manifests, interface hashes including the new III.3
   module-hash baseline recorded in `RATIFICATION.md`).

*Generated as part of BA-19 Rung 2 institutional evidence. All fixture
data is synthetic/structural; nothing in this pack is empirical
performance evidence.*
