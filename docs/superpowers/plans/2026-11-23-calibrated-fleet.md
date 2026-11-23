# Calibrated Synthetic Fleet & Health Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat 100-pack demo fleet with 24 months of deterministic synthetic daily history whose LFP degradation parameters are derived from public HUST and Aalborg measurements, and expose per-pack and fleet health summaries through the API.

**Architecture:** Offline `research/` scripts (numpy, research dependency group) derive `fleet-calibration.json` from pinned downloads and generate committed gzip CSV seed files. A new migration loads them; a migration runner skips applied files. A new `apps/api/app/health.py` turns rows into labelled indicators and deterministic triage flags; routes live in the existing fleet router plus a new `/api/fleet` router.

**Tech Stack:** Python 3.12, numpy (research group), pandas only inside an isolated extraction container, FastAPI/Pydantic, PostgreSQL 16 + psql `\copy`, Next.js 16 (one page edit), Docker Compose.

**Spec:** [docs/superpowers/specs/2026-11-23-calibrated-fleet-design.md](../specs/2026-11-23-calibrated-fleet-design.md) — read it before any task.

## Global Constraints

- Every fleet value displayed or returned carries `source_type: "synthetic"`; nothing in fleet tables is ever `measured_public`.
- Never write words "compliant", "certified", "safe to operate", "end of life reached", "replace now". Triage copy: "Suggested for specialist review" and "demo thresholds — not safety, warranty or end-of-life limits".
- Calibration never falls back to invented values: missing/unparseable data or checksum mismatch → raise, write nothing.
- Pinned HUST: `our_data.zip`, 1,188,136,932 bytes, sha256 `071d24617153693b0d29059568525e620f6af6512acc9d00c98c7adcf15125db`, URL `https://data.mendeley.com/public-files/datasets/nsc7hnsg4s/files/5ca0ac3e-d598-4d07-8dcb-879aa047e98b/file_downloaded`, CC BY 4.0, Ma et al. 2022 EES, DOI 10.17632/nsc7hnsg4s.2.
- Aalborg: Mendeley dataset `yz4pttm73n` v2, CC BY 4.0, Vilsen & Stroe, Data in Brief 2024. File URLs and sha256 come from the public API `https://data.mendeley.com/public-api/datasets/yz4pttm73n/files?folder_id=...&version=2` (pin them in `research/calibration.sha256`; never trust-on-first-download).
- **Untrusted pickles:** HUST pickles are unpickled ONLY inside `docker run --rm --network none --read-only` with the archive mounted read-only; host Python never calls `pickle.load` on them.
- Raw downloads under ignored `downloads/`; derived artifacts committed: `apps/api/app/artifacts/fleet-calibration.json`, `db/seed/fleet_v2/*`.
- RNG: `numpy.random.default_rng(20261123)`; gzip written with `mtime=0`; regeneration byte-identical.
- Data window: daily rows 2024-11-01 → 2026-10-31 inclusive; `DATA_CUTOFF = date(2026, 10, 31)`.
- Temperature regimes: `calibrated` 35–45 °C, `extrapolated_below_calibrated_range` 20–35 °C, `clamped_low` < 20 °C (uses 20 °C rate), `clamped_high` > 45 °C (uses 45 °C rate).
- Chemistry: lead-acid iff index % 5 == 0, else LFP. BAT-DEMO-024 LFP with passport fields unchanged (chemistry ref NULL, `rated_ah='unit absent'`).
- Passport mapping text: `"Annex XIII 4(a) per Commission guidance v3.2 (non-binding)"` / `"Annex XIII 4(c)"` / `"Annex XIII 4(d)"`; `access_class: "restricted_legitimate_interest"`; `mapping_status: "provisional — rule integration in part 3"`. 4(b) reported `not_applicable` with reason "Annex VII Part A state-of-health applies to stationary BESS only (guidance v3.2)".
- Guidance URL: `https://single-market-economy.ec.europa.eu/document/download/cd1e5e6c-4a4a-4b99-995a-49eb6916187e_en`, v3.2, 19 Oct 2026, accessed 2026-11-23.
- Research test command: `(cd apps/api && uv run --locked --group research pytest ../../research/tests -q)`. API tests: `(cd apps/api && uv run --locked pytest -q)`.
- Commits: only with the user's go-ahead (see Task 0).

## Review Focus

