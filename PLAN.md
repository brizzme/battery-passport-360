# Battery Passport 360 — Execution Plan

**Updated:** 2026-11-23  
**Status:** M0–M4 local demo complete. The Compose stack and measured cycle files are available on this workstation.
**References:** [SPEC.md](SPEC.md) · [AGENTS.md](AGENTS.md)

## Milestone overview

| Milestone | Result | Status |
|---|---|---|
| M0 Foundation | Bootable Next.js + FastAPI + PostgreSQL/pgvector with Docker | Complete (local) |
| M1 Passport Inspector | Deterministic synthetic fleet + versioned readiness rules + usable UI | Complete (local) |
| M2 Battery research ML | Actually parsed public cell data + real held-out model metrics | Complete (local) |
| M3 Evidence-grounded copilot | Retrieval, citations, allowlisted backend tools, labeled offline fallback | Complete (local) |
| M4 Showcase | 5-minute walkthrough, draft report, test evidence, optional private hosting | Local demo complete |

## M0 — Foundation (start here)
- [x] Inspect repo and existing README; do not overwrite unrelated changes.
- [x] Scaffold apps/web: Next.js TypeScript App Router with accessible responsive dashboard shell.
- [x] Scaffold apps/api: FastAPI, Pydantic validation, typed settings, GET /health and /docs.
- [x] Add PostgreSQL/pgvector with Docker Compose, migrations, health checks and named volume.
- [x] Add .env.example, .gitignore, dependency lockfiles and reproducible commands.
- [x] Document local run/test steps in README; create docs/ARCHITECTURE.md, docs/DATA_SOURCES.md, docs/LIMITATIONS.md.
- [x] Run docker compose up --build, API pytest and web lint/typecheck/build; record actual output.

**M0 exit gate:** Fresh clone boots locally without API key, real research dataset or external cloud account.

## M1 — Passport-ready data integration
- [x] First slice: seed 100 synthetic identities with source metadata and expose the read-only detail endpoint.
- [x] Model synthetic batteries, passport fields, provenance, assignments, charging sessions and service events.
- [x] Create deterministic seeded 100-fictional-battery fleet with consistent foreign keys and units.
- [x] Include BAT-DEMO-024 with documented missing/invalid evidence; keep additional corrupt input records in separate validation fixture.
- [x] Implement limited, versioned, legally sourced rule subset with battery-category/capacity and effective-date checks.
- [x] Implement statuses: present, missing_evidence, invalid, not_applicable, not_yet_effective, unknown.
- [x] Expose GET /api/batteries, GET /api/batteries/{id}, GET /api/batteries/{id}/passport-readiness?as_of=.
- [x] Build fleet search/filter, battery detail and rule/evidence inspector with date selector (today and 2027-02-18).
- [x] Show SIMULATED / MEASURED / DERIVED provenance; show informational readiness, not “EU compliant.”
- [x] Test deterministic generation, invalid/missing/not-applicable/unknown/date cases and BAT-DEMO-024 fixture.
- [x] Run full backend/frontend checks and update documentation.

**M1 exit gate:** Review BAT-DEMO-024 end to end and identify exact gaps with referenced sources. No ML/LLM claims.

## M2 — Measured battery health
- [x] Check accessible CALCE or MATR files, usage rights, schema, download size and attribution.
- [x] Write data manifest with source URL, date, file/checksum, units, transformations, license.
- [x] Ingest real experimental cell-level cycling records with validation.
- [x] Plot measured capacity vs cycle and compare baseline with real fitted model.
- [x] Split by whole battery cell, prevent leakage; compute MAE/RMSE and persist experiment output.
- [x] Show model card, train/test cell counts, target and limitations; no forklift-pack prediction claims.
- Source accessible; blocked fallback unnecessary.

**M2 exit gate:** Reproducible measured-data metrics shown, or explicitly blocked.

## M3 — RAG + decision copilot
- [x] Ingest permitted, versioned EU/technical reference passages and store exact sections, dates and URLs.
- [x] Index vector representations in pgvector, implement retrieval and cite actual matching passages.
- [x] Add read-only tools: get_battery, check_readiness, get_health_summary, search_docs, draft_inspection_summary.
- [x] Add optional LLM adapter with timeouts/cost bounds; a labeled offline deterministic mode must work.
- [x] Implement conversational evidence + tool trace UI.
- [x] Test no-evidence, unknown-battery, injected instructions and safety/compliance boundary requests.

**M3 exit gate:** Answer the example BAT-DEMO-024 question with genuine retrieval/tool evidence and uncertainty.

## M4 — Delivery and demo
- [x] Generate non-certifying draft investigation summary with provenance and uncertainties.
- [x] Check responsive/accessibility layout, browser routes, setup, security and tests.
- [x] Prepare docs/DEMO_RUNBOOK.md: five-minute investigation.
- [x] Document roadmap/business-value hypotheses without inventing ROI.
- Optional private hosting deferred by scope. The verified deployment binds to localhost.

**M4 exit gate:** Product demonstration is usable, honest, traceable and repeatable.

