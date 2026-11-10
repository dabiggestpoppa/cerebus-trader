"""Canonical identities for governed test files (F-08).

Two identities are kept strictly apart:

* **Committed object identity** — ``committed_blob_id()`` asks Git for the blob
  id recorded in the commit. That is the repository's authoritative stored
  bytes and is unaffected by how a checkout materialised the working tree.
* **Checkout-independent content identity** — ``canonical_sha256()`` hashes the
  working-tree bytes after applying one explicitly approved text policy. It is
  *not* a Git object id, and ``canonical_git_blob_sha1()`` (a content digest in
  Git's blob envelope) must never be compared with ``committed_blob_id()``
  unless the file is committed as-is.

Policy ``CANONICAL_TEXT_V1``
----------------------------
1. Read the working-tree bytes directly. Never use platform-default text mode.
2. Normalise ``CRLF`` to ``LF`` only. Lone ``CR`` is *preserved* — a file that
   contains a bare carriage return is not silently rewritten, so an alteration
   cannot hide behind normalisation.
3. Preserve the presence or absence of a trailing newline, repeated trailing
   newlines, all whitespace, case and line order.
4. Preserve every non-newline byte, including multi-byte UTF-8 sequences.
5. Reject NUL-containing content as binary and reject content that is not valid
   UTF-8; neither is silently decoded or lossily replaced.
6. Only governed text suffixes are accepted; anything else is unclassified.
7. A missing file is an error, never an empty digest.
8. Nothing on disk is modified.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

POLICY_VERSION = "CANONICAL_TEXT_V1"

#: The only approved checkout-driven transformation.
NORMALIZED_SEQUENCE = b"\r\n"
REPLACEMENT_SEQUENCE = b"\n"

#: Documented, not accidental: a lone CR is a content difference.
LONE_CR_POLICY = "PRESERVED"

GOVERNED_TEXT_SUFFIXES = frozenset(
    {
        ".cfg",
        ".css",
        ".html",
        ".ini",
        ".js",
        ".json",
        ".md",
        ".py",
        ".sql",
        ".toml",
        ".ts",
        ".txt",
        ".yaml",
        ".yml",
    }
)


class CanonicalHashError(Exception):
    """Base class for canonical identity failures."""


class MissingFileError(CanonicalHashError):
    """The governed file does not exist on disk."""


class BinaryContentError(CanonicalHashError):
    """The file contains NUL bytes and has no text identity."""


class UnsupportedEncodingError(CanonicalHashError):
    """The file is not valid UTF-8, so it has no approved text identity."""


class UnsupportedPolicyError(CanonicalHashError):
    """The file suffix or the requested policy is outside the approved scope."""


class NotCommittedError(CanonicalHashError):
    """The file has no committed blob at the requested revision."""


def _require_policy(policy: str) -> None:
    if policy != POLICY_VERSION:
        raise UnsupportedPolicyError(
            f"policy {policy!r} is not approved; only {POLICY_VERSION!r} is"
        )


def canonical_bytes_of(data: bytes, *, policy: str = POLICY_VERSION) -> bytes:
    """Apply the approved text policy to ``data`` without touching disk."""

    _require_policy(policy)
    if b"\x00" in data:
        raise BinaryContentError("content contains NUL bytes; no text identity")
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedEncodingError(f"content is not valid UTF-8: {exc}") from exc
    return data.replace(NORMALIZED_SEQUENCE, REPLACEMENT_SEQUENCE)


def canonical_bytes(
    path: Path | str,
    *,
    policy: str = POLICY_VERSION,
    require_governed_suffix: bool = True,
) -> bytes:
    """Return the approved canonical bytes for one governed file."""

    _require_policy(policy)
    target = Path(path)
    if require_governed_suffix and target.suffix.lower() not in GOVERNED_TEXT_SUFFIXES:
        raise UnsupportedPolicyError(
            f"{target.suffix or '<none>'} is not a governed text suffix"
        )
    if not target.is_file():
        raise MissingFileError(f"governed file is missing: {target}")
    return canonical_bytes_of(target.read_bytes(), policy=policy)


def canonical_sha256(path: Path | str, *, policy: str = POLICY_VERSION) -> str:
    """SHA-256 over canonical bytes. This is a content identity, not a blob id."""

    return hashlib.sha256(canonical_bytes(path, policy=policy)).hexdigest()


def git_blob_sha1_of(data: bytes) -> str:
    """Git's blob object id for arbitrary content, without a repository."""

    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def canonical_git_blob_sha1(path: Path | str, *, policy: str = POLICY_VERSION) -> str:
    """Git blob envelope over canonical bytes.

    Equals ``committed_blob_id(path)`` exactly when the committed blob is stored
    with the same canonical content; that equality is the only sanctioned
    comparison between a content identity and an object identity.
    """

    return git_blob_sha1_of(canonical_bytes(path, policy=policy))


def _repository_root(path: Path) -> Path:
    probe = path if path.is_dir() else path.parent
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=probe,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise NotCommittedError(f"not inside a git work tree: {path}")
    return Path(result.stdout.strip()).resolve()


def committed_blob_id(path: Path | str, revision: str = "HEAD") -> str:
    """Return the blob id Git recorded for ``path`` at ``revision``."""

    target = Path(path).resolve()
    root = _repository_root(target)
    try:
        relative = target.relative_to(root).as_posix()
    except ValueError as exc:
        raise NotCommittedError(f"{target} is outside {root}") from exc
    result = subprocess.run(
        ["git", "rev-parse", f"{revision}:{relative}"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise NotCommittedError(
            f"{relative} has no committed blob at {revision}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def committed_blob_bytes(path: Path | str, revision: str = "HEAD") -> bytes:
    """Return the committed bytes for ``path`` at ``revision``.

    Used to prove that a constant's derivation came from committed content
    rather than from whatever the working tree happened to contain.
    """

    target = Path(path).resolve()
    root = _repository_root(target)
    relative = target.relative_to(root).as_posix()
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise NotCommittedError(f"{relative} is not committed at {revision}")
    return result.stdout
