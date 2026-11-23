export type PackPoint = {battery_id: string; site_id: string | null; chemistry: string; capacity_pct: number | null; efc: number | null; review_rules: string[]};
export type ReviewFlag = {battery_id: string; rule: string; reason: string};
export type FleetHealth = {
  as_of: string; data_cutoff: string; source_type: "synthetic"; triage_version: string; triage_note: string;
  packs: number; capacity_bands: Record<string, number>; efc_total: number; events_30d: Record<string, number>;
  review: ReviewFlag[]; pack_points: PackPoint[]; regime_share: Record<string, number>; calibration_version: string | null; generator_version: string | null;
};
export type HistoryPoint = {day: string; capacity_pct: number | null; resistance_pct: number | null; efc: number; temp_mean_c: number; temp_max_c: number; soc_min_pct: number; soc_max_pct: number; temp_regime: string};
export type History = {battery_id: string; source_type: "synthetic"; source_id: string; generator_version: string; calibration_version: string; data_cutoff: string; from: string; to: string; points: HistoryPoint[]};
export type LifeModel = {label: string; kind: string; features: string[]; mae: number; rmse: number; mape: number; interval_coverage: number; interval_mean_width: number; folds: {test_groups: number[]; mae: number}[]};
export type LifeReport = {run_id: string; generated_at: string; source_type: "derived"; target: string; horizon_cycles: number; n_cells: number; n_batches: number; split: string; intervals: string; voltage_window_v: [number, number]; voltage_feature_note: string; life_summary: {min: number; median: number; max: number}; models: Record<string, LifeModel>; interpretation: {note: string; standardised_coefficients: Record<string, number>}; data: {dataset: string; digest: string; features: string[]}};
export type Pred = {pred: number; lo: number; hi: number};
export type LifeCell = {id: string; batch: number; life: number} & Record<string, Pred | number | string>;
export type CellDetail = {id: string; batch: number; life: number; cycles: number[]; capacity_ah: number[]; delta_q_ah: number[]; delta_q_grid_v: number[]; dataset: string} & Record<string, unknown>;
