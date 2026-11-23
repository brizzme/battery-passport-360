# Sharing the demo by link (own server)

For the managed option, see [DEPLOY_RAILWAY.md](DEPLOY_RAILWAY.md). The web app also has its own optional sign-in (`DEMO_USER`, `DEMO_PASSWORD`), used on Railway; with Caddy below it is not needed.

Goal: give a small audience a private HTTPS link to the PoC. The data is synthetic; nothing here is meant for real customer data.

## What you need
- A small Linux server in an EU region with Docker and the Compose plugin (2 vCPU / 4 GB RAM is comfortable; the first build needs the most memory).
- A DNS name pointing at the server, for example `bp360.example.com` (an A record to the server's IP).
- Ports 80 and 443 open. Nothing else needs to be reachable: the database and API stay on the private Docker network.

## Steps
1. Clone the repository on the server and copy `.env.example` to `.env`.
2. Create the sign-in password hash (bcrypt):
   ```bash
   docker run --rm caddy:2.10.2-alpine caddy hash-password --plaintext 'choose-a-long-password'
   ```
3. In `.env` set (keep the single quotes around the hash, it contains `$`):
   ```
   DOMAIN=bp360.example.com
   DEMO_USER=demo
   DEMO_PASSWORD_HASH='$2a$14$...'
   ANTHROPIC_API_KEY=          # optional: enables the LLM chat; leave empty for offline mode
   POSTGRES_PASSWORD=          # change from the example value
   ```
4. Start:
   ```bash
   docker compose -f compose.yaml -f compose.prod.yaml up -d --build
   ```
   Caddy obtains the HTTPS certificate on first request.
5. Check: `https://bp360.example.com` asks for the sign-in, then shows the PoC summary. Run `./scripts/check-demo.sh` on the server for the API checks.
6. Send the link `https://bp360.example.com` and the credentials through separate channels.

## What this setup provides
- HTTPS with automatic certificates, HSTS, `noindex`, no framing, 64 KB request-body limit.
- One shared sign-in (HTTP basic auth) in front of every page and API route.
- Access log on Caddy's stdout (`docker compose logs caddy`).
- LLM calls capped at `LLM_CALLS_PER_MINUTE` (default 20) across the app; above that the assistant falls back visibly to offline mode.

## What it does not provide
- Per-user accounts, roles or restricted passport access classes. Acceptable only because every record is synthetic and restricted data points are shown as unknown, never filled.
- General request rate limiting beyond the LLM cap. Keep the audience small and the password private.
- A privacy review for real data. Do not load real customer, employee or manufacturer data into this setup.

## Updating and stopping
```bash
git pull && docker compose -f compose.yaml -f compose.prod.yaml up -d --build
docker compose -f compose.yaml -f compose.prod.yaml down      # stop; add -v only to wipe the database
```
