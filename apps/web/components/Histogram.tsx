import type {Bin} from "@/app/fleet/api";
import {linearScale} from "@/lib/geometry";

const W = 340, H = 180, M = {l: 8, r: 8, t: 8, b: 34};

export function Histogram({bins, unit, title, color}: {bins: Bin[]; unit: string; title: string; color: string}) {
  if (!bins.length) return <p className="empty">No recorded hours in this period.</p>;
  const total = bins.reduce((s, b) => s + b.hours, 0);
  const max = Math.max(...bins.map(b => b.hours));
  const bw = (W - M.l - M.r) / bins.length;
  const y = linearScale([0, max], [H - M.b, M.t]);
  return <figure className="chart small">
    <figcaption><h3>{title} <small>hours since Nov 2024 · {total.toLocaleString("en", {maximumFractionDigits: 0})} h</small></h3></figcaption>
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${title}: ` + bins.map(b => `${b.bin_lower}–${b.bin_upper} ${unit}: ${b.hours.toFixed(0)} h`).join("; ")}>
      {bins.map((b, i) => <g key={b.bin_lower}>
        <rect x={M.l + i * bw + 1} y={y(b.hours)} width={bw - 2} height={H - M.b - y(b.hours)} fill={color}
          data-tip={`${b.bin_lower}–${b.bin_upper} ${unit}: ${b.hours.toFixed(0)} h (${total ? (100 * b.hours / total).toFixed(1) : "0"} %)`}/>
        {(i === 0 || i === bins.length - 1 || bins.length <= 6) && <text x={M.l + i * bw + bw / 2} y={H - M.b + 16} textAnchor="middle" className="axis">{b.bin_lower}</text>}
      </g>)}
      <text x={W - M.r} y={H - 4} textAnchor="end" className="axis">{unit}</text>
    </svg>
  </figure>;
}
