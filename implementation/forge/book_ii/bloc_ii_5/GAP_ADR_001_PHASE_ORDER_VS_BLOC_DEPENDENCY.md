# GAP/ADR-001 — Frozen phase grouping vs. dependency-ready Bloc execution

Status: **OPEN — recorded, decision required before Phase C begins**
Recorded: 2026-10-09 during Bloc II.5 execution (operator-authorized)
Scope: program build order only. Does **not** affect the dependency legality of
II.5 itself, and does not block II.5.
Decision authority: operator / CC (AGENTS change-control: only CC manages phase
gates via `tools/phase-gate.py --advance`).

## 1. The conflict (two frozen statements, both literal-illegal together)

**Statement A — phase grouping (frozen):**
`planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md` §10 "Program Build
Order" assigns blocs to Phases A–I. In that grouping:

- Phase A = I.1, I.2, II.1, II.2
- Phase B = II.3, II.4, I.3, I.4, I.5
- Phase C = Book III (III.1–III.6)
- Phase D = VI.1, VI.2, **II.5 Provider Ports/Fakes**, VI.4, II.6

So II.5 is grouped **after** Phase C (Market Intelligence Foundation).

**Statement B — dependency law (frozen):**

- `corpus/canonical/BOOKS_BLOCS_READINESS_GATE_V1.md` §1: "order within a Book
  by dependency (topological, not reading order)"; §2: a Bloc depends on its
  declared Book-internal predecessors and cross-Book prerequisites.
- Audit §10 preamble: "The implementation agent should not build eight Books
  serially as giant monoliths. **Execute dependency-ready Blocs.**"
- Book II plan bloc order: II.1 → II.2 → II.3 → II.4 → **II.5** → II.6 …
- II.5's declared predecessors are I.1–I.5 and II.1–II.4 — all ratified and all
  grouped in Phases A/B. Nothing in II.5's dependency closure is in Phase C.
- Book III's own dependency table (Book III plan) requires Book II's
  "Provider ports & observability contract" as an **input** — i.e. Phase C work
  depends on II.5, so deferring II.5 until after Phase C inverts a declared
  dependency arrow.

Under Statement A, starting II.5 now is out of phase order. Under Statement B,
II.5 was dependency-ready the moment II.4 ratified, and deferring it behind
Phase C delays a declared input to Phase C-adjacent work. Both statements are
inside the planning freeze (`60e0675`); both cannot be executed literally.

## 2. Root cause (same inconsistency, two shapes)

`planning/forge/GLX_FORGE_MASTER_BUILD_PLAN_V1.md` §Dependency order says
`I -> II -> III/VI foundations -> IV -> V -> VII -> VIII` (Book II completes
before Book III/VI foundations), while audit §10 interleaves Book II blocs
across Phases A/B/D/E and places Book VI blocs (VI.1, VI.2, VI.4) alongside
II.5/II.6 in Phase D — with Book III (Phase C) in between. A strict
"Book II first" reading contradicts the phase grouping; a strict phase reading
contradicts the Book-level dependency arrow and the readiness gate's
topological rule. The same root cause explains both shapes.

## 3. Resolution options (recorded, not decided)

- **A. Dependency-readiness governs; phase grouping is advisory.** Blocs
  execute as soon as their declared predecessors ratify. II.5 executes now
  (operator-authorized 2026-10-09); remaining phase groupings are re-derived
  topologically before Phase C starts.
- **B. Phase grouping is binding.** II.5 waits until Phase D. Consequence:
  Book III's declared "provider ports" input slips, and the audit's own
  "Execute dependency-ready Blocs" rule is violated for this bloc.
- **C. Split.** Cross-Book sequencing follows the Book-level arrow
  (I → II → III/VI …); within-Book execution follows dependency readiness.
  Book II blocs run in Book II topological order whenever their predecessors
  ratify; phases remain descriptive milestones.

## 4. Decision

OPEN. Operator/CC must choose before Phase C begins (and before any Phase D
grouped bloc — VI.1, VI.2, II.6 — is treated as gated or as free).

II.5 execution proceeds under explicit operator authorization of 2026-10-09.
That is consistent with options A and C, contradicts neither I.1–I.5 nor
II.1–II.4 ratifications, and pre-commits the program to no option: if B is
chosen later, II.5 is already complete and re-ratified rather than reworked
(its outputs are exactly what Book III declares as input).

## 5. Consequences if left unresolved

- Ambiguity about Phase C start legality and about whether the Phase D grouping
  (VI.1, VI.2, II.6) gates those blocs.
- No effect on II.5's predecessor chain, its evidence, or its ratification.
- No rework risk either way: II.5's deliverables are required by every option.

Recorded per operator directive of 2026-10-09 alongside the II.5 packet, so
Phase C's start is legally clean once the decision lands.
