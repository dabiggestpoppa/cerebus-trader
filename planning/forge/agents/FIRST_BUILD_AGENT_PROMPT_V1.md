# FIRST BUILD AGENT PROMPT — GLX FORGE V1

You are the implementation agent for GLX FORGE — Powered by CEREBUS.

Repository: dabiggestpoppa/cerebus-trader
Working branch: forge
Planning freeze head: 60e067547b9d9165d94e4f074e0db0ba58e59e24

Current state:
Book I / Bloc I.1 has an implementation and acceptance suite, but governance intentionally holds ratification at PENDING TEST EXECUTION because the planning session could not obtain executable CI evidence. Your first duty is to verify/repair/ratify I.1. Do not skip this gate.

## READ FIRST — IN THIS ORDER

1. planning/forge/PLANNING_FREEZE_MANIFEST_V1.md
2. planning/forge/MASTER_DEPENDENCY_ACCEPTANCE_AUDIT_V1.md
3. planning/forge/AGENT_EXECUTION_HANDOFF_V1.md
4. planning/forge/GLX_FORGE_MASTER_BUILD_PLAN_V1.md
5. planning/forge/books/BOOK_I_CORPUS_CANONICAL_PLAN_V1.md
6. corpus/canonical/CEREBUS_CANONICAL_TAXONOMY_V1.md
7. corpus/canonical/ONTOLOGY_CROSSWALK_V1.md
8. corpus/canonical/schemas/MODEL_CARD_SCHEMA_V1.md
9. corpus/canonical/schemas/EVIDENCE_CARD_SCHEMA_V1.md
10. corpus/canonical/schemas/SETUP_OPERATOR_CARD_SCHEMA_V1.md
11. corpus/canonical/RETRIEVAL_OBJECT_SCHEMA_V1.md
12. corpus/canonical/CLAIM_REGISTRY_V1.md
13. corpus/canonical/ANSWER_CONTRACT_V1.md
14. corpus/canonical/PRODUCT_EXPOSURE_RULES_V1.md
15. implementation/forge/book_i/bloc_i_1/PLAN.md
16. implementation/forge/book_i/bloc_i_1/ACCEPTANCE.md
17. implementation/forge/book_i/bloc_i_1/EVIDENCE.md
18. implementation/forge/book_i/bloc_i_1/RATIFICATION.md
19. app/forge/canonical.py
20. app/forge/schemas.py
21. tests/test_forge_canonical.py
22. tests/test_forge_schemas.py

Also inspect the actual repository tree before modifying anything. Reuse existing code; do not build parallel abstractions merely because the planning documents use conceptual names.

## GOVERNING LAW

This is a build mission, not a redesign mission.

Model != Claim != Evidence != Setup != Artifact.
L3 Destination != L2 Path != L1 Execution.
Manual validity != automation parity.
Target reach != WR.
Correlation != probability.
Simulation != empirical validation.
Historical claim != current verified claim.
Checkout != entitlement.
Provider identity != FORGE identity.
Semantic similarity != authority.

Do not:
- restart broad recovery;
- create a second ontology;
- automate ST;
- invent BTC Game;
- promote research;
- make Whop/OpenRouter domain authorities;
- add brokerage execution;
- silently change frozen architecture.

If a frozen contract is genuinely impossible or contradictory, STOP affected work and create a GAP/ADR. Do not improvise around it.

# PHASE 0 — VERIFY REPOSITORY TRUTH

Before edits:
- record current branch and HEAD;
- verify freeze head is an ancestor of current HEAD;
- inspect git status;
- identify any unrelated/uncommitted work;
- do not overwrite another thread's work;
- inspect the existing application/runtime/test structure.

Record this in the evidence trail.

# PHASE 1 — CLOSE BLOC I.1 TEST GATE

Run the repository's real test environment.

Minimum:
python -m pytest -q

Also run focused FORGE tests:
python -m pytest -q tests/test_forge_canonical.py tests/test_forge_schemas.py

If the repository uses an established alternative command/environment, run that too and document it.

Do NOT weaken tests to get green.

If failures occur:
1. classify whether implementation defect, test defect, environment defect or frozen-contract conflict;
2. repair implementation/test only when consistent with frozen acceptance;
3. add regression test for every real defect;
4. rerun focused and full suite.

Review the I.1 implementation for:
- typed canonical IDs;
- enum fidelity to frozen taxonomy;
- immutability;
- deterministic serialization/hash;
- duplicate/self/dangling reference handling;
- explicit historical-partial behavior;
- lifecycle transition safety;
- claim conflict identity;
- specialized Model/Evidence/Setup card type validation;
- no dependency/persistence/UI/provider leakage.

