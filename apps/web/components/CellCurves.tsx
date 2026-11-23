import type {CellDetail, Pred} from "@/lib/types";
import {linearScale, niceTicks} from "@/lib/geometry";

const W = 480, H = 260, M = {l: 56, r: 12, t: 12, b: 40};

export function CellCurves({cell, model}: {cell: CellDetail; model: string}) {
  const p = cell[model] as Pred;
  const caps = cell.capacity_ah, cyc = cell.cycles;
  const initial = cell.initial_ah;
  const xt = niceTicks(0, Math.max(cyc.at(-1)!, p.hi), 5), x = linearScale([0, xt.at(-1)!], [M.l, W - M.r]);
  const yMin = Math.floor(Math.min(...caps) * 20) / 20, yMax = Math.ceil(Math.max(...caps) * 20) / 20;
  const y = linearScale([yMin, yMax], [H - M.b, M.t]);
  const path = cyc.map((c, i) => `${i ? "L" : "M"}${x(c).toFixed(1)} ${y(caps[i]).toFixed(1)}`).join("");
  const dq = cell.delta_q_ah.map(v => v * 1000), grid = cell.delta_q_grid_v;
  const vx = linearScale([grid[0], grid.at(-1)!], [M.l, W - M.r]);
  const dmin = Math.min(0, ...dq), dmax = Math.max(0, ...dq), pad = (dmax - dmin) * 0.1 || 1;
  const vy = linearScale([dmin - pad, dmax + pad], [H - M.b, M.t]);
  const dpath = grid.map((v, i) => `${i ? "L" : "M"}${vx(v).toFixed(1)} ${vy(dq[i]).toFixed(1)}`).join("");
  return <div className="pack-grid two">
    <figure className="chart"><figcaption><h3>Cell {cell.id}: measured discharge capacity <small>Ah · batch {cell.batch} · life {cell.life} cycles · predicted {p.pred.toFixed(0)} ({p.lo.toFixed(0)}–{p.hi.toFixed(0)})</small></h3></figcaption>
      <div className="chart-scroll"><svg viewBox={`0 0 ${W} ${H}`} style={{"--w": `${W}px`} as React.CSSProperties} role="img" aria-label={`Capacity of cell ${cell.id} from ${caps[0].toFixed(3)} to ${caps.at(-1)!.toFixed(3)} Ah over ${cyc.at(-1)} cycles`}>
        <rect x={x(0)} y={M.t} width={x(100) - x(0)} height={H - M.b - M.t} fill="var(--ground)"/>
        <text x={x(100) + 4} y={M.t + 12} className="axis">features: cycles ≤ 100</text>
        <line x1={M.l} x2={W - M.r} y1={y(0.8 * initial)} y2={y(0.8 * initial)} stroke="var(--ink-2)" strokeDasharray="4 4"/>
        <text x={W - M.r} y={y(0.8 * initial) - 6} textAnchor="end" className="axis">80 % of initial</text>
        <line x1={x(cell.life)} x2={x(cell.life)} y1={M.t} y2={H - M.b} stroke="var(--ink)"/>
        <rect x={x(p.lo)} y={H - M.b - 6} width={Math.max(2, x(p.hi) - x(p.lo))} height={6} fill="var(--slate-mid)" data-tip={`80 % interval ${p.lo.toFixed(0)}–${p.hi.toFixed(0)} cycles`}/>
        <path d={path} fill="none" stroke="var(--ink)" strokeWidth={2}/>
        {xt.map(t => <text key={t} x={x(t)} y={H - M.b + 18} textAnchor="middle" className="axis">{t.toLocaleString("en")}</text>)}
        {[yMin, yMax].map(t => <text key={t} x={M.l - 8} y={y(t) + 4} textAnchor="end" className="axis">{t.toFixed(2)}</text>)}
        <text x={(M.l + W - M.r) / 2} y={H - 4} textAnchor="middle" className="axis">Cycle · bar under the axis: predicted 80 % interval</text>
      </svg></div></figure>
    <figure className="chart"><figcaption><h3>ΔQ₁₀₀₋₁₀(V) <small>mAh · capacity remaining to 2.0 V on the final 2C stage, cycle 100 minus cycle 10</small></h3></figcaption>
      <div className="chart-scroll"><svg viewBox={`0 0 ${W} ${H}`} style={{"--w": `${W}px`} as React.CSSProperties} role="img" aria-label={`Delta Q curve for cell ${cell.id} between ${grid[0]} and ${grid.at(-1)} volts`}>
        <line x1={M.l} x2={W - M.r} y1={vy(0)} y2={vy(0)} className="grid"/>
        <path d={dpath} fill="none" stroke="var(--ink)" strokeWidth={2}/>
        {[grid[0], (grid[0] + grid.at(-1)!) / 2, grid.at(-1)!].map(v => <text key={v} x={vx(v)} y={H - M.b + 18} textAnchor="middle" className="axis">{v.toFixed(2)} V</text>)}
        {[dmin, dmax].map(v => <text key={v} x={M.l - 8} y={vy(v) + 4} textAnchor="end" className="axis">{v.toFixed(1)}</text>)}
        <text x={(M.l + W - M.r) / 2} y={H - 4} textAnchor="middle" className="axis">Voltage</text>
      </svg></div></figure>
  </div>;
}
