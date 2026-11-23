export type Kpi = {label: string; value: string; unit?: string; detail?: string};
export function KpiStrip({items}: {items: Kpi[]}) {
  return <dl className="kpis">{items.map(k => <div key={k.label} className="kpi">
    <dt>{k.label}</dt>
    <dd><span className="kpi-num">{k.value}</span>{k.unit && <span className="kpi-unit">{k.unit}</span>}</dd>
    {k.detail && <dd className="kpi-detail">{k.detail}</dd>}
  </div>)}</dl>;
}
