# Fleet Health Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the plain workspace with an Ulm-signage fleet health dashboard at `/`, a shared shell on every route, and a charted health section on `/fleet/[id]`.

**Architecture:** One API addition (per-pack list + regime share on `FleetHealth`). Web: tokens and shell in `layout.tsx`/`globals.css`; pure geometry helpers in `apps/web/lib/` unit-tested with Vitest; server-rendered SVG chart components in `apps/web/components/`; one small client `Tooltip` layer.

**Tech Stack:** FastAPI/Pydantic, Next.js 16 App Router, React 19, TypeScript, Vitest 3.2.7, `@fontsource/barlow` 5.3.0 and `@fontsource/barlow-condensed` 5.3.0.

**Spec:** [docs/superpowers/specs/2026-11-23-fleet-dashboard-design.md](../specs/2026-11-23-fleet-dashboard-design.md) and direction contract `.impeccable/surfaces/apps-web-app-page-tsx.md`. Read both.

## Global Constraints

- Tokens: `--ground #f2f3ef`, `--ink #1d2b33`, `--cold #2f7fc1`, `--ambient #3d9a4b`, `--hot #e8742a`, `--neutral #b9c0c2`; Barlow for UI, Barlow Condensed for numerals; square corners; 8px grid.
- Site display: `SITE-COLD` "Cold store" (snowflake pictogram), `SITE-AMB` "Ambient warehouse" (building), `SITE-HOT` "Hot dock" (sun).
- Hatch pattern (45°, ink at 35 %) = extrapolated, clamped or unknown. Review marker = ink corner triangle. No red for review.
- Every chart: legend for ≥ 2 series, site pictogram + label (never colour alone), units, a `<details>` "View as table", hover/focus tooltip.
- Visible label on every data surface: "Synthetic" plus calibration version where values are calibrated.
- Banned words anywhere in UI: compliant, certified, safe to operate, replace, approved, end of life reached.
- Responsive to 375 px with no horizontal page scroll; keyboard-focusable tiles/dots with accessible names.
- No chart library; no runtime font fetch.
- Commit per task with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; branch `feat/fleet-dashboard`.

## Review Focus

1. Pack with `capacity_pct: null` (lead-acid) → tile is neutral + hatch, scatter omits it, accessible name says "capacity unknown". (Task 3, 4)
2. Fleet API unavailable → dashboard renders an error state with retry, not a crash. (Task 4)
3. Pack with no history for the window or no events → charts show an empty state sentence, not a blank SVG. (Task 5)
4. 375 px width → KPI strip 2-up, floor columns stacked, no horizontal scroll. (Task 4/6 screenshots)
5. Very long reason lists (pack with 4 flags) → wraps without overlapping the capacity column. (Task 4)

---

### Task 1: API — per-pack list and regime share

**Files:** Modify `apps/api/app/health.py` (`FleetHealth`, `fleet_summary`), `apps/api/app/fleet_health.py` (`load_fleet` returns regime counts), `apps/api/tests/test_routes_health.py`, `scripts/check-demo.sh`.

**Interfaces:**
- `class PackPoint(BaseModel): battery_id: str; site_id: str | None; chemistry: str; capacity_pct: float | None; efc: float | None; review_rules: list[str]`
- `FleetHealth.packs: list[PackPoint]`, `FleetHealth.regime_share: dict[str, float]` (keys: calibrated, extrapolated_below_calibrated_range, clamped_low, clamped_high; fractions of LFP pack-days ≤ as_of; sum 1.0 or all 0).
- `fleet_summary(summaries, flags, as_of, regime_days: dict[str, int] | None = None) -> FleetHealth`

