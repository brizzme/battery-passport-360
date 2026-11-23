import Link from "next/link";
import type {LifeReport} from "@/lib/types";

/** Held-out error per model; baseline first, lower is better. */
export function ModelComparison({report, selected, cell}: {report: LifeReport; selected: string; cell: string}) {
  const rows = Object.entries(report.models);
  const max = Math.max(...rows.map(([, m]) => m.mae));
  return <figure className="chart" aria-labelledby="cmp-h">
    <figcaption><h2 id="cmp-h">Held-out error by model <small>mean absolute error in cycles · {report.n_cells} cells · lower is better</small></h2></figcaption>
    <table className="cmp">
      <thead><tr><th scope="col">Model</th><th scope="col">MAE</th><th scope="col" className="num">RMSE</th><th scope="col" className="num">MAPE</th><th scope="col" className="num">80 % interval coverage</th></tr></thead>
      <tbody>{rows.map(([key, m]) => <tr key={key} className={key === selected ? "is-selected" : undefined}>
        <th scope="row"><Link href={`/research?model=${key}&cell=${cell}`} aria-current={key === selected ? "true" : undefined}>{m.label}</Link></th>
        <td><span className="bar-cell"><span className="bar" style={{width: `${(100 * m.mae) / max}%`}} data-tip={`${m.label}: MAE ${m.mae.toFixed(0)} cycles`}/><b>{m.mae.toFixed(0)}</b></span></td>
        <td className="num">{m.rmse.toFixed(0)}</td><td className="num">{m.mape.toFixed(1)} %</td><td className="num">{(100 * m.interval_coverage).toFixed(0)} %</td>
      </tr>)}</tbody>
    </table>
  </figure>;
}
