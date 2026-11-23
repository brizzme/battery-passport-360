# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Primary: a technical reviewer judging an independent Applied AI prototype for industrial batteries (for example a hiring panel at an industrial battery or intralogistics company). Within about a minute they need to see a credible operator product and the honest method behind it: where each number comes from, what is measured, what is simulated, what is extrapolated.

Personas the product is designed around (from SPEC.md): fleet manager (which packs need investigation), service engineer (which evidence and diagnostics to check), battery specialist (what evidence supports a lifecycle assessment).

## Product Purpose
Battery Passport 360 shows, for a fictional fleet of industrial forklift battery packs: EU battery-passport data readiness (Regulation (EU) 2023/1542), synthetic pack health calibrated on public LFP measurements, measured public cell research, an evidence assistant with cited passages, and a draft investigation summary. Success: a reviewer finds the pack that needs attention, understands why, and can trace every value to its source.

## Positioning
Every number carries its provenance (synthetic, measured public, derived, reference document), its calibration source and its uncertainty labels (extrapolated, clamped, unknown). The product never certifies compliance, safety or end of life; it suggests what a specialist should review.

## Operating Context
Local Docker Compose stack (Next.js web, FastAPI API, PostgreSQL/pgvector). Reviewers open it in a desktop browser, sometimes on a phone. Data cut-off for fleet history is 2026-10-31; the passport milestone preset is 2027-02-18.

## Capabilities and Constraints
- 100 fictional packs (80 LFP, 20 lead-acid), 3 fictional sites, 24 months of daily synthetic history; planted cases BAT-DEMO-007, -013, -024, -042.
- API: fleet health summary with review flags, per-pack health summary and daily history, passport readiness, CALCE research report, evidence assistant, Markdown draft.
- Labels required on every displayed fact: source type, source ID, timestamp, interpretation. Synthetic data must be labelled synthetic in UI, charts and exports.
- Banned wording: "EU compliant", "certified", "safe to operate", "approved", "replace now", "end of life reached".
- Not an official EU passport issuer and no affiliation with any battery manufacturer.

## Brand Commitments
Name: Battery Passport 360. No logo or brand palette is committed.

## Evidence on Hand
Real: HUST and Aalborg LFP datasets (CC BY 4.0) used for calibration; CALCE CS2 cell measurements; seven public EUR-Lex excerpts; Commission guidance v3.2. Absent and never to be fabricated: customers, testimonials, accuracy or savings claims, real pack telemetry.

## Product Principles
1. Provenance is part of the interface, not a footnote.
2. Suggest review, never decide; uncertainty is shown, not hidden.
3. Operator question first (which pack, why), method one step away.
4. Measured and simulated data never share a chart without a visible distinction.

## Accessibility & Inclusion
Keyboard navigation, visible focus, units on every value, identity never by colour alone, responsive down to 375 px (AGENTS.md).
