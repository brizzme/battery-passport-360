import Link from "next/link";
import {Battery, dateChoice, preset, read, statuses} from "./api";
export default async function Fleet({searchParams}:{searchParams:Promise<Record<string,string|undefined>>}) {
  const p = await searchParams;
  const args = new URLSearchParams({query:p.query ?? "",page:String(Math.max(1,parseInt(p.page || "1") || 1))});
  if(statuses.includes(p.status || "")) args.set("status",p.status!);
  if(dateChoice(p.as_of)) args.set("as_of",p.as_of!);
  const data = await read<{items:Battery[];total:number;page:number;page_size:number;as_of:string}>("/api/batteries?"+args);
  if(!data) throw Error("Fleet unavailable");
  function pageUrl(page:number){const next=new URLSearchParams(args);next.set("page",String(page));return "/fleet?"+next;}
  return <main className="desk"><Link href="/">← Workspace</Link><div className="hero"><div><small>SYNTHETIC INDUSTRIAL BATTERIES</small><h1>Fleet register</h1><p>Find a pack and inspect its passport evidence.</p></div></div>
  <form className="filters"><label>Battery ID or chemistry<input name="query" defaultValue={p.query} maxLength={100}/></label>
  <label>Rule status<select name="status" defaultValue={p.status}><option value="">All statuses</option>{statuses.map(s=><option key={s} value={s}>{s.replaceAll("_"," ")}</option>)}</select></label>
  <label>Assessment date<select name="as_of" defaultValue={dateChoice(p.as_of)}><option value="">Today (UTC)</option><option value={preset}>18 Feb 2027</option>{p.as_of && p.as_of!==preset && <option>{p.as_of}</option>}</select></label><button>Search</button></form>
  <h2>{data.total} matching batteries</h2><p>Assessed {data.as_of} · Synthetic seed</p>
  <ul className="records">{data.items.map(b=><li key={b.battery_id}><Link href={"/fleet/"+b.battery_id+"?as_of="+data.as_of}>{b.battery_id}</Link><span>{b.chemistry} · {b.rated_kwh} kWh</span></li>)}</ul>
  {!data.items.length && <p>No records on this page. <Link href="/fleet">Clear filters</Link></p>}
  <nav>{data.page>1 && <Link href={pageUrl(data.page-1)}>Previous page</Link>} {data.page*data.page_size<data.total && <Link href={pageUrl(data.page+1)}>Next page</Link>}</nav>
  {data.items[0] && <footer>{data.items[0].source_id} · {data.items[0].observed_at} · {data.items[0].explanation}</footer>}</main>;
}
