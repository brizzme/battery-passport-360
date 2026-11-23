/** Functional and technical views of the proof of concept, drawn as accessible HTML in the Ulm system. */

function Node({title, items, tone, href}: {title: string; items: string[]; tone?: "ink" | "plain" | "dashed"; href?: string}) {
  const body = <><h4>{title}</h4><p>{items.join(" · ")}</p></>;
  return <div className={`arch-node ${tone ?? "plain"}`}>{href ? <a href={href}>{body}</a> : body}</div>;
}
const Down = ({label}: {label?: string}) => <div className="arch-arrow" aria-hidden="true"><span>↓</span>{label && <small>{label}</small>}</div>;

export function FunctionalView() {
  return <figure className="arch" aria-labelledby="fv-h">
    <figcaption><h3 id="fv-h">Functional view <small>what a reviewer can do, top to bottom</small></h3></figcaption>
    <div className="arch-flow" role="list">
      <div role="listitem"><Node title="Battery identity and passport records" items={["100 fictional industrial packs", "chemistry and rated data", "model-sheet evidence", "24 months of daily history"]} href="/fleet"/></div>
      <Down/>
      <div className="arch-row" role="listitem">
        <Node title="Passport inspector" items={["72 data points from Commission guidance v3.2", "dates and battery category", "access classes", "provenance per value"]} href="/fleet/BAT-DEMO-024?as_of=2027-02-18"/>
        <Node title="Battery health" items={["synthetic fleet health calibrated on public LFP cells", "measured cell research: life from the first 100 cycles"]} href="/research"/>
      </div>
      <Down/>
      <div role="listitem"><Node tone="ink" title="Review support" items={["fleet review list", "evidence assistant with cited passages", "downloadable investigation draft", "suggests what a specialist should check; never decides use, repair, reuse or recycling"]} href="/"/></div>
      <Down label="hypotheses to validate"/>
      <div role="listitem"><Node tone="dashed" title="Customer and business value" items={["faster investigation preparation", "fewer information gaps before Feb 2027", "better-prepared service planning"]}/></div>
    </div>
  </figure>;
}

export function TechnicalView() {
  return <figure className="arch" aria-labelledby="tv-h">
    <figcaption><h3 id="tv-h">Technical view <small>local Docker Compose stack; offline pipelines produce committed artifacts</small></h3></figcaption>
    <div className="arch-tech">
      <section className="lane" aria-label="Runtime">
        <h4 className="lane-h">Runtime (localhost)</h4>
        <Node title="Browser" items={["keyboard and screen-reader friendly", "375 px to desktop"]}/>
        <Down label="HTTP"/>
        <Node title="Web · Next.js 16 (TypeScript)" items={["server components", "hand-built SVG charts", "shared shell and design system"]}/>
        <Down label="REST on the private network"/>
        <Node title="API · FastAPI (Python 3.12)" items={["readiness engine (catalogue)", "fleet health and review list", "evidence assistant (offline, cited)", "research endpoints", "draft generator"]}/>
        <Down label="SQL"/>
        <Node title="PostgreSQL 16 + pgvector" items={["fleet identities and daily history", "typed passport evidence", "reference passages (EU-*, GUID-DP-*)"]}/>
      </section>
      <section className="lane" aria-label="Offline pipelines">
        <h4 className="lane-h">Offline pipelines (research/)</h4>
        <Node title="Public sources, checksum-pinned" items={["HUST and Aalborg LFP (CC BY 4.0)", "CALCE CS2", "Commission guidance v3.2 PDF", "EUR-Lex excerpts"]}/>
        <Down/>
        <Node tone="dashed" title="Isolated extractor" items={["Docker, no network, read-only, non-root", "opens untrusted pickles only here"]}/>
        <Down/>
        <Node title="Calibration, generator, catalogue parser, life model" items={["deterministic seeds", "leakage-guarded evaluation", "verifier scripts"]}/>
        <Down label="committed artifacts and seeds"/>
        <Node title="Migrations 001–007 and API artifacts" items={["loaded at boot", "fresh clone needs no downloads"]}/>
      </section>
      <section className="lane narrow" aria-label="Optional">
        <h4 className="lane-h">Optional, not connected</h4>
        <Node tone="dashed" title="Claude API (proposed)" items={["server-side key only", "only synthetic IDs and statuses sent", "orders or phrases verified findings", "visible offline fallback"]}/>
      </section>
    </div>
  </figure>;
}