- [ ] Test: `fleet_summary` with LFP + lead-acid summaries → `packs` has both, lead-acid `capacity_pct is None`, `review_rules` lists rule ids per pack; `regime_share` from `{"calibrated": 1, "clamped_low": 3}` → `{calibrated: .25, clamped_low: .75, others 0}`; empty → all 0.
- [ ] Run → FAIL; implement (`load_fleet` adds `SELECT temp_regime, count(*) FROM pack_daily JOIN pack_profiles … WHERE chemistry='LFP' AND day <= %s GROUP BY 1`); run → PASS.
- [ ] `check-demo.sh`: `len(fleet["packs"]) == 100` and `abs(sum(fleet["regime_share"].values()) - 1) < 1e-6`.
- [ ] Commit `feat(api): per-pack points and regime share on fleet health`.

### Task 2: Shell, tokens, fonts, test runner

**Files:** Modify `apps/web/package.json` (+ `@fontsource/barlow@5.3.0`, `@fontsource/barlow-condensed@5.3.0`, dev `vitest@3.2.7`; script `"test": "vitest run"`), `apps/web/app/layout.tsx` (imports weights 400/500/600 + condensed 500/600; `<Shell>`), `apps/web/app/globals.css` (rewrite to tokens), Create `apps/web/components/Shell.tsx` (skip link, ink bar, wordmark, nav with `aria-current`, synthetic label), `apps/web/components/Pictogram.tsx` (`site: "SITE-COLD"|"SITE-AMB"|"SITE-HOT"`, 16px SVG, `aria-hidden`), `apps/web/lib/sites.ts` (`SITES` record: label, colour var, pictogram). Modify `fleet/page.tsx`, `fleet/[id]/page.tsx`, `research/page.tsx`, `assistant/page.tsx`, `fleet/error.tsx`, `fleet/loading.tsx` to drop their own "← Workspace" heroes for page headings inside the shell.

- [ ] `npm i` pinned; `npm run lint && npm run typecheck && npm run build` pass.
- [ ] Screenshot `/fleet`, `/research`, `/assistant` at 1440 and 375: shell present, no horizontal scroll.
- [ ] Commit `feat(web): Ulm shell, tokens and fonts`.

### Task 3: Geometry helpers (pure, Vitest)

**Files:** Create `apps/web/lib/geometry.ts`, `apps/web/lib/geometry.test.ts`, `apps/web/vitest.config.ts` (node env, include `lib/**/*.test.ts`).

**Interfaces:**
- `linearScale(domain: [number, number], range: [number, number]): (v: number) => number`
- `niceTicks(min: number, max: number, count: number): number[]`
- `tileFill(capacityPct: number | null): {fill: number; hatched: boolean}` — fill = clamp((cap-60)/40,0,1) mapping 60 %→0, 100 %→1 (fixed budget, 60 % = model floor); hatched when cap is null or < 80.
- `proportionalWidths(counts: number[], total: number): number[]` (percentages summing to 100).
- `idleSpans(days: {day: string; efc: number}[], minDays = 2): {start: string; end: string; days: number}[]`
- `bandCounts(bands: Record<string, number>): {key: string; count: number; share: number}[]` in order 95-100, 90-95, 80-90, below 80, unknown.
- `packLabel(p: PackPoint): string` → e.g. "BAT-DEMO-007, Hot dock, capacity 60.0 %, extrapolated, suggested for review" / "… capacity unknown (lead-acid)".

- [ ] Tests first for each (e.g. `tileFill(null)` → `{fill:0,hatched:true}`; `tileFill(100)` → `{fill:1,hatched:false}`; `tileFill(70)` hatched; `proportionalWidths([20,50,30],100)` → `[20,50,30]`; `idleSpans` with 3 zero days then 1 active → one span of 3 days; single zero day ignored; `niceTicks(0,2000,5)` → `[0,500,1000,1500,2000]`).
- [ ] `npm test` → FAIL; implement; → PASS. Commit `feat(web): chart geometry helpers`.

### Task 4: Dashboard at `/`

