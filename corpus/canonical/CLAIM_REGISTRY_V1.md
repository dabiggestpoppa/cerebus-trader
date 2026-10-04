# CEREBUS CLAIM REGISTRY V1

Status: ACTIVE CANONICALIZATION
Date:2026-10-04

Purpose: route bounded claims to models and evidence without letting a statistic float free of its identity.

| Claim ID | Model | Claim | Evidence | Status | Layer |
|---|---|---|---|---|---|
| CL.EUR.HO.D3_DIRECTION | EUR.HIGHER_ORDER.V1 | D3 state informs eventual quarter close direction | EV.EUR.HO.D3_DIRECTION.V1 | FORWARD_OOS | L3 |
| CL.EUR.HO.UNFINISHED_M3 | EUR.HIGHER_ORDER.V1 | unfinished side often completes in M3 | EV.EUR.HO.UNFINISHED_M3.V1 | FORWARD_OOS | L3 |
| CL.EUR.HO.M1_RANGE_CORR | EUR.HIGHER_ORDER.V1 | M1 range magnitude informs final quarter range magnitude | EV.EUR.HO.M1_RANGE_CORR.V1 | VALIDATED | L3 |
| CL.EUR.DAILY.TIER_CALIBRATION | EUR.DAILY.NEWS_REKEY.V1 | Phase1 Asian-range tiers calibrate daily distribution | EV.EUR.DAILY.PHASE1_TIERS.V1 | VALIDATED | L1 |
| CL.EUR.DAILY.NEWS_INCREMENT | EUR.DAILY.NEWS_REKEY.V1 | residual event field adds incremental classification information | EV.EUR.DAILY.NEWS_AUC.V1 | CANDIDATE | L1 |
| CL.EUR.WEEKLY.TIER_RANGE | EUR.WEEKLY.V1_1 | weekly tier conditions final range distribution | EV.EUR.WEEKLY.TIER_RANGE.V1 | VALIDATED_RESEARCH | L2 |
| CL.XAU.PROMOTION.68_80 | XAU.GAME.L1_L2_L3.V1 | 68+8h state promotes path toward80 | EV.XAU.PROMOTION.68_80.V1 | VALIDATED_SMALL_N | L2 |
| CL.XAU.PROMOTION.120_132 | XAU.GAME.L1_L2_L3.V1 | 120+8h state promotes path toward132 | EV.XAU.PROMOTION.120_132.V1 | RESEARCH_FLAG_SMALL_N | L2 |
| CL.JPY.CARRY.ROLE_RELATION | JPY.CARRY_GAME.L1_L3.V1 | primary pair agreement and EURJPY confirmation support role architecture | EV.JPY.CARRY.BASKET_RELATION.V1 | VALIDATED_RELATIONSHIP | CROSS_LAYER |
| CL.FIB.R11.GENERATOR_FAILURE | CROSSASSET.FIB.RANGE_BIRTH.V1 | generic local pivot generator overproduced anchors | EV.FIB.R11.ANCHOR_OVERGEN.V1 | NEGATIVE_EVIDENCE | L1_L2 |

## Retrieval rule
A numerical answer should resolve:
query -> canonical model -> claim -> evidence.
If no Evidence Card exists, state the knowledge is model doctrine/research context rather than a verified numerical claim.

## Conflict rule
Conflicts are only direct contradictions when event identity, conditioning population, clock, tolerance, horizon and implementation semantics match closely enough to compare.
Otherwise retain both as separate claims/generations.

## Promotion rule
No claim becomes CANONICAL_VERIFIED because it appears in an infographic, manual, indicator constant, Monte Carlo, journal or historical summary alone.
