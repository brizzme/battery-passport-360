import Link from "next/link";
import {read, type Inspection} from "./fleet/api";
import type {FleetHealth, LifeReport} from "@/lib/types";
import {FunctionalView, TechnicalView} from "@/components/ArchDiagrams";

export const dynamic = "force-dynamic";
export const metadata = {title: "PoC summary · Battery Passport 360"};
const fmt = (n: number) => n.toLocaleString("en", {maximumFractionDigits: 0});

const CONTENTS = [
  {href: "/fleet-health", name: "Fleet health", what: "Headline figures, the specialist review list with reasons, the fleet floor by site, capacity bands, capacity against cycles, where the temperature model is measured, data sources."},
  {href: "/fleet", name: "Passport inspector", what: "Fleet register with search and status filters; per pack: health charts (capacity history, temperature and state-of-charge exposure, idle spans and events) and coverage of all 72 guidance data points, gaps first."},
  {href: "/assistant?id=BAT-DEMO-024&as_of=2027-02-18", name: "Evidence assistant", what: "Answers a small set of evidence questions offline, citing the retrieved guidance and regulation passages; refuses approval or certification requests."},
  {href: "/research", name: "Cell research", what: "Early-cycle life models on 77 measured HUST cells, leave-one-batch-out, with intervals, per-cell curves and the method and leakage guards."},
  {href: "/fleet/BAT-DEMO-024?as_of=2027-02-18", name: "Investigation draft", what: "Downloadable Markdown draft per pack: coverage counts, every gap with references, health summary, synthetic provenance and the expert-review reminder."},
];

const NEXT = [
  {item: "LLM chat in the evidence assistant", detail: "Integrated: a cited summary and prioritised checks over verified gaps, validated server-side (known fields, retrieved citations only, no certifying words), with a visible offline fallback. Switch on with a server-side API key; then evaluate usefulness with specialists.", state: "Integrated, needs key"},
  {item: "RAG: open chat over guidance and the operator's documents", detail: "Today: six question templates and keyword retrieval over guidance and regulation excerpts. Next: ingest supplier declarations, datasheets, test reports and service logs; embed passages in pgvector (already in the stack) with keyword search; filter retrieval by pack, date and access class; answer open questions with mandatory citations; suggest which document holds a missing data point for a person to confirm. Documents stay untrusted data; statuses stay rule-based; release only after a question test set passes.", state: "Roadmap"},
  {item: "Access control before any hosting", detail: "Authentication, HTTPS, rate limits, logging and privacy review; restricted-access passport fields must be gated by role.", state: "Required before hosting"},
  {item: "Automated checks", detail: "CI with committed browser tests; today every check is run by hand.", state: "Deferred"},
  {item: "Verify two legal dates", detail: "Article 8 recycled-content timetable for LMT batteries (shown as unknown) and the exact responsible-sourcing start day (18 Aug 2027 used).", state: "Open"},
  {item: "Data-to-Value Explorer", detail: "Stretch goal from the specification: profile an unfamiliar CSV and suggest AI use cases with required fields and KPIs.", state: "Not started"},
];

