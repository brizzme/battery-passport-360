# Passport Data-Point Catalogue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace BP-01..05 with an engine that evaluates every data point of Commission guidance v3.2 from a committed, source-tested catalogue, with typed synthetic evidence, guidance passages for the copilot and a coverage view on the pack page.

**Architecture:** `research/guidance/` pins and parses the PDF into `apps/api/app/artifacts/passport-catalogue.json` (+ reviewed `overrides.json`). `readiness.py` loads it and applies the fixed precedence from the spec. Migration 006 retypes `passport_fields`, seeds evidence and indexes guidance rows. Consumers (fleet, fleet_health, copilot, summary, web) adapt.

**Tech Stack:** Python 3.12, `pypdf` (pinned, research group), FastAPI/Pydantic, PostgreSQL, Next.js.

**Spec:** [docs/superpowers/specs/2026-11-23-passport-catalogue-design.md](../specs/2026-11-23-passport-catalogue-design.md) — its "Calls made after the builder check" are binding.

## Global Constraints
- Guidance: v3.2, 19 Oct 2026, CC BY 4.0, non-binding; URL `https://single-market-economy.ec.europa.eu/document/download/cd1e5e6c-4a4a-4b99-995a-49eb6916187e_en`; accessed 2026-11-23.
- Statuses: present, missing_evidence, invalid, not_applicable, not_yet_effective, unknown. Gap = missing_evidence | invalid only.
- Article 77 start 2027-02-18; industrial ≤ 2 kWh → not_applicable; DP 19 unknown from 2027-08-18; recycled content earliest 2028-08-18 then unknown.
- Rule ids `DP-<n>` (`DP-38a`, `DP-38b`); catalogue version `catalogue-v3.2-1`.
- Evidence source `demo-inspection-v3` (synthetic). Planted gaps only: BAT-DEMO-024 (DP-12 missing ref, DP-11 invalid "unit absent"), BAT-DEMO-031 (DP-43 missing), BAT-DEMO-058 (DP-27 invalid), BAT-DEMO-077 (DP-14 missing).
- Never "compliant"/"certified"; guidance always labelled non-binding.
- Commits per task, `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`, branch `feat/passport-catalogue`.

## Review Focus
1. PDF row whose name is garbled → override applied, test proves the cleaned name. (Task 1)
2. as_of 2027-08-18 and 2028-08-18 boundaries → DP 19 / recycled rows switch exactly on those days. (Task 2)
3. Lead-acid vs LFP pack → DP 42 mandatory vs not_applicable. (Task 2)
4. Number evidence with SI multiple ("0.05 kWh" vs Wh unit) → present; wrong dimension → invalid. (Task 2)
5. Re-running migrate on an existing volume → 006 applies once; passport fields not duplicated. (Task 3)

---

### Task 1: Pin and parse the guidance into the catalogue
**Files:** Create `research/guidance/parse.py`, `research/guidance/overrides.json`, `research/guidance.sha256`, `research/tests/test_catalogue.py`; generated `apps/api/app/artifacts/passport-catalogue.json`; modify `apps/api/pyproject.toml` (+ `pypdf` pinned in research group, `uv lock`).
**Interfaces:** catalogue JSON `{version, source:{url,sha256,accessed,licence,title}, rows:[{id:"DP-11", dp:11, sub:null|"a"|"b", name, unit|null, value_type:"number|link|yes_no|month_year|code_list|free_text", legal_ref, access:"public|restricted_legitimate_interest|restricted_authorities", guidance:{ev,lmt,industrial} (verbatim cell text), kind:{ev,lmt,industrial} (normalised)}]}`. Kinds: mandatory, not_filled_repetition, not_filled_until_act, in_use, some_industrial, if_applicable, optional, ev_only, stationary_only, rechargeable_only, chemistry_conditional.
- [ ] Download PDF, pin sha256; tests first for known rows: DP-11 capacity Ah Annex VI A(6) public mandatory; DP-12 chemistry; DP-25 rated capacity industrial `not_filled_repetition` (repeats 11); DP-33 industrial not_filled (EV only); DP-34 temperature range mandatory; DP-38a/38b; DP-43 DoC link; DP-52 capacity fade restricted, `rechargeable_only`/in-use; DP-62 stationary_only; DP-68 in_use; row count = rows in PDF.
- [ ] Run → FAIL; implement parser + overrides; run → PASS; commit.

