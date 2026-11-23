# Calibrated synthetic fleet and health summary — design

**Date:** 2026-11-23 · **Status:** draft for approval · **Part 1 of 4** of the "Approach B" expansion
(1 calibrated fleet + health API → 2 dashboard redesign → 3 rule refresh against Commission guidance v3.2 → 4 HUST-based research model).

## 1. Intent and why

The prototype's synthetic fleet is flat: all 100 packs share one charge session, one telemetry sample and one service note (`db/migrations/003_inspector.sql`). A visually richer dashboard (part 2) has nothing to show until the data varies. No public forklift/intralogistics fleet dataset exists (research 2026-11-23), so the fleet stays **synthetic**, but its degradation and usage parameters must be **derived from real, citable, CC BY 4.0 measurements** so every number can be traced. Audience (from SPEC.md §1): a technical reviewer of an Applied AI portfolio, who will ask "where does this number come from?"

## 2. Goals

1. An offline calibration step that derives a small set of parameters from public LFP data and writes a committed, provenance-rich `fleet-calibration.json`.
2. A deterministic generator that turns calibration + fixed seed into ~24 months of daily history for 100 fictional packs, with realistic diversity (sites, shifts, temperatures, fade rates, events).
3. Fresh clone still boots with **no downloads** (M0 gate): calibration JSON and generated seed data are committed; downloads only needed to *re-derive* them.
4. Health-summary API per pack and for the fleet, aligned to the passport's in-use health data points (Annex XIII 4(a), 4(c,d) per Commission guidance v3.2), plus clearly marked operational KPIs.
5. Every value carries `source_type: synthetic`, the generator version, and the calibration source IDs it was derived from.

## 3. Non-goals

- Dashboard redesign / charts (part 2). In this part the existing pack detail page only swaps its "Simulated bench history" block for a plain-text health summary so nothing breaks.
- Passport rule changes (part 3). BAT-DEMO-024's passport gaps stay exactly as they are; existing readiness tests must keep passing.
- Replacing the CALCE research model (part 4).
- Ingesting real field datasets (ISEA home storage, RWTH vans) — rejected in approach selection.

## 4. Anti-goals (failure even if it works)

- Any synthetic value displayed or exported without a synthetic label, or labelled "measured".
- Implying the fleet predicts real pack remaining life, warranty status, or safety ("safe to operate", "end of life reached", "replace now").
- Calibration numbers that aren't reproducible from the pinned downloads, or a calibration that silently falls back to invented values when a download fails.
- Fleet triage that looks like an operational/safety alarm system. Flags are "suggested for specialist review".

## 5. Constraints

- AGENTS.md rules apply (provenance on displayed facts, no fabricated accuracy, no Jungheinrich data, version-pinned deps, deterministic seeds, honest PLAN.md).
- Stack unchanged: FastAPI + Pydantic, PostgreSQL migrations run by the existing `migrate` container (psql only), Next.js. No new services.
- Raw downloads stay in ignored `downloads/`; record checksums; attribution per CC BY 4.0 in `docs/DATA_SOURCES.md`.
- Pinned sources:
  - **HUST** (Ma et al. 2022, EES), Mendeley `10.17632/nsc7hnsg4s.2`, `our_data.zip`, 1,188,136,932 bytes, sha256 `071d24617153693b0d29059568525e620f6af6512acc9d00c98c7adcf15125db`. 77 LFP/graphite 1.1 Ah cells, 30 °C, 5C fast charge + multi-stage discharge. One pickle per cell; per-cycle DataFrame of `Current (mA)`, `Time (s)`, `Voltage (V)` — capacity must be integrated from current (BatteryML `preprocess_HUST.py` documents the structure).
  - **Aalborg forklift profile** (Vilsen & Stroe, Data in Brief 2024), Mendeley `yz4pttm73n` v2. 3 prismatic LFP 180 Ah cells aged on a forklift mission profile at 45/40/35 °C, ~29 FEC per round, 53–58 rounds; `RPT.csv` per round (C/4 capacity test at 25 °C, 20 s pulse resistance at 90/70/50/30 % SOC) and `Ageing.csv` (profile time series). Columns: Time [s], Current [A], Voltage [V], Energy [Wh], Temperature [°C]. Some rounds/parts missing (paper Table 2).
