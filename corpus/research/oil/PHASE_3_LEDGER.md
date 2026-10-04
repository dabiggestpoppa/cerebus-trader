# CEREBUS OIL — PHASE 3 RESULTS
## Oil-Native Tier Discovery

## Research object
Canonical Monday seed from Phase 2:

**Sunday 18:00 → Monday 14:30 ET**

Primary tier variable:

`seed_ATR = seed_range / prior ATR20`

Usable sample: **190 weeks**

---

# Headline result

A naive linear k-means fit on the full sample is dominated by the March-2026 shock outlier.

Full-sample linear k=3:
- centroids ≈ **0.801 / 1.648 / 8.711 ATR**
- counts **150 / 39 / 1**
- the entire third cluster is effectively one shock week

That is statistically real but **not an operational three-tier system**.

The correct refinement is therefore:

1. isolate the single extreme shock state as a candidate **T4 / no-go flag**;
2. discover T1/T2/T3 on the remaining core distribution.

---

# Core-distribution model comparison

| Space | k | Silhouette | Centroids | Counts |
|---|---:|---:|---|---|
| linear | 2 | 0.639 | 0.801 / 1.648 | 150 / 39 |
| linear | 3 | 0.565 | 0.721 / 1.265 / 2.677 | 116 / 67 / 6 |
| linear | 4 | 0.552 | 0.631 / 0.976 / 1.461 / 2.677 | 76 / 74 / 33 / 6 |
| log | 2 | 0.538 | 0.663 / 1.240 | 98 / 91 |
| log | 3 | 0.541 | 0.569 / 0.922 / 1.591 | 55 / 95 / 39 |
| log | 4 | 0.536 | 0.503 / 0.745 / 1.057 / 1.735 | 31 / 63 / 67 / 28 |

The linear k=2 solution has the best silhouette but is too coarse for the CEREBUS operator ontology.

The **log-space k=3** solution is preferred as the Phase-3 candidate because it:
- gives useful tier sample sizes,
- preserves monotonic weekly expansion behavior,
- avoids allowing the shock tail to define normal T3,
- is more balanced and interpretable than linear k=3.

---

# Candidate normalized tier system

Core log-k3 centroids:
- **T1 centroid ≈ 0.569 ATR**
- **T2 centroid ≈ 0.922 ATR**
- **T3 centroid ≈ 1.591 ATR**

Natural geometric boundaries:
- **T1/T2 ≈ 0.724 ATR**
- **T2/T3 ≈ 1.211 ATR**

Extreme / candidate T4 threshold:
- **≈ 5.694 ATR** from the linear k=4 upper boundary
- only **1 week** in the present sample

## Candidate tier summary

| Tier | n | Median seed ATR | Median seed $ | Median weekly multiplier | Q75 | Q90 | Median weekly $ | Median weekly ATR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| T1 | 55 | 0.582 | $1.42 | 3.04× | 3.75× | 4.42× | $4.04 | 1.73 |
| T2 | 95 | 0.932 | $1.92 | 2.09× | 2.64× | 3.21× | $4.31 | 2.01 |
| T3 | 39 | 1.468 | $2.93 | 1.72× | 2.06× | 2.60× | $5.07 | 2.56 |
| T4 | 1 | 8.711 | $24.10 | 1.56× | 1.56× | 1.56× | $37.48 | 13.55 |

The weekly multiplier ordering is clean:

**T1 > T2 > T3**

- T1: ~**3.04×**
- T2: ~**2.09×**
- T3: ~**1.72×**

This is the same convex scaling form seen in EUR/USD: smaller early-week seed states require larger subsequent multiples to construct the full week.

---

# Bootstrap stability

| Parameter | Median | 95% interval |
|---|---:|---:|
| T1 centroid | 0.566 | 0.519–0.659 |
| T2 centroid | 0.922 | 0.857–1.115 |
| T3 centroid | 1.589 | 1.402–2.357 |
| B12 | 0.725 | 0.670–0.854 |
| B23 | 1.209 | 1.115–1.631 |

