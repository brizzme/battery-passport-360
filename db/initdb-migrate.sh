#!/bin/sh
# Runs once, on the first start with an empty data volume (hosted single-container database).
# The init server listens on the local socket only, so PGHOST must not point elsewhere.
set -eu
unset PGHOST PGPASSWORD
export PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB"
/migrate.sh
