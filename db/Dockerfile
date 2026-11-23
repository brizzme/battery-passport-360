FROM pgvector/pgvector:0.8.2-pg16-trixie
COPY migrations /migrations
COPY seed /seed
COPY migrate.sh /migrate.sh
RUN chmod +x /migrate.sh
