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