- Download availability was checked via the public Mendeley API only; actual download is the builder's first verification step.

## 6. Approaches considered

| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | Hand-set synthetic parameters | Fastest; numbers untraceable | Rejected |
| **B** | **Synthetic fleet calibrated on real LFP data** | More work; every parameter traceable to a source | **Chosen by user** |
| C | Show real field data (home storage / vans) next to fleet | Wrong application, 21 GB, blurs real vs synthetic | Rejected |

## 7. Design

### 7.1 Calibration (`research/calibrate.py`, offline, research dependency group)

Same pattern as `research/prepare.py`: download if absent → verify sha256 (pinned in `research/calibration.sha256`) → parse → write `apps/api/app/artifacts/fleet-calibration.json` atomically. Fails loudly; never writes partial or default parameters.

What each source contributes — chosen so each dataset is used for what it is credible for:

| Parameter | Source | Derivation |
|---|---|---|
| Absolute capacity fade per equivalent full cycle (EFC) under a forklift profile, at 35/40/45 °C | Aalborg RPT.csv | Per round: C/4 discharge capacity (Ah) from RPT; EFC from cumulative ageing throughput ÷ (2 × nominal). Fit fade vs EFC per cell. |
| Temperature sensitivity | Aalborg (3 temperatures) | Fit an Arrhenius form to fade rate vs temperature; store coefficients and the 3 points. **Calibrated range 35–45 °C. Between 20 and 35 °C the fit is extrapolated and every affected value is labelled `extrapolated_below_calibrated_range`. Below 20 °C the 20 °C rate is used (clamped, labelled). Above 45 °C clamped at 45 °C (labelled).** *(My call — see §8.)* |
| Resistance increase vs capacity fade | Aalborg RPT pulses | Ratio/slope of 50 % SOC 20 s discharge-pulse resistance growth vs capacity fade. If not derivable cleanly, record `null` and the API reports resistance/power fade as `unknown` — no invented value. |
| Cell-to-cell variability and curve shape (incl. knee) | HUST, 77 cells | Integrate discharge capacity per cycle; per cell: life to 80 % of initial capacity; fit distribution (store e.g. lognormal μ, σ and empirical quantiles); median normalised fade curve (capacity fraction vs fraction of life, ~20 knots). Only the *relative spread and shape* are used, not HUST's absolute lab life (5C lab cycling ≠ forklift duty). |
| Daily duty-cycle shape | Aalborg Ageing.csv (one round per cell suffices) | Throughput per profile hour, share of time at rest/charge/discharge, typical depth of discharge per shift. |

Output JSON contains: parameters, fit residuals, n per fit, archive URLs, sizes, sha256, access date, licence + attribution strings, calibration version (`fleet-calib-v1-<digest12>`), and a `limitations` list (3 Aalborg cells only; cell-level not pack-level; 25 °C RPT; HUST 30 °C single temperature).

### 7.2 Fleet generator (`research/generate_fleet.py`, runs without downloads)

Input: committed calibration JSON + fixed seed (`numpy.random.default_rng(20261123)`). Output: committed `db/seed/fleet_v2/*.csv.gz` and a `manifest.json` (generator version, calibration version, seed, row counts, sha256 per file). Regenerating must reproduce byte-identical files (tested).

Fictional fleet structure (my calls, adjustable):
- **Identities:** keep `BAT-DEMO-001..100`, category industrial, existing `rated_kwh` formula. **Chemistry mix changes to 80 % LFP / 20 % lead-acid** (lead-acid on indices divisible by 5). BAT-DEMO-024 stays LFP. Reason: calibration data is LFP-only; lead-acid packs get operational history but their capacity/resistance fade is reported `unknown — no calibration source`, which demonstrates honest uncertainty.
  - Provenance: migration 005 adds source `demo-identities-v2` (synthetic, explanation states the 80/20 rule) and moves all identity rows to it; `fleet.py` queries filter on `source_type='synthetic'`, not a specific ID. The copied `chemistry` passport field is updated for the 30 changed packs under a new `demo-inspection-v2` source with a new observed time. BAT-DEMO-024's passport fields (missing chemistry reference, `rated_ah = 'unit absent'`) remain byte-identical; `check-fleet.sh` / `check-demo.sh` expectations updated only where the chemistry count changes.
