/** Forwards read-only API pages (docs, schema, health) so links work behind a single public origin. */
export async function forward(path: string): Promise<Response> {
  try {
    const res = await fetch((process.env.API_BASE_URL ?? "http://127.0.0.1:8000") + path, {cache: "no-store", signal: AbortSignal.timeout(8000)});
    return new Response(res.body, {status: res.status, headers: {"content-type": res.headers.get("content-type") ?? "text/plain"}});
  } catch {
    return new Response("API unavailable", {status: 502});
  }
}
