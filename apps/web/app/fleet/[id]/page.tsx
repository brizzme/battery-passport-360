import Link from "next/link";
import {notFound} from "next/navigation";
import {Inspection,dateChoice,preset,read} from "../api";
export default async function Detail({params,searchParams}:{params:Promise<{id:string}>;searchParams:Promise<{as_of?:string}>}) {
  const {id}=await params; const day=dateChoice((await searchParams).as_of);
  const path="/fleet/"+encodeURIComponent(id);
  const data=await read<Inspection>("/api/batteries/"+encodeURIComponent(id)+"/passport-readiness"+(day?"?as_of="+day:""));
  if(!data) notFound();
  const {battery:b,health}=data;
  return <div className="desk"><div className="page-head"><h1>{b.battery_id}</h1><p>{b.chemistry} · {b.rated_kwh} kWh rated energy <small>Synthetic industrial pack</small></p></div>
  <p className="meta">{b.source_id} · {b.observed_at} · {b.explanation}</p>
  <section><h2>Passport evidence</h2><p>{data.scenario} Illustrative data readiness. Missing evidence calls for review.</p>
  <form className="filters"><label>Assessment date<input type="date" name="as_of" defaultValue={data.as_of} required/></label><button>Apply date</button><Link href={path}>Today</Link><Link href={path+"?as_of="+preset}>18 Feb 2027 preset</Link></form>
  {data.results.map(r=><article key={r.rule_id}><small>DERIVED · {r.rule_id} v{r.version}</small><h3>{r.label} <span className="badge">{r.status.replaceAll("_"," ")}</span></h3><p>{r.reason}</p>
  <p className="meta">As of {data.as_of} · Earliest date {r.effective_from} · Public model field · <a href={r.source_url}>{r.section}</a></p>
  {r.evidence && <p className="meta">Synthetic entry “{r.evidence.value_text}” · {r.evidence.evidence_ref ?? "No evidence reference"} · {r.evidence.source_id} · {r.evidence.observed_at} · {r.evidence.explanation}</p>}</article>)}</section>
  <p><Link href={"/assistant?id="+id+"&as_of="+data.as_of}>Ask the evidence assistant</Link> · <a download href={"/api/draft?id="+id+"&as_of="+data.as_of}>Download draft summary</a></p>
  <section><h2>Synthetic pack health</h2>{health ? <article><p className="meta">Simulated · {health.source_id} · data cut-off {health.data_cutoff} · values as of {health.as_of} · {health.chemistry==="LFP" ? `calibration ${health.calibration_version} (HUST and Aalborg LFP measurements, CC BY 4.0)` : "no calibration source for this chemistry; operational values are generator assumptions"}</p>
  <ul>{health.indicators.map(i=><li key={i.key}><b>{i.label}</b>: {i.status==="value" ? `${i.value} ${i.unit ?? ""}` : `${i.status.replaceAll("_"," ")} — ${i.reason}`}<br/><small>{i.passport_field ? `${i.passport_ref} · restricted access · ${i.mapping_status}` : "Operational indicator, not a passport field"} · basis {i.calibration_refs.join(", ")}{i.labels.length ? " · " + i.labels.join(", ") : ""}</small></li>)}</ul>
  {health.not_applicable.map(i=><p key={i.key} className="meta">{i.label}: not applicable. {i.reason}</p>)}
  <p className="meta">{health.events.length} synthetic events recorded up to {health.as_of}.</p></article> : <p>No synthetic pack history available.</p>}</section></div>;
}
