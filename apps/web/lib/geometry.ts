import type {PackPoint} from "./types";
import {siteOf} from "./sites";

export function linearScale([d0, d1]: [number, number], [r0, r1]: [number, number]) {
  const k = d1 === d0 ? 0 : (r1 - r0) / (d1 - d0);
  return (v: number) => r0 + (v - d0) * k;
}

export function niceTicks(min: number, max: number, count: number): number[] {
  const raw = (max - min) / Math.max(1, count - 1);
  const mag = 10 ** Math.floor(Math.log10(raw || 1));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) ?? 10 * mag;
  const ticks: number[] = [];
  for (let v = Math.floor(min / step) * step; v < max + step; v += step) {
    ticks.push(+v.toFixed(10));
    if (v >= max) break;
  }
  return ticks;
}

/** Capacity drawn against a fixed budget: 60 % (model floor) is empty, 100 % is full. */
export function tileFill(capacityPct: number | null): {fill: number; hatched: boolean} {
  if (capacityPct === null) return {fill: 0, hatched: true};
  return {fill: Math.min(1, Math.max(0, (capacityPct - 60) / 40)), hatched: capacityPct < 80};
}

export function proportionalWidths(counts: number[], total: number): number[] {
  if (!total) return counts.map(() => 100 / counts.length);
  return counts.map(c => (100 * c) / total);
}

export function idleSpans(days: {day: string; efc: number}[], minDays = 2) {
  const spans: {start: string; end: string; days: number}[] = [];
  let run: {day: string}[] = [];
  const close = () => {
    if (run.length >= minDays) spans.push({start: run[0].day, end: run[run.length - 1].day, days: run.length});
    run = [];
  };
  for (const d of days) d.efc === 0 ? run.push(d) : close();
  close();
  return spans;
}

const BAND_ORDER = ["95-100", "90-95", "80-90", "below 80", "unknown"];
export function bandCounts(bands: Record<string, number>) {
  const total = BAND_ORDER.reduce((s, k) => s + (bands[k] ?? 0), 0);
  return BAND_ORDER.map(key => ({key, count: bands[key] ?? 0, share: total ? (bands[key] ?? 0) / total : 0}));
}

export function packLabel(p: PackPoint): string {
  const site = siteOf(p.site_id).label;
  if (p.capacity_pct === null) return `${p.battery_id}, ${site}, capacity unknown (${p.chemistry})`;
  const parts = [p.battery_id, site, `capacity ${p.capacity_pct.toFixed(1)} %`];
  if (p.capacity_pct < 80) parts.push("extrapolated");
  if (p.review_rules.length) parts.push("suggested for review");
  return parts.join(", ");
}