## Expansion part 1 — Calibrated synthetic fleet and health summary
Design: docs/superpowers/specs/2026-11-23-calibrated-fleet-design.md · Plan: docs/superpowers/plans/2026-11-23-calibrated-fleet.md
- [x] Migration runner skips applied files.
- [x] Calibration from pinned HUST and Aalborg LFP data (CC BY 4.0), HUST pickles opened only in an isolated container.
- [x] Deterministic 24-month synthetic fleet seed with planted cases; byte-identical regeneration tested.
- [x] Migration 005: identities v2, history tables, seed load.
- [x] Health summary, history and fleet triage API; draft summary and pack page show labelled health.
- [x] Part 2: fleet health dashboard (see below).
- [ ] Part 3: rule refresh against Commission guidance v3.2. Part 4: HUST-based research model.

## Expansion part 2 — Fleet health dashboard
Design: docs/superpowers/specs/2026-11-23-fleet-dashboard-design.md · Plan: docs/superpowers/plans/2026-11-23-fleet-dashboard.md · Direction: Ulm signage program (.impeccable/surfaces/apps-web-app-page-tsx.md)
- [x] Shared shell, tokens, self-hosted Barlow; `/` dashboard (KPI strip, review table, fleet floor, capacity bands, scatter, temperature-regime strip, provenance).
- [x] Pack page charts (capacity history, temperature and SoC histograms, idle/event timeline) with model-floor labelling.
- [x] Colour-blind-validated site palette; Impeccable finish review (3 rounds) and code review fixes.

## Follow-up decisions
- Expand rule coverage after verifying additional sources and amendments.
- Validate research results on more cells and independent batches.
- Consider private hosting only if a remote demo is needed.

## Work log
| Date | Milestone | Actual work | Tested evidence | Blockers |
|---|---|---|---|---|
| 2026-11-23 | Docs | SPEC, AGENTS and PLAN authored | Implementation not yet tested | None |
| 2026-11-23 | M0 | Next.js shell, FastAPI health endpoint, PostgreSQL 16 with pgvector 0.8.2. Packaged migration SQL in the migration image after the first temporary-clone bind mount failed. | uv run --locked pytest -q: 2 passed. npm run lint, npm run typecheck, npm run build passed. docker compose up --build -d from a fresh local Git snapshot and empty volume: migration exited 0, /health returned 200, /docs and /openapi.json reachable, workspace displayed Services online. Browser checked keyboard skip link, health link and layout at 375 and 1280 px. | Verified in Colima. Managed Cloud runtime unavailable. |
| 2026-11-23 | M1 slice | Added the deterministic identity seed, source join and typed battery detail response. | ./scripts/check-fleet.sh passed before and after docker compose run --rm migrate. Verified 100 identities, capacities, source type, full BAT-DEMO-024 response and HTTP 404 for BAT-DEMO-101. | Evidence fields, operational records, rules and fleet UI remain open. |
| 2026-11-23 | M1 | Completed fleet search, bench fixtures and five sourced readiness checks with date selection. | 14 pytest cases passed, lint/typecheck/build passed, inspector browser flow passed at 375 and 1280 px, clean clone and fleet SQL/API checks passed. | Illustrative prospective placement scenario only. |
| 2026-11-23 | M2 | Parsed four checksum-verified CALCE archives, deduplicated overlapping exports, fitted OLS on three whole cells and evaluated on CS2_38. | research/verify.py reproduced metrics on 1,025 held-out observations. API served all four cell series and the local research page rendered. | One test cell; raw and per-cycle data local only. |
| 2026-11-23 | M3 | Indexed seven public OJ passages in pgvector. Bounded read-only queries, attributed excerpts, explicit deterministic offline mode and optional field prioritization. | Actual retrieval returned EU-77, EU-XIII-B and EU-XIII-G for BAT-DEMO-024. Tested unsupported questions, untrusted passage handling, abstention and provider response validation. | No live LLM provider exercised. |
| 2026-11-23 | M4 | Downloadable dated investigation draft, five-minute walkthrough, data dictionary, limitations and model card. | 21 pytest tests passed (one test-client deprecation warning); frontend lint, typecheck and production build passed; clean clone and fresh volume passed docker compose up --build -d and scripts/check-demo.sh. Browser tests at 375 and 1280 px verified search, assessment date, cited answer, abstention, measured chart and draft download. | Local only. Fresh workstations run research preparation for per-cycle charts. |
| 2026-11-23 | Expansion part 1 | Calibrated synthetic fleet: HUST (77 cells, median life 1,706 cycles) and Aalborg (3 cells, Arrhenius Ea/R 2,581 K) calibration; 100 packs × 24 months seed; migration runner and 005; health, history and fleet triage API; labelled health on pack page and draft. | Research tests 51 passed; API pytest 40 passed (1 test-client deprecation warning); web lint, typecheck, build passed; existing volume applied 005 once then skipped; fresh clone with no downloads applied 001–005 and passed check-fleet.sh and check-demo.sh; pack pages checked at 375 and 1280 px. | Dashboard visuals are part 2. Most simulated days lie below the calibrated temperature range (labelled). |
| 2026-11-23 | Expansion part 2 | Ulm-signage fleet health dashboard and charted pack page; API adds pack points, regime share and versions to fleet health. | API pytest 46 passed; web Vitest 22 passed; lint, typecheck, build passed; palette validator pass after re-step; impeccable detect no findings; screenshots at 1440/768/390; finish reviewer rounds 1–2 resolved all 8 material fixes, round-3 regressions fixed and verified by screenshot; code review: 4 important fixed, 10 minor deferred. | Footer API links assume localhost; minor a11y items deferred. |
