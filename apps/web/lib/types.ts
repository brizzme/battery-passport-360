export type PackPoint = {battery_id: string; site_id: string | null; chemistry: string; capacity_pct: number | null; efc: number | null; review_rules: string[]};
export type ReviewFlag = {battery_id: string; rule: string; reason: string};
export type FleetHealth = {
  as_of: string; data_cutoff: string; source_type: "synthetic"; triage_version: string; triage_note: string;
  packs: number; capacity_bands: Record<string, number>; efc_total: number; events_30d: Record<string, number>;
  review: ReviewFlag[]; pack_points: PackPoint[]; regime_share: Record<string, number>; calibration_version: string | null; generator_version: string | null;
};
export type HistoryPoint = {day: string; capacity_pct: number | null; resistance_pct: number | null; efc: number; temp_mean_c: number; temp_max_c: number; soc_min_pct: number; soc_max_pct: number; temp_regime: string};
export type History = {battery_id: string; source_type: "synthetic"; source_id: string; generator_version: string; calibration_version: string; data_cutoff: string; from: string; to: string; points: HistoryPoint[]};
