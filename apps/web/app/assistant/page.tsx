import Link from "next/link";
import Console from "./console";
export default async function Assistant({searchParams}:{searchParams:Promise<{id?:string;as_of?:string}>}){
 const p=await searchParams;
 return <main className="desk"><Link href="/">← Workspace</Link><div className="hero"><div><small>SYNTHETIC FLEET</small><h1>Evidence assistant</h1><p>Review a battery’s evidence gaps with the public references used by the inspector.</p></div></div><Console id={p.id??"BAT-DEMO-024"} date={p.as_of??"2027-02-18"}/></main>;
}
