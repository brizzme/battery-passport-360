export async function GET(req:Request){
 const params=new URL(req.url).searchParams;
 try{
  const resp=await fetch((process.env.API_BASE_URL??"http://127.0.0.1:8000")+"/api/inspection-summaries",{
   method:"POST",headers:{"Content-Type":"application/json"},cache:"no-store",signal:AbortSignal.timeout(6000),
   body:JSON.stringify({battery_id:params.get("id"),as_of:params.get("as_of")})});
  if(!resp.ok)return new Response("Could not load this inspection.",{status:resp.status});
  return new Response(resp.body,{headers:{"Content-Type":"text/markdown; charset=utf-8","Content-Disposition":resp.headers.get("Content-Disposition")??"attachment"}});
 }catch{return new Response("Local API unavailable",{status:503})}
}
