---
name: Battery Passport 360
description: Independent prototype for industrial battery fleet health and passport evidence, drawn as an Ulm-style signage system.
colors:
  ground: "#f2f3ef"
  surface: "#ffffff"
  ink: "#1d2b33"
  ink-2: "#4a5961"
  rule: "#c9cec9"
  slate-mid: "#8a979c"
  cold: "#2f7fc1"
  ambient: "#256b3a"
  hot: "#f0a030"
  neutral: "#b9c0c2"
  focus: "#2f7fc1"
  nav-muted: "#cfd6d8"
  bar-rule: "#8fa0a6"
  ink-hover: "#33454f"
typography:
  display:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.15
  title:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.15
  body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "tnum"
  label:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    letterSpacing: "0.04em"
  meta:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
  numeral:
    fontFamily: "Barlow Condensed, Barlow, system-ui, sans-serif"
    fontSize: "3rem"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.01em"
  numeral-sm:
    fontFamily: "Barlow Condensed, Barlow, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1
rounded:
  none: "0px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "16px"
  s4: "24px"
  s5: "32px"
  s6: "48px"
  s7: "64px"
  gutter: "clamp(16px, 3vw, 32px)"
components:
  top-bar:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
    height: "56px"
    padding: "0 clamp(16px, 3vw, 32px)"
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
    rounded: "{rounded.none}"
    padding: "8px 12px"
  button-primary-hover:
    backgroundColor: "{colors.ink-hover}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "8px 12px"
  badge:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    padding: "1px 8px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.none}"
    padding: "24px"
  site-tab-cold:
    backgroundColor: "{colors.cold}"
    textColor: "{colors.surface}"
    padding: "10px 12px"
  site-tab-ambient:
    backgroundColor: "{colors.ambient}"
    textColor: "{colors.surface}"
    padding: "10px 12px"
  site-tab-hot:
    backgroundColor: "{colors.hot}"
    textColor: "{colors.ink}"
    padding: "10px 12px"
  tooltip:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.ground}"
    typography: "{typography.meta}"
    padding: "6px 10px"
  tile:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.none}"
    width: "minmax(30px, 1fr)"
---

# Design System: Battery Passport 360

## Overview

**Creative North Star: "The Ulm Signage Board"**

The fleet is read like a transit or factory signage program in the Ulm tradition: every site, state and source owns one fixed colour, one geometric pictogram and one position, and those assignments never move between views. The interface is a light ground with ink type and ink furniture; colour is spent almost entirely on the three sites, so a block of amber always means the hot dock and nothing else. Uncertainty has its own material: a diagonal ink hatch marks every extrapolated, clamped or unknown value, in tiles, bars and chart regions alike.

Density is operator-grade rather than marketing-grade. Figures sit in a ruled strip, tables carry the triage, and the signature fleet floor shows all hundred packs at once as tiles filled against a fixed budget. Charts are hand-built SVG on white plates with hairline grids, one shared tooltip, and an always-available "View as table" fallback. Corners are square everywhere, depth is flat, and rules appear only where a table, strip or furniture row needs them.

**Key Characteristics:**
- One fixed colour, pictogram and order per site: cold store, ambient warehouse, hot dock.
- Hatch is the single sign for extrapolated, clamped or unknown values.
- Barlow for the interface, Barlow Condensed for headline figures, tabular numerals throughout.
- Square corners, flat surfaces, 8px modular spacing.
- Hand-built SVG charts with a shared tooltip and a table fallback.

## Colors

A cool, near-neutral ink-and-paper ground carrying three saturated site colours that were re-stepped after colour-blind validation.

### Primary
- **Signal Ink** (ink): the top bar, all text, table header rules, primary buttons, the tooltip plate, the review corner marker, and the darkest capacity band. Ink is the structural colour of the system.

### Secondary (site colours)
- **Cold Store Blue** (cold): cold store tab, tiles, scatter circles and pack accents. Doubles as the focus ring colour (focus).
- **Ambient Green** (ambient): ambient warehouse tab, tiles and scatter squares.
- **Hot Dock Amber** (hot): hot dock tab, tiles and scatter triangles. Light enough that text on it must be ink, and its scatter mark carries an ink stroke instead of a white one.

