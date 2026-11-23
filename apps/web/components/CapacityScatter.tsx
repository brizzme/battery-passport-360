import type {PackPoint} from "@/lib/types";
import {SITE_ORDER, SITES, type SiteId} from "@/lib/sites";
import {capacityText, linearScale, niceTicks, packLabel} from "@/lib/geometry";
import {HatchDefs} from "./Hatch";

const W = 960, H = 340, M = {l: 56, r: 16, t: 16, b: 44};

function Mark({site, x, y}: {site: SiteId; x: number; y: number}) {
  const c = SITES[site].color;
  if (site === "SITE-COLD") return <circle cx={x} cy={y} r={5} fill={c} stroke="var(--surface)" strokeWidth={2}/>;
  if (site === "SITE-AMB") return <rect x={x - 5} y={y - 5} width={10} height={10} fill={c} stroke="var(--surface)" strokeWidth={2}/>;
  return <path d={`M${x} ${y - 6}L${x + 6} ${y + 5}H${x - 6}Z`} fill={c} stroke="var(--ink)" strokeWidth={1}/>;
}

export function CapacityScatter({points}: {points: PackPoint[]}) {
  const lfp = points.filter(p => p.capacity_pct !== null && p.efc !== null && p.site_id) as (PackPoint & {capacity_pct: number; efc: number; site_id: SiteId})[];
  const maxX = Math.max(1, ...lfp.map(p => p.efc));
  const xt = niceTicks(0, maxX, 6), yt = [60, 70, 80, 90, 100];
  const x = linearScale([0, xt.at(-1)!], [M.l, W - M.r]), y = linearScale([60, 100], [H - M.b, M.t]);
  return <figure className="chart" aria-labelledby="scatter-h">
    <figcaption><h2 id="scatter-h">Capacity vs cumulative cycles <small>{lfp.length} LFP packs · synthetic · lead-acid omitted (no calibration source)</small></h2></figcaption>
    <div className="chart-scroll"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Scatter of ${lfp.length} LFP packs: capacity percent against cumulative equivalent full cycles`}>
      <HatchDefs id="scatter-hatch"/>
      <rect x={M.l} y={y(80)} width={W - M.l - M.r} height={y(60) - y(80)} fill="url(#scatter-hatch)"/>
      <text x={W - M.r - 4} y={y(80) + 16} textAnchor="end" className="axis-note">Below 80 %: beyond the measured curve, extrapolated</text>
      {yt.map(t => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} className="grid"/><text x={M.l - 8} y={y(t) + 4} textAnchor="end" className="axis">{t} %</text></g>)}
      {xt.map(t => <text key={t} x={x(t)} y={H - M.b + 20} textAnchor="middle" className="axis">{t.toLocaleString("en")}</text>)}
      <text x={(M.l + W - M.r) / 2} y={H - 6} textAnchor="middle" className="axis">Cumulative equivalent full cycles (EFC)</text>
      {lfp.map(p => <a key={p.battery_id} href={`/fleet/${p.battery_id}?as_of=2027-02-18`} aria-label={`${packLabel(p)}, ${p.efc.toFixed(0)} EFC`}
        data-tip={`${packLabel(p)} · ${p.efc.toLocaleString("en", {maximumFractionDigits: 0})} EFC`}>
        <circle cx={x(p.efc)} cy={y(p.capacity_pct)} r={12} fill="transparent"/>
        <Mark site={p.site_id} x={x(p.efc)} y={y(p.capacity_pct)}/></a>)}
    </svg></div>
    <ul className="legend">{SITE_ORDER.map(id => <li key={id}><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><Mark site={id} x={7} y={7}/></svg>{SITES[id].label}</li>)}</ul>
    <details><summary>View as table</summary><table><thead><tr><th>Pack</th><th>Site</th><th className="num">EFC</th><th className="num">Capacity</th></tr></thead>
      <tbody>{lfp.map(p => <tr key={p.battery_id}><td>{p.battery_id}</td><td>{SITES[p.site_id].label}</td><td className="num">{p.efc.toFixed(0)}</td><td className="num">{capacityText(p.capacity_pct)}</td></tr>)}</tbody></table></details>
  </figure>;
}
