import type {HistoryPoint} from "@/lib/types";
import {idleSpans, linearScale} from "@/lib/geometry";

const W = 1200, H = 112, M = {l: 190, r: 12};
const KINDS = [
  {key: "over_temperature", label: "Over-temperature"},
  {key: "deep_discharge", label: "Deep discharge"},
  {key: "bms_comm_loss", label: "BMS communication loss"},
];
const dayIndex = (from: string, day: string) => Math.round((Date.parse(day) - Date.parse(from)) / 864e5);

/** Lanes on one day scale: idle spans drawn to exact length, events as one-day marks. */
export function EventTimeline({points, events}: {points: HistoryPoint[]; events: {observed_at: string; kind: string; detail: string}[]}) {
  if (!points.length) return <p className="empty">No history in this period.</p>;
  const from = points[0].day, to = points.at(-1)!.day, span = dayIndex(from, to) + 1;
  const x = linearScale([0, span], [M.l, W - M.r]), dw = (W - M.l - M.r) / span;
  const inRange = events.filter(e => e.observed_at.slice(0, 10) >= from && e.observed_at.slice(0, 10) <= to);
  const idle = idleSpans(points);
  const lanes = [{key: "idle", label: "Idle (no cycles)"}, ...KINDS];
  const lane = (k: string) => 12 + lanes.findIndex(l => l.key === k) * 24;
  return <div className="chart-scroll">
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${idle.length} idle spans and ${inRange.length} events between ${from} and ${to}`}>
      {lanes.map(l => <g key={l.key}><text x={0} y={lane(l.key) + 12} className="axis">{l.label}</text><line x1={M.l} x2={W - M.r} y1={lane(l.key) + 16} y2={lane(l.key) + 16} className="grid"/></g>)}
      {idle.map(s => <rect key={s.start} x={x(dayIndex(from, s.start))} y={lane("idle") + 4} width={Math.max(dw, s.days * dw)} height={12} fill="var(--ink-2)" data-tip={`Idle ${s.start} to ${s.end}: ${s.days} days`}/>)}
      {inRange.map(e => <rect key={e.observed_at + e.kind} x={x(dayIndex(from, e.observed_at.slice(0, 10)))} y={lane(e.kind) + 4} width={Math.max(2, dw)} height={12} fill="var(--ink)" data-tip={`${e.observed_at.slice(0, 10)}: ${e.detail}`}/>)}
    </svg>
    {!inRange.length && !idle.length && <p className="empty">No idle spans or events recorded in this period.</p>}
  </div>;
}
