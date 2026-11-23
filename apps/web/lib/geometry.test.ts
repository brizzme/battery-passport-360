import {describe, expect, it} from "vitest";
import {bandCounts, idleSpans, linearScale, niceTicks, packLabel, proportionalWidths, tileFill} from "./geometry";

describe("linearScale", () => {
  it("maps domain to range", () => expect(linearScale([0, 100], [200, 0])(25)).toBe(150));
});
describe("niceTicks", () => {
  it("steps by a round number", () => expect(niceTicks(0, 2000, 5)).toEqual([0, 500, 1000, 1500, 2000]));
  it("covers odd maxima", () => expect(niceTicks(0, 1942, 5).at(-1)).toBeGreaterThanOrEqual(1942));
});
describe("tileFill", () => {
  it("unknown capacity is empty and hatched", () => expect(tileFill(null)).toEqual({fill: 0, hatched: true}));
  it("full capacity fills the budget", () => expect(tileFill(100)).toEqual({fill: 1, hatched: false}));
  it("60 % is the empty end of the budget", () => expect(tileFill(60).fill).toBe(0));
  it("below 80 % is hatched as extrapolated", () => expect(tileFill(70)).toEqual({fill: 0.25, hatched: true}));
  it("clamps above 100", () => expect(tileFill(101).fill).toBe(1));
});
describe("proportionalWidths", () => {
  it("sums to 100", () => expect(proportionalWidths([20, 50, 30], 100)).toEqual([20, 50, 30]));
  it("handles zero total", () => expect(proportionalWidths([0, 0], 0)).toEqual([50, 50]));
});
describe("idleSpans", () => {
  const d = (day: string, efc: number) => ({day, efc});
  it("finds a multi-day idle run", () =>
    expect(idleSpans([d("2026-01-01", 0), d("2026-01-02", 0), d("2026-01-03", 0), d("2026-01-04", 1)]))
      .toEqual([{start: "2026-01-01", end: "2026-01-03", days: 3}]));
  it("ignores single idle days", () => expect(idleSpans([d("2026-01-01", 1), d("2026-01-02", 0), d("2026-01-03", 1)])).toEqual([]));
  it("closes a run at the end", () => expect(idleSpans([d("2026-01-01", 0), d("2026-01-02", 0)])[0].days).toBe(2));
});
describe("bandCounts", () => {
  it("orders bands and computes shares", () => {
    const r = bandCounts({"unknown": 20, "below 80": 4, "80-90": 11, "90-95": 19, "95-100": 46});
    expect(r.map(b => b.key)).toEqual(["95-100", "90-95", "80-90", "below 80", "unknown"]);
    expect(r[0].share).toBeCloseTo(0.46);
  });
});
describe("packLabel", () => {
  it("describes an extrapolated pack under review", () =>
    expect(packLabel({battery_id: "BAT-DEMO-007", site_id: "SITE-HOT", chemistry: "LFP", capacity_pct: 60, efc: 1942, review_rules: ["capacity_below_80"]}))
      .toBe("BAT-DEMO-007, Hot dock, capacity 60.0 %, extrapolated, suggested for review"));
  it("describes a lead-acid pack", () =>
    expect(packLabel({battery_id: "BAT-DEMO-005", site_id: "SITE-COLD", chemistry: "lead-acid", capacity_pct: null, efc: 869, review_rules: []}))
      .toBe("BAT-DEMO-005, Cold store, capacity unknown (lead-acid)"));
});
