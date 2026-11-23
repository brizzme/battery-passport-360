---
version: 1
slug: "apps-web-app-page-tsx"
primary_target: "apps/web/app/page.tsx"
related_targets: ["apps/web/app/fleet/[id]/page.tsx"]
---

# Fleet health dashboard

Scope: `/` (fleet health landing) plus the shared shell for all routes, and the health section of `/fleet/[id]`. Mode: Operate. Audience: technical reviewer (PRODUCT.md). Task: find the pack that needs specialist review, see why, trace every value to its source.

## Direction contract

THESIS: The fleet as a colour-coded signage system in the Ulm tradition: every site, state and source has one fixed colour, pictogram and position. Refuses the category default of a sidebar, four KPI cards and a generic line chart.

OWN-WORLD: Ground #f2f3ef, ink #1d2b33 (also the top bar), site colours cold store #2f7fc1, ambient #256b3a, hot dock #f0a030 (re-stepped after colour-blind validation), neutral #b9c0c2. Barlow for UI, Barlow Condensed for numerals. Strict 8px modular grid, square corners, rules only where a table or strip needs them. Geometric pictograms per site. Hatch = extrapolated, clamped or unknown. Dark corner marker = suggested for review.

STORY: The reviewer reads the KPI strip, sees which packs are suggested for review and why, sees where wear concentrates (hot dock) on the fleet floor, opens a pack, and finds every value labelled synthetic with its calibration basis.

FIRST VIEWPORT: Ink top bar with wordmark, four nav items and the "Synthetic fleet · calibrated · cut-off" label. KPI strip of five figures in Barlow Condensed. Left 40 %: review table. Right 60 %: fleet floor, three site columns with width-proportional site tabs, 100 tiles filled to capacity against a fixed budget, then the capacity-band bar. Below the fold: capacity vs cumulative cycles scatter, temperature-regime strip, provenance panel.

FORM: Ulm signage program; position 3 of 7 on the grounded list; seed:08a340f63df0a118. Raises: hatch for uncertainty (exposure record); site tabs proportional to pack count (acetate tab board); event and idle bars to exact day length (labanotation); capacity drawn against a fixed budget (J-card); fixed per-pack furniture (character catalog).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