- **Sites:** 3 fictional sites with ambient profiles (cold store ~5 °C, ambient warehouse ~20 °C, hot dock/summer-heavy ~30 °C) and seasonal variation.
- **Usage:** commissioning dates staggered across 2023–2025 (initial SoH sampled from history before window); 1–3 shifts/day, weekday/weekend pattern, opportunity-charging propensity per pack, occasional idle weeks.
- **Pack temperature:** ambient + usage-dependent rise (documented generator assumption, not calibrated — labelled as such). Expected effect: most packs at the ambient and hot sites run 25–40 °C during operation; cold-store packs mostly fall in the clamped region. The planted hot-site fast fader must come from temperature *and* a high life-multiplier draw; the test asserts the temperature contribution is labelled extrapolated/calibrated as appropriate.
- **Degradation (LFP):** per-pack life multiplier drawn from the HUST spread; fade per EFC from Aalborg at the pack's daily temperature via the fitted temperature model; follows the HUST median curve shape; small calendar term only if derivable, else omitted and stated.
- **Events:** over-temperature (> site/threshold), deep-discharge (< 10 % SoC), BMS communication loss; rates are generator assumptions (labelled).
- **Planted cases** (documented in DATA_SOURCES.md, tested): ≥1 fast-fading pack at the hot site, ≥1 pack with repeated over-temperature events, ≥1 idle pack, BAT-DEMO-024 retains passport gaps with otherwise ordinary health.
- **Window:** daily rows 2024-11-01 → 2026-10-31 (24 months, all before today). Assessment dates after the window use the last available day and state the data cut-off.

### 7.3 Storage (migration `005_fleet_history.sql`)

- New source record `demo-fleet-v2` (synthetic) whose explanation names the generator and calibration versions.
- Tables: `fleet_sites`, `pack_profiles` (battery_id → site, commissioned_on, shifts, life multiplier), `pack_daily` (battery_id, day, efc, throughput_kwh, soc_min/max, temp_mean/max_c, charge_sessions, opportunity_charges, capacity_pct, resistance_pct nullable), `pack_monthly_histograms` (battery_id, month, kind ∈ {temperature, soc}, bin_lower, bin_upper, hours), `pack_events` (battery_id, observed_at, kind, detail).
- Seed load via `\copy` from the gz CSVs (migration image gains the seed files and gunzip).
- **Migration runner change (my call):** the `migrate` command skips any file whose version is already in `schema_migrations` (a few lines of shell around psql). This fixes the re-run-everything behaviour, so 005 runs once and can drop tables. Editing earlier migration files is allowed — none are committed or deployed beyond local volumes — but not needed with the runner change.
- **Seed versioning:** a seed-data change ships as a new migration (e.g. `006_fleet_seed_v3.sql`) that truncates and reloads, rather than relying on `ON CONFLICT DO NOTHING`. The manifest digest is stored in the `demo-fleet-v2` source record so the API can report which seed is loaded.
- Old bench tables (`vehicle_assignments`, `charge_sessions`, `telemetry_samples`, `service_events`) are dropped in 005; their consumers (`fleet.inspect`, `summary.py`, copilot) move to the new tables.

### 7.4 API

