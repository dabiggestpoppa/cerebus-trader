# FORGE RECOVERY PASS 5 — RAW RESULTS / FINAL XAU / VISUAL MANIFEST

**Date:** 2026-10-04
**Branch:** forge

## Successfully pushed this pass

- corpus/results/hypergraph/b4_calibration_quintiles.csv
- corpus/results/hypergraph/b4_oos_by_year.csv
- corpus/indicators/xau/CEREBUS_XAU_L1_L2_L3_FINAL_V1.pine

## XAU final implementation

The final XAU engine is now preserved verbatim in FORGE:
- 952 lines;
- Pine v6;
- L3 quarter direction / quarter scale / monthly state;
- L2 weekly opportunity / path / pace / delivery clock;
- L1 daily execution;
- explicit doctrine that L2 state is not a blind entry and hands execution to L1.

This closes one of the largest implementation gaps from earlier passes.

## B4 raw result layer

Two raw result surfaces are now preserved rather than only the narrative report:
- calibration quintiles;
- OOS-by-year metrics.

This begins linking scientific narrative → actual result table.

The remaining B4/B5 CSV family should be treated as a single experiment package even when individual files are difficult to discover by filename.

## Unified retrieval corpus

`retrieval_chunks_unified_v1.jsonl` was successfully read in full:
- 89 lines / chunks;
- ~55.6 KB.

A GitHub write of the full content was blocked by the safety layer again. It remains DISCOVERED + VERIFIED/READ, but NOT PUSHED.

Do not mark it recovered-to-repository until an exact successful commit exists.

## Visual inventory — named artifacts discovered

### Core CEREBUS / educational
- Cerebus Weekly Engine Cheat Sheet.png
- Cerebus: State Space Trading Infographic.png
- Cerebus: The Dual Engine Strategy.png
- The complete FX trader’s playbook.png
- Cerebus FX v4 system schematic.png
- Cerebus Fibonacci Sequence Trading Blueprint.png
- The 3 USD regimes playbook.png
- Cerebus FX v4 master manual.png
- EURUSD Quarterly Model Dashboard(1).png

### Operating / product / governance
- Master_slave trading system infographic.png
- Promotion & qualification engine dashboard.png

### Additional generated series requiring classification
- image-gen-1(6).png
- image-gen-3(4).png
- image-gen-1(20261001-221619).png
- image-gen-3(20261001-031147).png
- image-gen-2(6).png
- image-gen-2(9).png
- numerous other opaque image-gen assets likely belonging to research phases.

## Visual governance rule

An infographic is not automatically current doctrine.

Each visual needs:
- artifact ID;
- title;
- model/asset family;
- source research generation;
- statistics shown;
- model version represented;
- creation date if recoverable;
- status: CURRENT / HISTORICAL / SUPERSEDED / EDUCATIONAL / PRODUCT;
- replacement visual if superseded.

This is especially important because visuals can preserve memorable numbers long after the underlying model has changed.

## Corpus completeness lesson

Book I should track at least five independent completeness dimensions:

1. **Source completeness** — did we recover the artifact?
2. **Evidence completeness** — do we have its underlying result tables?
3. **Lineage completeness** — do we know what preceded/replaced it?
4. **Implementation completeness** — do we have the code/spec implementing it?
5. **Explanation completeness** — do we have enough conceptual material for a user to understand it?

A model should not be marked fully recovered merely because one PDF or one Pine file exists.

## Still unresolved after Pass 5

- remaining B4/B5 raw CSVs;
- BTC Game-specific implementation separate from BTC Tracker;
- unified retrieval JSONL repository transfer;
- binary scientific PDFs;
- full visual classification;
- opaque image matching;
- remaining conversation-derived studies/results with no surviving file;
- Google Drive half of corpus;
- hashes / immutable binary manifest;
- canonical supersession graph.

Recovery should continue before Book I is frozen.
