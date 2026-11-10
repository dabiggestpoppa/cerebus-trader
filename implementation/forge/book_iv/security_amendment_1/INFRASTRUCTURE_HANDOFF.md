# Infrastructure handoff — F-08 cross-platform hash-guard invariance

**Status: OPEN. Deferred by this rung. Owner: test infrastructure.**
**Authorization required: a separate change control decision.** BA-32 Rung 2 is
expressly forbidden from repairing these tests, editing baselines, touching
`.gitattributes`, changing SQL migration bytes or applying a global line-ending
conversion.

AM1-R27 `test_am1_r27_hash_guards_are_checkout_encoding_invariant` is **not
implemented**. It is not skipped, not xfailed, and not counted as a pass. The
amendment stands at 26/26 authorized drivers with R27 outstanding.

## 1. Observed defect

At `d21ebd0523db649c5b5764746edf0ffc6a94ec1e`, a Windows CRLF checkout fails 17
frozen hash guards; an LF checkout of the same commit passes them. The guards
compare a hash of *working-tree bytes* against a constant derived from bytes that
were read under LF. No governed content differs, so the failures are identity
artefacts, not contract breaches. They are nevertheless real red tests and must be
resolved systemically rather than explained away.

## 2. Inventory — the 17 affected tests

1. `tests/test_forge_ask_cerebus_answer.py::test_a74_frozen_upstream_hashes_routes_and_migrations_unchanged`
2. `tests/test_forge_ask_cerebus_context.py::test_c87_frozen_iv1_plan_contract_unchanged`
3. `tests/test_forge_ask_cerebus_context.py::test_c88_frozen_iv2_bundle_refs_trace_unchanged`
4. `tests/test_forge_ask_cerebus_context.py::test_c89_frozen_book_i_ii_iii_contracts_unchanged`
5. `tests/test_forge_ask_cerebus_context.py::test_c91_routes_migrations_and_provider_seam_unchanged`
6. `tests/test_forge_ask_cerebus_gateway.py::test_a55_same_golden_suite_runs_against_candidate_provider`
7. `tests/test_forge_ask_cerebus_gateway.py::test_a70_frozen_iv3_context_contract_unchanged`
8. `tests/test_forge_ask_cerebus_gateway.py::test_a71_routes_migrations_and_provider_seams_unchanged`
9. `tests/test_forge_intelligence_api.py::test_boundary_frozen_upstream_hashes_unchanged`
10. `tests/test_forge_market_data_provider_compatibility.py::test_hash_record_updated`
11. `tests/test_forge_market_data_provider_compatibility.py::test_only_authorized_frozen_files_changed`
12. `tests/test_forge_market_data_provider_compatibility.py::test_wp3b_contract_suite_green`
13. `tests/test_forge_market_data_provider_integration.py::test_routes_hash_unchanged`
14. `tests/test_forge_policy.py::TestScopeGuards::test_001_and_002_unchanged`
15. `tests/test_forge_retrieval.py::TestInternalMaterial::test_policy_module_is_untouched`
16. `tests/test_forge_setup_engine.py::TestT12Boundaries::test_cross_platform_hash_stability`
17. `tests/test_forge_setup_engine.py::TestT12Boundaries::test_frozen_upstream_hashes_unchanged`

This list is stable across both BA-32 rungs: the same 17 fail before and after
this amendment, and no new failure was introduced.

## 3. Current comparison mechanism (the defect)

Each guard reads the target file with `Path.read_text()` / `open()` in text mode
and hashes the decoded string (`hashlib.sha256(...encode())`). Python's text mode
translates `\r\n` to `\n` on read, but only for files it actually opens with
universal newlines *and* whose content is CRLF; a Windows checkout writes CRLF,
and several guards instead compare `git hash-object`-style digests of raw bytes
(`read_bytes()`), which differ directly. The two paths disagree, so the constant
is only valid for the checkout that produced it.

## 4. Canonical hashing proposal

Introduce one shared, single-point-of-truth helper — proposed:
`tests/_support/canonical_bytes.py` — exposing:

```python
def canonical_bytes(path: Path) -> bytes:      # decode + normalise line endings
def canonical_sha256(path: Path) -> str:       # sha256 over canonical bytes
def git_blob_sha1(path: Path) -> str:          # sha1("blob <len>\0" + canonical)
```

Rules the helper must implement:

1. Read raw bytes, then normalise `\r\n` → `\n` and a lone `\r` → `\n`.
2. Do **not** strip a trailing newline, re-encode, or touch non-ASCII bytes;
   decoding must be `utf-8` with `surrogateescape` so binary-adjacent content is
   preserved byte-for-byte.
3. Hash the normalised bytes (or the normalised git blob envelope), never the
   decoded string from platform-default text mode.
4. Existing constants are **re-derived once** under the canonical function in a
   dedicated commit that shows, for every guarded file, `old constant`, `new
   constant`, and the proof that the underlying file content is unchanged
   (`git diff --exit-code` on the guarded paths).
5. No guard may keep its own local hashing inline afterwards; all 17 call the
   helper.

## 5. Expected file scope

- New: `tests/_support/canonical_bytes.py` and one focused unit test for it
  (LF, CRLF, mixed, lone-CR, trailing-newline, non-ASCII fixtures held as byte
  literals so no checkout can alter them).
- Modified: the **17** guard call sites listed in §2, and the frozen constant
  modules they import (`tests/_fixtures/…` hash tables), constants re-derived
  only.
- Explicitly **not** modified: guarded product source, SQL migrations, books I–III,
  IV.1–IV.5 source, `.gitattributes`, repository-wide line endings.

## 6. Regression checks the next owner must demonstrate

1. LF checkout: full suite green.
2. CRLF checkout (`git config core.autocrlf true` in a scratch clone): full suite
   green, all 17 formerly failing guards passing.
3. Genuine content modification still fails: mutate one byte in a guarded file and
   confirm the relevant guard fails, on both checkouts.
4. Deleting or adding a guarded file still fails.
5. Git blob identity remains authoritative: `git hash-object` of an unmodified
   guarded file equals the recorded constant after the re-derivation, on both
   checkouts.
6. The helper's own fixtures prove `canonical_bytes(LF) == canonical_bytes(CRLF)`
   and `canonical_bytes` differs when content differs.
7. AM1-R27 then becomes implementable as
   `test_am1_r27_hash_guards_are_checkout_encoding_invariant`, and the amendment
   can be re-issued as COMPLETE at 27/27.

## 7. Why it was not repaired here

- The rung's exclusion is explicit: no rewriting of historical hash-guard tests,
  no baseline replacement, no migration byte changes, no global line-ending
  conversion, no `.gitattributes` edit without separate change control.
- Re-deriving 17 frozen constants alters governed identity evidence; doing it
  inside a security-repair rung would let a security change silently re-baseline
  the very artefact that proves no upstream drift.
- The failure does not affect any security assertion in this amendment: every
  driver in this rung is deterministic, environment-independent and passing, and
  the LF worktree at the same head reproduces a green suite.

## 8. Interim reporting rule

Until the handoff lands, this repository must report its regression as
`2582 passed, 17 failed (checkout encoding), 29 skipped` and must not report a
Windows full-suite PASS, a 27/27 amendment, or BG-A as unconditional.