**Files:** Rewrite `apps/web/app/page.tsx`; Create `apps/web/components/{KpiStrip,ReviewTable,FleetFloor,BandBar,CapacityScatter,RegimeStrip,ProvenancePanel,Tooltip}.tsx` (`Tooltip` is `"use client"`: hover/focus on `[data-tip]` elements shows a positioned box; content from `data-tip`), `apps/web/app/error.tsx`, `apps/web/app/loading.tsx`; types in `apps/web/lib/api.ts` (move `read` + types from `fleet/api.ts`, re-export there).

- Data: one fetch `/api/fleet/health-summary`; calibration/seed versions from `/api/batteries/BAT-DEMO-024/health-summary` meta (generator/calibration version) — or include in Task 1 response if simpler (builder's call; ledger it).
- KPI strip: packs, packs suggested for review (distinct ids), below 80 %, events 30 d with breakdown, cumulative EFC; numerals Barlow Condensed ≥ 40px, never clipped.
- ReviewTable: one row per pack, reasons joined in order capacity_below_80, over_temperature_30d, fade_rate_p90, passport_gaps_at_milestone; first 7 rows + "Show all N" (`<details>`); note "Demo thresholds — not safety, warranty or end-of-life limits. Qualified specialists decide."
- FleetFloor: three site columns, tab widths from `proportionalWidths`, tiles as `<a href="/fleet/{id}" aria-label={packLabel}>` with fill height from `tileFill`, hatch overlay, review corner; legend.
- CapacityScatter: x = cumulative EFC, y = capacity %, LFP only, dot colour + shape per site, hatched band below 80 %, y axis 60–100 %, `niceTicks` x; tooltip per dot; table view.
- RegimeStrip: four segments from `regime_share`, hatched for extrapolated/clamped, labels with %.
- ProvenancePanel: HUST (77 cells, CC BY 4.0), Aalborg (3 cells, CC BY 4.0), calibration version, links to docs/DATA_SOURCES.md and LIMITATIONS.md on GitHub-relative paths, footer links API reference and health JSON.
- [ ] Build; screenshot 1440/768/375; check Review Focus 1, 2 (stop API container briefly → error state), 4, 5.
- [ ] Commit `feat(web): fleet health dashboard`.

### Task 5: Pack page health section

**Files:** Modify `apps/web/app/fleet/[id]/page.tsx`; Create `apps/web/components/{PackFurniture,CapacityHistory,Histogram,EventTimeline}.tsx`.

- Fetch `/api/batteries/{id}/history` (365 days) besides the existing inspection.
- PackFurniture: ID, site (pictogram), chemistry, rated kWh, commissioned, provenance line.
- CapacityHistory: daily line 2px, y 60–100 %, hatched region below 80 %, lead-acid → empty-state sentence "No calibrated capacity for lead-acid packs."
- Histogram: temperature (°C bins) and SoC (% bins), hours per bin, bars with 2px gaps.
- EventTimeline: 365-day axis; idle spans from `idleSpans` as bars of exact day length; events as 1-day marks by kind (shape + label legend); empty → "No events recorded in this period."
- Passport evidence section restyled (content unchanged); indicator list keeps all labels.
- [ ] Build; screenshots for BAT-DEMO-007, -005, -042, -024 at 1440/375; Review Focus 3.
- [ ] Commit `feat(web): charted pack health`.

### Task 6: Quality gates, docs

- [ ] `node <dataviz>/scripts/validate_palette.js "#2f7fc1,#3d9a4b,#e8742a" --mode light` → no FAIL (fix shades if it fails; ledger).
- [ ] `impeccable detect --json apps/web/app apps/web/components` → fix mechanical findings.
- [ ] API pytest, web `npm test`, lint, typecheck, build; `docker compose up --build -d`; `check-demo.sh`.
- [ ] Capture `.impeccable/review/desktop.png` (1440 full page) and `mobile.png` (390).
- [ ] Spawn Impeccable finish reviewer; act on disposition; spawn documenter → DESIGN.md + `.impeccable/design.json`.
- [ ] Update README (dashboard), docs/ARCHITECTURE.md (web components), PLAN.md (part 2 + work log). Commit `docs: fleet dashboard`.
