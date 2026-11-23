FROM pgvector/pgvector:0.8.2-pg16-trixie
COPY migrations /migrations
COPY migrate.sh /migrate.sh
RUN chmod +x /migrate.sh
