"""Multi-model instrument and JPY basket views. No confluence, no averages."""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Mapping, Sequence

from app.forge.intelligence_api.contracts import (
    BasketPair,
    BasketView,
    Classifications,
    InstrumentView,
    LayerSection,
    Snapshot,
    UnavailableSection,
)
from app.forge.intelligence_api.errors import RefusalError
from app.forge.intelligence_api.serialization import content_hash
from app.forge.intelligence_api.versions import (
    BASKET_VIEW_SCHEMA_VERSION,
    INSTRUMENT_VIEW_SCHEMA_VERSION,
)
from app.forge.model_runtime.contract import Layer

CANONICAL_LAYER_ORDER = (Layer.L3, Layer.L2, Layer.L1)
BASKET_ROLES = ("DRIVER", "CONFIRMATION_VETO")


def _section_order(layers: Iterable[Layer]) -> tuple[Layer, ...]:
    present = set(layers)
    return tuple(layer for layer in CANONICAL_LAYER_ORDER if layer in present)


def compose_instrument_view(
    *,
    instrument_id: str,
    snapshots: Mapping[Layer, Snapshot],
    layers: Sequence[Layer] | None = None,
    classifications: Classifications | None = None,
) -> InstrumentView:
    requested = tuple(layers) if layers is not None else CANONICAL_LAYER_ORDER
    for layer in requested:
        if layer not in CANONICAL_LAYER_ORDER:
            raise RefusalError("MALFORMED_REQUEST", detail="not_a_layer")
    for layer, snapshot in snapshots.items():
        if snapshot.key.instrument_id != instrument_id:
            raise RefusalError("MALFORMED_REQUEST", detail="cross_asset_leak")
        if snapshot.key.layer is not layer:
            raise RefusalError("MALFORMED_REQUEST", detail="layer_substitution")

    ordered = tuple(layer for layer in _section_order(requested) if layer in snapshots)
    sections: list[LayerSection] = []
    unresolved: list[UnavailableSection] = []
    for layer in CANONICAL_LAYER_ORDER:
        if layer not in requested:
            continue
        snapshot = snapshots.get(layer)
        if snapshot is None:
            unresolved.append(
                UnavailableSection(section="state", reason=f"LAYER_{layer.value}_UNAVAILABLE")
            )
            continue
        state = snapshot.state
        sections.append(
            LayerSection(
                layer=layer,
                snapshot_id=snapshot.snapshot_id,
                snapshot_hash=snapshot.snapshot_hash,
                model_id=snapshot.key.model_id,
                model_version=snapshot.key.model_version,
                state=state.state if state else "UNAVAILABLE",
                direction=state.direction if state else None,
                active_ranges=state.active_ranges if state else (),
                no_go=state.no_go if state else (),
                quality=snapshot.quality.outcome.value,
            )
        )

    conflicts: list[dict[str, object]] = []
    sides = {
        layer: section.direction.get("side")
        for layer, section in ((section.layer, section) for section in sections)
        if section.direction
    }
    if len(set(sides.values())) > 1:
        conflicts.append(
            {
                "kind": "DIRECTION_CONFLICT",
                "layers": tuple(layer.value for layer in sides),
                "sides": tuple(sides[layer] for layer in sides),
            }
        )
    for section in sections:
        if section.no_go and section.layer is not Layer.L1:
            conflicts.append(
                {
                    "kind": "HIGHER_LAYER_NO_GO",
                    "layer": section.layer.value,
                    "reasons": section.no_go,
                }
            )

    view = InstrumentView(
        instrument_id=instrument_id,
        sections=tuple(sections),
        conflicts=tuple(conflicts),
        unresolved=tuple(unresolved),
        classifications=classifications
        or Classifications(
            execution_class=None,
            exposure=None,
            research_only=False,
            manual_only=False,
            automation_permitted=False,
        ),
        schema_version=INSTRUMENT_VIEW_SCHEMA_VERSION,
    )
    view_id = "VIEW." + content_hash(
        {"instrument_id": instrument_id, "layers": tuple(s.layer.value for s in sections)}
    )[:40]
    return replace(view, view_id=view_id).finalized()


def compose_basket_view(
    *,
    basket_id: str,
    snapshots: Mapping[str, Snapshot],
    roles: Mapping[str, str],
    permitted_exposures: frozenset[str] | None = None,
    classifications: Classifications | None = None,
) -> BasketView:
    for pair, role in roles.items():
        if role not in BASKET_ROLES:
            raise RefusalError("MALFORMED_REQUEST", detail="basket_role_forbidden")
    pairs: list[BasketPair] = []
    unresolved: list[UnavailableSection] = []
    for pair in sorted(snapshots):
        snapshot = snapshots[pair]
        role = roles.get(pair, "DRIVER")
        exposure = snapshot.classifications.exposure
        if permitted_exposures is not None and exposure not in permitted_exposures:
            unresolved.append(
                UnavailableSection(section="state", reason=f"PAIR_{pair}_EXPOSURE_FILTERED")
            )
            continue
        state = snapshot.state
        pairs.append(
            BasketPair(
                pair=pair,
                role=role,
                snapshot_id=snapshot.snapshot_id,
                snapshot_hash=snapshot.snapshot_hash,
                state=state.state if state else "UNAVAILABLE",
                direction=state.direction if state else None,
                no_go=state.no_go if state else (),
                exposure=exposure,
                confirmation_only=role == "CONFIRMATION_VETO",
            )
        )
    for pair in sorted(set(roles) - set(snapshots)):
        unresolved.append(
            UnavailableSection(section="state", reason=f"PAIR_{pair}_UNAVAILABLE")
        )

    view = BasketView(
        basket_id=basket_id,
        pairs=tuple(pairs),
        unresolved=tuple(unresolved),
        classifications=classifications
        or Classifications(
            execution_class=None,
            exposure=None,
            research_only=False,
            manual_only=False,
            automation_permitted=False,
        ),
        schema_version=BASKET_VIEW_SCHEMA_VERSION,
    )
    view_id = "BASKET." + content_hash(
        {
            "basket_id": basket_id,
            "pairs": tuple((p.pair, p.role, p.snapshot_id) for p in pairs),
        }
    )[:40]
    return replace(view, view_id=view_id).finalized()


__all__ = [
    "CANONICAL_LAYER_ORDER",
    "BASKET_ROLES",
    "compose_instrument_view",
    "compose_basket_view",
]
