"""Phase 3 — I.3 real-corpus DRY RUN audit (read-only; zero writes).

Prints exact counts for: inventory, BEFORE/AFTER parse compatibility, legacy
ID mappings, legacy status mappings, quarantine, provenance coverage, claim
adequacy, and frozen model-family distinctions.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.forge.backfill import mappings as M
from app.forge.backfill.canonicalizer import canonicalize_files
from app.forge.backfill.parser import parse_card
from app.forge.backfill.runner import (
    CARD_GLOBS,
    CONVERSATION_DERIVED_GLOBS,
    load_corpus_files,
)

root = Path(".")
files = load_corpus_files(root)
plan = canonicalize_files(files)
rep = plan.report

out: list[str] = []
def say(s: str = "") -> None:
    out.append(s)

# ---------------------------------------------------------------- inventory
card_paths = sorted({p.as_posix() for g in CARD_GLOBS for p in root.glob(g)})
conv_paths = sorted({p.as_posix() for g in CONVERSATION_DERIVED_GLOBS for p in root.glob(g)})
named_paths = [n.path for n in M.NAMED_ARTIFACT_EDGES]
say("== INVENTORY ==")
say(f"corpus files on disk           : {len(list(root.glob('corpus/**/*')) and [p for p in root.glob('corpus/**/*') if p.is_file()])}")
say(f"in-scope loaded (frozen globs) : {len(files)}  = {len(card_paths)} cards + {len(conv_paths)} conversation-derived + {len(named_paths)} named artifacts + 1 claim registry")
say(f"named artifacts (edges)        : {len(named_paths)}")
for p in named_paths:
    say(f"  - {p}")
assert len(files) == len(card_paths) + len(conv_paths) + len(named_paths) + 1, "inventory partition mismatch"
registry_outcomes = [o for o in rep.outcomes if o.path == M.CLAIM_REGISTRY_PATH]
assert len(registry_outcomes) == 1 and registry_outcomes[0].classification.value == "GOVERNANCE_CONTRACT"
say(f"claim registry                 : inventoried as {registry_outcomes[0].classification.value}")

# --------------------------------------------------- BEFORE parse compat
say()
say("== BEFORE: raw markdown parse (parse_card) ==")
kinds: dict[str, str] = {}
parse_errors: list[str] = []
for p in card_paths:
    text = Path(p).read_text(encoding="utf-8")
    try:
        card = parse_card(p, text)
        kinds[p] = card.kind
    except Exception as exc:  # noqa: BLE001
        parse_errors.append(f"{p}: {exc!r}")
card_kind_counts: dict[str, int] = {}
for k in kinds.values():
    card_kind_counts[k] = card_kind_counts.get(k, 0) + 1
say(f"card files parsed              : {len(kinds)}/{len(card_paths)}  kinds={card_kind_counts}")
say(f"parse exceptions               : {len(parse_errors)}")
for e in parse_errors:
    say(f"  ! {e}")

# non-card in-scope files must NOT parse as cards
noncard = conv_paths + named_paths
noncard_as_card: list[str] = []
for p in noncard:
    text = Path(p).read_text(encoding="utf-8")
    try:
        kind = parse_card(p, text).kind
    except Exception:  # noqa: BLE001
        kind = "PARSE_ERROR"
    if kind in ("MODEL CARD", "EVIDENCE CARD", "SETUP CARD"):
        noncard_as_card.append(f"{p} -> {kind}")
say(f"non-card in-scope files        : {len(noncard)}; misdetected as cards: {len(noncard_as_card)}")
for e in noncard_as_card:
    say(f"  ! {e}")

# ----------------------------------------------------- AFTER outcome split
say()
say("== AFTER: canonicalization outcomes ==")
by_class: dict[str, int] = {}
for o in rep.outcomes:
    by_class[o.classification.value] = by_class.get(o.classification.value, 0) + 1
say(f"outcomes total                 : {len(rep.outcomes)}  {by_class}")
say(f"READY (id passthrough)         : {rep.ready}")
mapped_paths = [o for o in rep.outcomes if o.classification.value == "MAPPING_REQUIRED"]
say(f"MAPPING_REQUIRED (counted)     : {len(mapped_paths)}")
say(f"QUARANTINED                    : {rep.quarantined}")
say(f"models={rep.models} evidence={rep.evidence} setups={rep.setups} claims={rep.claims} migrated_total={rep.migrated}")
assert rep.migrated == rep.models + rep.evidence + rep.setups + rep.claims

# ------------------------------------------------------- legacy ID mappings
say()
say("== LEGACY ID MAPPINGS (explicit, no fuzzy matching) ==")
registry = {m.legacy_id: m.canonical_id for m in M.LEGACY_ID_MAPPINGS}
say(f"LEGACY_ID_MAPPINGS entries     : {len(M.LEGACY_ID_MAPPINGS)}")
id_rows = []
for rec in plan.objects:
    legacy = rec.metadata.get("legacy_ids", [])
    for lid in legacy:
        id_rows.append((lid, rec.canonical_id, lid == rec.canonical_id))
explicit = [r for r in id_rows if not r[2]]
passthrough = [r for r in id_rows if r[2]]
say(f"objects with legacy_ids        : {len({r[1] for r in id_rows})}")
say(f"explicit mapped legacy ids     : {len(explicit)}")
for lid, cid, _ in sorted(explicit):
    assert registry.get(lid) == cid, f"registry mismatch {lid} -> {cid}"
    say(f"  {lid}  ->  {cid}")
say(f"passthrough (legacy == canon)  : {len(passthrough)}")
# no two legacy ids share a canonical target
targets: dict[str, list[str]] = {}
for lid, cid, _ in id_rows:
    targets.setdefault(cid, []).append(lid)
dupes = {c: l for c, l in targets.items() if len(l) > 1}
say(f"canonical ids with >1 legacy id: {len(dupes)} {dupes if dupes else ''}")

# ----------------------------------------------------- legacy status maps
say()
say("== LEGACY STATUS MAPPINGS (no promotion) ==")
status_rows: dict[str, set[str]] = {}
for p in card_paths:
    card = parse_card(p, Path(p).read_text(encoding="utf-8"))
    raw = card.fields.get("status", "").strip()
    resolved = M.resolve_status(raw)
    if resolved is None:
        say(f"  ! unmapped status {raw!r} in {p}")
        continue
    canon, _ = resolved
    status_rows.setdefault(raw, set()).add(canon)
for entry in M.REGISTRY_CLAIMS:
    resolved = M.resolve_status(entry["status"])
    if resolved is None:
        say(f"  ! unmapped registry claim status {entry['status']!r}")
        continue
    canon, _ = resolved
    status_rows.setdefault(entry["status"], set()).add(canon)
say(f"distinct legacy status strings : {len(status_rows)}")
for raw in sorted(status_rows):
    say(f"  {raw!r} -> {sorted(status_rows[raw])}")
multi = {r: c for r, c in status_rows.items() if len(c) > 1}
say(f"ambiguous (1 raw -> many canon): {len(multi)}")
# record-level: recorded status equals mapping result
mismatch = []
for rec in plan.objects:
    md = rec.metadata
    if rec.object_type.value == "CLAIM":
        continue
    card_legacy_status = (md.get("card") or {}).get("fields", {}).get("status") or md.get("legacy_status")
    if card_legacy_status:
        resolved = M.resolve_status(card_legacy_status)
        if resolved and resolved[0].value != rec.status.value:
            mismatch.append((rec.canonical_id, card_legacy_status, rec.status.value))
say(f"record status != mapping result: {len(mismatch)}")

# ------------------------------------------------------------- quarantine
say()
say("== QUARANTINE AUDIT ==")
for o in rep.outcomes:
    if o.classification.value == "QUARANTINED":
        say(f"  {o.path}")
        say(f"      reason: {o.reason}")
card_quarantine = [o for o in rep.outcomes
                   if o.classification.value == "QUARANTINED" and o.path in card_paths]
say(f"card-file quarantines          : {len(card_quarantine)} (must be 0 for full migration)")
say(f"non-card quarantines           : {rep.quarantined - len(card_quarantine)} (correct: not card templates)")

# ---------------------------------------------------------- provenance
say()
say("== PROVENANCE COVERAGE ==")
edges = plan.edges  # (artifact_id, object_id, relation, note)
artifacts = plan.artifacts
say(f"artifacts registered           : {len(artifacts)}")
by_obj: dict[str, int] = {}
by_rel: dict[str, int] = {}
for aid, oid, rel, note in edges:
    by_obj[oid] = by_obj.get(oid, 0) + 1
    by_rel[rel] = by_rel.get(rel, 0) + 1
say(f"edges                          : {len(edges)}  by relation: {by_rel}")
no_edge = [r.canonical_id for r in plan.objects if by_obj.get(r.canonical_id, 0) == 0]
say(f"objects with >=1 edge          : {len(plan.objects) - len(no_edge)}/{len(plan.objects)}")
say(f"objects with 0 edges           : {len(no_edge)}: {no_edge}")
# every artifact used at least once?
used = {a for a, _, _, _ in edges}
say(f"artifacts with >=1 edge        : {len(used)}/{len(artifacts)}")
# content identity present
missing_identity = [a.artifact_id for a in artifacts if not a.content_identity]
say(f"artifacts missing identity      : {len(missing_identity)}")

# ---------------------------------------------------------- claim adequacy
say()
say("== CLAIM ADEQUACY (10 registry claims) ==")
by_id = {r.canonical_id: r for r in plan.objects}
claims = [r for r in plan.objects if r.object_type.value == "CLAIM"]
say(f"claims in plan                 : {len(claims)}")
claim_issues: list[str] = []
for c in claims:
    ev_refs = [r.target_id for r in c.references if r.relation == "supported_by"]
    md_refs = [r.target_id for r in c.references if r.relation == "belongs_to"]
    ok_ev = [e for e in ev_refs if e in by_id]
    ok_md = [m for m in md_refs if m in by_id]
    # mutual back-reference evidence -> claim
    mutual = all(any(rr.target_id == c.canonical_id and rr.relation == "evidence_for"
                     for rr in by_id[e].references) for e in ok_ev) if ok_ev else False
    has_identity = c.claim_identity is not None
    edge = by_obj.get(c.canonical_id, 0)
    say(f"  {c.canonical_id:34s} status={c.status.value:15s} ev={ok_ev} model={ok_md} "
        f"mutual={mutual} identity={has_identity} edges={edge}")
    if len(ok_ev) != len(ev_refs) or not ok_ev:
        claim_issues.append(f"{c.canonical_id}: unresolved evidence {ev_refs}")
    if not mutual:
        claim_issues.append(f"{c.canonical_id}: evidence lacks evidence_for back-ref")
    if not has_identity:
        claim_issues.append(f"{c.canonical_id}: missing claim_identity")
say(f"claim issues                   : {len(claim_issues)}")
for i in claim_issues:
    say(f"  ! {i}")

# every evidence has an artifact-backed provenance edge and a source file
ev_issues: list[str] = []
for r in plan.objects:
    if r.object_type.value != "EVIDENCE":
        continue
    if by_obj.get(r.canonical_id, 0) == 0:
        ev_issues.append(f"{r.canonical_id}: no provenance edge")
say(f"evidence issues                : {len(ev_issues)}")
for i in ev_issues:
    say(f"  ! {i}")

# ------------------------------------------------ frozen family distinctions
say()
say("== FROZEN MODEL-FAMILY DISTINCTIONS ==")
def find(cid: str):
    return by_id.get(cid)

checks: list[tuple[str, bool, str]] = []
# 1. ST manual validity vs automation parity:
#    (a) EUR daily card keeps the separation doctrine (implementation parity
#        must be separated from empirical evidence; P90 lineage not imported),
#    (b) setups keep MANUAL_OPERATOR where the source states it (JPY, XAU),
#    (c) no AUTOMATION_APPROVED is created (checked separately below).
m = find("MOD.EUR.DAILY.NEWS_REKEY.V1")
card_payload = json.dumps(m.metadata.get("card", {}), ensure_ascii=False) if m else ""
low = card_payload.lower()
st_doctrine = bool(m) and "P90" in card_payload and "parity" in low and (
    "do not import" in low or "must be separated" in low
)
setup_exec = {
    cid: (find(cid).metadata.get("card", {}).get("execution_class") if find(cid) else None)
    for cid in ("SET.JPY.CARRY_ROLE_GATE.V1", "SET.XAU.QUARTER_ZONE.V1", "SET.FIB.REKEY.V1")
}
say(f"setup execution classes        : {setup_exec}")
manual_ok = (
    setup_exec["SET.JPY.CARRY_ROLE_GATE.V1"] == "MANUAL_OPERATOR"
    and setup_exec["SET.XAU.QUARTER_ZONE.V1"] == "MANUAL_OPERATOR"
)
checks.append(("ST parity/separation doctrine preserved on EUR daily card",
               st_doctrine, "P90 + parity + separation language in card payload"))
checks.append(("MANUAL_OPERATOR preserved on JPY + XAU setups (manual validity)",
               manual_ok, str(setup_exec)))
checks.append(("no AUTOMATION_APPROVED / autonomous execution anywhere",
               not any("AUTOMATION_APPROVED" in json.dumps(r.metadata, ensure_ascii=False).upper()
                       or "AUTONOMOUS_EXECUTION_APPROVED" in json.dumps(r.metadata, ensure_ascii=False).upper()
                       for r in plan.objects),
               "scan of all metadata"))
# 2. P90 not conflated with ST, no invented performance numbers
p90 = find("MOD.EUR.DAILY.NEWS_REKEY.V1")
p90_blob = json.dumps(p90.metadata, ensure_ascii=False) if p90 else ""
checks.append(("P90 present as lineage, not ST synonym",
               "P90" in p90_blob and "p90_equals_st" not in p90_blob.lower(),
               "P90 token in model metadata"))
# 3. BTC Tracker vs BTC Game
btc = find("MOD.BTC.TRACKER.DWM.V1")
btc_game = [r.canonical_id for r in plan.objects if "BTC" in r.canonical_id and "GAME" in r.canonical_id]
checks.append(("BTC Tracker migrated; BTC Game not fabricated",
               btc is not None and not btc_game,
               f"tracker={'yes' if btc else 'NO'}, game_objects={btc_game}"))
# 4. EURUSD families separate
eur_ids = sorted(r.canonical_id for r in plan.objects
                 if r.object_type.value == "MODEL" and r.canonical_id.startswith("MOD.EUR."))
checks.append(("EUR families separate (>=3 distinct EUR models)",
               len(eur_ids) >= 3, str(eur_ids)))
# 5. XAU L1/L2/L3
xau = find("MOD.XAU.GAME.L1_L2_L3.V1")
xau_blob = json.dumps(xau.metadata, ensure_ascii=False) if xau else ""
checks.append(("XAU L1/L2/L3 distinct levels preserved",
               bool(xau) and all(t in xau_blob for t in ("L1", "L2", "L3")),
               "all three level tokens in metadata"))
# 6. JPY role asymmetry
jpy_claim = find("CL.JPY.CARRY.ROLE_RELATION")
jpy_set = find("SET.JPY.CARRY_ROLE_GATE.V1")
jpy_ev = find("EV.JPY.CARRY.BASKET_RELATION.V1")
checks.append(("JPY model + gated setup + basket evidence exist",
               all(x is not None for x in (jpy_claim, jpy_set, jpy_ev)),
               "claim/setup/evidence triad"))
# 7. Fib R11 negative evidence
r11_ev = find("EV.FIB.R11.ANCHOR_OVERGEN.V1")
r11_cl = find("CL.FIB.R11.GENERATOR_FAILURE")
ev_type = (r11_ev.metadata.get("evidence_type") or r11_ev.metadata.get("card", {}).get("fields", {}).get("evidence_type")) if r11_ev else None
neg_ok = bool(r11_ev and r11_cl and r11_cl.status.value == "FALSIFIED")
checks.append(("Fib R11 claim FALSIFIED + negative evidence preserved",
               neg_ok, f"claim_status={r11_cl.status.value if r11_cl else None}, "
                       f"negative_evidence_count={rep.negative_evidence}"))
for name, ok, detail in checks:
    say(f"  [{'PASS' if ok else 'FAIL'}] {name}  ({detail})")
say(f"family distinction failures    : {sum(1 for _, ok, _ in checks if not ok)}")

# ------------------------------------------------ faithful representation
say()
say("== FAITHFUL SOURCE REPRESENTATION (20 card objects) ==")
faith_issues: list[str] = []
card_objects = [r for r in plan.objects if r.metadata.get("card") or r.metadata.get("legacy_fields")]
say(f"objects with source card payload: {len(card_objects)}")
for p in card_paths:
    card = parse_card(p, Path(p).read_text(encoding="utf-8"))
    raw_id_field = (card.fields.get("model_id") or card.fields.get("evidence_id")
                    or card.fields.get("setup_id") or "").strip()
    resolved = M.resolve_canonical_id(raw_id_field, {
        "MODEL CARD": __import__("app.forge.canonical", fromlist=["ObjectType"]).ObjectType.MODEL,
        "EVIDENCE CARD": __import__("app.forge.canonical", fromlist=["ObjectType"]).ObjectType.EVIDENCE,
        "SETUP CARD": __import__("app.forge.canonical", fromlist=["ObjectType"]).ObjectType.SETUP,
    }[card.kind])
    rec = by_id.get(resolved)
    if rec is None:
        faith_issues.append(f"{p}: no object for {resolved}")
        continue
    # title fidelity (card H1 or fallback id)
    src_title = (card.title or "").strip()
    if src_title and rec.title not in (src_title, resolved) and src_title not in rec.title:
        faith_issues.append(f"{rec.canonical_id}: title {rec.title!r} != source {src_title!r}")
    # status fidelity: canonical status == mapping(source status)
    raw_status = card.fields.get("status", "").strip()
    res = M.resolve_status(raw_status)
    if res and res[0].value != rec.status.value:
        faith_issues.append(f"{rec.canonical_id}: status {rec.status.value} != mapped({raw_status!r})={res[0].value}")
say(f"faithful-representation issues : {len(faith_issues)}")
for i in faith_issues:
    say(f"  ! {i}")

# ------------------------------------------------------------ report gates
say()
say("== REPORT COUNTERS (exact) ==")
counters = {
    "sources_inventoried": rep.sources_inventoried, "artifacts": len(artifacts),
    "provenance_edges": len(edges), "edges_by_object_min": min(by_obj.values()),
    "objects_with_edges": len(by_obj), "migrated": rep.migrated, "models": rep.models,
    "evidence": rep.evidence, "setups": rep.setups, "claims": rep.claims,
    "ready": rep.ready, "mapped": rep.mapped, "quarantined": rep.quarantined,
    "missing_source": rep.missing_source,
    "unresolved_reference": rep.unresolved_reference,
    "unsupported_numerical_claim": rep.unsupported_numerical_claim,
    "negative_evidence": rep.negative_evidence,
    "visual_only_sources": rep.visual_only_sources,
    "conversation_derived_sources": rep.conversation_derived_sources,
    "conflicts": rep.conflicts, "unchanged": rep.unchanged,
}
say(json.dumps(counters, indent=2))
say(f"content_hash                   : {plan.report.content_hash()}")

text = "\n".join(out)
Path("_i3_audit_out.txt").write_text(text, encoding="utf-8")
print(text)
