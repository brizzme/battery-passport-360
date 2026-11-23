const R = [
  {key: "calibrated", label: "Calibrated 35–45 °C", bg: "var(--ink)"},
  {key: "extrapolated_below_calibrated_range", label: "Extrapolated 20–35 °C", bg: "#8a979c", hatch: true},
  {key: "clamped_low", label: "Clamped below 20 °C", bg: "#c9cec9", hatch: true},
  {key: "clamped_high", label: "Clamped above 45 °C", bg: "#4a5961", hatch: true},
];
const pct = (v: number) => `${(100 * v).toFixed(v < 0.01 ? 1 : 0)} %`;
export function RegimeStrip({share}: {share: Record<string, number>}) {
  return <figure className="regimes" aria-labelledby="regime-h">
    <figcaption><h2 id="regime-h">Where the temperature model is measured <small>share of LFP pack-days</small></h2>
      <p>Fade per cycle was measured on Aalborg cells at 35, 40 and 45 °C. Most simulated days run cooler, so their fade is extrapolated or clamped, and labelled that way on every pack.</p></figcaption>
    <div className="band-bar" role="img" aria-label={R.map(r => `${r.label}: ${pct(share[r.key] ?? 0)}`).join("; ")}>
      {R.filter(r => share[r.key]).map(r => <span key={r.key} data-tip={`${r.label}: ${pct(share[r.key])}`} style={{flexGrow: share[r.key], background: r.bg}} className={r.hatch ? "hatched" : undefined}/>)}
    </div>
    <ul className="legend">{R.map(r => <li key={r.key}><span className={"swatch" + (r.hatch ? " hatch" : "")} style={{background: r.bg}}/>{r.label}: <b>{pct(share[r.key] ?? 0)}</b></li>)}</ul>
  </figure>;
}