1. `as_of` before a pack's first daily row or before 2024-11-01 → summary returns indicators with `status: "unknown"`, reason "No synthetic history on or before this date", HTTP 200, not 500. (Task 8)
2. `as_of` after `DATA_CUTOFF` → values computed at cutoff and `data_cutoff: "2026-10-31"` returned; never extrapolated forward. (Task 8)
3. Lead-acid pack → capacity/power/resistance indicators `status: "unknown"`, reason "No calibration source for lead-acid", never `0`. (Task 8)
4. `/history` with `from > to`, or range > 366 days → 422. (Task 9)
5. Existing local DB volume (003 already applied, old runner) upgraded with new runner → 005 applies once, second boot skips all, bench tables gone. (Task 7)

---

### Task 0: Baseline commit and branch (needs user OK)

- [ ] **Step 1:** Ask the user whether to commit the existing uncommitted M0–M4 work to `main` as milestone commits, then branch `feat/calibrated-fleet`. Do not proceed with commits otherwise; implement without committing and report.
- [ ] **Step 2:** Verify baseline: `(cd apps/api && uv run --locked pytest -q)` → `21 passed`.

### Task 1: Migration runner that skips applied files

**Files:**
- Create: `db/migrate.sh`
- Modify: `db/Dockerfile`, `compose.yaml` (`migrate.command`)

**Interfaces:** Produces: `migrate` service runs `/migrate.sh`; prints `apply <version>` or `skip <version>` per file.

- [ ] **Step 1:** Write `db/migrate.sh` (`sh -eu`): for each `/migrations/*.sql` sorted, `version=$(basename "$f" .sql)`; check existence with `psql -tAc "SELECT 1 FROM pg_tables WHERE tablename='schema_migrations'"` first, then `psql -tAc "SELECT 1 FROM schema_migrations WHERE version='$version'"`; skip if `1`, else `psql -v ON_ERROR_STOP=1 -f "$f"`. Version strings already match file basenames (`001_foundation` … `004_public_passages`).
- [ ] **Step 2:** Dockerfile: `COPY migrate.sh /migrate.sh` + `RUN chmod +x /migrate.sh`; compose: `command: ["/migrate.sh"]`.
- [ ] **Step 3: Verify:** `docker compose up --build -d && docker compose logs migrate` → four `skip` lines on the existing volume; `docker compose down -v && docker compose up --build -d && docker compose logs migrate` → four `apply` lines; `./scripts/check-fleet.sh` passes.
- [ ] **Step 4: Commit** (if Task 0 approved): `git add db/ compose.yaml && git commit -m "build: skip already-applied migrations"`

### Task 2: Aalborg parsing and temperature fit (pure functions)

**Files:**
- Create: `research/fleetcal/__init__.py`, `research/fleetcal/aalborg.py`, `research/conftest.py` (adds `research/` to `sys.path`), `research/tests/test_aalborg.py`, `research/tests/fixtures/aalborg_rpt_small.csv`, `research/tests/fixtures/aalborg_ageing_small.csv`

**Interfaces:**
- Produces:
  - `rpt_capacity_ah(df: dict[str, np.ndarray]) -> float` — integrates |I| over the longest contiguous segment with current in [−47, −43] A (C/4 = 45 A); columns `"Time [s]"`, `"Current [A]"`, `"Voltage [V]"`.
  - `pulse_resistance_ohm(df, soc_order_index: int = 2) -> float | None` — third 20 s ~45 A discharge pulse (90/70/50/30 % order → index 2 = 50 %); `(V_before − V_end)/I`; `None` if not found.
  - `efc_per_round(ageing: dict[str, np.ndarray], nominal_ah: float = 180.0) -> float` — total |I|·dt /3600 / (2·nominal).
  - `duty_profile(ageing) -> dict` keys `share_discharge`, `share_charge`, `share_rest`, `efc_per_day`, `mean_discharge_c_rate`.
  - `fade_slope_per_efc(efc: np.ndarray, capacity_frac: np.ndarray) -> float` (least squares through (0,1)).
  - `fit_arrhenius(temps_c: list[float], slopes: list[float]) -> tuple[float, float]` returns `(ln_a, ea_over_r)`; `rate_at(temp_c, ln_a, ea_over_r) -> tuple[float, str]` returns `(rate, regime)` applying the Global-Constraints regimes.
  - `read_csv_columns(path: Path) -> dict[str, np.ndarray]` (numpy `genfromtxt`, names from header).

