import Link from "next/link";
import type {PackPoint} from "@/lib/types";
import {SITE_ORDER, SITES} from "@/lib/sites";
import {packLabel, tileFill} from "@/lib/geometry";
import {Pictogram} from "./Pictogram";

/** Signature: every pack as a tile filled to capacity against a fixed 60–100 % budget, grouped by site. */
export function FleetFloor({points}: {points: PackPoint[]}) {
  const groups = SITE_ORDER.map(id => ({id, site: SITES[id], packs: points.filter(p => p.site_id === id)}));
  return <section aria-labelledby="floor-h" className="floor">
    <h2 id="floor-h">Fleet floor <small>capacity as fill · 60 % empty to 100 % full</small></h2>
    <div className="floor-grid" style={{gridTemplateColumns: groups.map(g => `minmax(150px, ${Math.max(g.packs.length, 1)}fr)`).join(" ")}}>
      {groups.map(g => <div key={g.id} className="floor-col">
        <h3 className="site-tab" style={{background: g.site.color}}><Pictogram site={g.id}/>{g.site.label}<span>{g.packs.length}</span></h3>
        <ul className="tiles">{g.packs.map(p => {
          const {fill, hatched} = tileFill(p.capacity_pct);
          const label = packLabel(p);
          return <li key={p.battery_id}>
            <Link href={`/fleet/${p.battery_id}?as_of=2027-02-18`} aria-label={label} data-tip={label}
              className={"tile" + (p.capacity_pct === null ? " unknown" : "") + (p.review_rules.length ? " review" : "")}>
              <span className="tile-fill" style={{height: `${fill * 100}%`, background: g.site.color}}/>
              {hatched && <span className="tile-hatch"/>}
            </Link>
          </li>;
        })}</ul>
      </div>)}
    </div>
    <ul className="legend" aria-label="Fleet floor legend">
      {SITE_ORDER.map(id => <li key={id}><span className="swatch" style={{background: SITES[id].color}}/>{SITES[id].label}</li>)}
      <li><span className="swatch hatch"/>Hatch: extrapolated below 80 % or unknown (lead-acid)</li>
      <li><span className="swatch corner"/>Suggested for specialist review</li>
    </ul>
  </section>;
}
