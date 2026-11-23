# Early-cycle life model on HUST LFP cells — design (expansion part 4)

**Date:** 2026-11-23 · **Status:** draft for approval · Approach C (chosen by the user)

## Intent
Replace the CALCE straight-line baseline (one held-out cell) with a credible, leakage-guarded model on real measured LFP cells: predict each cell's cycle life (cycles to 80 % of initial capacity) from its first 100 cycles, and show that the result sits where published work says it should. Audience: a technical reviewer (PRODUCT.md). The model concerns laboratory cells only and never predicts the synthetic fleet.

## Approaches
| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | Capacity-vs-cycle regression on HUST | Simple; weak question, no literature anchor | Rejected |
| B | Early-cycle life from capacity features | Uses existing data; misses the field's standard feature | Folded into C as a comparison model |
| **C** | **B + Severson ΔQ₁₀₀₋₁₀(V) voltage feature** | Re-extraction needed; strongest, checkable against literature | **Chosen** |

## Data
HUST (Ma et al. 2022, CC BY 4.0, already pinned): 77 LFP/graphite 1.1 Ah cells, all reach 80 % of initial capacity (lives 978–2,336 cycles). Cell ids `b-n`: b = test batch 1…10. Each cell has its own discharge protocol: three C-rates applied over SOC 100–60 %, 60–40 %, 40–20 %, then always 1C to 2.0 V (per-cell table in Microsoft BatteryML `preprocess_HUST.py`, MIT, citing the paper's supplementary information). The isolated extractor (no network, read-only, runs as nobody) is extended to also write, per cell, the discharge capacity Q interpolated on a fixed voltage grid for cycles 10 and 100 (and the per-cycle capacity it already writes). Host Python never unpickles.

## Model
- **Target:** log10(cycle life), life from the existing `life_to_80`; metrics reported in cycles.
- **Features (cycles ≤ 100 only):**
  - voltage: log10 variance, log10 |minimum| and mean of ΔQ₁₀₀₋₁₀(V) on a shared voltage grid within the final 1C stage (SOC ≈ 20 % to 2.0 V), the one stage every cell shares — an adaptation of Severson et al. 2019, labelled as such;
  - capacity: discharge capacity at cycle 2; maximum minus cycle-2 capacity; slope and intercept of a linear fit over cycles 91–100.
- **Models compared:** (1) training-mean baseline; (2) variance-only linear model; (3) capacity-only regularised linear model; (4) full model (voltage + capacity). Regularised = elastic net (scikit-learn, pinned in the research group); its strength is chosen by grouped cross-validation inside the training folds only.
- **Evaluation:** leave-one-batch-out over the 10 cell-id batches (outer folds). Every cell is predicted exactly once by a model that never saw its batch; every cell also has a unique protocol, so no test protocol occurs in training. Report pooled MAE, RMSE and MAPE in cycles, plus per-fold spread. The comparison that matters is against our own training-mean baseline under the same split; published numbers are not used as targets (see calls).
- **Uncertainty:** split-conformal 80 % intervals from inner-fold residuals of the training data; report empirical coverage on the outer folds.
- **Leakage guards (tested):** no feature reads a cycle > 100; no group appears in both train and test of a fold; hyper-parameters selected without outer-test cells; the report records feature definitions and the dataset digest.

## Outputs
- `research/life_model.py` → committed `apps/api/app/artifacts/hust-life-report.json` (metrics per model, per-fold metrics, per-cell out-of-fold prediction + interval + actual life + group, feature table, coefficient summary of a model refit on all cells for interpretation only, digests, run id) and `apps/api/app/artifacts/hust-curves.json` (per cell: capacity curve downsampled to ≤ 60 points, ΔQ₁₀₀₋₁₀(V) on a coarse grid) so a fresh clone shows the research page without downloads. Derived data from CC BY 4.0 with attribution.
- `research/verify_life.py` recomputes every reported metric from the committed per-cell predictions.
- API (`research.py`): `GET /api/research/hust/report`, `GET /api/research/hust/cells`, `GET /api/research/hust/cells/{id}`; source_type `measured_public` for curves, `derived` for predictions. CALCE endpoints stay.
- Web `/research` rebuilt in the Ulm system (DESIGN.md): model comparison (MAE/RMSE per model, baseline first, yardsticks marked), predicted-vs-actual scatter with 80 % intervals and identity line (one dot per cell, coloured by group via shape/label, never colour alone), one selected cell's capacity curve with its life marker and its ΔQ(V) curve, a method and leakage panel, provenance; CALCE as a collapsed legacy section. Labels everywhere: "measured laboratory cells", never fleet packs.
- `docs/MODEL_CARD.md` rewritten with real results only; DATA_SOURCES, LIMITATIONS, PLAN updated.

## Non-goals
Pack-level or fleet predictions; deep learning; tuning to beat the literature; MATR data (licence unconfirmed).

## Anti-goals
Any metric computed on cells whose group informed training or tuning; presenting the model as predicting the fictional fleet; reporting numbers not reproducible by `verify_life.py`.

## Calls made after the builder check (review these)
1. **No external yardsticks as targets.** A training-mean baseline under our split already gives about MAE 270, RMSE 327 cycles, MAPE 17 % (HUST lives are tightly spread). Published figures (BatteryML, Severson) use other life definitions or splits, so they are mentioned only qualitatively with a "not comparable" note; no unverified number is quoted.
2. **Life = cycles to 80 % of each cell's initial capacity** (median of cycles 2–6), stated wherever life appears; not 80 % of nominal 1.1 Ah.
3. **Batches, not protocol groups.** The outer split holds out one id batch at a time; protocols are unique per cell, documented from the BatteryML table and the paper's SI reference.
4. **Voltage feature on the final 1C stage only**, the monotone window all cells share; labelled an adaptation. If it adds nothing over capacity-only, that null result ships as measured, with no switch back to approach B.
5. **Scatter marks are ink only** (DESIGN.md reserves colour for sites); cells are identified by tooltip, accessible name and the table view; the selected cell is emphasised by size and outline. No new palette.

## Left to the builder
Voltage grid bounds and resolution (within the discharge window shared by all cells), elastic-net parameter grid, chart details within DESIGN.md.
