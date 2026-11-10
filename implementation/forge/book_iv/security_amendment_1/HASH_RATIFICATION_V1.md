# Hash canonicalization — ratification V1

**F-08 verdict: PASS (closed for its authorized scope).**
**AM1-R27: PASS.** Amendment 1 requirement set: **27/27**.

This document closes only what it measured. F-06 and F-07 remain partial
evaluation-coverage findings; they are not closed here and nothing in this
repair changes them.

## 1. What passed

| Gate | Result |
|---|---|
| The 17 historical guards, LF checkout | 17/17 pass |
| The 17 historical guards, CRLF checkout | 17/17 pass |
| Genuine content mutation still detected | 4/4 targets, both environments; 65/65 in-process |
| Removed guarded file still detected | 1/1, both environments |
| AM1-R27 `test_am1_r27_hash_guards_are_checkout_encoding_invariant` | PASS |
| AM1-R01–R26 (original 26 drivers) | 26/26 pass |
| Helper acceptance drivers | 24/24 pass |
| IV.1 / IV.3 / IV.4 / IV.5 / IV.6 | 60 / 93 / 72 / 86 / 112 pass |
| Book I retrieval / Book III integration | 72 / 96 pass |
| Full repository, LF checkout | 2624 passed, 0 failed, 29 skipped |
| Full repository, CRLF checkout | 2624 passed, 0 failed, 29 skipped |
| Product source changed | **none** |
| Constants re-derived | **none** (65/65 old == new) |
| Both CI jobs at final HEAD | see `hash CI receipt` section below |

## 2. Constants and source integrity

`HASH_MIGRATION_LEDGER_V1.md` reconciles all 65 governed files. For every one:
old constant == canonical digest == SHA-256 of the committed blob. The constants
were therefore already correct; only the measurement was wrong. No hash was
rewritten, so no integrity guarantee was silently reset, and the recorded values
keep their original meaning.

`git diff 46dd69c..HEAD -- app/` is empty: no product module, route, migration,
validator, oracle, scoring module or golden fixture changed. Migration bytes
`001`–`004` and `app/forge/service/routes.py` are byte-identical to the previous
head; their guards still assert exact content identity.

## 3. AM1-R27 — why this is a real pass

The driver, in `tests/test_forge_ask_cerebus_evaluation_amendment1.py`:

1. asserts all seventeen guards exist and that each guard module imports the
   canonical helper (no guard left on raw working-tree bytes);
2. re-derives every governed digest from canonical content against the frozen
   constants;
3. proves `canonical_bytes(opposite encoding) == canonical_bytes(this checkout)`
   per file, and that hashing the raw opposite-encoding bytes would *not* match —
   so the historical failure is real and the fix is what removes it;
4. proves a one-byte change to canonical content changes the digest;
5. keeps `committed_blob_id` distinct from `canonical_sha256` while asserting the
   sanctioned bridge `committed_blob_id == canonical_git_blob_sha1`;
6. executes all seventeen guards in the running environment and fails if any of
   them raises.

It would fail if a guard were reverted to raw bytes, if a constant were
rebaselined to a wrong value, if normalization became overbroad, or if a guard
were removed or turned into a shape-only assertion.

## 4. Status of the surrounding record

| Item | Status | Note |
|---|---|---|
| F-01 execution guidance | closed | unchanged by this rung |
| F-02 untrusted rendering | closed | unchanged |
| F-03 no-go consistency | closed | unchanged |
| F-04 proposed-prose disposition | closed | unchanged |
| F-05 numeric populations | closed | unchanged |
| F-06 CHAIN evidence path | **PARTIAL** | per `SUPPLEMENTAL_EVALUATION.md` §6; untouched here |
| F-07 refusal limitation coverage | **PARTIAL** | per §6; untouched here |
| F-08 hash guards | **CLOSED** | this document |
| AM1-R01–R27 | **27/27 implemented and passing** | R27 satisfied now |
| BG-A / BG-B | PASS (amended scope) | baseline for BG-A improves: no environment-dependent red tests remain |
| BG-C | **BLOCKED** | no provider, market, entitlement or retention work |
| `EV-GATE-01`–`13` | **OPEN** | unchanged; `EV-GATE-12` not discharged |

The earlier `RATIFICATION_SUPPLEMENT_V1.md` said PARTIAL because R27 was
outstanding. That verdict was correct at that head and is not rewritten; this
supplement records that the outstanding requirement is now satisfied.

## 5. Remaining known gaps

1. No Linux/macOS **local** run in this rung; Linux is evidenced only by CI.
   A Linux run is not required to close F-08 — the defect was environment
   format, and both encodings are now measured identically on Windows while CI
   exercises Linux — but it is not claimed as executed locally.
2. `.gitattributes` remains untouched; the repository keeps its current checkout
   policy. A future global line-ending change would still be a separate decision.
3. F-06 and F-07 remain open evaluation-coverage items with their own owners.

## 6. CI receipt

The final-head run is recorded in `HASH_CI_RECEIPT.md` (commit after this one) so
that this ratification names a run rather than asserting a green build. Both
jobs at the implementation head `3ad0b2e` and at the final documentation head are
reported there with conclusions.

## 7. Commit ladder

| Stage | Content |
|---|---|
| 1 | canonical helper and its acceptance drivers |
| 2 | seventeen historical guard call sites migrated |
| 3 | policy plan and constant ledger |
| 4 | AM1-R27 behavioural driver |
| 5 | reproduction (this rung's LF/CRLF/mutation evidence) |
| 6 | this ratification |
| 7 | CI receipt |

Append-only; fast-forward push; no amend, squash, rebase, reset or force.
