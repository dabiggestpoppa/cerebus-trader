# FORGE RECOVERY PASS 6 — LEDGERS / MODEL LINEAGE / SEARCH-GAP MAP

**Date:** 2026-10-04
**Branch:** forge

## Successfully pushed

- EUR Daily Range Tracker Phase 1 ledger
- Oil Phase 2 early-week anchor-search ledger
- Oil Phase 3 oil-native tier-discovery ledger
- XAU Final Model Freeze V1

## New important finding: research ledgers are a distinct artifact class

The Library contains phase ledgers that preserve decisions made *between* raw tables and final manuals. These are critical because they explain:
- what question was asked;
- what was frozen before testing;
- what alternatives were rejected;
- why a candidate was promoted or parked;
- what changed in the next phase.

FORGE should therefore add:
`research-ledgers/`
as a first-class corpus class rather than burying these files under generic research.

## EUR Daily Range Phase 1 recovered

Frozen base test:
- EURUSD M5;
- 2022-11 through 2026-09;
- Asian 19:00–03:00 ET;
- hard daily cutoff 12:00 ET;
- T1 <20p, T2 20–30p, T3 30–45p, >45p NO-GO;
- original fixed multipliers 3.12 / 2.68 / 2.18;
- 995 complete research days;
- 891 normal T1–T3 days;
- 104 NO-GO days.

This is valuable lineage because later CEREBUS moved away from a single fixed daily target toward Slot×Tier range-left distributions. The ledger shows the predecessor model that motivated the later refinement.

## Oil Phase 2–3 recovered

Phase 2 explicitly searched for the best early-week seed after normalizing the 2026 regime shift.

Important conceptual result:
Oil preferred a broader Sunday-reopen → Monday envelope over one isolated Monday session.

Phase 3 then found that naive full-sample k-means was distorted by a single shock week.

The response was NOT to force that outlier into normal T3:
- normalize by prior ATR20;
- isolate extreme shock state;
- discover normal T1/T2/T3 on core distribution;
- retain extreme as candidate T4 / SHOCK / NO-GO until further evidence.

Candidate normalized oil tiers:
- T1 centroid ~0.569 ATR;
- T2 ~0.922 ATR;
- T3 ~1.591 ATR;
- boundaries ~0.724 and ~1.211 ATR;
- extreme candidate ~5.694 ATR.

Weekly multiplier ordering:
T1 ~3.04x > T2 ~2.09x > T3 ~1.72x.

This is a strong cross-market concept: architecture can transfer while calibration remains instrument-native.

## XAU model lineage

The 577-line Final Model Freeze is now preserved next to the final 952-line Pine implementation.

This gives FORGE both:
- scientific/operator design contract;
- executable chart implementation.

Older Gold Game v1/v2 artifacts were found again, but their bulk transfer was interrupted by safety checks during this pass. They remain discovered and should be retained under a LEGACY lineage, because the Final Model Freeze explicitly supersedes blind use of the earlier matrix.

## BTC search result

The BTC Daily/Weekly/Monthly Tracker is clearly present and recovered from prior pass.

However, this pass did NOT find a distinct surviving file explicitly named as a BTC Game L1/L2/L3 implementation. That means the BTC Game currently remains a conversation-derived/research family unless another artifact surfaces.

Do not silently rename the Tracker into “BTC Game.”

## Recovery methodology refinement

Search misses are now meaningful only after multiple semantic variants, but still do not prove nonexistence.

Use three statuses:
- FOUND_ARTIFACT
- CONVERSATION_DERIVED_NO_FILE_YET
- SEARCH_PENDING / POSSIBLY_MISSING

This is especially important for BTC Game, crypto ETH/SOL transfer tests, and some B4/B5 CSV surfaces.

## Next dig targets

- additional phase ledgers across EUR/Oil/BTC/XAU;
- Gold Game legacy Pine through safe isolated transfers;
- Master Game Pine source corresponding to 979-line manual snapshot;
- SPX Universal Matrix source;
- JPY DT geometry source/results;
- Base80 / Wednesday / afternoon-filter source/result artifacts;
- BTC/ETH/SOL crypto transfer results;
- binary scientific artifact manifest;
- visual registry;
- conversation-only result registry.
