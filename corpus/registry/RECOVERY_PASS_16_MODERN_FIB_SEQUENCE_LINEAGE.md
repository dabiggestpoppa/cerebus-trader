# FORGE RECOVERY PASS 16 — MODERN FIB SEQUENCE RECONSTRUCTION + VISUAL LINEAGE

Date: 2026-10-04

## Search strategy change
Per recovery guidance, do not burn recovery time forcing the six ASE expressions out of the historical workbook.
Likely sources are:
- larger Lab/Master research branch;
- later reconstruction files;
- infographics/visual artifacts;
- conversation-derived research not represented in the 97-sheet workbook.

## 1. Major modern reconstruction artifact found
CEREBUS_FIB_SEQUENCE_PROGRESS_R11.md

Objective:
common EURUSD/XAUUSD/BTCUSD reconstruction of Alpha/Beta/Gamma/Delta sequence geometry, delivery clocks, MAE/MFE, realistic frequency, and staged execution.

This is substantially more useful than trying to infer modern sequence behavior from the old workbook.

## 2. Delivery-clock result
Across EUR/XAU/BTC, most eventual 24h winners in promoted legs were already complete by 4h.

Examples:
A-B Beta/Delta ~96.5-97.2% of eventual winners complete by 4h.
B-C Delta ~96.3-96.7%.
B-C Gamma ~91.1-91.7%.
B-C Alpha ~87.5-87.9%.
C-D promoted families mostly ~96-98%.

Interpretation in source:
old 2-4h C-D failure clock is strongly supported.
4h degradation/time-stop deserves formal test.

## 3. MAE/MFE recovered
Normalized winner MAE is stable cross-asset.

Typical median winner MAE:
- A-B Beta/Delta ~9%R
- B-C Delta ~12%R
- B-C Gamma ~15-16%R
- B-C Alpha ~17%R
- C-D Delta ~12%R
- C-D Alpha ~13-15%R
- C-D Gamma ~16-17%R

This gives empirical stop-design evidence instead of blindly using named fib nodes.

## 4. Critical negative finding — anchor over-generation
Current local-pivot A-B generator produces unrealistic frequency even after collapsing simultaneous signals and limiting open positions:
- EUR ~81 trades/week
- XAU ~75/week
- BTC ~102/week

Conclusion from source:
sequence geometry appears robust, but generic local-pivot A-B generation overproduces active ranges.

Main unresolved rule:
WHICH A-B RANGES ARE LEGITIMATE SEQUENCE ANCHORS?

This is likely the missing qualification layer behind old initiation/timing/pattern language.

Do not patch with arbitrary cooldowns.

## 5. Modern sequence hierarchy
Structural:
- A-B leader: Alpha
- B-C leader: Beta
- C-D leader: Delta
- full raw sequence leader: Delta

Standalone:
- A-B Beta/Delta 50-node geometry viable but anchor qualification unresolved
- B-C Gamma/Delta strongest expectancy candidates
- Alpha B-C higher-WR/lower-RR alternative
- C-D Delta strongest overall
- Beta more useful as structural B-C state than best direct execution family

Same-family staged:
Delta leads across EUR/XAU/BTC.

Approx staged expectancy per B-C entry:
EUR Alpha +0.20R / Gamma +0.34R / Delta +0.35R
XAU +0.19 / +0.35 / +0.40
BTC +0.22 / +0.36 / +0.39

C-D availability after B-C:
Alpha ~28-29%
Gamma ~27-28%
Delta ~41-43%

## 6. Anchor qualification search space
R11 identifies the actual reverse-engineering targets:
- initiation hour
- impulse cleanliness
- minimum ATR-normalized range
- bars required to form A-B
- first touch vs repeated range
- session-local initiation
- whether A-B originates from previous sequence/rekey rather than arbitrary local pivot

A correct rule should reduce signal count drastically while preserving sequence rates cross-asset.

## 7. Visual artifact confirms sequence semantics
Cerebus Fibonacci Sequence Trading Blueprint.png explicitly preserves four named panels:
ALPHA / BETA / GAMMA / DELTA
with A→B→C→D leg structure and rekey context.

The visual states sequences operate inside active measured range until invalidated/rekeyed at 132%.

This is strong semantic/lineage evidence, but any percentages printed on the visual remain historical unless matched to frozen research.

## 8. State-space visual recovered
Cerebus: Time Carries Information.png states:
- market is a state-transition system
- TIME = WEIGHTING
- STATE = GEOMETRY
- TRANSITION = REALITY
- time influences probability of admissible next path rather than creating geometry.

This is a mature explanatory artifact connecting early Markov intuition to later state-age/semi-Markov research.

## 9. Important separation
Do not collapse:
A. old workbook Atomic Pattern AP-001..AP-012
B. Alpha/Beta/Gamma/Delta Fib Sequence families
C. ASE six cycle expressions
D. modern sequence reconstruction

They may share ancestry, but direct identity requires evidence.

## 10. Recovery direction
Shift next passes toward:
- Lab/Master branch artifacts
- Fib Sequence R-series
- infographics
- scientific PDFs
- model/research progress freezes
rather than exhausting historical workbook ambiguities.

Workbook remains useful for provenance, but modern reconstruction files should receive priority for current lineage.
