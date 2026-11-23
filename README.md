# Battery Passport 360

An independent local prototype for inspecting synthetic industrial pack evidence, exploring measured CALCE cell degradation, and preparing a source-linked investigation draft. Start with the [five-minute walkthrough](docs/DEMO_RUNBOOK.md).

## Run locally

Install Docker with Compose and start its daemon. From the repository root:

```sh
docker compose up --build -d
docker compose ps -a
curl --fail http://127.0.0.1:8000/health
```

Open the [fleet health dashboard](http://127.0.0.1:3000), [API reference](http://127.0.0.1:8000/docs), or [OpenAPI schema](http://127.0.0.1:8000/openapi.json). A healthy stack returns `{"status":"ok","database":"ready"}`. The first build downloads dependencies. All application services run locally without accounts, API keys, or research downloads.

The migration container exits successfully after applying the SQL files. Inspect startup problems with `docker compose logs migrate api web db`. Stop the stack with `docker compose down`. The named PostgreSQL volume persists across restarts. To replay the idempotent migrations on a running database, use `docker compose run --rm migrate`.

Optionally copy `.env.example` to `.env` before the first boot to change ports or the local database password. PostgreSQL initializes its password on first boot.

## Development checks

With uv, Python 3.12 and Node.js 22.13+:

```sh
(cd apps/api && uv run --locked pytest -q)
(cd apps/web && npm ci && npm test && npm run lint && npm run typecheck && npm run build)
```

See [architecture](docs/ARCHITECTURE.md), [data sources](docs/DATA_SOURCES.md), [limitations](docs/LIMITATIONS.md), and the [milestone checklist](PLAN.md).

The fleet API exposes [synthetic battery BAT-DEMO-024](http://127.0.0.1:8000/api/batteries/BAT-DEMO-024). Compose seeds 100 fictional identities during migration. Run `./scripts/check-fleet.sh` against the running stack to check their IDs, capacities, provenance and the detail endpoint.

## Research data

Open [cell research](http://127.0.0.1:3000/research). The fitted report is included. To download the original CALCE archives and enable per-cycle charts on a fresh checkout, run:

```sh
(cd apps/api && uv run --locked --group research python ../../research/prepare.py)
docker compose up --build -d
```

The preparation step verifies four archive hashes, writes cycle records to downloads/research and regenerates the model report. The API reads the cycle files from a read-only mount. Details and limitations are in [the model card](docs/MODEL_CARD.md).

## Calibrated synthetic fleet

The fleet history in db/seed/fleet_v2 is committed, so no download is needed to run it. To re-derive it (about 2 GB of public LFP data; Docker is required for the isolated HUST extraction):

```sh
(cd apps/api && uv run --locked --group research python ../../research/calibrate.py)
(cd apps/api && uv run --locked --group research python ../../research/generate_fleet.py)
(cd apps/api && uv run --locked --group research pytest ../../research/tests -q)
```

Shipping a regenerated seed needs a new migration. The API serves [fleet health](http://127.0.0.1:8000/api/fleet/health-summary), per-pack health summaries and daily history. Sources and limitations are in [data sources](docs/DATA_SOURCES.md) and [limitations](docs/LIMITATIONS.md).

## Cell research model

The research page compares early-cycle life models on 77 measured HUST LFP cells (leave-one-batch-out). Results are committed; to reproduce them (needs the HUST download and Docker for the isolated extraction):

```sh
(cd apps/api && uv run --locked --group research python ../../research/calibrate.py)
(cd apps/api && uv run --locked --group research python ../../research/life_model.py)
(cd apps/api && uv run --locked --group research python ../../research/verify_life.py)
```

## Five-minute local demo

Start at the [fleet health dashboard](http://127.0.0.1:3000); the [PoC summary](http://127.0.0.1:3000/summary) explains the objective, architecture, results and next actions. The [demo runbook](docs/DEMO_RUNBOOK.md) covers fleet health, a pack's health and passport coverage, the evidence assistant, cell research and the downloadable Markdown draft. Every step works from a fresh Compose boot; downloads are only needed to re-derive committed artifacts.

The assistant runs deterministically without credentials. Set `ANTHROPIC_API_KEY` in `.env` (server-side only) to add a Claude briefing (default model `claude-sonnet-5-5`): a short summary and prioritised checks over the already-verified gaps, each citing only retrieved passages. The server validates every field and citation and rejects certifying wording; refusals, errors or invalid output fall back visibly to offline mode. Only synthetic findings, statuses and public reference passages are sent. Independent research verification: `python3 research/verify_life.py` (committed HUST results) and `python3 research/verify.py` (legacy CALCE, after preparation).

Run the full local API smoke check with `./scripts/check-demo.sh`. It covers fleet consistency, real retrieval, unsupported questions, report downloads and research availability.
