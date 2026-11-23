import Link from "next/link";
import { Suspense } from "react";

export const dynamic = "force-dynamic";

async function ServiceStatus() {
  let ready = false;
  try {
    const response = await fetch(
      (process.env.API_BASE_URL ?? "http://127.0.0.1:8000") + "/health",
      { cache: "no-store", signal: AbortSignal.timeout(4000) }
    );
    if (response.ok) {
      const health = await response.json();
      ready = health.status === "ok" && health.database === "ready";
    }
  } catch {
    // A stopped service should leave the workspace and diagnostic links usable.
  }
  return <div className="status">
    <h3><span className={ready ? "dot ready" : "dot"} />{ready ? "Services online" : "Connection unavailable"}</h3>
    <p>{ready ? "The API reached PostgreSQL and verified the vector extension." : "Check the API and database, then reload this page to retry."}</p>
  </div>;
}

export default function Workspace() {
  const api = "http://127.0.0.1:" + (process.env.PUBLIC_API_PORT ?? "8000");
  return <>
    <a className="skip" href="#main">Skip to workspace</a>
    <header><div className="bar"><b><i aria-hidden="true">▥</i> Battery Passport 360</b><span>Local workspace</span></div></header>
    <main id="main">
      <div className="hero">
        <div><small>LOCAL DEMO</small><h1>Battery workspace</h1>
        <p>Inspect synthetic pack records and explore measured cell research.</p></div>
        <div className="cell-art" aria-hidden="true">{Array.from({length: 12}, (_, i) => <i key={i}/>)}</div>
      </div>
      <section className="entry"><h2>Passport inspector</h2><p><Link href="/fleet">Browse synthetic fleet</Link> · <Link href="/fleet/BAT-DEMO-024?as_of=2027-02-18">Inspect BAT-DEMO-024</Link></p></section>
      <section className="entry"><h2>Laboratory measurements</h2><Link href="/research">Explore CALCE cell research</Link></section>
      <section aria-labelledby="services"><h2 id="services">Service health</h2>
        <Suspense fallback={<p role="status">Checking the API and database…</p>}><ServiceStatus/></Suspense>
      </section>
      <section aria-labelledby="tools"><h2 id="tools">Developer tools</h2>
        <div className="links">{[
          ["API reference", "/docs", "Explore endpoints and response schemas."],
          ["Health response", "/health", "View the current service check as JSON."],
        ].map(([title, path, description]) => <a key={path} href={api + path}><small>{path}</small><h3>{title} <span aria-hidden="true">↗</span></h3><p>{description}</p></a>)}</div>
      </section>
      <footer>Battery Passport 360 · Independent industrial battery research prototype</footer>
    </main>
  </>;
}
