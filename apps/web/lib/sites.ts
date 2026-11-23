export type SiteId = "SITE-COLD" | "SITE-AMB" | "SITE-HOT";
export const SITES: Record<SiteId, {label: string; short: string; color: string}> = {
  "SITE-COLD": {label: "Cold store", short: "Cold", color: "var(--cold)"},
  "SITE-AMB": {label: "Ambient warehouse", short: "Ambient", color: "var(--ambient)"},
  "SITE-HOT": {label: "Hot dock", short: "Hot dock", color: "var(--hot)"},
};
export const SITE_ORDER: SiteId[] = ["SITE-COLD", "SITE-AMB", "SITE-HOT"];
export function siteOf(id: string | null | undefined) {
  return id && id in SITES ? SITES[id as SiteId] : {label: "Unassigned", short: "—", color: "var(--neutral)"};
}

const REGIME_LABEL: Record<string, string> = {
  calibrated: "calibrated 35–45 °C",
  extrapolated_below_calibrated_range: "extrapolated 20–35 °C",
  clamped_low: "clamped below 20 °C",
  clamped_high: "clamped above 45 °C",
  extrapolated_beyond_measured_curve: "below 80 %: beyond measured curve",
};
/** "clamped_low 34%" → "clamped below 20 °C: 34 %" */
export function regimeLabel(raw: string) {
  const m = raw.match(/^(\S+)(?: (\d+)%)?$/);
  if (!m) return raw;
  const name = REGIME_LABEL[m[1]] ?? m[1].replaceAll("_", " ");
  return m[2] ? `${name}: ${m[2]} %` : name;
}
