# BOOK III / BLOC III.1 — MARKET DATA & CLOCK CONTRACTS — RATIFICATION.md

## RATIFICATION

Ratified: 2026-10-13
Authority: BA-17 Rung 2 (operator-directed implementation, Bloc III.1 ONLY)
Ladder (append-only from the authorized start SHA `6a14e78`): `6a14e78` →
`8a95b55` (fixtures) → `faea521` (package) → `1d331a7` (focused suite) →
`5127fa7` (repair A, superseded) → `8b43cb4` (repair B, implementation head;
CI run `38446736874` success, jobs `test` + `postgres`) → this
evidence/ratification rung. No amend, squash, rebase, reset or force-push;
remote ancestry verified fast-forward.

**Verdict: PASS — CLOSED (with carried gaps GAP-1…GAP-5)**

## Explicit ratification statements

1. **Frozen specification met.** PLAN.md Ch III.1.1–III.1.9 is implemented in
   full: canonical instrument identity with asset-native units and
   fail-closed aliasing; the exact frozen bar contract with deterministic
   duplicate resolution, explicit revisions, visible gaps and a finality
   gate; named-IANA clock identities with preserved `EST_NO_DST` artifact
   identity; lineage-declared research-day ownership (no calendar-date
   assumption); a versioned session registry bound to model/calibration
   versions with disclosed family gaps; exact boundary semantics including
   the canonical M5 `02:55` final bar; the exact 8-flag quality vocabulary
   with per-model block-vs-warn declarations; offline provider
   normalization over scripted feeds; and replay/streaming parity runners
   (EVIDENCE §1–§2).
2. **Every frozen acceptance clause is proven executable.** All T1–T11
   groups (A–O) map to passing tests in `tests/test_forge_market_data.py`
   (65/65); zero clauses unmapped, zero weakened, zero skipped, zero
   xfailed. Tests were gained beyond the frozen map (adversarial coverage),
   never lost (EVIDENCE §2).
3. **The Book III gate §Data/clock is satisfied at this layer:** session/
   DST/research-day tests pass; nonfinal/missing bars are handled
   explicitly and never fabricated; provider-normalization parity passes
   (K1–K3).
4. **Authority-model preservation holds.** III.1 emits normalized data
   facts only: no claim, evidence, setup or model object exists; no Book I
   authority import; no corpus write; synthetic fixtures are labeled at
   creation and structurally cannot satisfy an evidence reference;
   quarantined sources are absent (EVIDENCE §2 N-clauses, §7).
5. **Frozen surfaces untouched.** Book II 50/50 freeze hashes, 23/23
   planning pins (locally; existence-only in shallow CI — disclosed), the
   Book I freeze manifest and the corpus tree all verify after the suite;
   migrations remain `[1, 2, 3, 4]`; the `market_data: NOT_CONFIGURED`
   readiness seam is byte-identical and unwired; no Book I/II file appears
   in the ladder (EVIDENCE §4).
6. **Regression proof.** Full suite 1081 passed / 29 pre-existing skips;
   Book I and Book II suites green unchanged; CI green on the
   implementation head (EVIDENCE §3).
7. **Honesty of the repair record.** The EOL manifest defect (CRLF-hashed
   fixture manifest versus LF CI checkout) was detected before push,
   root-caused in the generator, fixed append-only, and verified against
   index blobs (CI-equivalent) before publication (EVIDENCE §9).

## Stop conditions

None of the seven authorization stop conditions was hit: no frozen
Book I/II contract needed change; no migration or seam rewiring was
required; every session/research-day rule implemented comes from a cited
canonical source; no market-data source or empirical claim was invented;
no unrelated strategy/runtime was touched; no new authority rule was
introduced; no material deviation from ACCEPTANCE.md occurred. The one
canonical ambiguity encountered — the JPY DT window's model binding — was
left unresolved and disclosed (GAP-2), per the plan's stop conditions,
rather than bound by assumption.

## Outstanding limitations (carried, not closed)

- GAP-1: no real historical bar slices in-repo; labeled synthetic fixtures
  only.
- GAP-2: session families without canonical definitions (London/MLR,
  weekly-seed intraday, DT binding, month/quarter boundary frames) remain
  disclosed gaps carried in registry coverage output.
- GAP-3: final-bar rules beyond the canonical M5 example are not
  generalized; other lineages fail to `NO_CALCULATION`.
- GAP-4: no concrete provider selection/wiring; seam stays
  `NOT_CONFIGURED`.
- GAP-5: live-style streaming is a scripted runner over fixtures; true
  live-feed parity is deferred with GAP-4.
- `STALE` is declared but never auto-set (no canonical staleness
  threshold exists in the corpus).
- Planning-pin content verification requires full history (CI is shallow).

## Downstream handoff

The frozen Book III order allows III.2 to begin when its required
contracts are frozen and available. **III.1 prerequisites are satisfied**
for III.2's data/clock inputs: normalized bars with finality + quality
flags, session and research-day ownership, clock identities and
native-unit instruments are implemented, versioned
(`MARKET_DATA_SCHEMA_V1`, `CLOCK_REGISTRY_V1`, `SESSION_REGISTRY_V1`) and
parity-tested (PLAN §12). Measurement-engine work itself is **not**
authorized by this record and requires its own operator packet.
