import {bandCounts} from "@/lib/geometry";

const STYLE: Record<string, {bg: string; hatch?: boolean; label: string}> = {
  "95-100": {bg: "var(--ink)", label: "95–100 %"},
  "90-95": {bg: "#4a5961", label: "90–95 %"},
  "80-90": {bg: "#8a979c", label: "80–90 %"},
  "below 80": {bg: "#c9cec9", hatch: true, label: "below 80 % (extrapolated)"},
  "unknown": {bg: "var(--ground)", hatch: true, label: "unknown (lead-acid)"},
};

export function BandBar({bands}: {bands: Record<string, number>}) {
  const rows = bandCounts(bands);
  const total = rows.reduce((s, r) => s + r.count, 0);
  return <figure className="bands" aria-labelledby="bands-h">
    <figcaption id="bands-h"><h3>Capacity bands <small>{total} packs</small></h3></figcaption>
    <div className="band-bar" role="img" aria-label={rows.map(r => `${STYLE[r.key].label}: ${r.count}`).join("; ")}>
      {rows.filter(r => r.count).map(r => <span key={r.key} data-tip={`${STYLE[r.key].label}: ${r.count} packs`}
        style={{flexGrow: r.count, background: STYLE[r.key].bg}} className={STYLE[r.key].hatch ? "hatched" : undefined}/>)}
    </div>
    <ul className="legend">{rows.map(r => <li key={r.key}><span className={"swatch" + (STYLE[r.key].hatch ? " hatch" : "")} style={{background: STYLE[r.key].bg}}/>{STYLE[r.key].label}: <b>{r.count}</b></li>)}</ul>
  </figure>;
}
