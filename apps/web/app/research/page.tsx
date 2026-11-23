import Link from "next/link";
import {read} from "../fleet/api";
type Metrics={mae_ah:number;rmse_ah:number};
type Report={model_run_id:string;trained_at:string;train_cells:string[];test_cells:string[];train_cycles:number;test_cycles:number;linear:Metrics;baseline:Metrics;sources:Record<string,{cycles:number;url:string}>};
type Point={cycle:number;capacity_ah:number;observed_at:string;source_cycle:number;workbook:string};
export default async function Research({searchParams}:{searchParams:Promise<{cell?:string}>}){
  const r=await read<Report>("/api/research/model-report");
  if(!r?.sources)return <main><h1>Research model unavailable</h1></main>;
  const requested=(await searchParams).cell ?? "";
  const id=Object.hasOwn(r.sources,requested)?requested:r.test_cells[0];
  let points:Point[]=[];
  try{points=(await read<{points:Point[]}>("/api/research/cells/"+id+"/cycles"))?.points??[];}catch{}
  const upper=Math.max(1.1,...points.map(p=>p.capacity_ah));
  const line=points.map((p,i)=>[40+i*540/Math.max(1,points.length-1),170-p.capacity_ah*145/upper].join(",")).join(" ");
  return <main className="desk"><Link href="/">← Workspace</Link><div className="hero"><div><small>MEASURED PUBLIC · UNIVERSITY OF MARYLAND CALCE</small><h1>Cell research</h1><p>Discharge capacity across repeated laboratory cycles.</p></div></div>
  <section><h2>Measured discharge</h2><nav aria-label="Research cells">{Object.keys(r.sources).map(c=><Link key={c} href={"/research?cell="+c}>{c}</Link>)}</nav>
  <article><h3>{id}</h3>{points.length ? <><figure><svg viewBox="0 0 610 205" width="100%" role="img" aria-label={id+" discharge capacity in Ah by retained cycle order"}><path d="M40 25 V170 H580" fill="none" stroke="#7b8b83"/><polyline points={line} fill="none" stroke="#176442" strokeWidth="2"/><g fontSize="12"><text x="0" y="29">{upper.toFixed(2)}</text><text x="0" y="168">0 Ah</text><text x="40" y="190">1</text><text x="460" y="190">Retained cycle {points.length}</text></g></svg><figcaption>Counter difference during each qualifying discharge, in Ah. Tester clock times have no recorded time zone.</figcaption></figure>
  <details><summary>Inspect measurements and original workbook references</summary><ul>{points.map(p=><li key={p.cycle}>{p.cycle} · {p.capacity_ah.toFixed(4)} Ah · {p.observed_at} · {p.workbook} / cycle {p.source_cycle}</li>)}</ul></details></>:<p>Cycle files unavailable. Run the CALCE preparation command in the README to load the measurements locally.</p>}<p><a href={r.sources[id].url}>Original CALCE archive</a></p></article></section>
  <section><h2>Held-out cell evaluation</h2><article><p>Trained on {r.train_cells.join(", ")} ({r.train_cycles} cycles). Tested on {r.test_cells.join(", ")} ({r.test_cycles} cycles). Both estimates use only the training cells to fit their parameters.</p>
  {[["Linear fit",r.linear],["Training mean",r.baseline]].map(([name,m])=><p key={String(name)}><b>{String(name)}</b> · MAE {(m as Metrics).mae_ah.toFixed(4)} Ah · RMSE {(m as Metrics).rmse_ah.toFixed(4)} Ah</p>)}
  <p className="meta">Derived · {r.model_run_id} · {r.trained_at}. Single held-out laboratory cell. The fit estimates discharge capacity from retained cycle order.</p></article></section></main>;
}
