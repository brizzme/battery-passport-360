import Link from "next/link";
import {notFound} from "next/navigation";
import {Inspection, dateChoice, preset, read} from "../api";
import type {History} from "@/lib/types";
import {regimeLabel, siteOf} from "@/lib/sites";
import {Pictogram} from "@/components/Pictogram";
import {CapacityHistory} from "@/components/CapacityHistory";
import {Histogram} from "@/components/Histogram";
import {EventTimeline} from "@/components/EventTimeline";
import {Tooltip} from "@/components/Tooltip";
import {PassportCoverage} from "@/components/PassportCoverage";

type Ind = {key: string; status: string; value: number | string | null; unit: string | null; reason: string | null};
const num = (v: number) => v.toLocaleString("en", {maximumFractionDigits: Math.abs(v) >= 100 ? 0 : 1});
function show(i: Ind, floored: boolean) {
  if (i.status !== "value") return i.status.replaceAll("_", " ");
  if (floored && i.key === "capacity_fade_pct") return `≥ ${num(Number(i.value))} % (model floor)`;
  if (floored && i.key === "fade_rate_90d_pct") return "not measurable at model floor";
  if (i.key === "resistance_increase_pct") return `+${num(Number(i.value))} % vs initial`;
  const v = typeof i.value === "number" ? num(i.value) : String(i.value);
  return `${v}${i.unit ? " " + i.unit : ""}`;
}

export default async function Detail({params, searchParams}: {params: Promise<{id: string}>; searchParams: Promise<{as_of?: string}>}) {
  const {id} = await params;
  const day = dateChoice((await searchParams).as_of);
  const enc = encodeURIComponent(id), path = "/fleet/" + enc;
  const data = await read<Inspection>("/api/batteries/" + enc + "/passport-readiness" + (day ? "?as_of=" + day : ""));
  if (!data) notFound();
  const history = await read<History>("/api/batteries/" + enc + "/history");
  const {battery: b, health} = data;
  const site = siteOf(health?.site_id);
  const passportFields = health?.indicators.filter(i => i.passport_field) ?? [];
  const operational = health?.indicators.filter(i => !i.passport_field) ?? [];
  const fade = health?.indicators.find(i => i.key === "capacity_fade_pct");
  const floored = fade?.status === "value" && Number(fade.value) >= 39.99;
  return <div className="desk pack">
    <div className="page-head"><p className="crumb"><Link href="/fleet-health">Fleet health</Link> / <Link href="/fleet">Passport inspector</Link></p>
      <h1>{b.battery_id}</h1></div>

    <dl className="furniture">
      <div><dt>Site</dt><dd><span style={{color: site.color}}><Pictogram site={health?.site_id}/></span> {site.label}</dd></div>
      <div><dt>Chemistry</dt><dd>{b.chemistry}</dd></div>
      <div><dt>Rated energy</dt><dd>{b.rated_kwh} kWh</dd></div>
      <div><dt>Identity source</dt><dd>{b.source_id} · {b.observed_at.slice(0, 10)}</dd></div>
      <div><dt>History</dt><dd>{health ? `Synthetic, ${health.source_id}, cut-off ${health.data_cutoff}` : "none"}</dd></div>
      <div><dt>Calibration</dt><dd>{health?.chemistry === "LFP" ? `${health.calibration_version} (HUST + Aalborg LFP, CC BY 4.0)` : "None for this chemistry; operational values are generator assumptions"}</dd></div>
    </dl>

    {health ? <section aria-labelledby="health-h" className="pack-health">
      <h2 id="health-h">Synthetic pack health <small>values as of {health.as_of}</small></h2>
      <div className="pack-grid">
        <figure className="chart"><figcaption><h3>Capacity, last 365 days <small>% of initial · hatched below 80 % = extrapolated</small></h3></figcaption>
          {history ? <CapacityHistory points={history.points} color={site.color}/> : <p className="empty">History unavailable.</p>}</figure>
        <div className="indicators">
          <h3>Passport health fields <small>restricted access · provisional mapping</small></h3>
          <table><tbody>{passportFields.map(i => <tr key={i.key}>
            <th scope="row">{i.label}<small className="block">{i.passport_ref?.replace(" per Commission guidance v3.2 (non-binding)", "")}</small></th>
            <td className="num"><b>{show(i, floored)}</b>{i.status !== "value" && <small className="block">{i.reason}</small>}{i.labels.length > 0 && <small className="block">{i.labels.map(regimeLabel).join(" · ")}</small>}</td>
          </tr>)}</tbody></table>
          {health.not_applicable.map(i => <p key={i.key} className="note">{i.label}: not applicable. {i.reason}</p>)}
        </div>
      </div>
      <div className="pack-grid three">
        <Histogram title="Temperature exposure" unit="°C" bins={health.temperature_histogram} color={site.color}/>
        <Histogram title="State of charge" unit="% SoC" bins={health.soc_histogram} color="var(--ink-2)"/>
        <div className="indicators"><h3>Operational indicators <small>not passport fields</small></h3>
          <table><tbody>{operational.map(i => <tr key={i.key}><th scope="row">{i.label}</th><td className="num">{show(i, floored)}</td></tr>)}</tbody></table></div>
      </div>
      <figure className="chart"><figcaption><h3>Idle spans and events, last 365 days <small>bars drawn to exact day length</small></h3></figcaption>
        {history ? <EventTimeline points={history.points} events={health.events}/> : <p className="empty">History unavailable.</p>}</figure>
      <p className="meta">Every value on this page is simulated. Basis per field: {[...new Set(health.indicators.flatMap(i => i.calibration_refs))].join(", ")}. A qualified specialist decides any action.</p>
    </section> : <p className="empty">No synthetic pack history available.</p>}

    <section aria-labelledby="passport-h">
      <h2 id="passport-h">Passport evidence</h2>
      <p>{data.scenario} Illustrative data readiness against every data point in the Commission guidance; missing evidence calls for review, not a finding.</p>
      <form className="filters"><label>Assessment date<input type="date" name="as_of" defaultValue={data.as_of} required/></label><button>Apply date</button><Link href={path}>Today</Link><Link href={path + "?as_of=" + preset}>18 Feb 2027 preset</Link></form>
      <PassportCoverage results={data.results} coverage={data.coverage}/>
      <p><Link href={"/assistant?id=" + id + "&as_of=" + data.as_of}>Ask the evidence assistant</Link> · <a download href={"/api/draft?id=" + id + "&as_of=" + data.as_of}>Download draft summary</a></p>
    </section>
    <Tooltip/>
  </div>;
}
