import {read} from "../fleet/api";
import type {CellDetail, LifeCell, LifeReport} from "@/lib/types";
import {ModelComparison} from "@/components/ModelComparison";
import {LifeScatter} from "@/components/LifeScatter";
import {CellCurves} from "@/components/CellCurves";
import {Tooltip} from "@/components/Tooltip";

type Calce = {status: string; model_run_id?: string; train_cells?: string[]; test_cells?: string[]; test_cycles?: number;
  linear?: {mae_ah: number; rmse_ah: number}; baseline?: {mae_ah: number; rmse_ah: number}};

export default async function Research({searchParams}: {searchParams: Promise<{cell?: string; model?: string}>}) {
  const q = await searchParams;
  const report = await read<LifeReport>("/api/research/hust/report");
  const cells = await read<LifeCell[]>("/api/research/hust/cells");
  if (!report || !cells) throw Error("Research results unavailable");
  const model = q.model && q.model in report.models ? q.model : Object.entries(report.models).filter(([k]) => k !== "baseline").sort((a, b) => a[1].mae - b[1].mae)[0][0];
  const median = [...cells].sort((a, b) => Math.abs(a.life - report.life_summary.median) - Math.abs(b.life - report.life_summary.median))[0];
  const cellId = cells.some(c => c.id === q.cell) ? q.cell! : median.id;
  const cell = await read<CellDetail>(`/api/research/hust/cells/${encodeURIComponent(cellId)}`);
  const calce = await read<Calce>("/api/research/model-report");
  const m = report.models, base = m.baseline;
  const [, best] = Object.entries(m).filter(([k]) => k !== "baseline").sort((a, b) => a[1].mae - b[1].mae)[0];
  return <div className="dash research">
    <div className="page-head compact"><h1>Cell research</h1>
      <p>Measured laboratory cells (HUST LFP, CC BY 4.0) · not the fictional fleet · predictions are derived</p></div>

    <dl className="kpis">
      <div className="kpi"><dt>Cells</dt><dd><span className="kpi-num">{report.n_cells}</span></dd><dd className="kpi-detail">LFP/graphite 1.1 Ah, {report.n_batches} test batches</dd></div>
      <div className="kpi"><dt>Measured life</dt><dd><span className="kpi-num">{report.life_summary.min.toLocaleString("en")}–{report.life_summary.max.toLocaleString("en")}</span></dd><dd className="kpi-detail">cycles to 80 % of initial capacity</dd></div>
      <div className="kpi"><dt>Baseline error</dt><dd><span className="kpi-num">{base.mae.toFixed(0)}</span><span className="kpi-unit">cycles MAE</span></dd><dd className="kpi-detail">predicting the training mean</dd></div>
      <div className="kpi"><dt>Best held-out error</dt><dd><span className="kpi-num">{best.mae.toFixed(0)}</span><span className="kpi-unit">cycles MAE</span></dd><dd className="kpi-detail">{best.label.toLowerCase()}, first 100 cycles</dd></div>
      <div className="kpi"><dt>Interval coverage</dt><dd><span className="kpi-num">{(100 * best.interval_coverage).toFixed(0)} %</span></dd><dd className="kpi-detail">of cells inside their 80 % interval; varies by batch</dd></div>
    </dl>

    <div className="dash-main">
      <ModelComparison report={report} selected={model} cell={cellId}/>
      <section aria-labelledby="find-h" className="provenance">
        <h2 id="find-h">What the comparison shows</h2>
        <p>{best.label} from the first 100 cycles cut the error from {base.mae.toFixed(0)} to {best.mae.toFixed(0)} cycles against the training-mean baseline (per-fold range {best.fold_mae_range[0].toFixed(0)}–{best.fold_mae_range[1].toFixed(0)}). Model strength selection settled at effectively no regularisation.</p>
        <p>The voltage-curve feature, adapted from Severson et al. (2019), adds no skill here: alone it matches the baseline ({m.voltage_variance.mae.toFixed(0)} cycles), and adding it to the capacity features gives {m.full.mae.toFixed(0)} cycles. This null result is reported as measured.</p>
        <p className="meta">{report.voltage_feature_note}</p>
      </section>
    </div>

    <LifeScatter cells={cells} model={model} label={m[model].label} selected={cellId}/>
    {cell && <CellCurves cell={cell} model={model}/>}

    <div className="dash-pair">
      <section aria-labelledby="method-h" className="provenance">
        <h2 id="method-h">Method and leakage guards</h2>
        <dl>
          <div><dt>Target</dt><dd>{report.target}.</dd></div>
          <div><dt>Split</dt><dd>{report.split}.</dd></div>
          <div><dt>Intervals</dt><dd>{report.intervals}.</dd></div>
          <div><dt>Guards</dt><dd>Features read cycles ≤ {report.horizon_cycles} only; no batch appears in both training and test; model strength and intervals are chosen inside the training batches. <code>research/verify_life.py</code> recomputes every number from the per-cell predictions.</dd></div>
        </dl>
      </section>
      <section aria-labelledby="src-h" className="provenance">
        <h2 id="src-h">Data and limits</h2>
        <dl>
          <div><dt>Dataset</dt><dd>{report.data.dataset}. Per-cell protocols from Microsoft BatteryML (MIT).</dd></div>
          <div><dt>Run</dt><dd>{report.run_id} · {report.generated_at.slice(0, 10)}</dd></div>
          <div><dt>Limits</dt><dd>One cell type, one laboratory, 30 °C. Results describe these cells only and are not applied to fleet packs.</dd></div>
        </dl>
      </section>
    </div>

    {calce?.status === "trained" && <details className="dp-group">
      <summary>Legacy baseline: CALCE CS2 capacity trend <small>superseded</small></summary>
      <p>Linear fit of capacity on retained cycle order, trained on {calce.train_cells?.join(", ")}, tested on {calce.test_cells?.join(", ")} ({calce.test_cycles} cycles): MAE {calce.linear?.mae_ah.toFixed(4)} Ah against {calce.baseline?.mae_ah.toFixed(4)} Ah for the training mean. Kept for reference; one held-out cell cannot support a general claim.</p>
      <p className="meta">Derived · {calce.model_run_id}</p>
    </details>}
    <Tooltip/>
  </div>;
}