- **Passport mapping source:** European Commission, *Guidance Document: Digital Batteries Passport – data points by category*, v3.2, 19 Oct 2026, CC BY 4.0, non-binding ("not an authoritative interpretation"), https://single-market-economy.ec.europa.eu/document/download/cd1e5e6c-4a4a-4b99-995a-49eb6916187e_en, accessed 2026-11-23. Per that guidance: Annex XIII 4(a) performance/durability items (capacity fade, power fade, resistance increase, RTE fade where applicable, expected lifetime) apply to rechargeable industrial batteries; 4(c,d) (status, cycle count, negative events, temperature and SoC records) apply to all categories in use; **4(b) Annex VII Part A state-of-health applies only to stationary BESS and is `not_applicable` to these forklift packs.** All of 4(a)–(d) are **restricted access (legitimate interest)**, not public. The API marks each field with `passport_ref` (e.g. "Annex XIII 4(a) per Commission guidance v3.2, non-binding"), `access_class: "restricted_legitimate_interest"` and `mapping_status: "provisional — rule integration in part 3"`. Wording never says "required" or "compliant". Add this source to `docs/DATA_SOURCES.md`.
- `GET /api/batteries/{id}/health-summary?as_of=` (replaces the bench snapshot):
  - **Passport-aligned (Annex XIII 4(a), 4(c,d) via guidance v3.2):** capacity fade %, power fade % and internal-resistance increase % (or `unknown` with reason), expected lifetime fields → `unknown` (not modelled), EFC cycle count, negative events, temperature and SoC histograms (hours per bin, aggregated up to as_of), status `original`.
  - **Operational KPIs (explicitly `passport_field: false`):** energy throughput, EFC last 30/90 days, opportunity-charge share, mean/max temperature, fade rate last 90 days.
  - Every value: `source_type: synthetic`, `source_id`, `generator_version`, `calibration_refs` (e.g. `["aalborg-forklift-v2", "hust-lfp-v2"]` or `"generator_assumption"`), `data_cutoff`.
- `GET /api/batteries/{id}/history?from=&to=` → daily series for charts (part 2), capped range.
- `GET /api/fleet/health-summary?as_of=` → counts by capacity band, totals, events last 30 days, and **"suggested for specialist review"** list with the triggering rule per pack. Triage rules are deterministic, versioned (`triage-v1`), documented, labelled "demo thresholds — not safety, warranty or end-of-life limits": e.g. capacity < 80 %, 90-day fade rate above fleet P90, ≥ N over-temperature events in 30 days, passport readiness gaps. **The readiness-gap rule evaluates readiness at the 2027-02-18 milestone date (prospective placement scenario), independent of the health `as_of`, and the reason says so** — otherwise it could never fire before 2027 because `classify` returns `not_yet_effective`. BAT-DEMO-024 therefore appears in the review list via this rule. Fleet endpoint default `as_of` = min(today, data cut-off).
- No future leakage: nothing after `as_of` is aggregated (tested).
- Copilot tool `get_health_summary` and the Markdown draft (`summary.py`) switch to the new summary; the draft states calibration sources and limitations.

### 7.5 Tests and checks

- Calibration: unit tests on parsers with tiny committed synthetic fixtures (not raw data); JSON schema validation of the committed calibration; refuses to run on checksum mismatch.
- Generator: byte-identical regeneration; FK consistency; value ranges; planted cases present; lead-acid fade is `unknown`; every row synthetic.
- API: as_of cut-off, labels on every value, 404/422 cases, triage rule reasons, BAT-DEMO-024 readiness unchanged.
- Existing: 21 pytest tests, `scripts/check-fleet.sh`, `scripts/check-demo.sh` updated for new endpoints; frontend lint/typecheck/build; clean-clone `docker compose up --build` without downloads.
- Docs: DATA_SOURCES.md (calibration manifest, attribution), LIMITATIONS.md, ARCHITECTURE.md, PLAN.md work log.

## 8. Calls made without asking (review these)

1. Chemistry mix 80 % LFP / 20 % lead-acid; lead-acid fade reported `unknown`.
2. Temperature extrapolation 20–35 °C via Arrhenius fit, labelled; clamped below 20 °C and above 45 °C.
3. Triage readiness rule judged at 2027-02-18, health at `as_of`.
4. New provenance records `demo-identities-v2` / `demo-inspection-v2` for changed data.
5. Migration runner skips already-applied files.
6. Health fields mapped to non-binding Commission guidance v3.2, marked provisional and restricted-access.
7. 24-month window ending 2026-10-31; three fictional sites (≈5 / 20 / 30 °C ambient).

## 9. Left to the builder

Exact fit forms and bin edges; CSV column order; the precise generator assumptions' numbers (must be listed in the manifest and DATA_SOURCES.md); how many Aalborg rounds to read for the duty profile; triage N/P thresholds; module layout inside `apps/api/app/`. Stop and report (do not substitute invented values) if either dataset can't be downloaded or parsed as documented.
