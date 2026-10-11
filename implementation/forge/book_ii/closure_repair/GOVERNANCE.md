# BOOK II — CLOSURE REPAIR GOVERNANCE DISPOSITION RECORD

Status: GOVERNANCE RECORD (ladder rung 2) — operator interpretations recorded
verbatim; frozen planning documents are NOT modified by this record.
Start SHA for this packet: `eea25a35f15fea70df1b768d1e1a7c6db05d337f`.
Authority: Build Agent #13 operator authorization ("Do not ratify Book II,
amend frozen plans, or begin Book III/VII").

## 1. GAP_ADR_001 — phase-order dependency interpretation (DISPOSED)

Operator interpretation recorded verbatim:

> **Executable dependency prerequisites govern authorization; phase labels do
> not override explicitly declared prerequisite contracts.**

Consequences recorded here:

1. Book II closure work (this packet) precedes Book III work: Book III’s
   frozen plan declares Book II provider-port/observability/persistence
   contracts as inputs, so executable prerequisites — not the Phase A–I
   grouping labels in `MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md` §10 —
   govern what may start.
2. **The frozen planning documents remain unchanged.** The phase grouping
   text stays byte-identical (re-verified in `VERIFICATION.md`); this
   disposition does not edit, amend, or reinterpret any frozen file on disk.
   It is a governance reading that resolves the recorded contradiction for
   scheduling purposes.
3. The historical ADR file
   `implementation/forge/book_ii/bloc_ii_5/GAP_ADR_001_PHASE_ORDER_VS_BLOC_DEPENDENCY.md`
   is **not edited** (append-only history; it was carried byte-identical
   through II.5, II.6, step 7, and the evidence pack). Its status line
   remains as written; the disposition of record for the program is this
   file plus the consolidated gap register update.
4. GAP_ADR_001 moves from **OPEN — operator decision pending** to
   **DISPOSED — interpretation recorded** on the consolidated register.
   This does not ratify anything and does not authorize Book III by itself:
   Book III still starts only under its own explicit authorization once
   Book II’s ratified closure exists.

## 2. GAP-05 — durable audit/event-ledger ownership (INTERPRETATION RECORDED)

Operator ownership interpretation recorded verbatim:

> - Book II owns durable, content-minimized operational and security audit
>   infrastructure where explicitly required.
> - Book VI owns commercial entitlement decisions and their business meaning.
> - Book I owns evidence provenance.
> - Book II must not create an alternative licensing or evidence authority.

Verification against frozen contracts (required before use; stop condition
was "if the frozen contract contradicts either interpretation, stop"):

| Interpretation clause | Frozen contract evidence | Verdict |
|---|---|---|
| Book II owns durable operational/security audit infra where explicitly required | Book II plan `### Ch II.2.6 Audit/event ledger` sits in Book II’s **persistence** chapters and specifies append-oriented records (auth/security events, policy decisions, protected retrieval access, entitlement changes, provider event ingestion, administrative mutations) with "payloads must avoid secrets and unnecessary corpus content" (= content-minimized); `## Persistence domains` requires tables distinguishing `access/audit events` | **Consistent** — explicitly required by frozen Book II |
| Book VI owns commercial entitlement decisions and their business meaning | Book II plan `# HANDOFF TO BOOK III / VI`: "Book VI may assume … product-neutral entitlement storage … policy consumes internal capabilities, not Whop product IDs"; `# BOOK II EXCLUSIONS` (no pricing/licensing behavior); freeze-manifest invariant 18 (checkout ≠ entitlement) | **Consistent** |
| Book I owns evidence provenance | Freeze-manifest invariants 2 (Model ≠ Claim ≠ Evidence ≠ Setup ≠ Artifact), 7 (numerical CEREBUS claims require evidence identity), 20 (research publication ≠ canonical promotion); Book I packets are the provenance authority | **Consistent** |
| Book II must not create an alternative licensing or evidence authority | Freeze-manifest invariants 18/19 (checkout ≠ entitlement, provider IDs ≠ internal identity); CREATE TABLE audit of `001`/`002` contains no license, entitlement, plan, price, or evidence-truth table; identity migration header: "IDENTITY != ENTITLEMENT … no plan/license/entitlement/capability table exists here or may ever be added" | **Consistent — and currently over-satisfied: no such authority exists in code** |

**No contradiction found → Phase 1 stop condition not met; the
interpretation stands as recorded.**

Honest consequence (never silently closed):

- The ownership question is resolved **in Book II’s favor** for durable
  operational/security audit records — which makes the *absence* of that
  storage a Book II implementation fact, not a downstream deferral. Code
  audit at this SHA: audit/usage records live only in-process
  (`observability/audit.py` `BoundedAuditTrail`, `observability/usage.py`
  `UsageLedger`); `grep "INSERT INTO" app/forge` shows writes only to
  canonical/identity/migration tables — **no durable audit/event ledger
  exists**.
- GAP-05 is therefore updated on the consolidated register as:
  **ownership DISPOSED (this record); implementation split** — durable
  operational/security audit + event ledger = **Book II scope, implementation
  pending** (reclassified from "operator decision" to an explicit Book II
  open item); products/plans/licenses/entitlements/provider-event business
  tables = **Book VI downstream**. This packet does NOT implement the ledger
  (Build Agent #13 scopes GAP-05 to ownership clarification; Phase 2/3 name
  only GAP-01/GAP-02 implementation).

## 3. Bloc II.2 non-goal vs frozen Ch II.2.4 (conflict resolved toward the frozen plan)

- II.2 `ACCEPTANCE.md` "Explicit non-goals" states "no pgvector/embeddings/
  RAG"; the frozen Book II plan (Ch II.2.4, Persistence domains, gate
  G-D1/G-D4, Acceptance II.2) requires retrieval/embedding **storage**.
- Frozen planning outranks a bloc-level scope note: the freeze manifest’s
  change-control law allows narrowing only via an operator-approved
  amendment, which never happened — the bloc record itself logged GAP-01
  against the frozen chapter.
- The operator authorization for this packet explicitly directs
  implementation of the vector-storage substrate the frozen contract
  requires. Resolution: **frozen Ch II.2.4 governs; the substrate is
  implemented** (storage/schema only — embedding generation and model
  selection stay Book VII, canonical authority stays Book I).
- The historical II.2 packet files are **not edited** (append-only). Their
  non-goal text stands as the historical record of the deviation that
  GAP-01 tracked; the evidence pack matrix/gap register are updated with the
  repair facts only.

## 4. What this record does NOT do

- No frozen file changes (23 manifest-pinned files re-verified byte-identical
  in `VERIFICATION.md`).
- No Book II ratification, no contract freeze, no PASS verdict.
- No closure of GAP-02 (needs executed evidence, in EVIDENCE rung) and no
  closure of GAP-05 implementation (stays open, as recorded in §2).