### Neutral
- **Paper Ground** (ground): page background; also the "unknown" capacity band underlay.
- **Plate White** (surface): panels, chart plates, empty tiles, inputs.
- **Slate Text** (ink-2): secondary text, captions, axis labels, idle bars, the 90–95 % band and the state-of-charge histogram.
- **Slate Mid** (slate-mid): the 80–90 % capacity band and the extrapolated temperature regime; the mid step of the ink-to-rule grey ramp used by banded bars.
- **Hairline Grey** (rule): table row rules, chart grids, tile outlines, and the lightest band step.
- **Unassigned Grey** (neutral): packs with no site and tiles whose capacity is unknown.
- **Bar Text Grey** (nav-muted) and **Bar Rule Grey** (bar-rule): inactive nav items and the synthetic-label outline inside the ink top bar only.
- **Ink Hover** (ink-hover): primary button hover.

### Named Rules
**The One Site, One Colour Rule.** Cold, ambient and hot are reserved for their sites. No status, link, alert or decoration may borrow them; the only shared use is cold as the focus ring.

**The Grey Ramp Rule.** Banded quantities that are not sites (capacity bands, temperature regimes) step through ink, ink-2, slate-mid and rule, never through a new hue.

**The Never By Colour Alone Rule.** Every site colour travels with its pictogram or a distinct mark shape (circle, square, triangle) and a text label.

## Typography

**Display Font:** Barlow (with system-ui, sans-serif)
**Body Font:** Barlow (with system-ui, sans-serif)
**Label/Mono Font:** Barlow Condensed for figures (with Barlow, system-ui)

**Character:** A grotesque with DIN-like engineering roots for all prose and controls, and its condensed cut for the large figures, so numbers read like gauge readouts. Weights in use are 400, 500 and 600 only.

### Hierarchy
- **Display** (600, 2.5rem, 1.15, -0.02em; 2rem below 720px): the single page title per route.
- **Headline** (600, 1.5rem, 1.15): section titles such as the review table, fleet floor, charts and provenance panel. A trailing small qualifier in meta style (400) states count, unit or basis.
- **Title** (600, 1.125rem, 1.15): sub-sections, chart captions, the wordmark.
- **Body** (400, 0.9375rem, 1.5, tabular numerals): table cells, prose, controls. Paragraphs cap at 72ch.
- **Label** (600, 0.8125rem, 0.04em, uppercase): column headers of tables, KPI strip terms and pack-furniture terms only; it names a data field directly above its value.
- **Meta** (400, 0.8125rem, ink-2): captions, units, provenance lines, legend text, tooltip.
- **Numeral** (Barlow Condensed 600, 3rem, 1.05; 2.25rem below 720px): KPI figures. **Numeral-sm** (Condensed 600, 1.5rem, 1) for the pack count on site tabs.

### Named Rules
**The Unit Beside Every Number Rule.** Every figure carries its unit with a space ("74.3 %", "44 kWh", "1,942 EFC"); units in KPIs sit in ink-2 at body size beside the condensed figure.

**The Model Floor Rule.** Values at the model floor are never shown as exact: capacity reads "≤ 60.0 % (model floor)", fade reads "≥ 40 % (model floor)", a fade rate there reads "not measurable at model floor", and the capacity chart notes "At the 60 % model floor".

## Layout

Strict 8px modular rhythm (4px half step for tight gaps) with a fluid page gutter and a 1480px maximum content width. The landing route stacks: compact page head (title with inline meta line), a five-column KPI strip between two 2px ink rules, then a two-column main band (review table 1fr, fleet floor 1.4fr) with 48px gaps, a full-width scatter, and a 3fr/2fr pair of regime strip and provenance panel. The pack route opens with a six-column furniture row, then a 3fr/2fr chart-and-fields grid and a three-up grid of histograms and indicators.

Fleet floor columns are width-proportional to each site's pack count (minimum 150px), and tiles auto-fill at a 30px minimum with 4px gaps.

Responsive behaviour at two breakpoints: at 1100px the KPI strip drops to three columns, furniture to three, and every two- or three-column grid collapses to one. At 720px KPIs and furniture go to two columns, fleet floor columns stack, the review table becomes stacked rows (reason spanning full width), the nav becomes a single horizontally scrolling row with a right-edge fade cue, and wide SVG charts keep their native width inside a horizontal scroller that opens at the most recent or highest end, with a left-edge fade cue.

## Elevation & Depth

Flat. No drop shadows anywhere. Depth is conveyed by tone (white plates on the paper ground, the ink top bar) and by rules. The only shadows in the stylesheet are inset hairlines used as borders that do not disturb the grid: a 1px rule outline around tiles and swatches, a 2px ink outline on tile hover and focus, and a 1px ink top edge on tile fills.

### Named Rules
**The Flat Plate Rule.** Surfaces never lift. Hover and focus change outline weight or colour, not elevation.

## Shapes

