# Hash canonicalization plan V1 (F-08, BA-33)

Scope: the seventeen frozen-source hash guards inventoried in
`INFRASTRUCTURE_HANDOFF.md` §2. No product source, golden fixture, migration,
route, provider or IV.5/IV.6 module is in scope.

## 1. The defect, stated precisely

Each guard read a working-tree file and hashed the bytes it found:

```python
hashlib.sha256(path.read_bytes()).hexdigest()
```

The recorded constants are SHA-256 digests of the *committed* content, which is
stored LF. A checkout with `core.autocrlf=true` materialises the same governed
content as CRLF, so the measurement changed while the content did not. The
guards compared a checkout artefact against a content identity and reported
drift that had not happened.

This is not a source-integrity failure and not a test that "does not work on
Windows": it is a measurement that depended on an incidental encoding.

## 2. Two identities, never conflated

| Identity | Function | Meaning |
|---|---|---|
| Committed object identity | `committed_blob_id(path, revision="HEAD")` | The blob id Git recorded for the path at a revision — the repository's authoritative stored bytes. Independent of how a checkout materialised anything. |
| Checkout-independent content identity | `canonical_sha256(path)` | SHA-256 over the working-tree bytes after the approved text policy. This is what a frozen constant records. |
| Blob-envelope content digest | `canonical_git_blob_sha1(path)` | Git's `sha1("blob <len>\0" + content)` over canonical bytes. Equals `committed_blob_id` **only** when the committed blob is stored in canonical form; that equality is the single sanctioned bridge, and it is asserted rather than assumed. |

A normalized SHA-256 is never presented as a Git object id, and a raw CRLF
working-tree digest is never presented as a content identity.

## 3. Policy `CANONICAL_TEXT_V1`

Approved transformations: **`CRLF` → `LF`, nothing else.**

| Requirement | Implementation |
|---|---|
| Read working-tree bytes directly | `Path.read_bytes()`; never platform-default text mode |
| Normalize CRLF→LF | `data.replace(b"\r\n", b"\n")` |
| Lone CR | **preserved** — `LONE_CR_POLICY = "PRESERVED"`; a bare CR remains a content difference |
| Trailing newline presence | preserved exactly, including repeated trailing newlines |
| Non-newline bytes | preserved byte-for-byte, including multibyte UTF-8 |
| Binary / unclassified | `BinaryContentError` on any NUL byte; `UnsupportedPolicyError` for a suffix outside the governed text set |
| Unexpected encoding | `UnsupportedEncodingError` — never decoded lossily, never `errors="replace"` |
| Missing file | `MissingFileError` — never an empty digest |
| Whitespace / case / order | never stripped, folded or reordered |
| Disk | never modified |
| Policy version | `POLICY_VERSION = "CANONICAL_TEXT_V1"`; any other value raises `UnsupportedPolicyError` |

Governed suffixes: `.cfg .css .html .ini .js .json .md .py .sql .toml .ts .txt
.yaml .yml`.

### Why overbroad normalization is impossible

The policy accepts exactly one transformation, and a lone CR is not part of it.
An attacker cannot hide a content alteration behind normalization: changing a
character, a space, a line's presence or a line's order changes the canonical
bytes, and inserting or deleting a carriage return is itself detected (a lone CR
is preserved; a CRLF pair collapses to LF, so adding one to an LF-only line
still changes the result). The helper has no "strip whitespace", "decode
lossily" or "skip unreadable" mode.

## 4. Helper contract

`tests/_support/canonical_bytes.py` (test-only; imported by the guards as
`from tests._support.canonical_bytes import canonical_bytes, canonical_sha256`):

```python
POLICY_VERSION: str
LONE_CR_POLICY = "PRESERVED"
GOVERNED_TEXT_SUFFIXES: frozenset[str]

class CanonicalHashError(Exception)
class MissingFileError(CanonicalHashError)
class BinaryContentError(CanonicalHashError)
class UnsupportedEncodingError(CanonicalHashError)
class UnsupportedPolicyError(CanonicalHashError)
class NotCommittedError(CanonicalHashError)

canonical_bytes_of(data: bytes, *, policy=POLICY_VERSION) -> bytes
canonical_bytes(path, *, policy=POLICY_VERSION, require_governed_suffix=True) -> bytes
canonical_sha256(path, *, policy=POLICY_VERSION) -> str
git_blob_sha1_of(data: bytes) -> str
canonical_git_blob_sha1(path, *, policy=POLICY_VERSION) -> str
committed_blob_id(path, revision="HEAD") -> str
committed_blob_bytes(path, revision="HEAD") -> bytes
```

Acceptance tests live in `tests/test_canonical_bytes.py` (24 drivers): LF, CRLF,
mixed, lone CR, no/one/many trailing newlines, UTF-8, empty, NUL, invalid UTF-8,
unclassified suffix, unsupported policy, modified character, modified
whitespace, added line, removed line, missing file, untracked replacement, wrong
revision, blob-vs-content distinction, and the cross-encoding equality control.

## 5. Migration rule applied to the guards

For each of the seventeen call sites, only the measurement changes:

| | Before | After |
|---|---|---|
| Working-tree source | `read_bytes()` | `canonical_bytes()` |
| Comparison | `sha256(raw)` vs constant | `sha256(canonical)` vs the **same** constant |
| Files checked | unchanged | unchanged |
| Failure semantics | unchanged | unchanged |

No constant was re-derived, because the derivation audit (§2 of
`HASH_MIGRATION_LEDGER_V1.md`) showed all 65 constants already equal the
canonical digest *and* the committed-blob digest. Re-writing a constant would
have been the only way to weaken the guarantee; it was not needed and was not
done.

Migration guards (`001`–`004`) keep exact content identity: their intended
contract is the committed bytes, and canonical measurement of committed content
is exactly those bytes. No SQL file was touched. Route guards likewise keep
`app/forge/service/routes.py` at
`145757e0f2b19e76e2274018075c4b0fa7f0642498d4580e7e5fa8ec33d190af`.

## 6. What would have been refused

- Replacing a content assertion with a file-exists assertion — not done; every
  guard still compares a 64-hex content digest.
- Re-deriving a constant from the current working tree — not done; 65/65 old
  values retained and all reproduce.
- Skipping, xfail-ing or narrowing a guard — not done; 17/17 execute and assert.
- Global line-ending conversion or `.gitattributes` change — not done; the
  repository keeps its existing checkout policy.

## 7. Acceptance gates

1. All 17 guards pass under LF and under CRLF.
2. A genuine one-byte content change still fails the relevant guard.
3. `canonical_sha256(LF) == canonical_sha256(CRLF)` for every governed file.
4. `committed_blob_id == canonical_git_blob_sha1` for every governed file.
5. AM1-R27 passes and the original 26 amendment drivers stay green.
6. Product source unchanged; both CI jobs green at final HEAD.
