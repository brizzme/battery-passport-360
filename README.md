# Battery Passport 360

An independent local prototype for inspecting synthetic industrial pack evidence, exploring measured CALCE cell degradation, and preparing a source-linked investigation draft. Start with the [five-minute walkthrough](docs/DEMO_RUNBOOK.md).

## Run locally

Install Docker with Compose and start its daemon. From the repository root:

```sh
docker compose up --build -d
docker compose ps -a
curl --fail http://127.0.0.1:8000/health
```

Open the [workspace](http://127.0.0.1:3000), [API reference](http://127.0.0.1:8000/docs), or [OpenAPI schema](http://127.0.0.1:8000/openapi.json). A healthy stack returns `{"status":"ok","database":"ready"}`. The first build downloads dependencies. All application services run locally without accounts, API keys, or research downloads.

The migration container exits successfully after applying the SQL files. Inspect startup problems with `docker compose logs migrate api web db`. Stop the stack with `docker compose down`. The named PostgreSQL volume persists across restarts. To replay the idempotent migrations on a running database, use `docker compose run --rm migrate`.

Optionally copy `.env.example` to `.env` before the first boot to change ports or the local database password. PostgreSQL initializes its password on first boot.

## Development checks

With uv, Python 3.12 and Node.js 22.13+:

```sh
(cd apps/api && uv run --locked pytest -q)
(cd apps/web && npm ci && npm run lint && npm run typecheck && npm run build)
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

## Five-minute local demo

Start at the [workspace](http://127.0.0.1:3000). The [demo runbook](docs/DEMO_RUNBOOK.md) covers the fleet, the evidence inspector, measured cell research, the evidence assistant and a downloadable Markdown draft. The research preparation command above enables the measured chart. All other demo steps work from a fresh Compose boot.

The assistant runs deterministically without credentials. Optional server-only settings in .env.example configure a chat-completions endpoint to prioritize already verified findings. Only synthetic field IDs and statuses are sent. Provider failures and invalid selections fall back visibly to offline mode. Independent research verification: `python3 research/verify.py` after preparation.

Run the full local API smoke check with `./scripts/check-demo.sh`. It covers fleet consistency, real retrieval, unsupported questions, report downloads and research availability.
