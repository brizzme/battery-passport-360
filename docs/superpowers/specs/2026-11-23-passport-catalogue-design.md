# Passport data-point catalogue — design (expansion part 3)

**Date:** 2026-11-23 · **Status:** draft for approval · Approach B (chosen by the user)

## Intent
Replace the five hand-written readiness rules (BP-01..05) with a catalogue of every data point in the European Commission's *Guidance Document: Digital Batteries Passport – data points by category*, v3.2, 19 Oct 2026 (CC BY 4.0, non-binding), so a reviewer can check the rule set row by row against its source. Two current rules are wrong for industrial batteries: chemistry is data point 12 (Annex VI A(7)), not Annex XIII 1(b); rated capacity 1(g) is "not to be filled" (repeats data point 11, capacity in Ah, Annex VI A(6)).

## Approaches
| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | Patch five rules, add ~6 by hand | Fast; hand-picked, hard to audit | Rejected |
| **B** | **Catalogue generated from the pinned guidance PDF; engine evaluates every data point** | More work; auditable against source | **Chosen** |
| C | BatteryPass data model (DIN DKE SPEC 99100) | Unmaintained; different granularity; second source of truth | Rejected |

## Goals
1. `research/guidance/` script downloads the guidance PDF (pinned sha256 in `research/guidance.sha256`), parses its table into `apps/api/app/artifacts/passport-catalogue.json`: per data point `dp` (1–73 as numbered), `name`, `unit`, `legal_ref` (e.g. "Annex VI A(6)"), `access` (public / restricted_legitimate_interest / restricted_authorities), and `applicability` for `ev`, `lmt`, `industrial` as the guidance's own words plus a normalised `kind`. Garbled PDF glyphs are fixed by a small committed `overrides.json` (reviewed by hand, each override citing the row). Tests check known rows (DP 11, 12, 25, 33, 34, 43, 52, 62, 68) against the source text.
2. Normalised applicability kinds and how the engine maps them to the six statuses (assessment scenario stays "prospective first placement on the as-of date"; Article 77 start 2027-02-18; industrial ≤ 2 kWh → not_applicable for all):
   - `mandatory` → before 2027-02-18 not_yet_effective; then present / missing_evidence / invalid from evidence.
   - `not_filled_repetition` → not_applicable ("repeats data point N").
   - `not_filled_until_act` (carbon footprint, recycled content, responsible sourcing, instructions on hold) → not_yet_effective with the guidance's reason; recycled content keeps the Article 8 earliest date 2028-08-18, after which unknown.
   - `some_industrial` / `if_applicable` → unknown ("applicability depends on battery design; not resolved for these packs").
   - `optional` → not_applicable ("optional").
   - `in_use` (Annex XIII 4(c),(d)) → not_yet_effective ("applies once the battery is in use; scenario is first placement").
   - `stationary_only` / `ev_only` → not_applicable for these forklift packs.
   - Any restricted-access mandatory field → unknown ("restricted-access evidence is not modelled in this prototype") — no fake restricted evidence.
3. Evidence: migration 006 seeds synthetic model-sheet entries (source `demo-inspection-v3`) for every public, industrial-mandatory data point, for all 100 packs, with plausible values and units per chemistry. Planted gaps: BAT-DEMO-024 keeps a missing chemistry reference and gets an invalid capacity entry ("unit absent", now on DP 11); three more packs get one gap each (missing declaration-of-conformity link, invalid nominal voltage, missing extinguishing agent). Existing BP fields map onto DP 11/12/27.
4. Engine: `readiness.py` loads the catalogue; `Result` gains `dp`, `access`, `guidance_ref`; `rule_id` becomes `DP-11` etc.; versions `catalogue v3.2-1`. Each result cites both the guidance row and the regulation reference.
5. Retrieval: migration 006 indexes each catalogue row as a reference passage (`GUID-DP-11` …, title, section = data point + legal ref, version "Guidance v3.2, 19 Oct 2026", access public, source URL). The copilot cites the guidance passage for each gap plus EU-77; its supported-question templates are unchanged.
6. UI: the pack page's passport section shows a coverage strip (counts per status for industrial packs) and a table grouped by status (gaps first, open by default; other groups collapsed), each row with data point, name, status, reason, evidence, access class and source links. The dashboard's "passport gaps" review rule keeps using missing/invalid at 2027-02-18. The draft summary lists counts and every gap, not all 73 rows.
7. Docs: DATA_SOURCES (guidance pin, licence, parsing, overrides), LIMITATIONS (non-binding guidance, unresolved applicability, restricted fields not modelled), PLAN.

