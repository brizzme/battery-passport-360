# Local architecture

The Next.js App Router serves the workspace on port 3000. Its server fetches FastAPI on the private Compose network for each page request. The page reports a connection failure if the health check times out or fails. The browser can also open the API reference directly via the loopback port.

FastAPI exposes its Pydantic health response at GET /health. The endpoint returns HTTP 200 when a PostgreSQL connection succeeds and the vector extension exists, or HTTP 503 otherwise. GET /openapi.json describes the contract.

Compose starts PostgreSQL 16 with a named volume, waits for readiness, and runs db/migrate.sh. The runner applies numbered SQL files in lexical order with psql configured to stop on error, and skips any file whose version is already recorded in schema_migrations. Each migration must be transactional. Seed-data changes ship as a new migration rather than an edit to an applied one. The foundation migration enables pgvector and records its version. The API starts after successful migration and the web service starts after API readiness. Only the API and web ports are published, on loopback.

Python dependencies resolve through uv.lock and frontend dependencies through package-lock.json. Fonts are packaged with the web application.

Migration 002 creates the first two fleet tables and seeds fictional identities. GET /api/batteries/{battery_id} joins the identity to its source and returns HTTP 404 for an unknown ID. This first M1 slice is available through the API reference.

The inspector reads linked model-sheet fields and the synthetic pack health summary, then evaluates five versioned Python rules. The fleet status filter uses the same evaluator as the inspector. Reports and offline assistant findings therefore use the same date, scope checks, field values and evidence references.

The CALCE pipeline runs outside the server and emits an aggregate model artifact plus ignored local observation files. The research router has its own cell namespace with no pack identifier mapping. Empty local research storage leaves the aggregate report available.

The reference index stores seven public excerpts in PostgreSQL with section, version, access class and 256-dimensional term-hash vectors. Read-only queries rank candidates by cosine distance and check for the expected section before citing it. The corpus is small, so exact vector search is sufficient. This is lexical retrieval with curated field terms. The assistant accepts bounded investigation questions, uses fixed read-only functions, and returns a trace of its lookup operations. Retrieved text is data. The optional provider can reorder known fields only. The Markdown draft is generated on demand from the same inspector response.

## Calibrated synthetic fleet

Two offline steps produce committed artifacts, so a fresh clone boots without downloads:

1. research/calibrate.py downloads the pinned HUST and Aalborg LFP files (checksums in research/calibration.sha256), opens the HUST pickles only inside a network-less, read-only container (research/hust_extract), fits the parameters and writes apps/api/app/artifacts/fleet-calibration.json.
2. research/generate_fleet.py turns that file and a fixed seed into db/seed/fleet_v2 (gzip CSV plus manifest). Regeneration is byte-identical.

Migration 005 loads the seed into pack_profiles, pack_daily, pack_monthly_histograms, pack_events, fleet_sites and fleet_seed_manifest, and moves identities to demo-identities-v2. apps/api/app/health.py turns rows into labelled indicators and demo triage flags without database access. apps/api/app/fleet_health.py loads rows and serves GET /api/fleet/health-summary. The fleet router serves GET /api/batteries/{id}/health-summary and GET /api/batteries/{id}/history. Values after the 2026-10-31 data cut-off are never extrapolated forward.
