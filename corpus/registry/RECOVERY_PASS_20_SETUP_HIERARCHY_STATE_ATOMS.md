# FORGE RECOVERY PASS 20 — SETUP HIERARCHY + STATE ATOMS + JOURNAL SEARCH

Date: 2026-10-04

## 1. Standalone quant-lab repository checked
Current standalone dabiggestpoppa/quant-lab main tree does not surface literal journal/bible/ontology/Markov/P14/P15 naming hits.
The large corpus remains larger-lab/quant-lab.

This does not close the Quant Journal search. Branch/history/different naming remains possible.

## 2. Daily Setup layer recovered
CEREBUS_STRATEGY_ANALYSIS contains explicit Daily Setups 1-6 generation.

Setup 1 — First Breakout Close
917 days:
-25 89.2
-50 78.4
-100 64.1
on-time before12 84.9
avg -50 time 4.2h
80%+2p invalidation12.3.

Tier -50:
T1 84.6 / 3.1h
T2 79.1 / 4.5h
T3 68.5 / 6.8h.

Regime:
confirmed >=1.5x ->86.7
caution1.45-1.49 ->74.6
failed<1.45 ->59.3.

These are HISTORICAL REPORT CLAIMS.

## 3. Setup 2 — Temporal Delivery + EWS
T1:
mean -50 3.1h, median2.8h, edge thin if -25 absent by3h, EWS exit if -50 absent by4.2h.
T2:
mean4.6, median4.1, edge thin4.4, EWS exit6.2.

EWS at target is explicitly momentum exhaustion, NOT automatically a reversal.

This distinction is important lineage for later “opposite signal != opposite trade” doctrine.

## 4. Setup 3 — T3-specific behavior
N216 T3 days:
-25 81.5
-50 68.5
-10048.1
on-time72.3
avg -50 6.8h
invalidation18.9.

Important state dependence:
EWS at -25 ->73.2% continuation, treated as noise.
EWS at -50 ->41.8% continuation, treated as exhaustion.

Same event has different meaning conditional on location/state.

## 5. Setup 4 — Cascade EWS
917 days, 142 events (15.5%):
raw reversal entry64.8
trim/exit effectiveness78.4
avg reversal +1.18R
FAILED regime + cascade EWS77.1.

Patterns:
False Cascade32.4
Exhaustion Cascade49.3
Regime Flip Confirmation18.3.

Source verdict:
opposite cascade is not sufficient reversal signal.
A reversal requires additional state confirmation.

This is another direct ancestor of later conditional transition modeling.

## 6. Setup 5 surfaced
Setup 5 is a first-five-trading-days monthly anchor / monthly constraint-resolution model.

This should be cross-linked to the later EUR quarterly/monthly seed work, but not assumed identical until the rest of Setup5 is recovered.

## 7. Implementation state machine
The strategy analysis contains an implementation transition graph including:
SCANNING
failure TYPE1 stand-down
TYPE2 same-side re-entry
TYPE3 opposite flip after 2h
NO_GO
KILL_SWITCH
HARD_EXIT
CLOSED.

This gives another formal state-machine representation of the old CEREBUS generation.

## 8. Historical implementation priorities
Source recommended:
1 First Breakout Close
2 P90 Cascade
3 Dual Engine
4 Regime Filter
5 Failure Repair
6 Macro Setup5.

This is useful historical hierarchy because it distinguishes baseline signal from successive context layers.

## 9. State Atom Dictionary recovered
Later Quant Lab MECH-6 provides a clean ontology implementation pattern.

Canonical state axis examples:
BTC_CONCENTRATION
MIXED_NO_CLEAR_ROUTE
BROAD_RISK_EXPANSION
STABLECOIN_PARKING
ETH_BROADENING
NARROW_LEADERSHIP
LARGE_ALT_ROTATION
MID_CAP_ROTATION
CAPITAL_EXIT
SMALL_CAP_ROTATION.

Coordinate axes are explicitly separated:
BREADTH
RANK
CONCENTRATION
ETH-relative
BTC background.

This is a valuable design pattern:
STATE != one monolithic score.
State can be composed from orthogonal coordinate axes.

## 10. Priority-based microstate composition
MECH-6 uses a first-satisfied priority:
RANK_RECRUITMENT
BREADTH_FADE
BREADTH_EXPANSION
CONCENTRATION_REBUILD
CONCENTRATION_RELEASE
ETH_IMPROVING
ETH_WEAKENING
BTC_SUPPORT
BTC_WEAKNESS
NEUTRAL.

Priority is justified by earlier evidence: depth/breadth route gates before intermediate concentration/ETH and BTC background.

This shows how ontology became executable.

## 11. PIT discipline
State atoms are computed point-in-time.
Missing values excluded, not imputed.
Thresholds fixed/preregistered in that study rather than fit to outcomes.

This is a major methodological improvement over older narrative model generations and should inform FORGE evidence metadata.

## 12. Important hierarchy distinction
Three different hierarchies now recovered:

A. Semantic evidence hierarchy:
Instance -> Sequence -> Pattern -> Formation -> Structure.

B. Market field hierarchy:
Global constraint -> breadth/dispersion -> state age -> route gates -> perturbation -> health -> microstate -> peers -> clocks -> exit/reentry/propagation.

C. Executable state hierarchy:
continuous coordinates -> axis atoms -> composite microstate -> transition/path outcomes.

FORGE should preserve all three instead of flattening them into one ontology.

## 13. P14/P15 status
Literal standalone P14/P15 files were not present under current larger-lab tree.
Their content appears incorporated into consolidated strategy/manual artifacts:
- Blind Structural Chain / Recursive Loop generation referenced in the Parts map
- Part15/Atomic Market Structure embedded in CEREBUS_STRATEGY_ANALYSIS.

Do not spend excessive time assuming a missing filename must exist.

## 14. Recovery implication
The corpus is beginning to separate naturally into:
- OBSERVATION DATA
- MEASUREMENT/FEATURES
- STATE ATOMS
- TRANSITIONS/PATHS
- SETUPS/EXECUTION
- MODELS
- RESEARCH DOCTRINE
- ONTOLOGY/HIERARCHY
- GOVERNANCE/FREEZE STATUS
- VISUAL/TEACHING ARTIFACTS.

This should become the top-level FORGE corpus classification.

## Next
- recover remainder Setup5 + Setup6
- recover Dual/Triple Engine and Float mechanisms
- search git branches/history for journal artifacts
- inspect raw P90 JSON
- map old CEREBUS state labels into modern state-atom/field ontology
- begin a formal ONTOLOGY_CROSSWALK registry once enough terms are recovered.
