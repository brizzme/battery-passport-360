"use client";
import {FormEvent,useState} from "react";
type Answer={mode:string;battery_id:string;as_of:string;supported:boolean;message:string;next_step:string|null;tools:string[];
 findings:{field:string;status:string;observation:string;evidence:string|null;citation_ids:string[]}[];
 passages:{chunk_id:string;source_url:string;section:string;passage:string;version:string}[]};
export default function Console({id,date}:{id:string;date:string}){
 const [answer,setAnswer]=useState<Answer|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState("");
 async function submit(e:FormEvent<HTMLFormElement>){
  e.preventDefault();const f=new FormData(e.currentTarget);setBusy(true);setError("");setAnswer(null);
  try{const res=await fetch("/api/copilot",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(Object.fromEntries(f))});
   if(!res.ok)throw Error(res.status===404?"Battery not found.":"Unable to retrieve evidence. Check the local API and inputs.");
   setAnswer(await res.json());
  }catch(e){setError(e instanceof Error?e.message:"Request failed")}finally{setBusy(false)}
 }
 return <><form className="filters" onSubmit={submit}><label>Synthetic battery<input name="battery_id" defaultValue={id} pattern="BAT-DEMO-[0-9]{3}" required/></label>
 <label>Assessment date<input type="date" name="as_of" defaultValue={date} required/></label><label>Question<input name="question" defaultValue="What is missing?" maxLength={500} required/></label><button disabled={busy}>Review evidence</button></form>
 <p role="status">{busy?"Retrieving records and passages…":error}</p>{answer&&<section aria-live="polite"><small>{answer.mode}</small><h2>{answer.message}</h2><p>{answer.battery_id} · {answer.as_of}</p>
 {answer.findings.map(f=><article key={f.field}><h3>{f.field} · {f.status.replaceAll("_"," ")}</h3><p>{f.observation}</p><p className="meta">Synthetic evidence · {f.evidence??"No recorded entry"}</p>{f.citation_ids.map(c=><a key={c} href={"#"+c}> [{c}] </a>)}</article>)}
 {answer.next_step&&<p><b>Suggested expert check.</b> {answer.next_step}</p>}
 {answer.passages.map(p=><article id={p.chunk_id} key={p.chunk_id}><small>REFERENCE DOCUMENT · {p.chunk_id}</small><blockquote>{p.passage}</blockquote><a href={p.source_url}>{p.section} · {p.version}</a></article>)}
 <p className="meta">{answer.tools.join(" → ")}</p></section>}</>;
}