- [ ] **Step 1: Write failing tests** with tiny hand-made fixtures (≤ 200 rows, synthetic, committed):
```python
def test_rpt_capacity_integrates_c4_segment():  # fixture: 3600 s at -45 A plus noise segments
    assert rpt_capacity_ah(read_csv_columns(FIX/"aalborg_rpt_small.csv")) == pytest.approx(45.0, rel=1e-3)
def test_pulse_resistance_third_pulse():         # fixture: 4 pulses, 3rd drops 0.09 V at 45 A
    assert pulse_resistance_ohm(read_csv_columns(FIX/"aalborg_rpt_small.csv")) == pytest.approx(0.002, rel=1e-3)
def test_arrhenius_recovers_known_rates():
    ln_a, e = 5.0, 4000.0
    temps=[35,40,45]; slopes=[math.exp(ln_a-e/(t+273.15)) for t in temps]
    assert fit_arrhenius(temps, slopes) == pytest.approx((ln_a, e), rel=1e-6)
@pytest.mark.parametrize("t,regime",[(40,"calibrated"),(25,"extrapolated_below_calibrated_range"),(5,"clamped_low"),(50,"clamped_high")])
def test_regimes(t, regime): assert rate_at(t, 5.0, 4000.0)[1] == regime
def test_clamped_low_uses_20c_rate(): assert rate_at(5,5.0,4000.0)[0] == rate_at(20,5.0,4000.0)[0]
def test_missing_c4_segment_raises(): ...  # pytest.raises(ValueError)
```
- [ ] **Step 2:** Run research tests → FAIL (module missing).
- [ ] **Step 3:** Implement `research/fleetcal/aalborg.py` per Interfaces. Use numpy only.
- [ ] **Step 4:** Run research tests → PASS.
- [ ] **Step 5: Commit** `feat(research): Aalborg RPT parsing and Arrhenius fit`

### Task 3: HUST isolated extraction and life distribution

**Files:**
- Create: `research/hust_extract/Dockerfile` (python:3.12-slim + pinned `pandas==2.3.3`, `numpy`), `research/hust_extract/extract.py`, `research/fleetcal/hust.py`, `research/tests/test_hust.py`

**Interfaces:**
- `extract.py` (runs ONLY in container: `docker run --rm --network none --read-only --tmpfs /tmp -v <zip>:/in/our_data.zip:ro -v <out>:/out hust-extract`): for each cell pickle, writes `/out/<cell>.csv` with columns `cycle,discharge_ah` where `discharge_ah` = ∫ max(0, −I_mA)·dt / 3.6e6 per cycle. Host code never unpickles.
- `fleetcal/hust.py` produces:
  - `read_cell_csv(path) -> tuple[np.ndarray, np.ndarray]` (cycles, discharge_ah)
  - `life_to_80(cycles, cap) -> int | None` — initial = median of cycles 2–6; first cycle where 5-cycle rolling median < 0.8·initial; `None` if never.
  - `normalized_curve(cycles, cap, life, knots=21) -> np.ndarray` — capacity fraction at life fractions `linspace(0,1,21)` via interpolation.
  - `life_distribution(lives: list[int]) -> dict` keys `median`, `quantiles` (5,10,…,95 of `life/median`), `lognormal_sigma`, `n`, `n_excluded`.

- [ ] **Step 1: Failing tests** on synthetic arrays (no real data):
```python
def test_life_to_80_detects_crossing():
    c=np.arange(1,1001); cap=1.1*(1-0.0003*c)  # 0.8·1.1 reached near cycle 667
    assert life_to_80(c,cap) == pytest.approx(667, abs=3)
def test_life_none_when_never_reached(): assert life_to_80(np.arange(1,50), np.full(49,1.1)) is None
def test_curve_starts_at_one_and_ends_at_point_eight():
    k=normalized_curve(c,cap,667); assert k[0]==pytest.approx(1,abs=1e-2) and k[-1]==pytest.approx(0.8,abs=1e-2) and len(k)==21
def test_distribution_quantiles_relative_to_median():
    d=life_distribution([1000,1500,2000]); assert d["median"]==1500 and d["n"]==3
```
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5:** Build image `docker build -t hust-extract research/hust_extract` → success (no run yet; real data in Task 4).
- [ ] **Step 6: Commit** `feat(research): isolated HUST extraction and life distribution`

