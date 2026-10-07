"""FORGE request-correlation boundary.

II.1 introduces only the minimum needed:
- read/generate a safe, bounded request id;
- return the effective id on FORGE responses;
- do not trust arbitrary unbounded user input.

It does not retrofit correlation into the existing Signal Guard routes.
"""

from __future__ import annotations

import re
import secrets

# Safe bound for an inbound request id: short, alphanumeric plus hyphen/underscore.
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def parse_request_id(raw: str | None) -> str | None:
    """Return a safe inbound request id if present and well-formed, else None."""

    if not raw:
        return None
    if _REQUEST_ID_RE.fullmatch(raw):
        return raw
    return None


def generate_request_id() -> str:
    """Generate a bounded, non-guessable request id for FORGE responses."""

    token = secrets.token_hex(8)
    return f"fg-{token}"