### Task 2: Catalogue engine
**Files:** Rewrite `apps/api/app/readiness.py`; rewrite `apps/api/tests/test_readiness.py` (all old scenarios kept on catalogue rows).
**Interfaces:** `Evidence` gains `unit: str | None`; `Result` fields: rule_id, dp, field (=rule_id), label, section(legal_ref), guidance_ref ("Guidance v3.2, data point N"), access, effective_from, version, source_url, status, reason, evidence, as_of, source_type "derived". `assess(category, kwh, chemistry, when, fields) -> list[Result]`; `validate(row, evidence) -> (Status, reason)`; `GAPS = {missing_evidence, invalid}`; `coverage(results) -> dict[status,int]`.
- [ ] Tests first (precedence calls 1–10, boundaries, DP 42, SI multiples, link/yes_no/month_year validation, future evidence excluded, ≤2 kWh, unknown category); FAIL → implement → PASS; commit.

### Task 3: Migration 006 — typed evidence, seed, guidance passages
**Files:** Create `db/migrations/006_passport_catalogue.sql` (generated seed rows from a script `research/guidance/seed_evidence.py` → `db/seed/passport_v3/fields.csv` committed, deterministic); modify `scripts/check-fleet.sh`.
- `passport_fields`: add `unit text`; rename codes chemistry→DP-12, rated_ah→DP-11 (unit Ah), nominal_v→DP-27 (unit V); insert DP rows for every public industrial-mandatory field (+ DP-42 for lead-acid) under `demo-inspection-v3`; planted gaps per Global Constraints.
- `document_chunks`: one `GUID-DP-*` passage per catalogue row (title, section "Data point N · legal_ref", version "Guidance v3.2, 19 Oct 2026", URL, terms from name) — CSV from catalogue.
- [ ] check-fleet expectations first (024 gaps DP-11 invalid + DP-12 missing; `?status=invalid&as_of=2027-02-18` total 2; packs with gaps = 4); run → FAIL; migrate → PASS on existing volume (006 applies once) and a throwaway fresh project; commit.

### Task 4: API consumers
**Files:** `fleet.py` (assess with chemistry; `Inspection.coverage`), `fleet_health.py` (gaps via `GAPS`), `copilot.py` (gaps = GAPS; citations `GUID-<rule_id>` + EU-77 via retrieval of the row's terms), `summary.py` (coverage counts + every gap + unresolved count), tests (`test_copilot.py`, route tests).
- [ ] Tests first (copilot finds exactly 024's two gaps with GUID citations; summary lists gaps not all rows; fleet gaps set = 4 planted packs); FAIL → implement → PASS; `check-demo.sh` updated and passing; commit.

### Task 5: Pack page passport section
**Files:** `apps/web/app/fleet/api.ts` (types), `apps/web/components/PassportCoverage.tsx`, `apps/web/app/fleet/[id]/page.tsx`, `apps/web/app/globals.css` (within DESIGN.md system).
- Coverage strip (counts per status, hatch for unknown/not-yet-effective), groups: Gaps (open), Present, Unresolved, Not yet effective, Not applicable (collapsed `<details>`); each row: data point, name, status, reason, evidence + unit, access, links (guidance, EUR-Lex).
- [ ] lint/typecheck/build; screenshots 1440/390 for BAT-DEMO-024 and -005; commit.

### Task 6: Docs, checks, reviews
- [ ] DATA_SOURCES, LIMITATIONS, ARCHITECTURE, PLAN, README; API + research + web tests; check-fleet/check-demo; clean-clone boot; whole-branch code review (opus) and fixes; commit; PR.