### Task 4: Calibration run → committed `fleet-calibration.json`

**Files:**
- Create: `research/calibrate.py`, `research/calibration.sha256`, `research/tests/test_calibration_schema.py`
- Create (generated, committed): `apps/api/app/artifacts/fleet-calibration.json`
- Modify: `apps/api/pyproject.toml` only if a research dep is missing (pin it; `uv lock`).

**Interfaces:** Produces JSON with top-level keys: `calibration_version` (`"fleet-calib-v1-" + sha256(calibration.sha256)[:12]`), `generated_at`, `sources` (per file: url, bytes, sha256, licence, attribution, accessed `"2026-11-23"`), `aalborg` {`cells`: [{cell, temp_c, rounds_used, efc_per_round, fade_slope_per_efc, residual_rmse}], `arrhenius` {ln_a, ea_over_r, calibrated_range_c:[35,45]}, `resistance_growth_per_fade` (float|null), `duty_profile` {...}}, `hust` {`life_distribution`, `median_curve` (21 floats), `n_cells`, `n_excluded`}, `limitations` (list of strings from spec §7.1).

- [ ] **Step 1:** Query the Aalborg Mendeley API, list `RPT.csv` for every round of Cell1–3 and `Ageing.csv` for one mid-life round per cell; write url + sha256 + bytes lines into `research/calibration.sha256` along with the HUST line. If the API gives no checksum for a file, stop and report.
- [ ] **Step 2: Failing schema test** `test_committed_calibration_schema`: loads the committed JSON; asserts keys above, `len(median_curve)==21`, `hust.n_cells + hust.n_excluded == 77`, all three Aalborg temps present `[35,40,45]`, every `sources[*].sha256` appears in `calibration.sha256`, `fade_slope_per_efc < 0` per cell.
- [ ] **Step 3:** Implement `calibrate.py` (pattern of `research/prepare.py`: download to `.part`, verify sha256, rename; run HUST container into `downloads/hust_csv/`; parse; atomic write). Missing Aalborg rounds (paper Table 2) are skipped and counted, not filled.
- [ ] **Step 4:** Run `(cd apps/api && uv run --locked --group research python ../../research/calibrate.py)`. If download or parse fails: STOP, report to user; do not continue to Task 5.
- [ ] **Step 5:** Run research tests → PASS. Sanity-print: Aalborg EFC-to-80 % at 35 °C and HUST median life; record both in the task report (no expected values are asserted — they are findings).
- [ ] **Step 6: Commit** `feat(research): derive fleet calibration from HUST and Aalborg`

### Task 5: Generator model (pure functions)

**Files:**
- Create: `research/fleetgen/__init__.py`, `research/fleetgen/model.py`, `research/tests/test_fleetgen_model.py`

**Interfaces:**
- Consumes: `fleetcal.aalborg.rate_at`, calibration dict (Task 4 schema).
- Produces:
  - `SITES: tuple[Site, ...]` — `Site(site_id, name, ambient_mean_c, seasonal_amp_c)`: `("SITE-COLD","Cold store",5,2)`, `("SITE-AMB","Ambient warehouse",20,5)`, `("SITE-HOT","Hot dock",30,6)`.
  - `GENERATOR_ASSUMPTIONS: dict[str, float]` — every hand-set number (temperature rise per shift, event rates, opportunity-charge propensity range, SoC model params, over-temp threshold 45 °C, deep-discharge threshold 10 % SoC). Written verbatim into the manifest.
  - `pack_temperature(site, day: date, shifts: int, rng) -> tuple[float, float]` (mean, max °C).
  - `capacity_fraction(effective_life_used: float, median_curve: np.ndarray) -> float` — interpolate curve on [0,1]; beyond 1 extend with last segment slope.
  - `daily_effective_efc(efc: float, temp_c: float, cal: dict) -> tuple[float, str]` = `efc × rate_at(temp)/rate_at(35)` and the regime.
  - `life_efc_ref(cal) -> float` = `0.2 / |mean fade_slope at 35 °C|`.
  - `resistance_pct(cap_frac: float, growth: float | None) -> float | None` = `100·(1 + growth·(1−cap_frac))` or `None`.