Interpretation:
- T1/T2 boundary is fairly stable.
- T2/T3 boundary is less certain because the upper tail is smaller and more regime-sensitive.
- This is exactly why the model should keep normalized coordinates and avoid one permanent raw-dollar threshold.

---

# Regime / raw-dollar translation

The normalized tier system is the model coordinate system.

Raw-dollar equivalents must breathe with prevailing ATR.

Selected regime translations:

- **Post-shock elevated T1**: n=14, median seed=$3.27, IQR=$2.19–$4.56, median weekly multiplier=2.33×
- **Post-shock elevated T2**: n=2, median seed=$5.34, IQR=$5.14–$5.55, median weekly multiplier=2.12×
- **Pre-shock T1**: n=130, median seed=$1.60, IQR=$1.36–$2.12, median weekly multiplier=2.44×
- **Pre-shock T2**: n=35, median seed=$2.81, IQR=$2.39–$3.60, median weekly multiplier=1.72×
- **Shock-transition T1**: n=6, median seed=$4.14, IQR=$3.38–$5.55, median weekly multiplier=3.63×
- **Shock-transition T2**: n=2, median seed=$12.49, IQR=$10.22–$14.77, median weekly multiplier=1.06×
- **Shock-transition T3**: n=1, median seed=$24.10, IQR=$24.10–$24.10, median weekly multiplier=1.56×

Do **not** freeze one raw-dollar T1/T2/T3 boundary across 2022–2026.

---

# Candidate T4 / no-go class

The full sample contains one extreme seed at approximately **8.711 ATR** with a raw Monday seed around **$24.10** and final weekly range around **$37.48**.

Candidate extreme rules were tested using:
- Q90
- Q95
- k=4 upper boundary
- median + 2 robust-sigma

The k=4 upper boundary of **~5.694 ATR** isolates only that one week.

### Phase-3 decision
**Do not freeze T4 as a predictive tier yet.**

For now:
- T1/T2/T3 = normal operator tiers
- seed ≥ ~5.7 ATR = **SHOCK / EXTREME FLAG**
- treat it as a no-go / special-state candidate until Phase 4–5 proves incremental forecasting value

A one-observation T4 cannot support a reliable multiplier distribution.

---

# Frozen Phase-3 candidate ontology

### T1
`seed_ATR < 0.724`

### T2
`0.724 ≤ seed_ATR < 1.211`

### T3
`1.211 ≤ seed_ATR < 5.694`

### SHOCK / EXTREME
`seed_ATR ≥ 5.694`

Important:
The **5.694** threshold is provisional because it is defined by one extreme observation. It is a protective state flag, not yet a production forecasting class.

---

# What this means

Oil's normalized Monday-seed topology is now much cleaner than the raw-dollar distribution suggested.

The structural form is:

`small seed → larger weekly multiple`
`medium seed → medium weekly multiple`
`large seed → smaller weekly multiple`

This is exactly the kind of convex weekly scaling architecture we wanted to discover independently.

The war-shock week does **not** redefine normal T3 once it is isolated.

---

# Phase 3 status

- ATR-normalized tier geometry: **candidate frozen**
- T1/T2/T3 ordering: **strong**
- exact T1/T2 boundary: **reasonably stable**
- exact T2/T3 boundary: **moderate uncertainty**
- raw-dollar boundaries: **not stationary**
- T4 predictive class: **not supported yet**
- shock/no-go flag: **supported as a protective classification**

---

# Next — Phase 4

Build the progressive oil information curve using:
- Monday seed tier,
- Sunday→Tuesday 09:00 challenger,
- Tuesday RTH,
- Wednesday overnight / RTH checkpoints,
- final range OOS error,
- median range already consumed,
- median range remaining,
- regime stability,
- strict no-Thursday/Friday discovery.

The goal is to identify the earliest useful oil **reforecast / lock window**, not simply the latest checkpoint with the smallest error.