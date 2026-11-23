import Link from "next/link";
import type {FleetHealth} from "@/lib/types";
import {siteOf} from "@/lib/sites";
import {Pictogram} from "./Pictogram";
import {capacityText} from "@/lib/geometry";

const SHORT: Record<string, string> = {
  capacity_below_80: "Capacity below 80 %",
  over_temperature_30d: "Repeated over-temperature (30 days)",
  fade_rate_p90: "Fast fade, top 10 % of fleet (90 days)",
  passport_gaps_at_milestone: "Passport evidence gaps at 18 Feb 2027",
};
const ORDER = ["capacity_below_80", "over_temperature_30d", "fade_rate_p90", "passport_gaps_at_milestone"];

export function reviewRows(data: FleetHealth) {
  const byPack = new Map<string, {rule: string; reason: string}[]>();
  for (const f of data.review) byPack.set(f.battery_id, [...(byPack.get(f.battery_id) ?? []), f]);
  const points = new Map(data.pack_points.map(p => [p.battery_id, p]));
  return [...byPack.entries()].map(([id, flags]) => ({
    id, point: points.get(id), flags: flags.sort((a, b) => ORDER.indexOf(a.rule) - ORDER.indexOf(b.rule)),
  })).sort((a, b) => ORDER.indexOf(a.flags[0].rule) - ORDER.indexOf(b.flags[0].rule) || a.id.localeCompare(b.id));
}

function Rows({rows}: {rows: ReturnType<typeof reviewRows>}) {
  return <>{rows.map(r => {
    const site = siteOf(r.point?.site_id);
    const cap = r.point?.capacity_pct;
    return <tr key={r.id}>
      <th scope="row"><Link href={`/fleet/${r.id}?as_of=2027-02-18`}>{r.id}</Link></th>
      <td><span className="site-tag"><Pictogram site={r.point?.site_id}/></span> {site.short}</td>
      <td><ul className="reasons">{r.flags.map(f => <li key={f.rule} data-tip={f.reason} tabIndex={0} aria-label={`${SHORT[f.rule] ?? f.rule}. ${f.reason}`}>{SHORT[f.rule] ?? f.rule}</li>)}</ul></td>
      <td className="num">{cap === null || cap === undefined ? "unknown" : capacityText(cap)}{cap !== null && cap !== undefined && cap < 80 && <small className="block">extrapolated</small>}</td>
    </tr>;
  })}</>;
}

export function ReviewTable({data}: {data: FleetHealth}) {
  const rows = reviewRows(data);
  const first = rows.slice(0, 7), rest = rows.slice(7);
  return <section aria-labelledby="review-h" className="review">
    <h2 id="review-h">Suggested for specialist review <small>{rows.length} packs</small></h2>
    <table>
      <thead><tr><th scope="col">Pack</th><th scope="col">Site</th><th scope="col">Reason</th><th scope="col" className="num">Capacity</th></tr></thead>
      <tbody><Rows rows={first}/></tbody>
    </table>
    {rest.length > 0 && <details className="more"><summary>Show all {rows.length} packs</summary>
      <table><thead><tr><th scope="col">Pack</th><th scope="col">Site</th><th scope="col">Reason</th><th scope="col" className="num">Capacity</th></tr></thead><tbody><Rows rows={rest}/></tbody></table></details>}
    <p className="note">{data.triage_note} Qualified specialists decide.</p>
  </section>;
}
