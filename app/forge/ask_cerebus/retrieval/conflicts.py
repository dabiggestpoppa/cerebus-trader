"""Identity-aware evidence conflict classification."""

from __future__ import annotations

from dataclasses import dataclass

from .enums import LimitationCode
from .refs import ClaimRef, Limitation


@dataclass(frozen=True)
class ConflictAssessment:
    limitations: tuple[Limitation, ...] = ()
    conflicting: tuple[str, ...] = ()
    incomparable: tuple[str, ...] = ()


def assess(claim_refs: tuple[ClaimRef, ...]) -> ConflictAssessment:
    limitations: list[Limitation] = []
    conflicting: list[str] = []
    incomparable: list[str] = []

    for index, left in enumerate(claim_refs):
        for right in claim_refs[index + 1:]:
            if left.identity_key is None or right.identity_key is None:
                continue
            if left.identity_key == right.identity_key:
                if (
                    left.result_value is not None
                    and right.result_value is not None
                    and left.result_value != right.result_value
                ):
                    conflicting.extend([left.claim_id, right.claim_id])
                    limitations.append(
                        Limitation(
                            LimitationCode.EVIDENCE_CONFLICT,
                            left.claim_id,
                            right.claim_id,
                        )
                    )
            else:
                incomparable.extend([left.claim_id, right.claim_id])
                limitations.append(
                    Limitation(
                        LimitationCode.INCOMPARABLE_EVIDENCE,
                        left.claim_id,
                        right.claim_id,
                    )
                )

    return ConflictAssessment(
        limitations=tuple(limitations),
        conflicting=tuple(dict.fromkeys(conflicting)),
        incomparable=tuple(dict.fromkeys(incomparable)),
    )


__all__ = ["ConflictAssessment", "assess"]
