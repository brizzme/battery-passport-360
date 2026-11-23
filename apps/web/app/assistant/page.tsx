import Console from "./console";
export default async function Assistant({searchParams}:{searchParams:Promise<{id?:string;as_of?:string}>}){
 const p=await searchParams;
 return <div className="desk"><div className="page-head"><h1>Evidence assistant</h1><p>Review a battery’s evidence gaps with the public references used by the inspector. <small>Synthetic fleet</small></p></div><Console id={p.id??"BAT-DEMO-024"} date={p.as_of??"2027-02-18"}/></div>;
}
