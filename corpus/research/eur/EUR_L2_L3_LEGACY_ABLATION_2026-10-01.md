# EUR L2/L3 Legacy Setup Ablation — 2026-10-01

## Purpose
Test the older CEREBUS Game setup families against the newer EUR weekly/higher-order state engine before allowing them into the quarterly indicator.

## L2 weekly legacy setup test
Recent EURUSD M15 sample: 2022-11-08 through 2026-07-14. Research clock reconstructed as server -7h, consistent with the frozen EUR stack.

### Results
| Legacy setup | N | +0.25 MR | +0.50 MR | +1.00 MR | New-filter result | Decision |
|---|---:|---:|---:|---:|---|---|
| Weekly Coiled Spring | 7 | 100% | 100% | 85.7% | All 7 were compatible with directional-third + Behind/Normal pace | Keep only as small-N research flag |
| Weekly Deep Reset | 2 | 100% | 100% | 50.0% | Both compatible | Park: N too small |
| Weekly Standard Rekey | 8 | 100% | 87.5% | 75.0% | Filtered N=3: 100% to +0.50 and +1.00 | Promising, but park as primary setup due small N |
| Weekly Standard Breath | 14 | 100% | 71.4% | 50.0% | New filter did not improve it | Park old name; modern directional state is cleaner |
| Weekly Exhausted Snap | 18 | 61.1% | 33.3% | 0% | Monday midpoint actually reached only 1/18; filtered 1/5 | Reject / park |

A broad T2 Wednesday OCC that did not fit the old Breath/Rekey labels produced strong continuation on its own, which supports the newer conclusion that **location + pace + range-left** are more fundamental than the old pattern names.

### L2 decision
Core V1.2 setups use the newer weekly states:
- Upper-third continuation
- Lower-third continuation
- Tier-specific prime-window reload (Behind/Normal pace)
- Middle-third + Ahead/Extreme Ahead exhaustion / no-edge

Legacy Coiled Spring remains optional as a research flag only. Other old weekly names are parked unless new independent sample size justifies revival.

## L3 legacy macro tier ablation
Long-history EURUSD H1: 59 complete quarters, 2005 Q3–2020 Q1.
Legacy first-3-day macro tiers tested with EUR thresholds:
- T1 <= 108.1 pips
- T2 108.1–177.7 pips
- T3 > 177.7 pips

### Results
| Legacy macro tier | N | D1-D3 -> quarter direction | M2 reaches +1.0 seed range | Median M2 continuation | Interpretation |
|---|---:|---:|---:|---:|---|
| T1 compressed | 16 | 81.3% | 81.3% | 3.31x | Useful compression filter on the newer M1 seed continuation state |
| T2 rotation | 18 | 66.7% | 77.8% | 1.70x | Mixed; useful as shaping context, not standalone destination setup |
| T3 shock | 25 | 68.0% | 40.0% | 0.55x | Old War-Premium label too broad; newer M2/M3 geometry is better |

For external M2 rejection/re-entry, midpoint delivery after re-entry was 75% in T2 (12/16) and 73.3% in T3 (11/15), but the old "Macro Fade" definition is too loose to promote as a primary setup without stricter trigger/stop geometry.

### L3 decision
Core V1.2 setup engine:
- M1 Seed Continuation
- M1 Seed Reload candidate
- M2 Continuation
- M2 Normal Reload (early 25–50% M1 rekey)
- M2 Deferred Resolution (50%+ rekey)
- M3 Resolution Continuation
- M3 Repair (68%+)
- Monthly Snap AOI (100–110%)
- 120 -> 132 promotion after 8h+ acceptance
- 132 -> 168 deep rekey after 8h+ acceptance

Legacy T1 compressed seed is retained only as a **research flag** because it increased D1-D3 quarter-direction accuracy to 81.3% in N=16. The old Macro Fade and War Premium Chain names are parked.