- [ ] **Step 1: Failing tests:**
```python
def test_hotter_day_consumes_more_life(cal): assert daily_effective_efc(1,40,cal)[0] > daily_effective_efc(1,35,cal)[0]
def test_regime_reported(cal): assert daily_effective_efc(1,25,cal)[1]=="extrapolated_below_calibrated_range"
def test_capacity_fraction_monotone(cal):
    xs=np.linspace(0,1.2,50); ys=[capacity_fraction(x,np.array(cal["hust"]["median_curve"])) for x in xs]
    assert all(a>=b for a,b in zip(ys,ys[1:])) and ys[0]==pytest.approx(1,abs=0.02)
def test_resistance_none_without_growth(): assert resistance_pct(0.9,None) is None
def test_assumptions_have_no_calibrated_keys(): assert "fade" not in " ".join(GENERATOR_ASSUMPTIONS)
```
(`cal` fixture loads the committed JSON.)
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement. **Step 4:** Run → PASS.
- [ ] **Step 5: Commit** `feat(research): fleet generator model`

### Task 6: Deterministic fleet generation and seed files

**Files:**
- Create: `research/generate_fleet.py`, `research/tests/test_generate_fleet.py`
- Create (generated, committed): `db/seed/fleet_v2/{sites.csv, profiles.csv, daily.csv.gz, histograms.csv.gz, events.csv.gz, manifest.json}`

**Interfaces:**
- Produces `generate(cal: dict, seed: int = 20261123) -> dict[str, list[dict]]` and `write(tables, out_dir) -> dict` (manifest).
- CSV columns (exact, in this order):
  - `sites.csv`: `site_id,name,ambient_mean_c,seasonal_amp_c`
  - `profiles.csv`: `battery_id,chemistry,site_id,commissioned_on,shifts,life_multiplier,opportunity_propensity`
  - `daily.csv.gz`: `battery_id,day,efc,throughput_kwh,soc_min_pct,soc_max_pct,temp_mean_c,temp_max_c,charge_sessions,opportunity_charges,capacity_pct,resistance_pct,temp_regime` (`capacity_pct`/`resistance_pct` empty for lead-acid; `resistance_pct` empty when growth is null)
  - `histograms.csv.gz`: `battery_id,month,kind,bin_lower,bin_upper,hours` (`kind` ∈ `temperature`,`soc`; month = first day)
  - `events.csv.gz`: `battery_id,observed_at,kind,detail` (`kind` ∈ `over_temperature`,`deep_discharge`,`bms_comm_loss`)
- `manifest.json`: `generator_version` (`"fleet-gen-v1"`), `calibration_version`, `seed`, `window` [start, end], `assumptions` (= `GENERATOR_ASSUMPTIONS`), `planted` (below), `rows` per file, `sha256` per file, `digest` (sha256 over the per-file hashes in file-name order).
- Planted cases (fixed overrides, documented in manifest): `BAT-DEMO-007` SITE-HOT, life_multiplier = HUST 5th-percentile quantile (fast fader); `BAT-DEMO-013` SITE-HOT with ≥ 6 over-temperature events in Oct 2026; `BAT-DEMO-042` idle (efc 0) 2026-08-01 → 2026-09-30; `BAT-DEMO-024` SITE-AMB, ordinary.
- Commissioning drawn 2023-01-01 … 2025-06-30; packs commissioned inside the window start rows on commission day; pre-window life consumed = days before window × the pack's mean daily effective EFC over its first window year.

- [ ] **Step 1: Failing tests:**
```python
def test_regeneration_is_byte_identical(tmp_path, cal):
    m1=write(generate(cal),tmp_path/"a"); m2=write(generate(cal),tmp_path/"b"); assert m1["digest"]==m2["digest"]
def test_committed_seed_matches_regeneration(tmp_path, cal):
    assert write(generate(cal),tmp_path)["digest"]==json.loads((SEED/"manifest.json").read_text())["digest"]
def test_lead_acid_rows_have_no_capacity(tables): assert all(r["capacity_pct"]=="" for r in tables["daily"] if r["battery_id"].endswith(("005","010","100")))
def test_chemistry_rule(tables): assert sum(p["chemistry"]=="LFP" for p in tables["profiles"])==80
def test_planted_fast_fader_is_lowest_capacity_at_hot_site(tables): ...
def test_planted_overtemp(tables): assert sum(e["battery_id"]=="BAT-DEMO-013" and e["kind"]=="over_temperature" and e["observed_at"].startswith("2026-10") for e in tables["events"])>=6
def test_window_bounds_and_fk(tables): ...  # min day ≥ 2024-11-01, max = 2026-10-31, all battery_ids in profiles, ≤ 730 rows per pack
def test_capacity_monotone_non_increasing_per_pack(tables): ...
```
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement; write gzip via `gzip.GzipFile(fileobj=..., mtime=0)`; CSV via `csv.writer` with `lineterminator="\n"`; floats formatted `"{:.4f}"`.
- [ ] **Step 4:** Run `(cd apps/api && uv run --locked --group research python ../../research/generate_fleet.py)` then research tests → PASS. Check total seed size < 15 MB.
- [ ] **Step 5: Commit** `feat(research): deterministic calibrated fleet seed`

