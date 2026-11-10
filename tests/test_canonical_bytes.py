"""Acceptance tests for the canonical hash helper (F-08).

These tests are the contract the seventeen historical guards rely on: one
approved content identity that follows governed content across checkout
encodings, and no identity at all when content genuinely differs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests._support.canonical_bytes import (
    LONE_CR_POLICY,
    POLICY_VERSION,
    BinaryContentError,
    MissingFileError,
    NotCommittedError,
    UnsupportedEncodingError,
    UnsupportedPolicyError,
    canonical_bytes,
    canonical_bytes_of,
    canonical_git_blob_sha1,
    canonical_sha256,
    committed_blob_bytes,
    committed_blob_id,
    git_blob_sha1_of,
)

LF_TEXT = b"alpha\nbeta\ngamma\n"
CRLF_TEXT = b"alpha\r\nbeta\r\ngamma\r\n"


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------------------
# encoding equivalence
# ---------------------------------------------------------------------------


def test_lf_and_crlf_produce_the_same_canonical_bytes(tmp_path):
    lf = _write(tmp_path / "lf.py", LF_TEXT)
    crlf = _write(tmp_path / "crlf.py", CRLF_TEXT)
    assert canonical_bytes(lf) == canonical_bytes(crlf) == LF_TEXT
    assert canonical_sha256(lf) == canonical_sha256(crlf)


def test_mixed_line_endings_normalize_to_the_lf_identity(tmp_path):
    mixed = _write(tmp_path / "mixed.py", b"a\r\nb\nc\r\nd\n")
    lf = _write(tmp_path / "lf.py", b"a\nb\nc\nd\n")
    assert canonical_bytes(mixed) == canonical_bytes(lf)


def test_lone_cr_is_preserved_and_is_a_content_difference(tmp_path):
    assert LONE_CR_POLICY == "PRESERVED"
    lone = _write(tmp_path / "lone.py", b"a\rb\n")
    lf = _write(tmp_path / "lf.py", b"a\nb\n")
    assert canonical_bytes(lone) == b"a\rb\n"
    assert canonical_sha256(lone) != canonical_sha256(lf)


# ---------------------------------------------------------------------------
# trailing newline and whitespace fidelity
# ---------------------------------------------------------------------------


def test_no_trailing_newline_is_preserved(tmp_path):
    assert canonical_bytes(_write(tmp_path / "a.py", b"alpha\nbeta")) == b"alpha\nbeta"


def test_single_trailing_newline_is_preserved(tmp_path):
    assert canonical_bytes(_write(tmp_path / "a.py", b"alpha\n")) == b"alpha\n"


def test_multiple_trailing_newlines_are_preserved(tmp_path):
    data = b"alpha\n\n\n"
    assert canonical_bytes(_write(tmp_path / "a.py", data)) == data


def test_whitespace_is_never_stripped_or_collapsed(tmp_path):
    data = b"  alpha\t \n\tbeta  \n"
    assert canonical_bytes(_write(tmp_path / "a.py", data)) == data


# ---------------------------------------------------------------------------
# non-ASCII, empty and binary content
# ---------------------------------------------------------------------------


def test_multibyte_utf8_is_preserved_byte_for_byte(tmp_path):
    data = "café — 日本語\n".encode("utf-8")
    assert canonical_bytes(_write(tmp_path / "a.py", data)) == data


def test_empty_file_has_a_stable_identity(tmp_path):
    empty = _write(tmp_path / "empty.py", b"")
    assert canonical_bytes(empty) == b""
    assert canonical_sha256(empty) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_nul_containing_content_is_rejected_as_binary(tmp_path):
    binary = _write(tmp_path / "blob.py", b"alpha\x00beta\n")
    with pytest.raises(BinaryContentError):
        canonical_bytes(binary)


def test_unexpected_encoding_is_rejected_not_replaced(tmp_path):
    latin1 = _write(tmp_path / "latin.py", b"caf\xe9\n")
    with pytest.raises(UnsupportedEncodingError):
        canonical_bytes(latin1)


def test_unclassified_suffix_is_rejected(tmp_path):
    unknown = _write(tmp_path / "payload.bin", b"alpha\n")
    with pytest.raises(UnsupportedPolicyError):
        canonical_bytes(unknown)


def test_unsupported_policy_is_rejected(tmp_path):
    governed = _write(tmp_path / "a.py", LF_TEXT)
    with pytest.raises(UnsupportedPolicyError):
        canonical_bytes(governed, policy="NORMALIZE_ALL_V0")
    with pytest.raises(UnsupportedPolicyError):
        canonical_bytes_of(b"alpha\n", policy="NORMALIZE_ALL_V0")


# ---------------------------------------------------------------------------
# change detection — the guarantee the guards exist for
# ---------------------------------------------------------------------------


def test_modified_character_changes_the_digest(tmp_path):
    original = _write(tmp_path / "a.py", LF_TEXT)
    modified = _write(tmp_path / "b.py", LF_TEXT.replace(b"beta", b"Beta"))
    assert canonical_sha256(original) != canonical_sha256(modified)


def test_modified_whitespace_changes_the_digest(tmp_path):
    original = _write(tmp_path / "a.py", b"alpha = 1\n")
    spaced = _write(tmp_path / "b.py", b"alpha  = 1\n")
    assert canonical_sha256(original) != canonical_sha256(spaced)


def test_added_line_changes_the_digest(tmp_path):
    original = _write(tmp_path / "a.py", LF_TEXT)
    added = _write(tmp_path / "b.py", LF_TEXT + b"delta\n")
    assert canonical_sha256(original) != canonical_sha256(added)


def test_removed_line_changes_the_digest(tmp_path):
    original = _write(tmp_path / "a.py", LF_TEXT)
    removed = _write(tmp_path / "b.py", b"alpha\nbeta\n")
    assert canonical_sha256(original) != canonical_sha256(removed)


def test_missing_file_is_an_error_not_an_empty_digest(tmp_path):
    with pytest.raises(MissingFileError):
        canonical_sha256(tmp_path / "absent.py")
    with pytest.raises(MissingFileError):
        canonical_bytes(tmp_path / "absent.py")


# ---------------------------------------------------------------------------
# Git object identity versus content identity
# ---------------------------------------------------------------------------


def test_committed_blob_matches_the_canonical_content_identity():
    routes = ROOT / "app/forge/service/routes.py"
    assert committed_blob_id(routes) == canonical_git_blob_sha1(routes)
    assert committed_blob_bytes(routes) == canonical_bytes(routes)


def test_content_identity_is_not_a_blob_object_id():
    routes = ROOT / "app/forge/service/routes.py"
    assert canonical_sha256(routes) != committed_blob_id(routes)
    assert len(committed_blob_id(routes)) == 40


def test_wrong_revision_is_an_error():
    routes = ROOT / "app/forge/service/routes.py"
    with pytest.raises(NotCommittedError):
        committed_blob_id(routes, revision="0" * 40)


def test_untracked_replacement_file_has_no_committed_identity(tmp_path):
    replacement = _write(tmp_path / "routes.py", b"# replacement\n")
    with pytest.raises(NotCommittedError):
        committed_blob_id(replacement)
    with pytest.raises(NotCommittedError):
        committed_blob_bytes(replacement)
    assert canonical_sha256(replacement) != canonical_sha256(
        ROOT / "app/forge/service/routes.py"
    )


def test_git_blob_sha1_follows_canonical_content_across_encodings(tmp_path):
    lf = _write(tmp_path / "lf.py", LF_TEXT)
    crlf = _write(tmp_path / "crlf.py", CRLF_TEXT)
    assert git_blob_sha1_of(LF_TEXT) == canonical_git_blob_sha1(lf) == canonical_git_blob_sha1(crlf)


def test_policy_version_is_explicit():
    assert POLICY_VERSION == "CANONICAL_TEXT_V1"
