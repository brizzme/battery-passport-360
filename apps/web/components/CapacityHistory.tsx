import type {HistoryPoint} from "@/lib/types";
import {linearScale} from "@/lib/geometry";
import {HatchDefs} from "./Hatch";

const W = 720, H = 260, M = {l: 52, r: 12, t: 12, b: 36};

export function CapacityHistory({points, color}: {points: HistoryPoint[]; color: string}) {
  const pts = points.filter(p => p.capacity_pct !== null) as (HistoryPoint & {capacity_pct: number})[];
  if (!pts.length) return <p className="empty">No calibrated capacity for this pack: lead-acid packs have no calibration source.</p>;
  const x = linearScale([0, Math.max(1, points.length - 1)], [M.l, W - M.r]);
  const lo = Math.min(60, Math.floor(Math.min(...pts.map(p => p.capacity_pct)) / 5) * 5);
  const y = linearScale([lo, 100], [H - M.b, M.t]);
  const index = new Map(points.map((p, i) => [p.day, i]));
  const d = pts.map((p, i) => `${i ? "L" : "M"}${x(index.get(p.day)!).toFixed(1)} ${y(p.capacity_pct).toFixed(1)}`).join("");
  const ticks = [lo, ...[70, 80, 90, 100].filter(t => t > lo)];
  const last = pts[pts.length - 1];
  return <div className="chart-scroll"><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Daily synthetic capacity from ${pts[0].capacity_pct.toFixed(1)} % to ${last.capacity_pct.toFixed(1)} % between ${points[0].day} and ${points.at(-1)!.day}`}>
    <HatchDefs id="hist-hatch"/>
    {lo < 80 && <rect x={M.l} y={y(80)} width={W - M.l - M.r} height={y(lo) - y(80)} fill="url(#hist-hatch)"/>}
    {ticks.map(t => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} className="grid"/><text x={M.l - 8} y={y(t) + 4} textAnchor="end" className="axis">{t} %</text></g>)}
    <text x={M.l} y={H - 10} className="axis">{points[0].day}</text>
    <text x={W - M.r} y={H - 10} textAnchor="end" className="axis">{points.at(-1)!.day}</text>
    {last.capacity_pct <= 60.01 && <text x={W - M.r - 8} y={y(lo) - 8} textAnchor="end" className="axis-note">At the 60 % model floor: the generator does not extend fade below this</text>}
    <path d={d} fill="none" stroke={color} strokeWidth={2}/>
    <circle cx={x(index.get(last.day)!)} cy={y(last.capacity_pct)} r={4} fill={color} data-tip={`${last.day}: ${last.capacity_pct.toFixed(1)} %`}/>
  </svg></div>;
}