### Task 7: Migration 005 — identities v2, history tables, seed load

**Files:**
- Create: `db/migrations/005_fleet_history.sql`
- Modify: `db/Dockerfile` (`COPY seed /seed`), `scripts/check-fleet.sh`

**Interfaces:** Tables (all `source_id NOT NULL REFERENCES source_records`):
`fleet_sites(site_id PK, name, ambient_mean_c, seasonal_amp_c)`, `pack_profiles(battery_id PK FK batteries, site_id FK, commissioned_on date, shifts int, life_multiplier real, opportunity_propensity real, source_id)`, `pack_daily(battery_id FK, day date, …columns as CSV…, source_id, PK(battery_id, day))`, `pack_monthly_histograms(battery_id, month, kind, bin_lower, bin_upper, hours, source_id, PK(battery_id, month, kind, bin_lower))`, `pack_events(battery_id, observed_at timestamptz, kind, detail, source_id, PK(battery_id, observed_at, kind))`.
Source records: `demo-identities-v2` (synthetic, `2026-11-23T00:00:00Z`, "Fictional identities v2: lead-acid when index divisible by 5, otherwise LFP; rated energy 16 + 4 × (index mod 8) kWh."), `demo-inspection-v2` (synthetic, chemistry passport-field updates), `demo-fleet-v2` (synthetic, explanation contains generator version, calibration version and manifest digest).

- [ ] **Step 1:** Update `scripts/check-fleet.sh` expectations first (failing against current stack): identity `source_id == 'demo-identities-v2'` with the new explanation; `count(*) FILTER (WHERE chemistry='LFP') = 80`; BAT-DEMO-024 readiness statuses unchanged `["missing_evidence","invalid","present","not_applicable","not_yet_effective"]`; `pack_daily` has 100 distinct packs and max(day)='2026-10-31'; old `vehicle_assignments` absent (`to_regclass` is NULL); remove the `bench.vehicle_id` assertion.
- [ ] **Step 2:** Run `./scripts/check-fleet.sh` → FAIL.
- [ ] **Step 3:** Write 005 in one transaction: insert source records; `UPDATE batteries SET chemistry=…, source_id='demo-identities-v2'`; `UPDATE passport_fields SET value_text=b.chemistry, source_id='demo-inspection-v2'` only for `field_code='chemistry'` rows whose value changed (BAT-DEMO-024 unaffected); `DROP TABLE IF EXISTS vehicle_assignments, charge_sessions, telemetry_samples, service_events`; create tables; `\copy … FROM PROGRAM 'gunzip -c /seed/fleet_v2/daily.csv.gz' WITH (FORMAT csv, HEADER true, NULL '')` (plain `\copy … FROM '/seed/…csv'` for uncompressed); insert `005_fleet_history` into `schema_migrations`.
- [ ] **Step 4: Verify upgrade path (Review Focus 5):** on the existing volume `docker compose up --build -d` → migrate log `skip` ×4, `apply 005_fleet_history`; restart → `skip` ×5; `./scripts/check-fleet.sh` PASS. Then `docker compose down -v && docker compose up --build -d` → PASS again.
- [ ] **Step 5: Commit** `feat(db): calibrated fleet history and identities v2`

### Task 8: Health summary domain (`app/health.py`, no DB)

**Files:**
- Create: `apps/api/app/health.py`, `apps/api/tests/test_health_summary.py`, `apps/api/tests/fixtures/health_rows.json` (hand-made rows for 2 packs: one LFP, one lead-acid, 10 days)

