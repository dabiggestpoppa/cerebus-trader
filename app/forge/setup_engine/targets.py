"""Ordered targets and governed promotion (Ch III.5.5).

Target order is the **declared** canonical order, never a sort by price,
distance or convenience.  A deeper coordinate is never auto-active: a
target becomes active only through its declared promotion condition,
which requires a real III.4 transition reference and an authority
reference.  III.4's first-delivery order and conditional range-left are
consumed verbatim — this module never re-sorts a path.
"""

from __future__ import annotations

from dataclasses import replace

from app.forge.state_engine.delivery import DeliveryPath

from .contracts import PromotionCondition, SetupTarget, TransitionRef
from .errors import SetupRefusalCode, SetupContractError, TargetPromotionRefused

__all__ = [
    "first_delivery_order",
    "order_targets",
    "promote_target",
    "validate_declared_targets",
]


def order_targets(targets: tuple[SetupTarget, ...]) -> tuple[SetupTarget, ...]:
    """Return targets in their declared canonical order (stable, never sorted)."""

    for target in targets:
        if not isinstance(target, SetupTarget):
            raise SetupContractError("targets are typed SetupTarget values")
    return tuple(sorted(targets, key=lambda target: target.declared_order_index))


def validate_declared_targets(
    declared: tuple[SetupTarget, ...], requested: tuple[str, ...]
) -> None:
    """Refuse a target that the card did not declare (F12)."""

    allowed = {target.target_id for target in declared}
    for target_id in requested:
        if target_id not in allowed:
            raise TargetPromotionRefused(
                "target is not declared by the card: "
                f"{target_id} ({SetupRefusalCode.TARGET_NOT_DECLARED.value})"
            )


def promote_target(
    target: SetupTarget,
    *,
    condition: PromotionCondition | None = None,
    transition_ref: str | None = None,
    transitions: tuple[TransitionRef, ...] = (),
) -> SetupTarget:
    """Activate a target only through its declared, authorized condition."""

    declared = condition or target.promotion
    if declared is None:
        raise TargetPromotionRefused(
            "target has no declared promotion condition "
            f"({SetupRefusalCode.TARGET_PROMOTION_WITHOUT_AUTHORITY.value})"
        )
    if not isinstance(declared, PromotionCondition):
        raise SetupContractError("a promotion condition is typed")
    if not declared.authority_ref:
        raise TargetPromotionRefused(
            "promotion condition carries no authority "
            f"({SetupRefusalCode.TARGET_PROMOTION_WITHOUT_AUTHORITY.value})"
        )
    if not transition_ref:
        raise TargetPromotionRefused(
            "promotion requires a transition reference "
            f"({SetupRefusalCode.TARGET_PROMOTION_WITHOUT_AUTHORITY.value})"
        )
    known = {transition.transition_id for transition in transitions}
    if transition_ref not in known:
        raise TargetPromotionRefused(
            "promotion transition is not among the recorded transitions "
            f"({SetupRefusalCode.TARGET_PROMOTION_WITHOUT_AUTHORITY.value})"
        )
    if target.confirmation_only:
        raise TargetPromotionRefused(
            "a confirmation/evidence state is never promoted to a core target "
            f"({SetupRefusalCode.FORBIDDEN_PROMOTION.value})"
        )
    return replace(target, active=True, transition_ref=transition_ref)


def first_delivery_order(path: DeliveryPath) -> tuple[str, ...]:
    """The III.4 recorded delivery order, verbatim (never re-sorted)."""

    if not isinstance(path, DeliveryPath):
        raise SetupContractError("first-delivery order consumes a III.4 DeliveryPath")
    return tuple(record.target_id for record in path.deliveries)
