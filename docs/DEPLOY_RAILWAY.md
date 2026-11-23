# Deploying the demo on Railway

Result: a private HTTPS link such as `https://bp360-web-production.up.railway.app`, behind one sign-in. All data is synthetic; do not load real customer, employee or manufacturer data.

Three Railway services, all built from this repository:

| Service | Root directory | Public? | What it runs |
|---|---|---|---|
| `db` | `/db` | no | pgvector Postgres; applies migrations and the synthetic seed on first start (`db/railway.Dockerfile`) |
| `api` | `/apps/api` | no | FastAPI; reached by the web app over Railway's private network |
| `web` | `/apps/web` | **yes** | Next.js; the only public address, with the sign-in |

Name the services exactly `db`, `api` and `web`: the variables below refer to them by name.

## Before you start
- A Railway account connected to the GitHub account that can read this repository.
- The code you want to show on the branch Railway deploys. Until the open pull requests are merged into `main`, set each service's source branch to `feat/poc-summary` (Settings → Source).
- A long random password for the database and another for the demo sign-in (for example `openssl rand -base64 24`).

## 1. Database (`db`)
1. Railway → **New Project** → **Deploy from GitHub repo** → pick this repository. Rename the new service to `db` (Settings → Service name).
2. Settings → **Root Directory**: `/db`.
3. Variables:
   ```
   RAILWAY_DOCKERFILE_PATH=railway.Dockerfile
   POSTGRES_USER=passport
   POSTGRES_DB=passport
   POSTGRES_PASSWORD=<long random password>
   ```
4. Add a **Volume** to the service (right-click the service, or Command palette → "Volume"), mount path `/var/lib/postgresql/data`.
5. Do **not** generate a public domain.
6. Deploy. The logs should show `apply 001_foundation` … `apply 007_catalogue_seed_fixes`, then `PostgreSQL init process complete` and `database system is ready to accept connections`.

## 2. API (`api`)
1. In the project: **+ New** → **GitHub Repo** → same repository. Rename to `api`.
2. Settings → **Root Directory**: `/apps/api`. Settings → **Healthcheck Path**: `/health`.
3. Variables:
   ```
   PORT=8000
   PGHOST=${{db.RAILWAY_PRIVATE_DOMAIN}}
   PGUSER=passport
   PGDATABASE=passport
   PGPASSWORD=${{db.POSTGRES_PASSWORD}}
   LLM_CALLS_PER_MINUTE=20
   ANTHROPIC_API_KEY=          # optional: switches on the LLM chat; leave out for offline mode
   ```
   Leave `HOST` unset (defaults to `0.0.0.0`). Set `HOST=::` only in an older Railway environment whose private network is IPv6-only; it then listens on IPv6 only, which can also fail Railway's health check.
4. Do **not** generate a public domain. Deploy; the logs end with `Uvicorn running on http://0.0.0.0:8000`.

## 3. Web (`web`)
1. **+ New** → **GitHub Repo** → same repository. Rename to `web`.
2. Settings → **Root Directory**: `/apps/web`. Settings → **Healthcheck Path**: `/health`.
3. Variables:
   ```
   PORT=3000
   API_BASE_URL=http://${{api.RAILWAY_PRIVATE_DOMAIN}}:8000
   DEMO_USER=<user name to share>        # optional
   DEMO_PASSWORD=<long random password>  # optional
   CONTACT_NAME=...                      # optional contact panel on the PoC summary (home page)
   CONTACT_EMAIL=...
   CONTACT_PHONE=...
   ```
   With `DEMO_USER` and `DEMO_PASSWORD` set, every page and API route asks for the sign-in (only `/health` and `/robots.txt` stay open). Leave both out for an open link: anyone with the URL can view the synthetic demo; pages are marked noindex and LLM calls stay capped by `LLM_CALLS_PER_MINUTE`.
4. Settings → Networking → **Generate Domain** (target port `3000`). Deploy.

## 4. Check it
1. Open `https://<web domain>`. The browser asks for the sign-in; after it, the PoC summary shows 100 packs, 14 suggested for review and 72 data points.
2. Open `/fleet/BAT-DEMO-024?as_of=2027-02-18`, ask the assistant "What is missing?", and download the draft.
3. Send the link `https://<web domain>` and the sign-in through separate channels.

## Troubleshooting
| Symptom | Likely cause |
|---|---|
| Pages load but figures show "–" | The web app cannot reach the API: check `API_BASE_URL` and that `api` is running. |
| `api` health check fails ("service unavailable") | `HOST=::` set (remove it), or `/health` returns 503 because the database is unreachable: check that `PGHOST`/`PGPASSWORD` resolve (service must be named `db`). |
| `api` logs show connection errors | `PGHOST` / `PGPASSWORD` references, or `db` not yet ready. Redeploy `api` after `db` is up. |
| `db` fails with "directory not empty" | The image sets `PGDATA` to a subfolder; make sure `RAILWAY_DOCKERFILE_PATH=railway.Dockerfile` is set so that image is used. |
| No sign-in prompt | `DEMO_USER` or `DEMO_PASSWORD` missing on `web`. |
| Assistant says offline | Expected without `ANTHROPIC_API_KEY`; with a key, "rate limit reached" means more than `LLM_CALLS_PER_MINUTE` calls in a minute. |

## Updating and costs
- Every push to the deployed branch rebuilds the services. To rebuild only what changed, set **Watch Paths** per service (`/db/**`, `/apps/api/**`, `/apps/web/**`).
- The seed is applied only on the database's first start. If a new migration is added, delete the `db` volume and redeploy `db` to recreate the synthetic data (nothing else is stored).
- Railway bills by usage on its paid plan after trial credits; check current pricing. To pause the demo, remove the web domain or scale the services down.

## What this setup does not provide
One shared sign-in, not per-user accounts or roles; no restricted passport access classes; no general rate limiting beyond the LLM cap; no privacy review for real data. Acceptable for a small audience viewing synthetic data only (see docs/LIMITATIONS.md).