**Interfaces:** Produces:
```python
DATA_CUTOFF = date(2026, 10, 31)
GUIDANCE = "Commission guidance v3.2 (non-binding)"
class Indicator(BaseModel):
    key: str; label: str; value: float | int | str | None; unit: str | None
    status: Literal["value", "unknown", "not_applicable"]; reason: str | None
    passport_field: bool; passport_ref: str | None
    access_class: Literal["restricted_legitimate_interest", "operational_internal"]
    mapping_status: str | None; calibration_refs: list[str]; labels: list[str]
class HistogramBin(BaseModel): bin_lower: float; bin_upper: float; hours: float
class PackEvent(BaseModel): observed_at: datetime; kind: str; detail: str
class HealthSummary(BaseModel):
    battery_id: str; as_of: date; data_cutoff: date; source_type: Literal["synthetic"] = "synthetic"
    source_id: str; generator_version: str; calibration_version: str; site_id: str | None
    indicators: list[Indicator]; temperature_histogram: list[HistogramBin]; soc_histogram: list[HistogramBin]
    events: list[PackEvent]; not_applicable: list[Indicator]
class ReviewFlag(BaseModel): battery_id: str; rule: str; reason: str
class FleetHealth(BaseModel):
    as_of: date; data_cutoff: date; source_type: Literal["synthetic"] = "synthetic"; triage_version: str = "triage-v1"
    triage_note: str = "Suggested for specialist review — demo thresholds, not safety, warranty or end-of-life limits."
    packs: int; capacity_bands: dict[str, int]; efc_total: float; events_30d: dict[str, int]; review: list[ReviewFlag]
def effective_date(as_of: date | None, today: date) -> date  # min(as_of or today, DATA_CUTOFF)
def summarize(profile: dict, daily: list[dict], hist: list[dict], events: list[dict], meta: dict, as_of: date) -> HealthSummary
def triage(summaries: list[HealthSummary], readiness_gap_ids: set[str], as_of: date) -> list[ReviewFlag]
```
Indicator keys and mapping: `capacity_fade_pct` (4(a)), `power_fade_pct` (4(a), always `unknown`: "Power capability not modelled"), `resistance_increase_pct` (4(a); `unknown` when null), `expected_lifetime` (4(a), `unknown`: "Not modelled in this prototype"), `cycle_count_efc` (4(c)), `negative_events` (4(c), count), `status` (4(c), `"original"`); operational (`passport_field: false`, `operational_internal`): `throughput_kwh_total`, `efc_30d`, `efc_90d`, `opportunity_charge_share`, `temp_mean_30d_c`, `temp_max_30d_c`, `fade_rate_90d_pct`. `labels` on capacity/resistance = distinct `temp_regime` values with share ≥ 1 % of the pack's days, formatted `"<regime> <share>%"`. `calibration_refs`: `["aalborg-forklift-v2","hust-lfp-v2"]` for fade; `["generator_assumption"]` for temperature/events/SoC-derived values. `not_applicable`: one Indicator for 4(b) with the Global-Constraints reason.
Triage rules (`rule` ids): `capacity_below_80` (capacity < 80 %), `fade_rate_p90` (90-day fade rate > fleet P90 among LFP packs), `over_temperature_30d` (≥ 3 over-temperature events in last 30 days), `passport_gaps_at_milestone` (reason: "Passport evidence gaps when assessed at 2027-02-18 (prospective placement scenario)").

- [ ] **Step 1: Failing tests** (fixture-driven): capacity fade = 100 − last capacity_pct ≤ as_of; nothing after `as_of` used (Review Focus 1: as_of before first row → all 4(a)/4(c) indicators `unknown` with "No synthetic history on or before this date"); `effective_date(date(2027,2,18), today)==DATA_CUTOFF` (Review Focus 2); lead-acid capacity/resistance `unknown`, reason "No calibration source for lead-acid", value `None` (Review Focus 3); every indicator has non-empty `calibration_refs`; 4(b) in `not_applicable`; triage returns `passport_gaps_at_milestone` for an id in `readiness_gap_ids`; no string in any model dump contains "compliant", "certified", "safe to operate", "replace".
- [ ] **Step 2:** `(cd apps/api && uv run --locked pytest tests/test_health_summary.py -q)` → FAIL. **Step 3:** Implement. **Step 4:** → PASS.
- [ ] **Step 5: Commit** `feat(api): health summary and triage domain`

### Task 9: Routes, consumers and detail page

