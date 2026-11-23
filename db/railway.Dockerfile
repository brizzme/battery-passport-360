# Hosted database (Railway): pgvector Postgres that applies migrations and the synthetic seed on first start.
# Local development keeps using compose.yaml (separate db + migrate services).
FROM pgvector/pgvector:0.8.2-pg16-trixie
# Data in a subdirectory: a freshly mounted volume contains lost+found, which initdb refuses.
ENV PGDATA=/var/lib/postgresql/data/pgdata
COPY migrations /migrations
COPY seed /seed
COPY migrate.sh /migrate.sh
COPY initdb-migrate.sh /docker-entrypoint-initdb.d/10-migrate.sh
RUN chmod +x /migrate.sh /docker-entrypoint-initdb.d/10-migrate.sh
