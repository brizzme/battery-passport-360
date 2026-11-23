import {read} from "./fleet/api";
import type {FleetHealth} from "@/lib/types";
import {KpiStrip} from "@/components/KpiStrip";
import {ReviewTable, reviewRows} from "@/components/ReviewTable";
import {FleetFloor} from "@/components/FleetFloor";
import {BandBar} from "@/components/BandBar";
import {CapacityScatter} from "@/components/CapacityScatter";
import {RegimeStrip} from "@/components/RegimeStrip";
import {ProvenancePanel} from "@/components/ProvenancePanel";
import {Tooltip} from "@/components/Tooltip";

export const dynamic = "force-dynamic";
const fmt = (n: number) => n.toLocaleString("en", {maximumFractionDigits: 0});

export default async function FleetHealthPage() {
  const data = await read<FleetHealth>("/api/fleet/health-summary");
  if (!data) throw Error("Fleet health unavailable");
  const ev = data.events_30d;
  const events = Object.values(ev).reduce((a, b) => a + b, 0);
  return <div className="dash">
    <div className="page-head compact"><h1>Fleet health</h1>
      <p>As of {data.as_of} · all simulated: LFP fade calibrated on public cell data, lead-acid values are generator assumptions</p></div>
    <KpiStrip items={[
      {label: "Packs", value: fmt(data.packs), detail: "fictional, 3 sites"},
      {label: "Suggested for review", value: String(reviewRows(data).length), unit: "packs", detail: `${data.review.length} reasons`},
      {label: "Below 80 % capacity", value: String(data.capacity_bands["below 80"] ?? 0), unit: "packs", detail: "extrapolated values"},
      {label: "Events, last 30 days", value: fmt(events), detail: `over-temperature ${ev.over_temperature ?? 0} · BMS comm loss ${ev.bms_comm_loss ?? 0} · deep discharge ${ev.deep_discharge ?? 0}`},
      {label: "Cumulative cycles", value: fmt(data.efc_total), unit: "EFC", detail: "equivalent full cycles, all packs"},
    ]}/>
    <div className="dash-main">
      <ReviewTable data={data}/>
      <div><FleetFloor points={data.pack_points}/><BandBar bands={data.capacity_bands}/></div>
    </div>
    <CapacityScatter points={data.pack_points}/>
    <div className="dash-pair">
      <RegimeStrip share={data.regime_share}/>
      <ProvenancePanel calibration={data.calibration_version ?? "unavailable"} generator={data.generator_version ?? "unavailable"} cutoff={data.data_cutoff}/>
    </div>
    <Tooltip/>
  </div>;
}
