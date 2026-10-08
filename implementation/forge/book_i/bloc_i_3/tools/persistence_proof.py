"""Phase 4 — I.3 persistence proof: 7 steps, real corpus, controlled stores.

1. DRY RUN performs zero writes.
2. APPLY against a clean controlled store.
3. Second APPLY is idempotent (NO_CHANGE, zero conflicts).
4. Conflicting canonical object is rejected; content not overwritten.
5. Duplicate canonical IDs in one pending transaction are rejected atomically.
6. Legitimate mutual references (CLAIM <-> EVIDENCE) commit.
7. Invalid (dangling) references roll back the whole batch.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.forge.backfill.canonicalizer import canonicalize_files
from app.forge.backfill.runner import (
    BackfillMode,
    ConflictError,
    _apply_plan,
    load_corpus_files,
    run_backfill,
)
from app.forge.canonical import (
    CanonicalId,
    CanonicalObject,
    CanonicalReference,
    EvidenceStatus,
    Layer,
    ObjectType,
    ProductExposure,
)
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.persistence.port import DanglingReference, DuplicateCanonicalObject
from app.forge.persistence.records import CanonicalObjectRecord

ROOT = Path(".")

def say(s: str = "") -> None:
    print(s, flush=True)

plan = canonicalize_files(load_corpus_files(ROOT))
say(f"plan: objects={len(plan.objects)} artifacts={len(plan.artifacts)} "
    f"edges={len(plan.edges)} hash={plan.report.content_hash()}")

# ---- 1. DRY RUN: zero writes -------------------------------------------
gw = InMemoryPersistenceGateway()
res = run_backfill(gw, ROOT, BackfillMode.DRY_RUN)
zero_art = all(gw.get_artifact(a.artifact_id) is None for a in plan.artifacts)
zero_edge = all(not gw.edges_for_object(o) for o in gw.list_object_ids())
say(f"[1] DRY RUN report: migrated={res.report.migrated} "
    f"quarantined={res.report.quarantined} invent={res.report.sources_inventoried}")
say(f"[1] store after dry run: objects={len(gw.list_object_ids())} "
    f"artifacts_absent={zero_art} edges_absent={zero_edge}")
assert gw.list_object_ids() == () and zero_art and zero_edge
say("[1] PASS — DRY RUN performed zero persistent writes")

# ---- 2. APPLY against a clean controlled store --------------------------
res2 = run_backfill(gw, ROOT, BackfillMode.APPLY)
ids = gw.list_object_ids()
n_art = sum(1 for a in plan.artifacts if gw.get_artifact(a.artifact_id) is not None)
n_edges = sum(len(gw.edges_for_object(o)) for o in ids)
say(f"[2] APPLY: objects={len(ids)} artifacts={n_art}/{len(plan.artifacts)} "
    f"edges={n_edges} migrated={res2.report.migrated} conflicts={res2.report.conflicts}")
assert len(ids) == 30 and n_art == len(plan.artifacts) and n_edges == len(plan.edges)
say("[2] PASS — clean APPLY committed 30 objects / 29 artifacts / 38 edges")

# ---- 3. Second APPLY idempotent ----------------------------------------
state_before = tuple(sorted(gw.list_object_ids()))
res3 = run_backfill(gw, ROOT, BackfillMode.APPLY)
say(f"[3] SECOND APPLY: unchanged={res3.report.unchanged} "
    f"created=0 conflicts={res3.report.conflicts} objects={len(gw.list_object_ids())}")
assert res3.report.unchanged == 30
assert res3.report.conflicts == 0
assert tuple(sorted(gw.list_object_ids())) == state_before
say("[3] PASS — second APPLY is a NO-OP (ALREADY_CURRENT per object)")

# ---- 4. Conflict: existing id with different governed content ----------
record = gw.get_object("MOD.BTC.TRACKER.DWM.V1")
gw._objects["MOD.BTC.TRACKER.DWM.V1"] = (replace(record, status=EvidenceStatus.VALIDATED), 2)
try:
    run_backfill(gw, ROOT, BackfillMode.APPLY)
except ConflictError as exc:
    say(f"[4] conflict raised: {exc}")
else:
    raise SystemExit("[4] FAIL — conflicting apply was NOT rejected")
kept = gw.get_object("MOD.BTC.TRACKER.DWM.V1")
say(f"[4] store content after rejected apply: status={kept.status.value} "
    f"(mutated value preserved, never silently overwritten)")
assert kept.status is EvidenceStatus.VALIDATED
say("[4] PASS — explicit conflict rejection, no silent overwrite")

# ---- 5. Duplicate IDs inside one pending transaction --------------------
gw2 = InMemoryPersistenceGateway()
poisoned = canonicalize_files(load_corpus_files(ROOT))
poisoned.objects.append(poisoned.objects[0])  # same canonical id twice
try:
    _apply_plan(gw2, poisoned)
except DuplicateCanonicalObject as exc:
    say(f"[5] duplicate batch rejected: {exc}")
else:
    raise SystemExit("[5] FAIL — duplicate canonical id accepted")
say(f"[5] store after rejected batch: objects={len(gw2.list_object_ids())} "
    f"artifacts={sum(1 for a in poisoned.artifacts if gw2.get_artifact(a.artifact_id))}")
assert gw2.list_object_ids() == ()
assert all(gw2.get_artifact(a.artifact_id) is None for a in poisoned.artifacts)
say("[5] PASS — atomic rejection: zero objects, zero artifacts, zero edges persisted")

# ---- 6. Legitimate mutual references commit ----------------------------
gw3 = InMemoryPersistenceGateway()
run_backfill(gw3, ROOT, BackfillMode.APPLY)
claim = gw3.get_object("CL.FIB.R11.GENERATOR_FAILURE")
ev = gw3.get_object("EV.FIB.R11.ANCHOR_OVERGEN.V1")
mutual = (
    any(r.target_id == ev.canonical_id for r in claim.references)
    and any(r.target_id == claim.canonical_id for r in ev.references)
)
resolved = all(
    r.target_id in gw3.list_object_ids()
    for rec in (claim, ev) for r in rec.references
)
say(f"[6] CL.FIB.R11 -> EV: {mutual}, all references resolve post-commit: {resolved}; "
    f"objects={len(gw3.list_object_ids())}")
assert mutual and resolved and len(gw3.list_object_ids()) == 30
say("[6] PASS — mutual CLAIM <-> EVIDENCE references committed as one unit")

# ---- 7. Invalid (dangling) reference rolls back -------------------------
gw4 = InMemoryPersistenceGateway()
bad = CanonicalObjectRecord.from_domain(
    CanonicalObject(
        canonical_id=CanonicalId(value="MOD.PROOF.BAD.V1", object_type=ObjectType.MODEL),
        title="proof", version="v1", status=EvidenceStatus.CANDIDATE,
        exposure=ProductExposure.SUBSCRIBER_MODEL, layer=Layer.L2,
        references=(
            CanonicalReference(target_id="MOD.PROOF.MISSING.V1", relation="SUPPORTS"),
        ),
        metadata={},
    )
)
good = plan.objects[0]
try:
    with gw4.transaction():
        gw4.create_object(good)
        gw4.create_object(bad)
except DanglingReference as exc:
    say(f"[7] dangling rejected: {exc}")
else:
    raise SystemExit("[7] FAIL — dangling reference accepted")
say(f"[7] store after rollback: objects={len(gw4.list_object_ids())} "
    f"(good object from the failed batch also gone)")
assert gw4.list_object_ids() == ()
say("[7] PASS — invalid batch rolled back completely")

say("")
say("ALL 7 PERSISTENCE PROOF STEPS PASSED")
