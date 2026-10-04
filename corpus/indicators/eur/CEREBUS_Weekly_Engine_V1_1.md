# CEREBUS Weekly Engine V1.1

This Markdown file contains the **same Pine Script v6 indicator code** as `CEREBUS_Weekly_Engine_V1_1.pine`, so it can be read and reviewed directly.

## What changed from V1
- Replaced the temporary pace proxy with the **exact 104-week Hour × Tier Median/MAD lookup**.
- Embedded all **288 H1–H96 × T1/T2/T3 states**.
- Added exact robust sigma:
  `z = (PrintedRange - Median(Hour,Tier)) / (1.4826 × MAD(Hour,Tier))`
- Added exact Hour × Tier remaining-range Q50/Q75/Q90.
- Added exact Hour × Tier probability of another weekly extreme.
- Added pace states: **Behind / Normal / Ahead / Extreme Ahead**.
- Added exhaustion rule: **Middle Third + Ahead/Extreme Ahead = Weekly Exhaustion / No Edge**.
- Added tier-specific prime quality windows:
  - T1: H58–H60
  - T2: H64–H67
  - T3: H58–H62

## Pine Script

```pine
//@version=6
indicator("CEREBUS Weekly Engine V1.1", overlay=true, max_lines_count=100, max_labels_count=100)

// ============================================================================
// CEREBUS WEEKLY ENGINE V1.1
// Frozen weekly matrix + exact 104-week Hour × Tier Median/MAD pace engine
// Timezone: America/New_York
//
// Architecture:
//   1) SIZE      -> Monday Asian range × tier-specific Q50/Q75/Q90 factors
//   2) RANGE LEFT-> Exact Hour × Tier remaining-range lookup
//   3) SIDE      -> Weekly close location (upper/middle/lower third)
//   4) PACE      -> Exact robust sigma from Hour × Tier Median/MAD
//   5) EXHAUSTION-> Middle Third + Ahead/Extreme Ahead
//
// Pace formula:
//   z = (PrintedRange - Median(Hour,Tier)) / (1.4826 × MAD(Hour,Tier))
//
// Frozen current reference:
//   104-week Hour × Tier table, 288 states = 96 hours × 3 tiers
// ============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// Inputs
// ─────────────────────────────────────────────────────────────────────────────
string TZ = input.string("America/New_York", "Timezone")
bool showDashboard = input.bool(true, "Show dashboard")
bool showWeeklyLevels = input.bool(true, "Plot Monday-base weekly Q50/Q75/Q90 bands")
bool showLocationBands = input.bool(false, "Plot current weekly thirds")
bool showLabels = input.bool(true, "Show checkpoint labels")

float tier1Max = input.float(20.0, "T1 max Monday Asian range (pips)", step=0.1)
float tier2Max = input.float(30.0, "T2 max Monday Asian range (pips)", step=0.1)
float tier3Max = input.float(45.0, "T3 max Monday Asian range (pips)", step=0.1)

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────
f_pips(float x) =>
    x / syminfo.mintick / 10.0

f_price_from_pips(float p) =>
    p * syminfo.mintick * 10.0

f_prob_fmt(float x) =>
    na(x) ? "—" : str.tostring(x, "#.0") + "%"

f_pip_fmt(float x) =>
    na(x) ? "—" : str.tostring(x, "#.1") + "p"

// ─────────────────────────────────────────────────────────────────────────────
// Frozen 104-week Hour × Tier lookup arrays
// Flattening convention:
// index = (hour-1)*3 + (tier-1), with hour H1..H96 and tier 1..3
// ─────────────────────────────────────────────────────────────────────────────
var float[] MEDIAN_RANGE = array.from(
    8.9, 8.9, 10.6, 12.1, 14.3, 17.35, 14.2, 15.8, 20.25, 16.6, 19.85, 23.4,
    16.6, 22.4, 25.45, 16.6, 22.8, 30.65, 18.2, 22.8, 34.65, 18.2, 25.85, 34.65,
    18.6, 25.85, 35.1, 19.4, 28.05, 39.55, 25.8, 33.2, 43.75, 30.1, 37.35, 46.1,
    33.4, 38.75, 50.55, 33.4, 40.35, 53.65, 33.4, 43.05, 57.5, 35.6, 47.15, 62.25,
    37.7, 52.35, 63.2, 42.5, 52.8, 66.45, 44.9, 54.55, 71.15, 44.9, 56.7, 71.15,
    44.9, 57.25, 72.25, 44.9, 58.7, 72.3, 45.6, 59.15, 72.55, 45.6, 59.15, 72.55,
    45.6, 60.2, 72.55, 45.6, 60.2, 72.55, 45.6, 60.2, 72.55, 48.6, 60.2, 73.8,
    48.6, 60.2, 76.5, 48.6, 60.2, 78.55, 48.6, 60.2, 78.55, 48.6, 60.2, 78.55,
    48.6, 60.2, 78.55, 48.6, 60.2, 78.55, 48.6, 61.25, 84.7, 48.6, 63.7, 84.7,
    48.6, 64.4, 84.7, 51.7, 65.95, 84.7, 51.9, 65.95, 86.85, 59.9, 65.95, 86.85,
    59.9, 70.15, 88.7, 68.1, 74.5, 96.7, 68.1, 75.95, 98.15, 68.1, 75.95, 105.65,
    68.1, 75.95, 106.05, 68.1, 75.95, 106.05, 68.1, 76.9, 106.05, 68.1, 76.9, 106.05,
    68.1, 77.95, 106.05, 68.1, 77.95, 107.55, 68.1, 77.95, 107.55, 68.1, 78.9, 108.85,
    68.1, 78.9, 108.85, 68.1, 78.9, 111.9, 68.1, 78.9, 111.9, 68.1, 78.9, 112.4,
    68.1, 78.9, 114.35, 68.1, 79, 114.8, 68.1, 82.05, 119.85, 68.7, 84.15, 119.85,
    68.7, 85.85, 119.85, 68.7, 86.25, 119.85, 68.7, 86.25, 119.85, 68.7, 86.9, 121.05,
    69.6, 87.5, 123.65, 69.6, 89.1, 123.65, 70.6, 91.65, 125.15, 72.5, 92.45, 128,
    75.1, 95.9, 130, 90.9, 98.3, 136.4, 92.5, 98.95, 136.4, 92.9, 98.95, 140.7,
    92.9, 98.95, 140.7, 92.9, 99.65, 140.7, 92.9, 100.4, 140.7, 92.9, 100.4, 141.1,
    92.9, 100.4, 141.1, 92.9, 100.4, 141.1, 92.9, 100.4, 141.1, 92.9, 100.9, 143.05,
    92.9, 100.9, 143.05, 92.9, 100.9, 143.05, 92.9, 100.9, 143.05, 92.9, 100.9, 143.05,
    92.9, 102.95, 143.05, 98, 104.4, 143.05, 101, 104.4, 143.05, 103.3, 111.05, 143.05,
    119.3, 111.05, 143.05, 119.3, 111.05, 149.7, 119.3, 114.85, 150.2, 119.3, 116, 151.6,
    119.3, 119.4, 154.4, 119.3, 119.4, 157.65, 119.3, 120.5, 157.65, 119.3, 121.75, 157.65
)
var float[] MAD_RANGE = array.from(
    4.7, 3.35, 2.85, 3.9, 3.75, 4.4, 2.9, 3.8, 4.7, 3.1, 5.45, 4.45,
    3.4, 5.9, 5.05, 2.3, 5.25, 7.2, 2.6, 5.1, 8.25, 2.6, 4.7, 7.6,
    3, 4.7, 7.85, 2.5, 4.35, 4.65, 6, 3.95, 7.55, 10, 5.9, 10.1,
    12.1, 8.05, 11.65, 12.1, 8.3, 11.25, 11.4, 10.55, 14.65, 10, 10.25, 13.95,
    12.5, 9.35, 15.35, 15.6, 9.8, 14.35, 15.3, 7.75, 13.7, 15.5, 8.3, 13.7,
    13.4, 9.15, 14.5, 13.4, 9.2, 16, 13.7, 9.65, 16.25, 13.7, 9.9, 16.1,
    13.7, 10.5, 18.4, 13.7, 10.5, 18.4, 13.7, 10.5, 20.3, 14.7, 11.1, 21.55,
    14.7, 14, 23.15, 14.7, 14, 21.65, 16.7, 13.55, 21.65, 16.4, 12.35, 21.65,
    15.8, 10.7, 21.65, 13.8, 10.7, 23.9, 12.6, 11.75, 22.3, 12.6, 12.95, 24.25,
    12.6, 12.95, 24.3, 15.1, 14.15, 24.3, 14.9, 12.85, 24.7, 12.5, 12.85, 24.7,
    13.6, 12.95, 30.1, 16.4, 12.25, 24.45, 16.4, 11.35, 25.65, 16.4, 11.35, 27.3,
    16, 11.1, 27.35, 16, 11.35, 28.6, 19.5, 12.3, 28.25, 19.5, 12.3, 28.25,
    19.5, 13.35, 28.25, 19.5, 13.35, 31.35, 19.5, 13.35, 28.25, 19.5, 14.3, 29.6,
    19.5, 14.3, 32.65, 19.5, 14.3, 34.15, 19.5, 14.3, 34.15, 17.8, 14.3, 33.65,
    25.2, 14.6, 31.7, 25.2, 14.6, 33.6, 21.9, 17.1, 35.6, 25.5, 18.4, 35.85,
    32, 15.05, 35.85, 32.3, 15.05, 36.45, 32.3, 18.4, 35.85, 24.2, 15.05, 33.85,
    25.1, 15.05, 33.85, 24.5, 14.65, 37.3, 26.1, 13.7, 35.4, 27.4, 14.5, 35.4,
    25.9, 17, 34.4, 29.9, 12.85, 33.55, 31.5, 14.95, 33.55, 31.9, 15.9, 32.3,
    31.9, 17.5, 32.3, 31.9, 17.9, 31.25, 31.9, 18.55, 31.25, 31.9, 18.55, 32.25,
    31.9, 19.4, 32.25, 31.9, 19.4, 32.25, 27.4, 19.4, 32.25, 27.4, 19.55, 33.65,
    27.4, 19.55, 33.65, 27.4, 19.55, 34.7, 27.4, 16.1, 34.7, 24.2, 16.1, 34.7,
    27.4, 16, 38.05, 29.3, 18.85, 37.7, 31, 18.85, 36.95, 28.1, 18.6, 33.65,
    43.7, 21.3, 33.1, 44.1, 21.3, 29.55, 44.1, 22.55, 32.05, 44.1, 23.3, 32.05,
    44.1, 25.75, 32.9, 44.1, 25.75, 33.8, 44.1, 26.85, 34.75, 44.1, 26.7, 34.75
)
var float[] ROBUST_SIGMA = array.from(
    6.96822, 4.96671, 4.22541, 5.78214, 5.55975, 6.52344, 4.29954, 5.63388, 6.96822, 4.59606, 8.08017, 6.59757,
    5.04084, 8.74734, 7.48713, 3.40998, 7.78365, 10.67472, 3.85476, 7.56126, 12.23145, 3.85476, 6.96822, 11.26776,
    4.4478, 6.96822, 11.63841, 3.7065, 6.44931, 6.89409, 8.8956, 5.85627, 11.19363, 14.826, 8.74734, 14.97426,
    17.93946, 11.93493, 17.27229, 17.93946, 12.30558, 16.67925, 16.90164, 15.64143, 21.72009, 14.826, 15.19665, 20.68227,
    18.5325, 13.86231, 22.75791, 23.12856, 14.52948, 21.27531, 22.68378, 11.49015, 20.31162, 22.9803, 12.30558, 20.31162,
    19.86684, 13.56579, 21.4977, 19.86684, 13.63992, 23.7216, 20.31162, 14.30709, 24.09225, 20.31162, 14.67774, 23.86986,
    20.31162, 15.5673, 27.27984, 20.31162, 15.5673, 27.27984, 20.31162, 15.5673, 30.09678, 21.79422, 16.45686, 31.95003,
    21.79422, 20.7564, 34.32219, 21.79422, 20.7564, 32.09829, 24.75942, 20.08923, 32.09829, 24.31464, 18.31011, 32.09829,
    23.42508, 15.86382, 32.09829, 20.45988, 15.86382, 35.43414, 18.68076, 17.42055, 33.06198, 18.68076, 19.19967, 35.95305,
    18.68076, 19.19967, 36.02718, 22.38726, 20.97879, 36.02718, 22.09074, 19.05141, 36.62022, 18.5325, 19.05141, 36.62022,
    20.16336, 19.19967, 44.62626, 24.31464, 18.16185, 36.24957, 24.31464, 16.82751, 38.02869, 24.31464, 16.82751, 40.47498,
    23.7216, 16.45686, 40.54911, 23.7216, 16.82751, 42.40236, 28.9107, 18.23598, 41.88345, 28.9107, 18.23598, 41.88345,
    28.9107, 19.79271, 41.88345, 28.9107, 19.79271, 46.47951, 28.9107, 19.79271, 41.88345, 28.9107, 21.20118, 43.88496,
    28.9107, 21.20118, 48.40689, 28.9107, 21.20118, 50.63079, 28.9107, 21.20118, 50.63079, 26.39028, 21.20118, 49.88949,
    37.36152, 21.64596, 46.99842, 37.36152, 21.64596, 49.81536, 32.46894, 25.35246, 52.78056, 37.8063, 27.27984, 53.15121,
    47.4432, 22.31313, 53.15121, 47.88798, 22.31313, 54.04077, 47.88798, 27.27984, 53.15121, 35.87892, 22.31313, 50.18601,
    37.21326, 22.31313, 50.18601, 36.3237, 21.72009, 55.30098, 38.69586, 20.31162, 52.48404, 40.62324, 21.4977, 52.48404,
    38.39934, 25.2042, 51.00144, 44.32974, 19.05141, 49.74123, 46.7019, 22.16487, 49.74123, 47.29494, 23.57334, 47.88798,
    47.29494, 25.9455, 47.88798, 47.29494, 26.53854, 46.33125, 47.29494, 27.50223, 46.33125, 47.29494, 27.50223, 47.81385,
    47.29494, 28.76244, 47.81385, 47.29494, 28.76244, 47.81385, 40.62324, 28.76244, 47.81385, 40.62324, 28.98483, 49.88949,
    40.62324, 28.98483, 49.88949, 40.62324, 28.98483, 51.44622, 40.62324, 23.86986, 51.44622, 35.87892, 23.86986, 51.44622,
    40.62324, 23.7216, 56.41293, 43.44018, 27.94701, 55.89402, 45.9606, 27.94701, 54.78207, 41.66106, 27.57636, 49.88949,
    64.78962, 31.57938, 49.07406, 65.38266, 31.57938, 43.81083, 65.38266, 33.43263, 47.51733, 65.38266, 34.54458, 47.51733,
    65.38266, 38.17695, 48.77754, 65.38266, 38.17695, 50.11188, 65.38266, 39.80781, 51.52035, 65.38266, 39.58542, 51.52035
)
var float[] PROGRESS_MEDIAN = array.from(
    7.164404, 7.244772, 6.275968, 11.921182, 10.251357, 11.302661, 12.019704, 11.794234, 12.207308, 13.793103, 13.933151, 14.646907,
    14.490446, 15.86921, 15.855187, 14.490446, 16.832069, 19.539738, 14.490446, 18.04617, 20.291339, 14.490446, 19.790202, 20.965908,
    16.081633, 21.024801, 22.099673, 16.081633, 23.102615, 26.16119, 20.658135, 24.339059, 27.130863, 24.048913, 27.714507, 30.535461,
    24.369422, 29.409263, 31.930853, 24.369422, 30.829043, 31.930853, 24.588665, 31.898647, 35.30822, 29.061224, 34.509856, 41.480512,
    29.55102, 35.855743, 42.899928, 29.55102, 36.754169, 43.250523, 29.55102, 40.27666, 45.617797, 29.55102, 41.894566, 46.941222,
    33.284672, 41.900237, 46.941222, 33.539095, 42.673124, 51.256301, 34.782609, 43.474896, 51.256301, 34.782609, 43.474896, 51.256301,
    35.869565, 43.474896, 53.190721, 35.869565, 44.056652, 53.574767, 35.869565, 44.056652, 55.141212, 35.869565, 45.089947, 55.272047,
    35.869565, 47.705699, 55.492184, 36.548913, 47.705699, 55.492184, 36.548913, 48.216565, 55.538344, 36.548913, 49.473049, 55.538344,
    36.684783, 51.114439, 55.538344, 37.01979, 51.679763, 55.538344, 41.16242, 52.063493, 56.591619, 41.871921, 53.323691, 59.174691,
    41.871921, 53.323691, 59.174691, 42.367347, 53.323691, 59.36551, 46.467391, 54.598338, 59.36551, 46.467391, 55.655261, 59.36551,
    46.467391, 57.847007, 62.258114, 52.488688, 58.228272, 63.947807, 52.488688, 58.228272, 64.514954, 52.488688, 58.228272, 64.514954,
    52.488688, 58.803103, 64.514954, 52.488688, 59.446666, 65.380862, 52.488688, 59.446666, 66.028768, 52.488688, 60.499298, 66.028768,
    52.488688, 64.699761, 66.028768, 52.488688, 64.699761, 66.657919, 52.488688, 65.12946, 67.468544, 52.488688, 65.12946, 67.468544,
    52.488688, 65.12946, 68.387187, 52.488688, 65.12946, 71.138188, 52.488688, 65.12946, 73.230455, 52.488688, 65.12946, 73.230455,
    52.488688, 65.12946, 73.230455, 52.488688, 65.238333, 74.54059, 52.488688, 65.238333, 75.093182, 55.474453, 66.183667, 75.093182,
    55.591837, 66.183667, 75.424287, 55.591837, 66.183667, 75.424287, 55.591837, 66.183667, 75.424287, 55.836735, 66.233647, 77.718069,
    59.346939, 75.027603, 80.414306, 59.346939, 77.464785, 81.32231, 59.346939, 78.444394, 82.585748, 59.346939, 78.475344, 82.585748,
    65.686275, 79.879011, 82.585748, 68.552036, 80.146549, 86.719818, 69.758673, 80.724002, 86.719818, 70.060332, 80.724002, 86.719818,
    70.060332, 80.724002, 86.719818, 70.060332, 80.724002, 86.719818, 70.060332, 80.724002, 86.719818, 70.060332, 81.267557, 86.719818,
    70.060332, 81.846756, 86.719818, 70.060332, 82.011768, 86.719818, 74.523571, 82.011768, 87.714091, 74.744526, 82.011768, 87.951779,
    74.744526, 82.011768, 87.980951, 74.744526, 84.080342, 88.943611, 74.744526, 84.690691, 89.824105, 74.744526, 84.690691, 90.683099,
    74.744526, 84.848248, 90.860035, 75.426279, 86.119767, 92.166021, 77.673797, 86.498358, 92.166021, 86.058394, 89.110719, 94.122805,
    92.798354, 91.546649, 94.122805, 92.798354, 93.554809, 98.071719, 99.507389, 94.463434, 98.883627, 99.634274, 97.154063, 100,
    100, 99.734043, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100
)
var float[] PROGRESS_MAD = array.from(
    3.413339, 2.496095, 1.623617, 4.327564, 3.56921, 4.478811, 3.022889, 3.337673, 4.608001, 3.082975, 3.811686, 5.18018,
    3.780318, 3.60495, 5.021826, 4.938902, 4.120732, 4.771824, 5.670036, 4.370668, 6.010889, 5.670036, 5.241864, 6.21684,
    5.371505, 5.990633, 7.164851, 5.371505, 5.748007, 6.185447, 6.167689, 7.648254, 6.594, 5.920834, 6.84431, 9.755522,
    4.467944, 7.320896, 9.973647, 4.20894, 7.693257, 9.549659, 2.676641, 7.259722, 10.425439, 4.691803, 8.96504, 12.422175,
    4.962355, 8.863754, 14.132023, 4.962355, 10.150163, 14.10182, 4.962355, 10.79016, 13.516039, 4.962355, 11.770351, 12.424289,
    4.508758, 13.457172, 12.424289, 4.763182, 12.299079, 12.488611, 6.006696, 12.299079, 12.488611, 6.006696, 12.299079, 13.100011,
    6.710516, 12.299079, 12.128775, 6.710516, 13.524953, 12.017729, 6.318545, 13.524953, 12.91596, 6.002356, 13.339834, 13.127146,
    6.002356, 13.043117, 13.347282, 5.323008, 13.043117, 13.347282, 5.253197, 12.783257, 13.393443, 5.253197, 12.202451, 13.393443,
    5.187139, 12.70091, 13.393443, 4.14263, 12.70091, 12.299287, 6.547036, 10.735817, 13.347344, 7.256537, 11.966618, 13.013844,
    8.473587, 12.366454, 13.013844, 7.978161, 13.767372, 13.362982, 9.468244, 13.767372, 15.101037, 9.468244, 12.912314, 16.173041,
    10.860571, 11.684855, 14.346276, 11.326267, 16.393079, 12.672673, 11.326267, 18.187542, 11.730515, 11.326267, 17.916185, 11.712521,
    10.87957, 18.139301, 11.712521, 10.87957, 16.259253, 10.846613, 10.87957, 14.698547, 11.924542, 10.87957, 14.698547, 11.924542,
    10.87957, 16.763585, 11.924542, 10.87957, 16.61762, 9.569556, 10.87957, 16.187922, 10.837949, 10.87957, 15.752271, 11.012917,
    10.87957, 15.752271, 9.53858, 10.87957, 15.752271, 9.502193, 10.87957, 15.752271, 9.871525, 10.87957, 15.752271, 9.871525,
    10.87957, 16.333887, 10.142734, 10.87957, 16.382661, 11.18166, 10.87957, 17.558797, 12.15649, 19.466428, 17.910565, 14.741073,
    19.583813, 17.910565, 14.409968, 19.583813, 18.421386, 15.396327, 19.583813, 19.455326, 15.396327, 11.202833, 18.421386, 15.0406,
    14.713037, 18.42747, 14.596609, 14.713037, 18.778353, 14.728836, 14.713037, 19.757961, 15.038163, 14.713037, 19.788911, 14.464519,
    14.422314, 20.120989, 14.464519, 15.773983, 19.853451, 13.280182, 20.866942, 17.074018, 13.280182, 21.168601, 17.074018, 13.280182,
    21.168601, 18.377335, 13.280182, 21.168601, 19.055707, 13.280182, 21.168601, 18.381359, 13.280182, 21.168601, 18.601651, 13.280182,
    17.703261, 18.153244, 13.280182, 17.703261, 17.988232, 13.280182, 15.176632, 17.988232, 12.285909, 15.397587, 17.988232, 12.048221,
    15.397587, 17.988232, 12.019049, 15.397587, 15.919658, 11.056389, 15.397587, 15.309309, 10.175895, 15.397587, 15.309309, 9.316901,
    13.107697, 15.151752, 9.139965, 13.78945, 13.880233, 7.833979, 16.036968, 13.501642, 7.833979, 13.57588, 10.889281, 5.877195,
    7.201646, 8.453351, 5.877195, 7.201646, 6.445191, 1.928281, 0.492611, 5.536566, 1.116373, 0.365726, 2.845937, 0,
    0, 0.265957, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
)
var float[] REMAIN_MEDIAN = array.from(
    115, 121.2, 152.5, 109.6, 120.15, 137.9, 108.3, 117.25, 136.45, 105.9, 114.15, 131.05,
    105.9, 112.35, 127.15, 105.9, 110.75, 126.55, 105.9, 110.75, 126.55, 105.9, 110.75, 126.45,
    102.8, 109.55, 126.45, 102.8, 101.8, 121.35, 86.8, 95.8, 119.95, 83.1, 88.9, 110.5,
    82.7, 88.9, 106.6, 82.5, 88.1, 103.6, 82.5, 88.1, 98.95, 82.5, 88.1, 92.3,
    82.5, 87.3, 89.6, 82.5, 80.05, 89.25, 82.5, 72.6, 89.25, 82.5, 72.45, 89.25,
    77.5, 70.95, 89.25, 77.5, 69.85, 85.3, 77, 69.85, 85.1, 77, 69.85, 85.1,
    77, 69.85, 82.3, 77, 69.85, 82.2, 77, 69.85, 80.2, 77, 69.85, 80.1,
    77, 69.85, 80.1, 77, 69.85, 80.1, 77, 69.85, 80, 77, 69.85, 79.2,
    75.3, 69.85, 79.2, 73.9, 67.55, 77.9, 73.4, 66.2, 77.9, 73.4, 66.2, 73.4,
    73.4, 66.2, 73.4, 70.9, 66.2, 73.4, 70.9, 59.8, 72, 70.9, 55.45, 63.7,
    64.2, 55.45, 63.7, 63, 52.1, 58.95, 63, 50.65, 56.25, 54.4, 50.65, 56.25,
    54.4, 50.65, 56.25, 54.4, 50.65, 56.25, 54.4, 50.15, 52.8, 54.4, 50.15, 52.8,
    54.4, 50.15, 52.8, 54.4, 50.15, 52.8, 54.4, 50.15, 50.7, 54.4, 49.4, 46.9,
    54.4, 48.15, 46.9, 54.4, 46.9, 45.5, 54.4, 46.9, 44.75, 54.4, 46.9, 44.75,
    54.4, 46.9, 44.75, 54.4, 46.9, 39.6, 54.4, 46.9, 37.55, 54.4, 46.9, 37.55,
    51, 44.4, 37.55, 51, 44.4, 37.55, 51, 43.8, 37.55, 51, 38.15, 28.7,
    46.4, 33.55, 26.4, 46.3, 33.35, 24.55, 40.3, 33.35, 21, 40.3, 33.35, 21,
    40.3, 30.95, 21, 34.6, 28.15, 18.8, 34.6, 28.15, 18.8, 34.6, 28.15, 18.8,
    34.6, 28.15, 18.8, 34.6, 28.15, 18.8, 34.6, 28.15, 18.8, 34.6, 25.9, 18.8,
    34.6, 24.4, 18.8, 34.6, 24.05, 18.8, 27.8, 24.05, 18.8, 27.8, 24.05, 18.8,
    27.8, 24.05, 18.8, 24.5, 23.1, 18.4, 24.5, 21, 15.25, 24.5, 19.95, 15.25,
    24.5, 19.35, 11.9, 24.5, 15.95, 10.6, 24.5, 14.55, 10.6, 10.9, 11.6, 8.1,
    7, 10.75, 8.1, 7, 10, 2.85, 0.7, 7.55, 1.65, 0.5, 4.35, 0,
    0, 0.4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
)
var float[] REMAIN_Q75 = array.from(
    127.7, 153.975, 196.6, 125.1, 151.375, 186.3, 121.7, 148.675, 184.975, 121.7, 146.4, 181.45,
    121.7, 142.65, 181.075, 121.1, 142.65, 181.075, 117.5, 142.65, 181.075, 117.5, 142.65, 181.075,
    117.4, 142.65, 181.075, 117.4, 142.65, 169.575, 115.1, 134.95, 161.2, 115.1, 131.55, 152.5,
    115.1, 124.65, 152.05, 115.1, 117.6, 146.975, 108.1, 117.025, 146.975, 107, 114.95, 130.275,
    107, 112.675, 124.725, 107, 108.85, 122.825, 104.3, 104.3, 122.825, 104.3, 101.875, 118.825,
    104.3, 101.675, 116.05, 104.3, 101.2, 116.05, 104.3, 98.875, 116.05, 104.3, 98.2, 116.05,
    104.3, 97.225, 116.05, 104.3, 96.975, 116.05, 100.1, 96.975, 116.05, 98.7, 96.975, 114.175,
    98.6, 94.95, 114.175, 96, 94.95, 114.175, 96, 94.8, 114.175, 93.7, 94.8, 114.175,
    93.7, 94.775, 113.4, 91.4, 94.775, 113.05, 91.4, 91.3, 108.7, 91.4, 91.3, 105.925,
    91.4, 87.275, 105.275, 91.4, 87.275, 105.275, 91.4, 87.275, 103.4, 81.3, 87.275, 103.4,
    78.1, 87.275, 99.45, 73.9, 87.275, 92.625, 73.9, 85.475, 91.15, 73.9, 85.475, 91.15,
    73.4, 84.725, 91.15, 73.4, 84.725, 91.15, 73.4, 84.725, 88.3, 73.4, 84.725, 88.3,
    73.4, 84.2, 88.3, 73.4, 84.2, 86.45, 73.4, 84.2, 85.725, 73.4, 82.025, 82.5,
    73.4, 82.025, 79.725, 73.4, 82.025, 70.575, 73.4, 82.025, 70.575, 73.4, 82.025, 70.325,
    73.4, 82.025, 69.35, 73.4, 82.025, 65.5, 73.4, 82.025, 65.5, 64.1, 81.15, 65.5,
    64.1, 78.975, 64.225, 64.1, 78.975, 64.025, 64.1, 78.975, 61.75, 64.1, 78.125, 61.75,
    64.1, 78.125, 61.525, 63, 73.3, 60.85, 63, 73.3, 59.675, 60.1, 73.3, 59.3,
    55.2, 69.625, 59.3, 49.8, 64.8, 59.3, 49.8, 61.15, 59.3, 49.8, 61.15, 59.3,
    49.8, 61.15, 59.3, 49.8, 61.15, 59.3, 49.8, 61.15, 58.175, 49.8, 61.15, 55.575,
    47.5, 61.15, 53.425, 47.5, 61.15, 53.425, 40.2, 61.15, 53.425, 40.2, 61.15, 53.425,
    40.2, 61.15, 53.425, 39.7, 61.15, 53.425, 39.7, 61.15, 53.425, 39.7, 61.15, 53.425,
    39.7, 56.3, 45.375, 38, 55.2, 37.425, 38, 49.425, 37.425, 24.5, 35.575, 25.525,
    24.5, 33.25, 22.225, 24.5, 30.925, 22.225, 19.8, 30.925, 18.5, 19.8, 30.925, 18.5,
    19.8, 30.925, 17.225, 19.8, 30.925, 17.225, 19.8, 30.925, 13.65, 19.8, 30.925, 13.65
)
var float[] REMAIN_Q90 = array.from(
    209.6, 180.05, 243.75, 205.88, 171.75, 229.7, 204.74, 171.75, 224.5, 202.82, 163.3, 222.75,
    202.82, 161.55, 222.75, 201.9, 161.55, 212.9, 201.9, 161.55, 212.6, 201.54, 160.55, 212.6,
    201.54, 160.05, 209.15, 198.12, 157.1, 202.15, 188.16, 156.35, 197.4, 182.6, 156.35, 197.4,
    178.1, 156.35, 195.75, 170.14, 156.35, 193.7, 167.46, 155.45, 193.65, 153.2, 151, 188.6,
    149.68, 149, 188.05, 146.36, 147.3, 187.65, 146.36, 147, 181, 145.7, 147, 181,
    145.7, 147, 180.25, 145.7, 146.55, 180.25, 145.7, 146.5, 180.25, 145.7, 146.15, 180.25,
    145.7, 144.65, 180.25, 145.7, 144.65, 180.25, 145.7, 144.65, 180.25, 145.7, 144.65, 180.25,
    145.7, 144.65, 180.25, 143.84, 144.65, 175.35, 138.26, 144.65, 171.75, 138.26, 144.65, 171.75,
    138.26, 143.7, 171.75, 138.02, 143.7, 171.75, 138.02, 143.7, 171.75, 137.54, 143.7, 169.7,
    135.14, 140.85, 169.7, 131.86, 139.45, 169.7, 128.98, 139.45, 156.05, 123.88, 139.45, 153.8,
    116.92, 139.45, 145.45, 114.66, 139.45, 133, 112.38, 139.45, 132.85, 105.92, 139.45, 132.85,
    104.6, 139.45, 132.85, 104.6, 130.55, 132.85, 104.6, 130.55, 121.6, 104.6, 130.55, 119.9,
    104.6, 130.55, 119.9, 104.6, 130.55, 104.1, 104.6, 130.55, 104.1, 104.6, 130.55, 103,
    104.6, 130.55, 98.55, 104.6, 130.55, 98.55, 104.6, 130.55, 98.55, 104.6, 130.55, 98.55,
    104.6, 130.55, 98.55, 104.6, 130.55, 94.7, 104.6, 130.55, 93.85, 104.6, 130.55, 93.85,
    104.6, 130.55, 93.85, 104.6, 128.6, 89.5, 104.6, 128.6, 87.3, 104.6, 128.6, 86.8,
    104.6, 120.1, 81.4, 98.42, 120.1, 73.75, 96.74, 110.25, 72.85, 96.74, 98.5, 72.85,
    96.74, 97.9, 72.85, 71.1, 89.6, 72.85, 71.1, 80.4, 64.35, 71.1, 79.45, 64.35,
    71.1, 79.45, 64.35, 71.1, 79.45, 64.35, 71.1, 79.45, 64.35, 71.1, 77.45, 62.65,
    71.1, 77.45, 62.55, 71.1, 77.45, 62.55, 70.86, 77.45, 62.55, 70.86, 76.2, 62.55,
    67.94, 75.35, 62.55, 67.94, 75.35, 62.55, 67.94, 75.35, 62.55, 67.94, 75.35, 62.55,
    66.98, 75.35, 60.9, 65.72, 75.35, 60.05, 64.7, 75.35, 60.05, 64.7, 70.75, 60.05,
    64.7, 64.65, 56.8, 51.94, 56.3, 55.5, 50.86, 50.45, 55.45, 50.86, 50.05, 55,
    47.32, 50.05, 44.45, 45.88, 50.05, 37.35, 45.88, 47.25, 37.05, 45.88, 46.6, 37.05
)
var float[] P_ANY_EXTREME = array.from(
    100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
    100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
    100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
    100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
    100, 100, 100, 100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222,
    100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222,
    100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222,
    100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222,
    100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222, 100, 100, 97.222222,
    100, 100, 94.444444, 100, 100, 94.444444, 100, 100, 94.444444, 100, 100, 94.444444,
    100, 100, 91.666667, 94.117647, 100, 91.666667, 94.117647, 100, 91.666667, 94.117647, 100, 88.888889,
    94.117647, 100, 88.888889, 94.117647, 100, 86.111111, 94.117647, 100, 83.333333, 94.117647, 100, 83.333333,
    94.117647, 100, 83.333333, 94.117647, 100, 83.333333, 94.117647, 100, 83.333333, 94.117647, 100, 83.333333,
    94.117647, 97.222222, 83.333333, 94.117647, 97.222222, 83.333333, 94.117647, 97.222222, 83.333333, 94.117647, 97.222222, 83.333333,
    94.117647, 97.222222, 83.333333, 94.117647, 97.222222, 83.333333, 94.117647, 97.222222, 83.333333, 94.117647, 97.222222, 83.333333,
    94.117647, 94.444444, 80.555556, 88.235294, 94.444444, 80.555556, 88.235294, 91.666667, 77.777778, 88.235294, 86.111111, 75,
    82.352941, 83.333333, 75, 82.352941, 83.333333, 72.222222, 82.352941, 83.333333, 72.222222, 82.352941, 80.555556, 72.222222,
    82.352941, 80.555556, 72.222222, 76.470588, 77.777778, 72.222222, 76.470588, 77.777778, 72.222222, 76.470588, 77.777778, 72.222222,
    76.470588, 77.777778, 72.222222, 76.470588, 75, 72.222222, 76.470588, 75, 72.222222, 76.470588, 75, 72.222222,
    76.470588, 72.222222, 69.444444, 76.470588, 72.222222, 69.444444, 76.470588, 72.222222, 69.444444, 76.470588, 72.222222, 69.444444,
    76.470588, 72.222222, 69.444444, 76.470588, 72.222222, 69.444444, 76.470588, 69.444444, 69.444444, 76.470588, 69.444444, 66.666667,
    76.470588, 69.444444, 66.666667, 76.470588, 69.444444, 61.111111, 76.470588, 69.444444, 61.111111, 76.470588, 66.666667, 52.777778,
    64.705882, 63.888889, 52.777778, 64.705882, 58.333333, 50, 58.823529, 55.555556, 50, 52.941176, 52.777778, 47.222222,
    47.058824, 50, 47.222222, 47.058824, 47.222222, 44.444444, 47.058824, 44.444444, 41.666667, 47.058824, 44.444444, 41.666667
)

f_lookup(float[] arr, int hourState, int tierState) =>
    int h = math.max(1, math.min(96, hourState))
    int t = math.max(1, math.min(3, tierState))
    int idx = (h - 1) * 3 + (t - 1)
    array.get(arr, idx)

// ─────────────────────────────────────────────────────────────────────────────
// NY clock / week-hour convention
// Research week starts Sunday 19:00 ET.
// H1 = Sunday 19:00–19:59 ET, H60 = Wednesday 05:00 ET.
// ─────────────────────────────────────────────────────────────────────────────
int nyDow = dayofweek(time, TZ)
int nyHour = hour(time, TZ)
int nyMinute = minute(time, TZ)

bool sun19 = nyDow == dayofweek.sunday and nyHour == 19 and nyMinute == 0
bool mon03 = nyDow == dayofweek.monday and nyHour == 3 and nyMinute == 0
bool tue12 = nyDow == dayofweek.tuesday and nyHour == 12 and nyMinute == 0
bool wed03 = nyDow == dayofweek.wednesday and nyHour == 3 and nyMinute == 0
bool wed05 = nyDow == dayofweek.wednesday and nyHour == 5 and nyMinute == 0
bool wed12 = nyDow == dayofweek.wednesday and nyHour == 12 and nyMinute == 0

bool inMonAsian =
    (nyDow == dayofweek.sunday and nyHour >= 19) or
    (nyDow == dayofweek.monday and nyHour < 3)

// Compute elapsed hour state H1..H96 from Sunday 19:00 ET.
// Monday=dayofweek.monday etc. Pine enums are 1..7, Sunday=1.
int dayOffset =
    nyDow == dayofweek.sunday ? 0 :
    nyDow == dayofweek.monday ? 1 :
    nyDow == dayofweek.tuesday ? 2 :
    nyDow == dayofweek.wednesday ? 3 :
    nyDow == dayofweek.thursday ? 4 :
    nyDow == dayofweek.friday ? 5 : 6

int hourFromSun19 = dayOffset * 24 + nyHour - 19
if hourFromSun19 < 0
    hourFromSun19 += 168

int weekHour = math.max(1, math.min(96, hourFromSun19 + 1))

// ─────────────────────────────────────────────────────────────────────────────
// Weekly state
// ─────────────────────────────────────────────────────────────────────────────
var float weekHigh = na
var float weekLow = na
var float monAsianHigh = na
var float monAsianLow = na
var float monAsianPips = na
var bool monAsianLocked = false

if sun19
    weekHigh := high
    weekLow := low
    monAsianHigh := high
    monAsianLow := low
    monAsianPips := na
    monAsianLocked := false
else
    if not na(weekHigh)
        weekHigh := math.max(weekHigh, high)
        weekLow := math.min(weekLow, low)

if inMonAsian
    monAsianHigh := na(monAsianHigh) ? high : math.max(monAsianHigh, high)
    monAsianLow := na(monAsianLow) ? low : math.min(monAsianLow, low)

if mon03 and not monAsianLocked and not na(monAsianHigh) and not na(monAsianLow)
    monAsianPips := f_pips(monAsianHigh - monAsianLow)
    monAsianLocked := true

if not monAsianLocked and nyDow == dayofweek.monday and nyHour >= 3 and not na(monAsianHigh) and not na(monAsianLow)
    monAsianPips := f_pips(monAsianHigh - monAsianLow)
    monAsianLocked := true

float printedWeekPips = not na(weekHigh) and not na(weekLow) ? f_pips(weekHigh - weekLow) : na
float location = not na(weekHigh) and not na(weekLow) and weekHigh > weekLow ? (close - weekLow) / (weekHigh - weekLow) : na

string locationState =
    na(location) ? "—" :
    location < 1.0/3.0 ? "Lower Third" :
    location > 2.0/3.0 ? "Upper Third" : "Middle Third"

// ─────────────────────────────────────────────────────────────────────────────
// Monday Asian tier + frozen weekly size factors
// ─────────────────────────────────────────────────────────────────────────────
int tier =
    na(monAsianPips) ? 0 :
    monAsianPips < tier1Max ? 1 :
    monAsianPips < tier2Max ? 2 :
    monAsianPips <= tier3Max ? 3 : 4

string tierText = tier == 1 ? "T1" : tier == 2 ? "T2" : tier == 3 ? "T3" : tier == 4 ? "NO-GO" : "—"

float q50Factor = tier == 1 ? 7.33 : tier == 2 ? 5.39 : tier == 3 ? 4.20 : na
float q75Factor = tier == 1 ? 10.44 : tier == 2 ? 7.16 : tier == 3 ? 6.04 : na
float q90Factor = tier == 1 ? 12.77 : tier == 2 ? 7.73 : tier == 3 ? 6.95 : na

float q50WeekPips = monAsianPips * q50Factor
float q75WeekPips = monAsianPips * q75Factor
float q90WeekPips = monAsianPips * q90Factor

float completionPct = not na(q50WeekPips) and q50WeekPips > 0 ? 100.0 * printedWeekPips / q50WeekPips : na

// ─────────────────────────────────────────────────────────────────────────────
// Exact Hour × Tier pace / remaining-range engine
// ─────────────────────────────────────────────────────────────────────────────
bool lookupReady = tier >= 1 and tier <= 3 and weekHour >= 1 and weekHour <= 96

float hourlyMedian = lookupReady ? f_lookup(MEDIAN_RANGE, weekHour, tier) : na
float hourlyMAD = lookupReady ? f_lookup(MAD_RANGE, weekHour, tier) : na
float hourlyRobustSigma = lookupReady ? f_lookup(ROBUST_SIGMA, weekHour, tier) : na
float hourlyProgressMedian = lookupReady ? f_lookup(PROGRESS_MEDIAN, weekHour, tier) : na
float hourlyRemainQ50 = lookupReady ? f_lookup(REMAIN_MEDIAN, weekHour, tier) : na
float hourlyRemainQ75 = lookupReady ? f_lookup(REMAIN_Q75, weekHour, tier) : na
float hourlyRemainQ90 = lookupReady ? f_lookup(REMAIN_Q90, weekHour, tier) : na
float pAnyExtreme = lookupReady ? f_lookup(P_ANY_EXTREME, weekHour, tier) : na

float paceZ = lookupReady and hourlyRobustSigma > 0 ? (printedWeekPips - hourlyMedian) / hourlyRobustSigma : na

string paceState =
    na(paceZ) ? "—" :
    paceZ < -1.0 ? "Behind" :
    paceZ <= 1.0 ? "Normal" :
    paceZ <= 2.0 ? "Ahead" : "Extreme Ahead"

// ─────────────────────────────────────────────────────────────────────────────
// Checkpoint state + frozen direction matrix
// ─────────────────────────────────────────────────────────────────────────────
int minsOfWeek = (nyDow - dayofweek.sunday) * 1440 + nyHour * 60 + nyMinute
int tue12M = (dayofweek.tuesday - dayofweek.sunday) * 1440 + 12 * 60
int wed03M = (dayofweek.wednesday - dayofweek.sunday) * 1440 + 3 * 60
int wed12M = (dayofweek.wednesday - dayofweek.sunday) * 1440 + 12 * 60

int checkpoint =
    minsOfWeek >= wed12M ? 3 :
    minsOfWeek >= wed03M ? 2 :
    minsOfWeek >= tue12M ? 1 : 0

string checkpointText =
    checkpoint == 1 ? "Tuesday London" :
    checkpoint == 2 ? "Wednesday Asian" :
    checkpoint == 3 ? "Wednesday London" : "Monday Base"

bool primeWindow = nyDow == dayofweek.wednesday and nyHour >= 3 and nyHour < 12
bool primaryCall = nyDow == dayofweek.wednesday and nyHour == 5

string tierPrime =
    tier == 1 ? (weekHour >= 58 and weekHour <= 60 ? "HIGH" : "OFF-PEAK") :
    tier == 2 ? (weekHour >= 64 and weekHour <= 67 ? "HIGH" : "OFF-PEAK") :
    tier == 3 ? (weekHour >= 58 and weekHour <= 62 ? "HIGH" : "OFF-PEAK") : "—"

float pNewHigh = na
float pNewLow = na
float medianUp = na
float medianDown = na

if checkpoint == 1
    if locationState == "Lower Third"
        pNewHigh := 38.6
        pNewLow := 88.6
        medianDown := 33.5
        medianUp := 0.0
    else if locationState == "Upper Third"
        pNewHigh := 80.6
        pNewLow := 25.0
        medianUp := 48.3
        medianDown := 0.0
    else if locationState == "Middle Third"
        pNewHigh := 59.5
        pNewLow := 57.1
        medianUp := 0.0
        medianDown := 0.0

if checkpoint == 2
    if locationState == "Lower Third"
        pNewHigh := 22.2
        pNewLow := 91.1
        medianDown := 31.0
        medianUp := 0.0
    else if locationState == "Upper Third"
        pNewHigh := 87.9
        pNewLow := 9.1
        medianUp := 34.2
        medianDown := 0.0
    else if locationState == "Middle Third"
        pNewHigh := 59.1
        pNewLow := 54.5
        medianUp := 0.0
        medianDown := 0.0

if checkpoint == 3
    if locationState == "Lower Third"
        pNewHigh := 19.1
        pNewLow := 78.7
        medianDown := 33.1
        medianUp := 0.0
    else if locationState == "Upper Third"
        pNewHigh := 73.3
        pNewLow := 11.1
        medianUp := 23.7
        medianDown := 0.0
    else if locationState == "Middle Third"
        pNewHigh := 36.7
        pNewLow := 43.3
        medianUp := 0.0
        medianDown := 0.0

bool exhaustion = locationState == "Middle Third" and (paceState == "Ahead" or paceState == "Extreme Ahead")

string directionalState =
    exhaustion ? "WEEKLY EXHAUSTION / NO EDGE" :
    checkpoint == 0 ? "BASE MAP" :
    locationState == "Upper Third" ? "HIGH CONTINUATION" :
    locationState == "Lower Third" ? "LOW CONTINUATION" : "NEUTRAL"

float dominantProb =
    directionalState == "HIGH CONTINUATION" ? pNewHigh :
    directionalState == "LOW CONTINUATION" ? pNewLow : math.max(nz(pNewHigh), nz(pNewLow))

string confidence =
    exhaustion ? "NO EDGE" :
    checkpoint == 0 ? "WAIT" :
    locationState == "Middle Third" ? "LOW" :
    dominantProb >= 85 ? "HIGH" :
    dominantProb >= 75 ? "MED-HIGH" : "MODERATE"

// ─────────────────────────────────────────────────────────────────────────────
// Monday-base weekly projection bands
// ─────────────────────────────────────────────────────────────────────────────
float q50AboveLow = not na(weekLow) and not na(q50WeekPips) ? weekLow + f_price_from_pips(q50WeekPips) : na
float q75AboveLow = not na(weekLow) and not na(q75WeekPips) ? weekLow + f_price_from_pips(q75WeekPips) : na
float q90AboveLow = not na(weekLow) and not na(q90WeekPips) ? weekLow + f_price_from_pips(q90WeekPips) : na

float q50BelowHigh = not na(weekHigh) and not na(q50WeekPips) ? weekHigh - f_price_from_pips(q50WeekPips) : na
float q75BelowHigh = not na(weekHigh) and not na(q75WeekPips) ? weekHigh - f_price_from_pips(q75WeekPips) : na
float q90BelowHigh = not na(weekHigh) and not na(q90WeekPips) ? weekHigh - f_price_from_pips(q90WeekPips) : na

plot(showWeeklyLevels ? q50AboveLow : na, "Q50 from Week Low", color=color.new(color.yellow, 20), linewidth=1, style=plot.style_linebr)
plot(showWeeklyLevels ? q75AboveLow : na, "Q75 from Week Low", color=color.new(color.orange, 25), linewidth=1, style=plot.style_linebr)
plot(showWeeklyLevels ? q90AboveLow : na, "Q90 from Week Low", color=color.new(color.red, 35), linewidth=1, style=plot.style_linebr)

plot(showWeeklyLevels ? q50BelowHigh : na, "Q50 from Week High", color=color.new(color.yellow, 20), linewidth=1, style=plot.style_linebr)
plot(showWeeklyLevels ? q75BelowHigh : na, "Q75 from Week High", color=color.new(color.orange, 25), linewidth=1, style=plot.style_linebr)
plot(showWeeklyLevels ? q90BelowHigh : na, "Q90 from Week High", color=color.new(color.red, 35), linewidth=1, style=plot.style_linebr)

float lowerThird = not na(weekLow) and not na(weekHigh) ? weekLow + (weekHigh - weekLow) / 3.0 : na
float upperThird = not na(weekLow) and not na(weekHigh) ? weekLow + 2.0 * (weekHigh - weekLow) / 3.0 : na
plot(showLocationBands ? lowerThird : na, "Weekly Lower Third", color=color.new(color.red, 55), style=plot.style_linebr)
plot(showLocationBands ? upperThird : na, "Weekly Upper Third", color=color.new(color.green, 55), style=plot.style_linebr)

// ─────────────────────────────────────────────────────────────────────────────
// Labels
// ─────────────────────────────────────────────────────────────────────────────
if showLabels and tue12
    label.new(bar_index, high, "CEREBUS\nTUE LONDON\nFIRST REFORECAST", style=label.style_label_down, textcolor=color.white, color=color.new(color.orange, 15))
if showLabels and wed03
    label.new(bar_index, high, "CEREBUS\nWED ASIAN\nHIGH-CONFIDENCE MAP", style=label.style_label_down, textcolor=color.white, color=color.new(color.blue, 15))
if showLabels and wed05
    label.new(bar_index, high, "CEREBUS\nH60 PRIMARY CALL", style=label.style_label_down, textcolor=color.black, color=color.new(color.yellow, 0))
if showLabels and wed12
    label.new(bar_index, high, "CEREBUS\nWED LONDON\nFINAL RANGE LOCK", style=label.style_label_down, textcolor=color.white, color=color.new(color.red, 15))

// ─────────────────────────────────────────────────────────────────────────────
// Dashboard
// ─────────────────────────────────────────────────────────────────────────────
var table dash = table.new(position.top_right, 4, 11, border_width=1)

f_cell(int c, int r, string txt, color bg, color fg=color.white) =>
    table.cell(dash, c, r, txt, bgcolor=bg, text_color=fg, text_size=size.small)

if barstate.islast and showDashboard
    color hdr = color.rgb(15, 18, 24)
    color panel = color.rgb(22, 26, 34)
    color gold = color.rgb(184, 146, 63)
    color green = color.rgb(18, 120, 83)
    color red = color.rgb(145, 47, 55)
    color blue = color.rgb(33, 93, 142)
    color neutral = color.rgb(72, 72, 72)

    table.clear(dash, 0, 0, 3, 10)

    f_cell(0, 0, "CEREBUS WEEKLY ENGINE V1.1", hdr, color.rgb(235, 205, 120))
    f_cell(1, 0, "H" + str.tostring(weekHour), hdr)
    f_cell(2, 0, checkpointText, hdr)
    f_cell(3, 0, tierPrime, tierPrime == "HIGH" ? blue : hdr)

    f_cell(0, 1, "Monday AR", panel)
    f_cell(1, 1, f_pip_fmt(monAsianPips), panel)
    f_cell(2, 1, "Tier", panel)
    f_cell(3, 1, tierText, tier == 1 ? green : tier == 2 ? gold : tier == 3 ? blue : red)

    f_cell(0, 2, "Week Q50", panel)
    f_cell(1, 2, f_pip_fmt(q50WeekPips), panel)
    f_cell(2, 2, "Q75 / Q90", panel)
    f_cell(3, 2, f_pip_fmt(q75WeekPips) + " / " + f_pip_fmt(q90WeekPips), panel)

    f_cell(0, 3, "Printed", panel)
    f_cell(1, 3, f_pip_fmt(printedWeekPips), panel)
    f_cell(2, 3, "Completion", panel)
    f_cell(3, 3, na(completionPct) ? "—" : str.tostring(completionPct, "#.0") + "%", panel)

    f_cell(0, 4, "Hour Median", panel)
    f_cell(1, 4, f_pip_fmt(hourlyMedian), panel)
    f_cell(2, 4, "MAD / Robust σ", panel)
    f_cell(3, 4, f_pip_fmt(hourlyMAD) + " / " + f_pip_fmt(hourlyRobustSigma), panel)

    f_cell(0, 5, "Pace Z", panel)
    f_cell(1, 5, na(paceZ) ? "—" : str.tostring(paceZ, "#.00") + "σ", panel)
    f_cell(2, 5, "Pace State", panel)
    f_cell(3, 5, paceState, paceState == "Behind" ? green : paceState == "Normal" ? blue : red)

    f_cell(0, 6, "Range Left Q50", panel)
    f_cell(1, 6, f_pip_fmt(hourlyRemainQ50), panel)
    f_cell(2, 6, "Q75 / Q90 Left", panel)
    f_cell(3, 6, f_pip_fmt(hourlyRemainQ75) + " / " + f_pip_fmt(hourlyRemainQ90), panel)

    f_cell(0, 7, "Any New Extreme", panel)
    f_cell(1, 7, f_prob_fmt(pAnyExtreme), pAnyExtreme >= 85 ? green : panel)
    f_cell(2, 7, "Week Location", panel)
    f_cell(3, 7, locationState, locationState == "Upper Third" ? green : locationState == "Lower Third" ? red : neutral)

    f_cell(0, 8, "New Week High", panel)
    f_cell(1, 8, f_prob_fmt(pNewHigh), pNewHigh >= 70 ? green : panel)
    f_cell(2, 8, "New Week Low", panel)
    f_cell(3, 8, f_prob_fmt(pNewLow), pNewLow >= 70 ? red : panel)

    f_cell(0, 9, "Median Up / Down", panel)
    f_cell(1, 9, f_pip_fmt(medianUp) + " / " + f_pip_fmt(medianDown), panel)
    f_cell(2, 9, "Confidence", panel)
    f_cell(3, 9, confidence, confidence == "HIGH" ? green : confidence == "MED-HIGH" ? blue : confidence == "NO EDGE" ? red : gold)

    color stateBg = directionalState == "HIGH CONTINUATION" ? green : directionalState == "LOW CONTINUATION" ? red : exhaustion ? red : neutral
    f_cell(0, 10, "STATE", hdr, color.rgb(235, 205, 120))
    f_cell(1, 10, directionalState, stateBg)
    f_cell(2, 10, "Prime Window", hdr)
    f_cell(3, 10, primeWindow ? "YES" : "NO", primeWindow ? blue : panel)

// ─────────────────────────────────────────────────────────────────────────────
// Alerts
// ─────────────────────────────────────────────────────────────────────────────
bool highContinuation = checkpoint > 0 and not exhaustion and locationState == "Upper Third" and pNewHigh >= 70
bool lowContinuation = checkpoint > 0 and not exhaustion and locationState == "Lower Third" and pNewLow >= 70
bool exhaustionAlert = exhaustion
bool behindPrime = primeWindow and paceState == "Behind"

alertcondition(highContinuation, "CEREBUS High Continuation", "CEREBUS Weekly Engine: high-side continuation state.")
alertcondition(lowContinuation, "CEREBUS Low Continuation", "CEREBUS Weekly Engine: low-side continuation state.")
alertcondition(exhaustionAlert, "CEREBUS Weekly Exhaustion", "CEREBUS Weekly Engine: middle-third + ahead pace exhaustion/no-edge state.")
alertcondition(behindPrime, "CEREBUS Prime Behind Pace", "CEREBUS Weekly Engine: prime window active and week is behind pace.")
alertcondition(primaryCall, "CEREBUS H60 Primary Call", "CEREBUS Weekly Engine: Wednesday 05:00 ET primary call.")

```