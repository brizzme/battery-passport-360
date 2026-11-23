import type {Result} from "@/app/fleet/api";

const GROUPS = [
  {key: "gaps", label: "Gaps: missing or invalid evidence", statuses: ["missing_evidence", "invalid"], open: true, bg: "var(--ink)"},
  {key: "present", label: "Present", statuses: ["present"], open: false, bg: "var(--slate-mid)"},
  {key: "unknown", label: "Unresolved (not gaps)", statuses: ["unknown"], open: false, bg: "var(--neutral)", hatch: true},
  {key: "nye", label: "Not yet effective", statuses: ["not_yet_effective"], open: false, bg: "var(--rule)"},
  {key: "na", label: "Not applicable", statuses: ["not_applicable"], open: false, bg: "var(--surface)"},
];
const ACCESS: Record<string, string> = {public: "Public", restricted_legitimate_interest: "Restricted: legitimate interest", restricted_authorities: "Restricted: authorities"};

function Rows({rows}: {rows: Result[]}) {
  return <table className="dp-table"><thead><tr><th scope="col">Data point</th><th scope="col">Status</th><th scope="col">Reason</th><th scope="col">Evidence</th><th scope="col">Access</th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.rule_id}>
      <th scope="row"><span className="dp-id">{r.rule_id}</span> {r.label}<small className="block"><a href={r.source_url}>{r.guidance_ref}</a> · <a href={r.eurlex_url}>{r.section}</a></small></th>
      <td><span className="badge">{r.status.replaceAll("_", " ")}</span></td>
      <td>{r.reason}{r.effective_from && r.status === "not_yet_effective" ? <small className="block">From {r.effective_from}</small> : null}</td>
      <td>{r.evidence ? <>“{r.evidence.value_text}”{r.evidence.unit ? ` ${r.evidence.unit}` : ""}<small className="block">{r.evidence.evidence_ref ?? "no evidence reference"} · {r.evidence.source_id}</small></> : <small>none</small>}</td>
      <td><small>{ACCESS[r.access] ?? r.access}</small></td>
    </tr>)}</tbody></table>;
}

/** Coverage of every Commission guidance v3.2 data point for one pack, gaps first. */
export function PassportCoverage({results, coverage}: {results: Result[]; coverage: Record<string, number>}) {
  const groups = GROUPS.map(g => ({...g, rows: results.filter(r => g.statuses.includes(r.status))}));
  const total = results.length;
  return <div className="coverage">
    <div className="band-bar" role="img" aria-label={groups.map(g => `${g.label}: ${g.rows.length}`).join("; ")}>
      {groups.filter(g => g.rows.length).map(g => <span key={g.key} data-tip={`${g.label}: ${g.rows.length} of ${total}`}
        style={{flexGrow: g.rows.length, background: g.bg}} className={(g.hatch ? "hatched " : "") + (g.key === "na" ? "outlined" : "")}/>)}
    </div>
    <ul className="legend">{groups.map(g => <li key={g.key}><span className={"swatch" + (g.hatch ? " hatch" : "")} style={{background: g.bg}}/>{g.label}: <b>{g.rows.length}</b></li>)}</ul>
    <p className="meta">{total} data points from the Commission guidance (v3.2, non-binding). Missing: {coverage.missing_evidence ?? 0} · invalid: {coverage.invalid ?? 0}. Unresolved rows are not gaps.</p>
    {groups.filter(g => g.rows.length).map(g => <details key={g.key} open={g.open} className="dp-group">
      <summary>{g.label} <small>{g.rows.length}</small></summary><Rows rows={g.rows}/></details>)}
    {!groups[0].rows.length && <p className="empty">No missing or invalid evidence on this date.</p>}
  </div>;
}
