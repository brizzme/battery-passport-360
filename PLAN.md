# Battery Passport 360 — Execution Plan

**Updated:** 2026-11-23  
**Status:** Documentation prepared; implementation not started.  
**References:** [SPEC.md](SPEC.md) · [AGENTS.md](AGENTS.md)

## Milestone overview

| Milestone | Result | Status |
|---|---|---|
| M0 Foundation | Bootable Next.js + FastAPI + PostgreSQL/pgvector with Docker | Not started |
| M1 Passport Inspector | Deterministic synthetic fleet + versioned readiness rules + usable UI | Not started |
| M2 Battery research ML | Actually parsed public cell data + real held-out model metrics | Not started |
| M3 Evidence-grounded copilot | Retrieval, citations, allowlisted backend tools, labeled offline fallback | Not started |
| M4 Showcase | 5-minute walkthrough, draft report, test evidence, optional private hosting | Not started |

## M0 — Foundation (start here)
- [ ] Inspect repo and existing README; do not overwrite unrelated changes.
- [ ] Scaffold apps/web: Next.js TypeScript App Router with accessible responsive dashboard shell.
- [ ] Scaffold apps/api: FastAPI, Pydantic validation, typed settings, GET /health and /docs.
- [ ] Add PostgreSQL/pgvector with Docker Compose, migrations, health checks and named volume.
- [ ] Add .env.example, .gitignore, dependency lockfiles and reproducible commands.
- [ ] Document local run/test steps in README; create docs/ARCHITECTURE.md, docs/DATA_SOURCES.md, docs/LIMITATIONS.md.
- [ ] Run docker compose up --build, API pytest and web lint/typecheck/build; record actual output.

**M0 exit gate:** Fresh clone boots locally without API key, real research dataset or external cloud account.

## M1 — Passport-ready data integration
- [ ] Model synthetic batteries, passport fields, provenance, assignments, charging sessions and service events.
- [ ] Create deterministic seeded 100-fictional-battery fleet with consistent foreign keys and units.
- [ ] Include BAT-DEMO-024 with documented missing/invalid evidence; keep additional corrupt input records in separate validation fixture.
- [ ] Implement limited, versioned, legally sourced rule subset with battery-category/capacity and effective-date checks.
- [ ] Implement statuses: present, missing_evidence, invalid, not_applicable, not_yet_effective, unknown.
- [ ] Expose GET /api/batteries, GET /api/batteries/{id}, GET /api/batteries/{id}/passport-readiness?as_of=.
- [ ] Build fleet search/filter, battery detail and rule/evidence inspector with date selector (today and 2027-02-18).
- [ ] Show SIMULATED / MEASURED / DERIVED provenance; show informational readiness, not “EU compliant.”
- [ ] Test deterministic generation, invalid/missing/not-applicable/unknown/date cases and BAT-DEMO-024 fixture.
- [ ] Run full backend/frontend checks and update documentation.

**M1 exit gate:** Review BAT-DEMO-024 end to end and identify exact gaps with referenced sources. No ML/LLM claims.

## M2 — Measured battery health
- [ ] Check accessible CALCE or MATR files, usage rights, schema, download size and attribution.
- [ ] Write data manifest with source URL, date, file/checksum, units, transformations, license.
- [ ] Ingest real experimental cell-level cycling records with validation.
- [ ] Plot measured capacity vs cycle and compare baseline with real fitted model.
- [ ] Split by whole battery cell, prevent leakage; compute MAE/RMSE and persist experiment output.
- [ ] Show model card, train/test cell counts, target and limitations; no forklift-pack prediction claims.
- [ ] If unavailable, mark blocked rather than generate fake ML results.

**M2 exit gate:** Reproducible measured-data metrics shown, or explicitly blocked.

## M3 — RAG + decision copilot
- [ ] Ingest permitted, versioned EU/technical reference passages and store exact sections, dates and URLs.
- [ ] Index vector representations in pgvector, implement retrieval and cite actual matching passages.
- [ ] Add read-only tools: get_battery, check_readiness, get_health_summary, search_docs, draft_inspection_summary.
- [ ] Add optional LLM adapter with timeouts/cost bounds; a labeled offline deterministic mode must work.
- [ ] Implement conversational evidence + tool trace UI.
- [ ] Test no-evidence, unknown-battery, injected instructions and safety/compliance boundary requests.

**M3 exit gate:** Answer the example BAT-DEMO-024 question with genuine retrieval/tool evidence and uncertainty.

## M4 — Delivery and demo
- [ ] Generate non-certifying draft investigation summary with provenance and uncertainties.
- [ ] Check responsive/accessibility layout, browser routes, setup, security and tests.
- [ ] Prepare docs/DEMO_RUNBOOK.md: five-minute investigation.
- [ ] Document roadmap/business-value hypotheses without inventing ROI.
- [ ] Only when authorized: password-protected HTTPS German-region deployment with appropriate access controls.

**M4 exit gate:** Product demonstration is usable, honest, traceable and repeatable.

## Decision backlog (not blockers for M0)
- CALCE vs MATR dataset after verifying file access and permissions.
- OpenAI/other LLM provider at M3; no API key at M0.
- UI component library and charting package after compatibility review.
- Cloud hosting after local technical validation.
- Passport rule coverage expansion only after source-by-source verification.

## Work log
| Date | Milestone | Actual work | Tested evidence | Blockers |
|---|---|---|---|---|
| 2026-11-23 | Docs | SPEC, AGENTS and PLAN authored | Implementation not yet tested | None |

## First Codex prompt
Read `AGENTS.md`, `SPEC.md` and `PLAN.md` completely. Implement **M0 only**: scaffold Next.js + FastAPI + PostgreSQL/pgvector with Docker Compose, a responsive UI shell, basic API/health route and tests. Do not implement ML, RAG, deployment or invent any real research-data claims. Run the app and quality checks, document exact results, and update PLAN.md. Proceed to M1 only if M0 works and passes its gates.