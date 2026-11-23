# Fleet health dashboard — design (expansion part 2)

**Date:** 2026-11-23 · **Status:** draft for approval · Visual direction: `.impeccable/surfaces/apps-web-app-page-tsx.md` (Ulm signage program, chosen by the user) · Product context: `PRODUCT.md`

## Intent
Turn the plain-text prototype into a dashboard a technical reviewer understands in about a minute: which packs need specialist review and why, where wear concentrates, and where every number comes from. Data comes from the part 1 API (calibrated synthetic fleet).

## Approaches
| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | Triage first | Clear next action; method hidden | Combined |
| B | Fleet floor by site | Shows the temperature story; no method | Combined |
| **A+B+C** | Triage landing, fleet floor beside it, analyst charts below | Longer page, but serves operator question and reviewer's method check | **Chosen by user** |
| — | Charting library (Recharts etc.) | Faster charts; heavier, harder to style to the world | Rejected: hand-built SVG is small, server-rendered and on-style |

## Goals
1. `/` becomes the fleet health dashboard; the old link list goes. Shared shell (ink top bar, nav: Fleet health, Passport inspector, Cell research, Evidence assistant, synthetic label) on every route via `layout.tsx`.
2. First viewport as in the direction contract: KPI strip; review table; fleet floor (100 tiles, capacity fill against a fixed budget, hatch for extrapolated or unknown, corner marker for review, site tabs proportional to pack count); capacity-band bar.
3. Below the fold: capacity vs cumulative EFC scatter (one dot per LFP pack, coloured by site, hatched zone below 80 %); temperature-regime strip (calibrated, extrapolated, clamped low, clamped high, share of pack-days); provenance panel (HUST, Aalborg, calibration version, seed digest, generator assumptions link to docs).
4. Pack page `/fleet/[id]`: health section rebuilt as fixed furniture (ID, site, chemistry, commissioned, provenance), a capacity history line (daily, 365 days to cut-off, hatched below 80 %), temperature and SoC histograms (hours per bin), and an event timeline where bars are drawn to exact day length. Passport evidence section restyled in the same world, content unchanged.
5. Every chart: hover tooltip (small client component), a visible legend for 2+ series, identity never by colour alone (site pictogram + label), units on every value, a "View as table" disclosure.

## Non-goals
- Rule refresh (part 3), research model (part 4), evidence assistant changes.
- Dark mode (scene: reviewer at a desk in daylight; light only).
- New data or claims; no live telemetry.

## Anti-goals
- Synthetic values without the synthetic label; extrapolated values without hatch or label.
- Any certifying wording; review flags styled as alarms (no red sirens; review marker is ink, not red).
- Decorative charts with invented numbers.

## API change (small)
`FleetHealth` gains `packs: [{battery_id, site_id, chemistry, capacity_pct|null, efc, review_rules[]}]` and `regime_share: {calibrated, extrapolated_below_calibrated_range, clamped_low, clamped_high}` so the dashboard needs one request. Tested like part 1 (pure function + route test).

## Constraints
- Next.js 16 App Router, server components fetch the API; charts are server-rendered SVG with a small client layer for tooltips. No chart library. Barlow via pinned `@fontsource` packages (no runtime font fetch).
- Responsive to 375 px: KPI strip wraps 2-up, review table becomes a list, fleet floor columns stack with tabs on top.
- Keyboard: tiles and dots are links to the pack page with accessible names ("BAT-DEMO-007, hot dock, capacity 60.0 %, extrapolated, suggested for review").
- Fix from the sketch: KPI numerals must not be clipped by the strip rule.

## Verification
API pytest; web lint, typecheck, build; `check-demo.sh` extended for the new fields; Playwright screenshots at 375 / 768 / 1440; `impeccable detect`; dataviz palette validator on the site colours; Impeccable finish reviewer; DESIGN.md written by the documenter at the end.

## Calls made after the builder check (review these)
1. **No HUST curve on the scatter.** The HUST curve is cell life to 80 %, not pack EFC; rescaling it would be an invented overlay. The scatter shows packs only (site colour + pictogram), with the < 80 % zone hatched and a note linking to the calibration source.
2. **Timeline bars come from daily history**, not a new field: idle spans = runs of ≥ 2 days with zero EFC, drawn to exact length; events are one-day marks by kind. Uses the existing `/history` (extended with `efc`, already present) and health-summary events.
3. **`regime_share`** = fraction of LFP pack-days per temperature regime, all history up to `as_of` (matches the per-pack labels); lead-acid excluded because its fade is not calibrated.
4. **Shell and tokens apply to every route**; other pages keep their content and get the new styling (one product). Nav: Passport inspector → `/fleet` (the register is the inspector's entry), Evidence assistant → `/assistant?id=BAT-DEMO-024&as_of=2027-02-18` default; Cell research → `/research`.
5. **Review table: one row per pack**, reasons joined; order of reasons: capacity below 80 %, over-temperature, fade above P90, passport gaps. The KPI counts packs.
6. **Old landing content** (service health, API reference, health JSON links) moves to a small footer on the dashboard.

## Left to the builder
Exact type scale steps, tile size per breakpoint, tooltip positioning, scatter axis ticks, histogram bin labels.
