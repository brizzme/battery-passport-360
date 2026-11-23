import type {SiteId} from "@/lib/sites";
/** Site pictograms: one consistent 1.75px stroke on a 16px grid. */
export function Pictogram({site, size = 16}: {site: SiteId | string | null | undefined; size?: number}) {
  const common = {width: size, height: size, viewBox: "0 0 16 16", fill: "none", stroke: "currentColor",
    strokeWidth: 1.75, strokeLinecap: "square" as const, "aria-hidden": true, focusable: false};
  if (site === "SITE-COLD") return <svg {...common}><path d="M8 1v14M1.9 4.5l12.2 7M1.9 11.5l12.2-7"/></svg>;
  if (site === "SITE-AMB") return <svg {...common}><path d="M1.5 14.5V6.5L8 2l6.5 4.5v8M5.5 14.5v-5h5v5"/></svg>;
  if (site === "SITE-HOT") return <svg {...common}><circle cx="8" cy="8" r="3"/><path d="M8 .8v2.4M8 12.8v2.4M.8 8h2.4M12.8 8h2.4M2.9 2.9l1.7 1.7M11.4 11.4l1.7 1.7M2.9 13.1l1.7-1.7M11.4 4.6l1.7-1.7"/></svg>;
  return <svg {...common}><rect x="3" y="3" width="10" height="10"/></svg>;
}