## Non-goals
Restricted-access evidence; EV/LMT evidence (catalogue holds their columns, engine evaluates them, no seed data); implementing or delegated acts not yet adopted; the HUST research model (part 4).

## Anti-goals
Any value described as compliant or certified; treating the guidance as binding; inventing evidence for restricted fields; flagging all 100 packs as gapped (gaps stay planted and few).

## Changed expectations
`check-fleet.sh` BAT-DEMO-024 status list and the `?status=invalid` count change; tests are updated to the catalogue, not deleted. Readiness unit tests keep every existing scenario (scope, ≤ 2 kWh, unknown category, future evidence) on catalogue rows.

## Calls made after the builder check (review these)
1. **Placement view vs in-use view.** Readiness stays the first-placement scenario. In-use data points (Annex XIII 4(a) performance, 4(c) status, 4(d) cycles/events/temperature/SoC: DP 52–60, 67–71) are `not_yet_effective` with the reason "applies once the battery is in use; the synthetic in-use values are in the pack health section (restricted access)". So the two sections never contradict each other.
2. **Fixed precedence for the industrial column:** (1) category and kWh scope; (2) "not to be filled – repetition" or "same as data point N" → not_applicable; (3) EV-only / stationary-only → not_applicable; (4) optional → not_applicable; (5) "not to be filled as of February 2027" → not_yet_effective; (6) in-use rows (call 1) → not_yet_effective; (7) "only for rechargeable batteries" counts as applicable (all packs are rechargeable); (8) restricted-access mandatory → unknown (evidence not modelled); (9) "only some industrial" / "if applicable" → unknown unless resolved by chemistry (call 5); (10) public mandatory → evidence check.
3. **A gap means missing_evidence or invalid only**, everywhere: dashboard, copilot findings, draft summary, the gaps-first table. `unknown` is shown as its own "unresolved" group, never as a gap. The copilot stops treating unknown as a gap.
4. **Deferred fields after their date.** Responsible sourcing (DP 19, "required from August 2027", aligned with Reg. (EU) 2025/1561) becomes `unknown` from 2027-08-18 ("required per guidance; evidence not modelled"), not missing. Carbon footprint and instructions stay not_yet_effective at every date until an act is adopted. Recycled content keeps 2028-08-18, then unknown.
5. **Chemistry-resolved applicability.** The engine receives chemistry. DP 42 (cadmium/lead symbol) is mandatory for lead-acid packs (seeded) and not_applicable for LFP. Other "if applicable" rows (e.g. commercial warranty, DP 35) stay unknown.
6. **Identity.** Catalogue rows follow the pinned PDF's own numbering (71 data points). DP 38 holds two values, so it becomes `DP-38a` (cell) and `DP-38b` (pack). The PDF is downloaded from the URL in DATA_SOURCES.md and pinned; parsing runs on that file, and row-count tests use what it actually contains.
7. **Regulation citations** are a section label plus the EUR-Lex link (no new verbatim regulation text; EUR-Lex blocks automated fetches). Existing OJ passages stay; the copilot cites `GUID-DP-*` rows plus EU-77.
8. **Evidence typing.** `passport_fields` gains a `unit` column and `field_code` becomes `DP-11` etc. Existing rows migrate (chemistry → DP-12, rated_ah → DP-11, nominal_v → DP-27). Validation follows the guidance's format hints: number (finite, positive, unit matching the catalogue unit or an SI multiple), web link (http/https), yes/no, month-year, code list or free text (non-empty).

## Left to the builder
PDF library (pinned, research group), parsing strategy, exact synthetic values per field, UI group styling within the existing design system (DESIGN.md).
