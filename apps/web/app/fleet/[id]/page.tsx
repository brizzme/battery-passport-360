import Link from "next/link";
import {notFound} from "next/navigation";
import {Inspection,dateChoice,preset,read} from "../api";
export default async function Detail({params,searchParams}:{params:Promise<{id:string}>;searchParams:Promise<{as_of?:string}>}) {
  const {id}=await params; const day=dateChoice((await searchParams).as_of);
  const path="/fleet/"+encodeURIComponent(id);
  const data=await read<Inspection>("/api/batteries/"+encodeURIComponent(id)+"/passport-readiness"+(day?"?as_of="+day:""));
  if(!data) notFound();
  const {battery:b,bench}=data;
  return <main className="desk"><Link href="/fleet">← Fleet register</Link><div className="hero"><div><small>SYNTHETIC · INDUSTRIAL PACK</small><h1>{b.battery_id}</h1><p>{b.chemistry} · {b.rated_kwh} kWh rated energy</p></div></div>
  <p className="meta">{b.source_id} · {b.observed_at} · {b.explanation}</p>
  <section><h2>Passport evidence</h2><p>{data.scenario} Illustrative data readiness. Missing evidence calls for review.</p>
  <form className="filters"><label>Assessment date<input type="date" name="as_of" defaultValue={data.as_of} required/></label><button>Apply date</button><Link href={path}>Today</Link><Link href={path+"?as_of="+preset}>18 Feb 2027 preset</Link></form>
  {data.results.map(r=><article key={r.rule_id}><small>DERIVED · {r.rule_id} v{r.version}</small><h3>{r.label} <span className="badge">{r.status.replaceAll("_"," ")}</span></h3><p>{r.reason}</p>
  <p className="meta">As of {data.as_of} · Earliest date {r.effective_from} · Public model field · <a href={r.source_url}>{r.section}</a></p>
  {r.evidence && <p className="meta">Synthetic entry “{r.evidence.value_text}” · {r.evidence.evidence_ref ?? "No evidence reference"} · {r.evidence.source_id} · {r.evidence.observed_at} · {r.evidence.explanation}</p>}</article>)}</section>
  <p><Link href={"/assistant?id="+id+"&as_of="+data.as_of}>Ask the evidence assistant</Link> · <a download href={"/api/draft?id="+id+"&as_of="+data.as_of}>Download draft summary</a></p>
  <section><h2>Simulated bench history</h2>{bench ? <article><h3>{bench.vehicle_id}</h3><p>Assigned {bench.assigned_on}. Charge session {bench.started_at} to {bench.ended_at} delivered {bench.energy_kwh} kWh.</p>
  <p>At {bench.sampled_at}: {bench.soc_pct}% charge, {bench.temperature_c} °C. {bench.serviced_at}: {bench.note}.</p><p className="meta">Synthetic · {bench.source_id} · {bench.observed_at} · {bench.explanation}</p></article>:<p>No bench records available on this date.</p>}</section></main>;
}