Square corners throughout (0px), including buttons, inputs, tooltips, tiles and tabs. Lines are hairline (1px rule) for rows and grids, 2px ink for table heads and the KPI strip frame, and 3px for the active nav underline. The recurring geometry is the 16px pictogram grid with a 1.75px square-capped stroke, the three scatter marks (circle, square, triangle) and a 12px triangular corner wedge in ink marking packs suggested for specialist review.

## Components

### Buttons
Blunt and inky.
- **Shape:** square (0px).
- **Primary:** ink fill, ground text, weight 600, 8px 12px padding.
- **Hover / Focus:** fill steps to ink-hover; focus is the global 3px cold outline at 2px offset. Disabled at 50 % opacity.

### Inputs / Fields
- **Style:** 1px ink stroke, white fill, square, 8px 12px padding, inheriting the body font. Labels sit above in meta size, weight 500, inside a white filter bar.
- **Focus:** global 3px cold outline.

### Chips (badges)
- **Style:** ground fill, 1px ink stroke, label size and weight, lowercase status text ("not yet effective", "missing evidence").

### Cards / Containers
- **Corner Style:** square.
- **Background:** white plate on the paper ground.
- **Shadow Strategy:** none (see Elevation & Depth).
- **Border:** none; separation is tonal.
- **Internal Padding:** 24px.

### Navigation
Ink top bar, 56px minimum, with the battery wordmark, four text links and an outlined "Synthetic fleet · calibrated · cut-off" label pushed right. Inactive links in nav-muted, hover and active in ground, active marked by a 3px ground underline and `aria-current`. Below 720px the label wraps under the wordmark and links scroll horizontally.

### KPI Strip
Five definition-list cells between 2px ink rules, separated by hairline verticals: uppercase label, condensed figure with unit, meta detail line.

### Fleet Floor (signature)
Three site columns, each headed by a full-colour site tab (pictogram, label, condensed count) whose text must reach 4.5:1 on its fill: white on ambient (6.5:1), ink on hot (6.8:1). White on cold measures 4.26:1, which passes only for the 24px condensed count; the 15px cold label is a known contrast shortfall, not a precedent. Under it, one square tile per pack, filled from the bottom in the site colour against a fixed 60–100 % budget (60 % empty, 100 % full). Tiles below 80 % carry the hatch; unknown capacity is neutral grey with hatch; packs suggested for review get the ink corner wedge. Each tile is a link with a full text label and tooltip.

### Banded Bar
A 28px flex bar of segments sized to count or share with 2px gaps, using the grey ramp, hatched where values are extrapolated, clamped or unknown, followed by a legend of swatches with bold counts.

### Charts
Hand-built SVG on a white plate: hairline rule grids, 12px axis labels in ink-2, 12px weight-500 annotations in ink, site marks by shape, and a hatched region for the extrapolated range below 80 %. Every chart has a role="img" summary label and, where it plots records, a "View as table" disclosure.

### Tooltip
One shared tooltip for every element carrying `data-tip`: ink plate, ground text, meta size, 6px 10px padding, max 320px, centred 8px above the target. It follows hover and keyboard focus, and hides on Escape or scroll.

### Review Table
Pack id link, site pictogram plus short name, dotted-underlined reason items that open the tooltip on hover or focus, right-aligned capacity with an "extrapolated" sub-line. The first seven rows show; the rest sit behind a "Show all" disclosure. A ruled note closes it, ending "Qualified specialists decide."

## Do's and Don'ts

### Do:
- **Do** reach for the CSS custom properties in globals.css (--ink, --cold, --s3, --t-xs) for every new rule; components reference sites through `SITES[id].color`.
- **Do** keep site order cold, ambient, hot in every legend, column and table.
- **Do** mark every extrapolated, clamped or unknown value with the hatch (CSS `--hatch`, or the shared SVG `HatchDefs` pattern in charts) and say so in the legend.
- **Do** put ink text on hot amber and give the hot scatter mark an ink stroke; any text on a site fill must reach 4.5:1 (3:1 only at large sizes).
- **Do** pair each chart with a text summary and a table fallback, and open wide charts at their recent end on narrow screens.
- **Do** label figures at the model floor as bounds ("≤ 60.0 % (model floor)"), never as exact values.

### Don't:
- **Don't** use rounded corners, drop shadows or elevated cards.
- **Don't** use site colours for anything except their site (the cold focus ring is the one exception).
- **Don't** introduce a new hue for statuses or bands; use the grey ramp plus hatch.
- **Don't** show identity by colour alone; always pair with pictogram, mark shape or text.
- **Don't** use the hatch for anything other than extrapolated, clamped or unknown values.
- **Don't** add a sidebar, rows of KPI cards or generic gradient line charts; figures live in the ruled strip.
