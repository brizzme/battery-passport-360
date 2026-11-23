export async function POST(req:Request) {
  try {
    const body=await req.text();
    if(body.length>2048)return Response.json({detail:"Question too long"},{status:413});
    const res=await fetch((process.env.API_BASE_URL??"http://127.0.0.1:8000")+"/api/copilot/query",{method:"POST",headers:{"Content-Type":"application/json"},body,signal:AbortSignal.timeout(12000)});
    return Response.json(await res.json(),{status:res.status});
  }catch{return Response.json({detail:"Local service unavailable"},{status:503})}
}