Do not claim all hand-authored corpus cards parse unless you actually test the current files or machine-readable fixtures representing them. If current Markdown cards are not directly machine-parseable, state that accurately and distinguish schema-contract validation from corpus backfill, which belongs to I.3.

# PHASE 2 — RATIFY I.1 ONLY IF EVIDENCE PASSES

Update:
implementation/forge/book_i/bloc_i_1/EVIDENCE.md
implementation/forge/book_i/bloc_i_1/RATIFICATION.md

Evidence must contain:
- exact commands;
- exact pass/fail counts;
- environment/runtime;
- changed-file inventory;
- defects found and repairs;
- known gaps;
- final acceptance mapping.

Ratification is PASS only if I.1 acceptance is met.

Use an append-only, reviewable commit ladder. No amend/squash/rebase/reset/force-push.

If I.1 cannot pass, STOP and report the blocker. Do NOT begin I.2.

# PHASE 3 — BEGIN BOOK I / BLOC I.2 ONLY AFTER I.1 PASS

Target: Source & Provenance Fabric.

Create:
implementation/forge/book_i/bloc_i_2/PLAN.md
implementation/forge/book_i/bloc_i_2/ACCEPTANCE.md

Then implement I.2 according to Book I:

I.2.1 Artifact registry
Supported source classes must include PDF/MD/Pine/CSV/XLSX/visual/notebook/conversation-derived and allow extension without turning artifacts into evidence automatically.

I.2.2 Content identity
Represent hash, source generation, version, repository/library locator and materialization/source state.

I.2.3 Object provenance edges
Support typed provenance relationships such as SUPPORTS/DEFINES/IMPLEMENTS/VISUALIZES/SUPERSEDES as appropriate. Do not confuse lineage between concepts/models with provenance between physical artifacts and canonical objects.

I.2.4 Visual semantics
An infographic may preserve teaching/relationship/historical/operator information but cannot independently validate a numerical claim.

I.2.5 Incomplete source states
At minimum:
LOCATED
READ
VERIFIED
MATERIALIZED
MISSING
PARTIAL
CONVERSATION_DERIVED.

Search miss must not be encoded as proof of nonexistence.

I.2.6 Provenance audit
Produce deterministic source-coverage/orphan reporting.

## I.2 invariants

- Artifact != Evidence.
- Visual != statistical proof.
- Conversation-derived != verified empirical evidence.
- Missing/partial provenance is explicit, never silently filled.
- A launch numerical claim must ultimately route Claim -> Evidence -> Source/Artifact.
- Provenance does not change canonical status by itself.
- Do not create persistence yet; Book II owns persistence.
- Do not restart recovery to fill every historical source. I.2 must represent gaps honestly.

## I.2 tests

At minimum test:
- valid artifact identities/types;
- deterministic content identity;
- duplicate artifact identity;
- valid/invalid provenance edges;
- source-state lifecycle/validation;
- visual cannot be marked as independent empirical proof;
- conversation-derived source restrictions;
- missing/partial states;
- orphan canonical object report;
- evidence/source coverage report;
- launch numerical claim with no provenance is surfaced as a gap;
- historical unresolved source remains explicit rather than fabricated.

Use current canonical/evidence objects as fixtures where practical, but do not mutate their scientific status merely to make tests pass.

# PHASE 4 — I.2 EVIDENCE / RATIFICATION

When implementation passes:
- write EVIDENCE.md;
- write RATIFICATION.md;
- include exact test output and coverage counts;
- list unresolved provenance gaps;
- commit ratification separately.

Then STOP and report. Do not begin I.3 in the same handoff unless explicitly instructed.

# COMMIT DISCIPLINE

Expected shape:
1. I.1 repair commit(s), if needed
2. I.1 test/evidence update
3. I.1 ratification
4. I.2 PLAN
5. I.2 ACCEPTANCE
6. I.2 implementation in bounded commits
7. I.2 tests
8. I.2 evidence
9. I.2 ratification

Pure documentation/evidence commits should remain distinguishable from implementation commits.

# FINAL REPORT FORMAT

Return:
1. repository HEAD;
2. I.1 final status;
3. exact full/focused test results;
4. I.1 defects/repairs;
5. I.2 final status;
6. I.2 files/features implemented;
7. I.2 exact tests/results;
8. commit ladder;
9. unresolved gaps;
10. next dependency-ready packet.

Never say COMPLETE if the relevant ratification gate is not PASS.
