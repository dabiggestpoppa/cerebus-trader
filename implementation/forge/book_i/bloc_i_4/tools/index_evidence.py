#!/usr/bin/env python3
"""Book I / Bloc I.4 — index evidence harness.

Builds the retrieval index from the real governed corpus through the
persistence port (in-memory store), then asserts — with exact numbers — the
state recorded in ``implementation/forge/book_i/bloc_i_4/EVIDENCE.md``:

- persisted counts (30 objects / 29 artifacts / 38 edges / 9 quarantined)
- index identity (generation, source_fingerprint, index_hash) and idempotent
  rebuild
- structured + lexical query coverage counts
- Claim -> Evidence -> Artifact navigation for all 10 registry claims
- the real-corpus exposure matrix and content-free denials
- quarantine treatment (never ordinary, safe-metadata only when explicit)

Run from the repository root:

    PYTHONPATH=. python implementation/forge/book_i/bloc_i_4/tools/index_evidence.py

Exit status 0 only when every assertion holds. Read-only with respect to the
corpus and to any database: it uses the in-memory gateway only.
"""
from __future__ import annotations

import dataclasses
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO_ROOT))

from app.forge.backfill.canonicalizer import canonicalize_files
from app.forge.backfill.runner import BackfillMode, load_corpus_files, run_backfill
from app.forge.canonical import ObjectType
from app.forge.identity import ForgePrincipal
from app.forge.persistence.memory import InMemoryPersistenceGateway
from app.forge.policy import (
    CAPABILITY_ADMIN_RESEARCH,
    CAPABILITY_CORPUS_READ_MEMBER,
    CAPABILITY_EVIDENCE_READ_RESEARCH,
    CAPABILITY_FORGE_INTERNAL,
    CAPABILITY_MODEL_READ_OPERATOR,
    AuthorizationContext,
)
from app.forge.retrieval import (
    IndexBuildMode,
    IndexBuildOutcome,
    QuarantineCatalog,
    RetrievalIndex,
    RetrievalQuery,
    RetrievalService,
    run_index_build,
)

CARD_PREFIXES = (
    "corpus/canonical/models/",
    "corpus/canonical/evidence/",
    "corpus/canonical/setups/",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

AUTH = ForgePrincipal(authenticated=True, forge_user_id="user-r", session_id=None)
ANON = ForgePrincipal.anonymous()
CONTEXTS = {
    "anon": (ANON, AuthorizationContext.empty()),
    "auth_nocap": (AUTH, AuthorizationContext.empty()),
    "member": (AUTH, AuthorizationContext.of(CAPABILITY_CORPUS_READ_MEMBER)),
    "operator": (AUTH, AuthorizationContext.of(CAPABILITY_MODEL_READ_OPERATOR)),
    "research": (AUTH, AuthorizationContext.of(CAPABILITY_EVIDENCE_READ_RESEARCH)),
    "admin_research": (AUTH, AuthorizationContext.of(CAPABILITY_ADMIN_RESEARCH)),
    "internal": (AUTH, AuthorizationContext.of(CAPABILITY_FORGE_INTERNAL)),
}

CHECKS: list[tuple[str, bool]] = []


def check(name: str, condition: bool) -> None:
    CHECKS.append((name, bool(condition)))
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}")