**Files:**
- Modify: `apps/api/app/fleet.py` (remove `BenchSnapshot`, bench SQL; `Inspection.bench` → `health: HealthSummary | None`; replace `get_health_summary`; add `history`), `apps/api/app/main.py` (include `fleet_health_router`), `apps/api/app/summary.py` (health section + calibration sources/limitations in draft), `apps/api/app/copilot.py` (tools list name stays `get_health_summary`; no behaviour change otherwise), `apps/api/tests/test_copilot.py` (`bench=None` → `health=None`), `apps/web/app/fleet/api.ts` (types), `apps/web/app/fleet/[id]/page.tsx` (replace "Simulated bench history" section with a plain list of indicators: label, value+unit or status+reason, "Synthetic · calibrated from …" / labels, data cut-off), `scripts/check-demo.sh`
- Create: `apps/api/app/fleet_health.py` (DB loaders + `/api/fleet` router), `apps/api/tests/test_routes_health.py`

**Interfaces:**
- `load_summary(cursor, battery_id: str, as_of: date) -> HealthSummary` (queries `pack_profiles`, `pack_daily` ≤ as_of, histograms for months ≤ as_of, events ≤ as_of, `demo-fleet-v2` source for meta).
- `GET /api/batteries/{id}/health-summary?as_of=` → `HealthSummary` (404 unknown id).
- `GET /api/batteries/{id}/history?from=&to=` → `{battery_id, source_type:"synthetic", data_cutoff, points:[{day, capacity_pct, resistance_pct, efc, temp_mean_c, temp_max_c, soc_min_pct, soc_max_pct}]}`; defaults: last 365 days to cutoff; 422 if `from > to` or span > 366 days (Review Focus 4).
- `GET /api/fleet/health-summary?as_of=` → `FleetHealth`; readiness gaps computed with `assess(..., date(2027,2,18), fields)` statuses in {missing_evidence, invalid}.

- [ ] **Step 1: Failing route tests** with `monkeypatch` on loaders (pattern of `test_copilot.py`): 422 on inverted/oversized history range; health-summary 404 passthrough; fleet endpoint includes BAT-DEMO-024 with rule `passport_gaps_at_milestone` when its fields are the 024 fixture.
- [ ] **Step 2:** Run API tests → FAIL. **Step 3:** Implement. **Step 4:** API tests → all PASS (21 existing + new).
- [ ] **Step 5:** Extend `scripts/check-demo.sh`: `/api/fleet/health-summary` has `packs == 100`, review list contains BAT-DEMO-024, BAT-DEMO-007, BAT-DEMO-013; `/api/batteries/BAT-DEMO-005/health-summary` capacity indicator `unknown`; `/api/batteries/BAT-DEMO-024/health-summary?as_of=2027-02-18` returns `data_cutoff "2026-10-31"`; draft summary contains "aalborg" and "hust" attribution.
- [ ] **Step 6:** `(cd apps/web && npm run lint && npm run typecheck && npm run build)` → pass; `docker compose up --build -d && ./scripts/check-fleet.sh && ./scripts/check-demo.sh` → pass; open `/fleet/BAT-DEMO-024` and `/fleet/BAT-DEMO-005` at 375 px and 1280 px, confirm synthetic labels and unknown reasons render.
- [ ] **Step 7: Commit** `feat: health summary, history and fleet triage endpoints`

### Task 10: Docs and full verification

**Files:** Modify `docs/DATA_SOURCES.md` (calibration sources table with URLs, sha256 pointer, licences, attribution strings, access date; guidance v3.2 entry; generator assumptions pointer to manifest; planted cases), `docs/LIMITATIONS.md` (3 Aalborg cells, cell→pack scaling, 20–35 °C extrapolation, lead-acid uncalibrated, power fade/lifetime not modelled, provisional mapping), `docs/ARCHITECTURE.md` (calibration → generator → seed → migration → API flow; migration runner), `README.md` (re-derive commands: calibrate, generate; Docker required for HUST extraction; ~2 GB downloads), `PLAN.md` (new "Expansion part 1" section + work-log row with actual results).

- [ ] **Step 1:** Write docs.
- [ ] **Step 2:** Full checks, record real output: research tests; API pytest; web lint/typecheck/build; fresh clone into scratch dir → `docker compose up --build -d` with no `downloads/` → `check-fleet.sh` + `check-demo.sh` pass.
- [ ] **Step 3: Commit** `docs: calibrated fleet sources, limitations and plan`
