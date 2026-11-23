import type {LifeCell, Pred} from "@/lib/types";
import {linearScale, niceTicks} from "@/lib/geometry";

const W = 640, H = 460, M = {l: 64, r: 16, t: 16, b: 48};

/** Predicted vs actual life for every held-out cell, with 80 % intervals and the identity line. */
export function LifeScatter({cells, model, label, selected}: {cells: LifeCell[]; model: string; label: string; selected: string}) {
  const lo = Math.min(...cells.map(c => Math.min(c.life, (c[model] as Pred).lo)));
  const hi = Math.max(...cells.map(c => Math.max(c.life, (c[model] as Pred).hi)));
  const ticks = niceTicks(Math.floor(lo / 500) * 500, hi, 6);
  const d: [number, number] = [ticks[0], ticks.at(-1)!];
  const x = linearScale(d, [M.l, W - M.r]), y = linearScale(d, [H - M.b, M.t]);
  return <figure className="chart" aria-labelledby="sc-h">
    <figcaption><h2 id="sc-h">Predicted vs measured life <small>{label} · each cell predicted by a model that never saw its batch · bars: 80 % interval</small></h2></figcaption>
    <div className="chart-scroll"><svg viewBox={`0 0 ${W} ${H}`} style={{"--w": `${W}px`} as React.CSSProperties} role="img" aria-label={`Predicted against measured cycle life for ${cells.length} cells`}>
      {ticks.map(t => <g key={t}><line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} className="grid"/><text x={M.l - 8} y={y(t) + 4} textAnchor="end" className="axis">{t.toLocaleString("en")}</text>
        <text x={x(t)} y={H - M.b + 18} textAnchor="middle" className="axis">{t.toLocaleString("en")}</text></g>)}
      <line x1={x(d[0])} y1={y(d[0])} x2={x(d[1])} y2={y(d[1])} stroke="var(--ink-2)" strokeDasharray="4 4"/>
      <text x={x(d[1]) - 4} y={y(d[1]) + 16} textAnchor="end" className="axis">predicted = measured</text>
      <text x={(M.l + W - M.r) / 2} y={H - 6} textAnchor="middle" className="axis">Measured cycle life</text>
      <text x={14} y={(M.t + H - M.b) / 2} transform={`rotate(-90 14 ${(M.t + H - M.b) / 2})`} textAnchor="middle" className="axis">Predicted cycle life</text>
      {cells.map(c => { const p = c[model] as Pred; const s = c.id === selected;
        return <a key={c.id} href={`/research?model=${model}&cell=${c.id}`} aria-label={`Cell ${c.id}, batch ${c.batch}: measured ${c.life}, predicted ${p.pred.toFixed(0)} (80 % interval ${p.lo.toFixed(0)}–${p.hi.toFixed(0)}) cycles`}
          data-tip={`Cell ${c.id} · measured ${c.life} · predicted ${p.pred.toFixed(0)} (${p.lo.toFixed(0)}–${p.hi.toFixed(0)})`}>
          <line x1={x(c.life)} x2={x(c.life)} y1={y(p.lo)} y2={y(p.hi)} stroke="var(--rule)" strokeWidth={s ? 2 : 1}/>
          <circle cx={x(c.life)} cy={y(p.pred)} r={12} fill="transparent"/>
          <circle cx={x(c.life)} cy={y(p.pred)} r={s ? 6.5 : 4} fill={s ? "var(--surface)" : "var(--ink)"} stroke="var(--ink)" strokeWidth={s ? 3 : 1}/>
        </a>; })}
    </svg></div>
    <details><summary>View as table</summary><table><thead><tr><th>Cell</th><th>Batch</th><th className="num">Measured</th><th className="num">Predicted</th><th className="num">80 % interval</th></tr></thead>
      <tbody>{cells.map(c => { const p = c[model] as Pred; return <tr key={c.id}><td>{c.id}</td><td>{c.batch}</td><td className="num">{c.life}</td><td className="num">{p.pred.toFixed(0)}</td><td className="num">{p.lo.toFixed(0)}–{p.hi.toFixed(0)}</td></tr>; })}</tbody></table></details>
  </figure>;
}