def main() -> int:
    # ---------------------------------------------------------------- state
    print("== persisted state (memory gateway, APPLY) ==")
    gateway = InMemoryPersistenceGateway()
    run_backfill(gateway, REPO_ROOT, BackfillMode.APPLY)
    ids = sorted(gateway.list_object_ids())
    by_type: Counter = Counter()
    by_exposure: Counter = Counter()
    by_status: Counter = Counter()
    edge_total = 0
    artifact_ids: set[str] = set()
    relations: set[str] = set()
    for oid in ids:
        rec = gateway.get_object(oid)
        by_type[rec.object_type.value] += 1
        by_exposure[rec.exposure.value] += 1
        by_status[rec.status.value] += 1
        for edge in gateway.edges_for_object(oid):
            edge_total += 1
            artifact_ids.add(edge.artifact_id)
            relations.add(edge.relation)

    report = canonicalize_files(load_corpus_files(REPO_ROOT)).report
    catalog = QuarantineCatalog.from_report(report)
    card_quarantines = [e.source_path for e in catalog.entries
                        if e.source_path.startswith(CARD_PREFIXES)]

    print(f"  objects={len(ids)} by_type={dict(sorted(by_type.items()))}")
    print(f"  by_exposure={dict(sorted(by_exposure.items()))}")
    print(f"  by_status={dict(sorted(by_status.items()))}")
    print(f"  artifacts={len(artifact_ids)} edges={edge_total}")
    print(f"  quarantined={report.quarantined} card_quarantines={card_quarantines}")
    check("30 objects", len(ids) == 30)
    check("type split 10/10/7/3",
          dict(by_type) == {"CLAIM": 10, "EVIDENCE": 10, "MODEL": 7, "SETUP": 3})
    check("exposure split 24/4/2",
          dict(by_exposure) == {"SUBSCRIBER_MODEL": 24,
                                "RESEARCH_LAB": 4, "OPERATOR_ONLY": 2})
    check("29 artifacts", len(artifact_ids) == 29)
    check("38 edges", edge_total == 38)
    check("9 quarantined sources", report.quarantined == 9 and len(catalog) == 9)
    check("0 card-file quarantines", card_quarantines == [])

    # ------------------------------------------------------- index identity
    print("== index build ==")
    index = RetrievalIndex()
    outcome = run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, index)
    gen = index.require()
    print(f"  outcome={outcome.outcome} generation={gen.generation} "
          f"records={len(gen.ids)}")
    print(f"  source_fingerprint={gen.source_fingerprint}")
    print(f"  index_hash={gen.index_hash}")
    check("build published", outcome.outcome is IndexBuildOutcome.PUBLISHED)
    check("generation 1, 30 records",
          gen.generation == 1 and len(gen.ids) == 30)
    check("counts_by_type match",
          gen.counts_by_type() == dict(sorted(by_type.items())))
    check("fingerprint and index_hash are sha256 hex",
          bool(SHA256_RE.match(gen.source_fingerprint))
          and bool(SHA256_RE.match(gen.index_hash)))
    check("fresh build is not stale", index.is_stale(gateway) is False)
    check("record identity excludes generation bookkeeping",
          all("generation" not in json.loads(r.deterministic_payload())
              for r in gen.records))

    outcome2 = run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, index)
    gen2 = index.require()
    print(f"  rebuild outcome={outcome2.outcome} generation={gen2.generation}")
    check("idempotent rebuild: UNCHANGED, same generation",
          outcome2.outcome is IndexBuildOutcome.UNCHANGED and gen2.generation == 1)
    check("idempotent rebuild: identical fingerprint and hash",
          gen2.source_fingerprint == gen.source_fingerprint
          and gen2.index_hash == gen.index_hash)

    other = RetrievalIndex()
    run_index_build(gateway, REPO_ROOT, IndexBuildMode.APPLY, other)
    check("two independent builds byte-identical",
          other.require().index_hash == gen.index_hash
          and other.require().source_fingerprint == gen.source_fingerprint)

    # ------------------------------------------------------- query coverage
    print("== query coverage (operator context: PUBLIC+SUBSCRIBER+OPERATOR+RESEARCH) ==")
    service = RetrievalService(index)
    _, op_ctx = CONTEXTS["operator"]

    def count(query: RetrievalQuery) -> tuple[int, int]:
        response = service.retrieve(AUTH, op_ctx, query)
        return len(response.results), len(response.denied)

    expected: list[tuple[str, RetrievalQuery, int]] = [
        ("unfiltered", RetrievalQuery(), 30),
        ("type=CLAIM", RetrievalQuery(object_type="CLAIM"), 10),
        ("type=EVIDENCE", RetrievalQuery(object_type="EVIDENCE"), 10),
        ("type=MODEL", RetrievalQuery(object_type="MODEL"), 7),
        ("type=SETUP", RetrievalQuery(object_type="SETUP"), 3),
        ("market=EURUSD", RetrievalQuery(market="EURUSD"), 17),
        ("market=XAUUSD", RetrievalQuery(market="XAUUSD"), 8),
        ("family=EUR", RetrievalQuery(model_family="EUR"), 15),
        ("family=XAU", RetrievalQuery(model_family="XAU"), 6),
        ("family=JPY", RetrievalQuery(model_family="JPY"), 4),
        ("family=BTC", RetrievalQuery(model_family="BTC"), 1),
        ("status=CANDIDATE", RetrievalQuery(status="CANDIDATE"), 8),
        ("status=VALIDATED", RetrievalQuery(status="VALIDATED"), 10),
        ("status=FALSIFIED", RetrievalQuery(status="FALSIFIED"), 2),
        ("status=FORWARD_OOS", RetrievalQuery(status="FORWARD_OOS"), 4),
        ("status=RESEARCH_FLAG", RetrievalQuery(status="RESEARCH_FLAG"), 5),
        ("status=DESCRIPTIVE", RetrievalQuery(status="DESCRIPTIVE"), 1),
        ("exposure=SUBSCRIBER_MODEL",
         RetrievalQuery(exposure="SUBSCRIBER_MODEL"), 24),
        ("exposure=RESEARCH_LAB", RetrievalQuery(exposure="RESEARCH_LAB"), 4),
        ("exposure=OPERATOR_ONLY", RetrievalQuery(exposure="OPERATOR_ONLY"), 2),
        ("layer=NONE", RetrievalQuery(layer="NONE"), 23),
        ("layer=CROSS_LAYER", RetrievalQuery(layer="CROSS_LAYER"), 4),
        ("layer=L1", RetrievalQuery(layer="L1"), 1),
        ("layer=L2", RetrievalQuery(layer="L2"), 1),
        ("layer=L3", RetrievalQuery(layer="L3"), 1),
        ("relation=DEFINES", RetrievalQuery(provenance_relation="DEFINES"), 30),
        ("relation=IMPLEMENTS", RetrievalQuery(provenance_relation="IMPLEMENTS"), 3),
        ("relation=SUPPORTS", RetrievalQuery(provenance_relation="SUPPORTS"), 1),
        ("relation=VISUALIZES", RetrievalQuery(provenance_relation="VISUALIZES"), 1),
        ("exact id", RetrievalQuery(canonical_id="CL.FIB.R11.GENERATOR_FAILURE"), 1),
        ("unknown id", RetrievalQuery(canonical_id="CL.DOES.NOT.EXIST.V1"), 0),
        ("text=anchor overgeneration", RetrievalQuery(text="anchor overgeneration"), 3),
        ("text=weekly engine", RetrievalQuery(text="weekly engine"), 4),
        ("text=carry basket", RetrievalQuery(text="carry basket"), 3),
        ("text=quarter zone", RetrievalQuery(text="quarter zone"), 6),
        ("text=news residual auc", RetrievalQuery(text="news residual auc"), 3),
        ("text=p90", RetrievalQuery(text="p90"), 11),
    ]
    for label, query, want in expected:
        got, denied = count(query)
        print(f"  {label}: results={got} denied={denied}")
        check(f"query {label} -> {want}", got == want and denied == 0)

    sample_artifact = sorted(artifact_ids)[0]
    got, _ = count(RetrievalQuery(source_artifact=sample_artifact))
    check(f"source_artifact={sample_artifact} -> 1", got == 1)

    claim_ids = [i for i in ids
                 if gateway.get_object(i).object_type is ObjectType.CLAIM]
    claim_identity = gateway.get_object(claim_ids[0]).claim_identity
    got, _ = count(RetrievalQuery(claim_identity=claim_identity))
    check("claim_identity query returns SAME_POPULATION only (1)", got == 1)

    # ------------------------------------------------- provenance navigation
    print("== provenance navigation (research context) ==")
    _, rctx = CONTEXTS["research"]
    found = supported = 0
    for claim_id in sorted(claim_ids):
        chain = service.navigate(AUTH, rctx, claim_id)
        found += int(chain.found)
        supported += int(chain.supported)
        print(f"  {claim_id}: found={chain.found} supported={chain.supported} "
              f"evidence={list(chain.evidence_ids)} artifacts={len(chain.artifacts)} "
              f"missing={[m.reason for m in chain.missing]}")
        check(f"chain complete: {claim_id}",
              chain.found and chain.supported and chain.allowed
              and bool(chain.evidence_ids) and bool(chain.artifacts)
              and not chain.missing)
    check("all 10 claims found", found == 10)
    check("all 10 claims supported", supported == 10)

    missing = service.navigate(AUTH, rctx, "CL.NOT.IN.INDEX.V1")
    check("missing object reported, never invented",
          missing.found is False and missing.supported is False
          and [m.reason for m in missing.missing] == ["NOT_IN_INDEX"])

    # ----------------------------------------------------- exposure matrix
    print("== exposure matrix (retrievable count per context) ==")
    exposures = sorted(by_exposure)
    print("  " + "exposure".ljust(20)
          + "".join(name.ljust(16) for name in CONTEXTS))
    expected_matrix = {
        "OPERATOR_ONLY":     {"anon": 0, "auth_nocap": 0, "member": 0,
                              "operator": 2, "research": 2,
                              "admin_research": 0, "internal": 0},
        "RESEARCH_LAB":      {"anon": 0, "auth_nocap": 0, "member": 0,
                              "operator": 4, "research": 4,
                              "admin_research": 0, "internal": 0},
        "SUBSCRIBER_MODEL":  {"anon": 0, "auth_nocap": 0, "member": 24,
                              "operator": 24, "research": 24,
                              "admin_research": 0, "internal": 0},
    }
    for exposure in exposures:
        row = exposure.ljust(20)
        for name, (principal, ctx) in CONTEXTS.items():
            response = service.retrieve(principal, ctx,
                                        RetrievalQuery(exposure=exposure))
            row += str(len(response.results)).ljust(16)
            check(f"matrix {exposure}/{name} == {expected_matrix[exposure][name]}",
                  len(response.results) == expected_matrix[exposure][name])
        print("  " + row)

    anon = service.retrieve(ANON, AuthorizationContext.empty(), RetrievalQuery())
    check("anonymous: 0 results, 30 denials",
          len(anon.results) == 0 and len(anon.denied) == 30)
    denied_fields = {f.name for f in dataclasses.fields(anon.denied[0])}
    check("denial entries are content-free (object_id, exposure, reason_code)",
          denied_fields == {"object_id", "exposure", "reason_code"})

    # ------------------------------------------------------------ quarantine
    print("== quarantine ==")
    ordinary = service.retrieve(AUTH, rctx, RetrievalQuery())
    explicit = service.retrieve(AUTH, rctx,
                                RetrievalQuery(include_quarantine=True))
    anon_q = service.retrieve(ANON, AuthorizationContext.empty(),
                              RetrievalQuery(include_quarantine=True))
    print(f"  ordinary notices={len(ordinary.quarantined)} "
          f"explicit(research) notices={len(explicit.quarantined)} "
          f"explicit(anon) notices={len(anon_q.quarantined)}")
    check("ordinary search never surfaces quarantine",
          ordinary.quarantined == ()
          and not ({r.object_id for r in ordinary.results} & catalog.paths))
    check("explicit discovery under research returns 9 safe notices",
          len(explicit.quarantined) == 9)
    check("anonymous quarantine discovery fails closed",
          len(anon_q.quarantined) == 0 and len(anon_q.results) == 0)
    check("index ids disjoint from quarantine paths",
          not (set(gen.ids) & catalog.paths))

    # --------------------------------------------------------------- result
    failed = [name for name, ok in CHECKS if not ok]
    print()
    print(f"total checks: {len(CHECKS)}, failed: {len(failed)}")
    if failed:
        for name in failed:
            print(f"  FAILED: {name}")
        return 1
    print("ALL INDEX EVIDENCE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
