# Model card: early-cycle life of HUST LFP cells

Run `hust-life-v1-2bb4259f3f0a` (see `apps/api/app/artifacts/hust-life-report.json`). This model describes **measured laboratory cells only**. It is not applied to, and says nothing about, the fictional fleet packs.

## Task
Predict each cell's cycle life from its first 100 cycles. Life is the first cycle whose centred 5-cycle median discharge capacity falls below 80 % of the median of cycles 2–6 (80 % of *initial*, not of the 1.1 Ah nominal). Target: log10(life); errors reported in cycles.

## Data
HUST LFP/graphite 1.1 Ah cylindrical cells (Ma et al. 2022, Mendeley Data 10.17632/nsc7hnsg4s.2, CC BY 4.0): 77 cells, 10 test batches (cell-id prefix), each cell with its own multi-stage discharge protocol (per-cell table from Microsoft BatteryML, MIT). Measured lives: 978–2,336 cycles (median 1,706). Raw pickles are opened only in a network-less, read-only container.

## Features (cycles ≤ 100)
- Capacity: capacity at cycle 2; maximum minus cycle-2 capacity; slope and intercept of a linear fit over cycles 91–100.
- Voltage: log10 variance, log10 |minimum| and mean of ΔQ₁₀₀₋₁₀(V), the change in capacity remaining to the 2.0 V cut-off along the final constant-current stage (measured 2.2 A for every cell), on a shared 2.00–3.105 V grid. This adapts Severson et al. (2019), whose feature uses a constant 4C discharge.

## Evaluation
Outer leave-one-batch-out (10 folds): every cell is predicted once by a model that never saw its batch; protocols are unique per cell. Elastic-net strength and 80 % split-conformal intervals are chosen with GroupKFold(5) by batch inside the training batches only. `research/verify_life.py` recomputes every number below from the per-cell predictions.

| Model | MAE (cycles) | RMSE (cycles) | MAPE | 80 % interval coverage |
|---|---:|---:|---:|---:|
| Training mean (baseline) | 272 | 328 | 16.8 % | 82 % |
| ΔQ(V) variance only | 269 | 324 | 16.5 % | 81 % |
| Capacity features (elastic net) | **200** | **255** | **11.8 %** | 82 % |
| Capacity + ΔQ(V) features (elastic net) | 205 | 274 | 12.2 % | 83 % |

## Findings
- Early capacity features reduce held-out error by about a quarter relative to predicting the mean.
- The adapted voltage feature adds no skill on these cells (a null result, reported as measured). Plausible reasons, not tested: the final discharge stage covers only the last ~20 % of charge, and the multi-stage protocols differ per cell.
- Intervals are close to their nominal 80 % coverage.
- Published error figures for other datasets use other life definitions and splits; they are not comparable and are not used as targets.

## Limitations
One cell type, one laboratory, one temperature (30 °C), 77 cells. Cell-level only; no pack-level, fleet, warranty or safety use. Elastic-net coefficients from a refit on all cells are stored for interpretation only.

## Legacy baseline
The earlier CALCE CS2 linear capacity trend (one held-out cell, run `calce-index-ols-v1-3b0d3ac7e4ba`, MAE 0.097 Ah vs 0.163 Ah for the training mean) remains available at `/api/research/model-report` and as a collapsed section on the research page. It is superseded.