export default async function Summary() {
  // Contact details come from server-side settings, never from the repository.
  const contact = {name: process.env.CONTACT_NAME, email: process.env.CONTACT_EMAIL, phone: process.env.CONTACT_PHONE};
  const fleet = await read<FleetHealth>("/api/fleet/health-summary");
  const life = await read<LifeReport>("/api/research/hust/report");
  const pack = await read<Inspection>("/api/batteries/BAT-DEMO-024/passport-readiness?as_of=2027-02-18");
  const reviewPacks = fleet ? new Set(fleet.review.map(r => r.battery_id)).size : 0;
  const gapPacks = fleet ? new Set(fleet.review.filter(r => r.rule === "passport_gaps_at_milestone").map(r => r.battery_id)).size : 0;
  const best = life ? Object.entries(life.models).filter(([k]) => k !== "baseline").sort((a, b) => a[1].mae - b[1].mae)[0][1] : null;
  return <div className="dash summary">
    <div className="page-head"><h1>Battery Passport 360: proof of concept</h1>
      <p>An independent prototype showing how EU battery-passport readiness, battery-health analytics and evidence-based review support can work together for industrial battery fleets. Not an official passport service, and not affiliated with any battery manufacturer.</p>
      {contact.name && <p className="byline">Prepared by <b>{contact.name}</b>{contact.email && <> · <a href={"mailto:" + contact.email}>{contact.email}</a></>}{contact.phone && <> · <a href={"tel:" + contact.phone.replace(/\s/g, "")}>{contact.phone}</a></>}</p>}</div>

    <section aria-labelledby="prob-h" className="panel">
      <h2 id="prob-h">Problem statement</h2>
      <p>From 18 February 2027 the EU battery passport (Regulation (EU) 2023/1542, Article 77) applies to industrial batteries above 2 kWh, subject to detailed applicability, phased requirements and access rules. Fleet operators and service teams then need to show, per battery, which passport data exists and where it comes from.</p>
      <ul className="plain">
        <li><b>Evidence is scattered.</b> Passport data sits in documents, ERP records, BMS exports and supplier files, with no single view per pack.</li>
        <li><b>Requirements are dated and restricted.</b> The Commission guidance lists 72 data points; some apply only later, some only to certain designs, some only to authorised readers.</li>
        <li><b>Health is not linked to the passport.</b> State of health and expected life depend on operating data (temperature, cycles, idle time) that is rarely joined to passport fields.</li>
        <li><b>Specialists lack a worklist.</b> Without ranked reasons, attention goes to the loudest pack, not the one that needs it.</li>
      </ul>
    </section>

    <section aria-labelledby="obj-h" className="summary-grid">
      <div className="panel"><h2 id="obj-h">Objective</h2>
        <p>Help a fleet manager, service engineer or battery specialist answer three questions with traceable evidence: which packs need a specialist&apos;s attention, what passport evidence is missing ahead of 18 February 2027, and what measured data says about ageing.</p>
        <p>Success for this PoC: a reviewer finds the right pack, understands why, and can trace every value to its source within minutes.</p></div>
      <div className="panel"><h2>Boundaries</h2>
        <ul className="plain">
          <li>Fleet data is fictional and simulated; research data is measured public data. They never share a model.</li>
          <li>Readiness is illustrative and follows non-binding Commission guidance; nothing is called compliant or certified.</li>
          <li>The system suggests what to review; qualified specialists decide on operation, repair, reuse or recycling.</li>
          <li>Runs without accounts or downloads; the LLM chat is optional and falls back visibly to offline mode.</li>
        </ul></div>
    </section>

    <section aria-labelledby="views-h"><h2 id="views-h">Architecture</h2>
      <div className="arch-stack"><FunctionalView/><TechnicalView/></div>
    </section>

    <section aria-labelledby="res-h"><h2 id="res-h">Key results <small>read live from the running API</small></h2>
      <dl className="kpis">
        <div className="kpi"><dt>Fleet packs</dt><dd><span className="kpi-num">{fleet ? fleet.packs : "–"}</span></dd><dd className="kpi-detail">fictional, 3 sites, 24 months daily history</dd></div>
        <div className="kpi"><dt>Suggested for review</dt><dd><span className="kpi-num">{reviewPacks}</span><span className="kpi-unit">packs</span></dd><dd className="kpi-detail">{gapPacks} with passport evidence gaps at the 2027 milestone</dd></div>
        <div className="kpi"><dt>Guidance data points</dt><dd><span className="kpi-num">{pack ? pack.results.length : "–"}</span></dd><dd className="kpi-detail">evaluated per pack; BAT-DEMO-024: {pack?.coverage.missing_evidence ?? 0} missing, {pack?.coverage.invalid ?? 0} invalid</dd></div>
        <div className="kpi"><dt>Cell life error</dt><dd><span className="kpi-num">{best ? fmt(best.mae) : "–"}</span><span className="kpi-unit">cycles MAE</span></dd><dd className="kpi-detail">vs {life ? fmt(life.models.baseline.mae) : "–"} for the baseline, {life?.n_cells ?? 0} held-out cells</dd></div>
        <div className="kpi"><dt>Interval coverage</dt><dd><span className="kpi-num">{best ? `${Math.round(100 * best.interval_coverage)} %` : "–"}</span></dd><dd className="kpi-detail">of cells inside their 80 % interval</dd></div>
      </dl>
    </section>

    <section aria-labelledby="cont-h"><h2 id="cont-h">What the PoC contains</h2>
      <table className="summary-table"><thead><tr><th scope="col">Area</th><th scope="col">What it shows</th></tr></thead>
        <tbody>{CONTENTS.map(c => <tr key={c.name}><th scope="row"><Link href={c.href}>{c.name}</Link></th><td>{c.what}</td></tr>)}</tbody></table>
    </section>

    <section aria-labelledby="how-h" className="summary-grid">
      <div className="panel"><h2 id="how-h">How to use it</h2>
        <ol className="plain">
          <li><Link href="/fleet-health">Fleet health</Link>: start with the packs suggested for review and the reason given for each.</li>
          <li><Link href="/fleet/BAT-DEMO-024?as_of=2027-02-18">Passport inspector</Link>: open a pack, set the date (for example 18 Feb 2027) and read the gaps first; change the date to see requirements phase in.</li>
          <li><Link href="/assistant?id=BAT-DEMO-024&as_of=2027-02-18">Evidence assistant</Link>: ask what is missing; every answer cites the passages it retrieved.</li>
          <li>Download the investigation draft from the pack page and hand it to a specialist.</li>
          <li><Link href="/research">Cell research</Link>: compare the life models with the baseline and open any cell&apos;s curve.</li>
        </ol></div>
      <div className="panel"><h2>How to read the results</h2>
        <dl className="summary-dl">
          <div><dt>Present</dt><dd>Evidence on file and valid.</dd></div>
          <div><dt>Missing evidence</dt><dd>Required at the chosen date, nothing on file. A task to close, not a finding of non-compliance.</dd></div>
          <div><dt>Invalid</dt><dd>Evidence on file fails a check, such as format or date.</dd></div>
          <div><dt>Not yet effective</dt><dd>Required only after the chosen date.</dd></div>
          <div><dt>Not applicable</dt><dd>Does not apply to this battery category.</dd></div>
          <div><dt>Unknown</dt><dd>Restricted-access or design-dependent; the system never fills it in.</dd></div>
          <div><dt>Source labels</dt><dd>Synthetic (simulated fleet), measured public (lab cells), derived (computed by a model), reference document (regulation or guidance).</dd></div>
          <div><dt>Hatched areas</dt><dd>Extrapolated beyond measured data, or unknown: a hint, not a measurement.</dd></div>
          <div><dt>Suggested for review</dt><dd>Demo thresholds that rank attention; not safety, warranty or end-of-life limits.</dd></div>
          <div><dt>80 % interval</dt><dd>About 8 in 10 measured cells fall inside overall; fewer in some batches.</dd></div>
        </dl></div>
    </section>

    <section aria-labelledby="src-h" className="summary-grid">
      <div className="panel"><h2 id="src-h">Data and evidence</h2>
        <ul className="plain">
          <li><b>Commission guidance v3.2</b> (19 Oct 2026, CC BY 4.0, non-binding): 71 data points parsed from the checksum-pinned PDF.</li>
          <li><b>Regulation (EU) 2023/1542</b>: Article 77 and selected excerpts from EUR-Lex.</li>
          <li><b>HUST LFP cells</b> (Ma et al. 2022, CC BY 4.0): 77 cells for calibration and the life model.</li>
          <li><b>Aalborg forklift-profile LFP cells</b> (Vilsen &amp; Stroe 2024, CC BY 4.0): fade per cycle and temperature.</li>
          <li><b>CALCE CS2</b>: legacy research baseline.</li>
        </ul></div>
      <div className="panel"><h2>Limitations</h2>
        <ul className="plain">
          <li>Calibration rests on few cells; most simulated days lie outside the measured temperature range and are labelled extrapolated.</li>
          <li>Restricted-access and design-dependent passport data points are unresolved, never filled with invented evidence.</li>
          <li>The life model covers one cell type from one laboratory; the voltage feature adds no skill.</li>
          <li>Localhost only: no authentication or access control yet.</li>
        </ul></div>
    </section>

    <section aria-labelledby="next-h"><h2 id="next-h">Open points and next actions</h2>
      <table className="summary-table"><thead><tr><th scope="col">Item</th><th scope="col">Detail</th><th scope="col">Status</th></tr></thead>
        <tbody>{NEXT.map(n => <tr key={n.item}><th scope="row">{n.item}</th><td>{n.detail}</td><td><span className="badge">{n.state}</span></td></tr>)}</tbody></table>
      {contact.name && <div className="panel contact" aria-labelledby="contact-h">
        <h2 id="contact-h">Contact</h2>
        <p><b>{contact.name}</b>{contact.email && <> · <a href={"mailto:" + contact.email}>{contact.email}</a></>}{contact.phone && <> · <a href={"tel:" + contact.phone.replace(/\s/g, "")}>{contact.phone}</a></>}</p>
      </div>}
    </section>
  </div>;
}
