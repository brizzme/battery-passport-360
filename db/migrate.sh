#!/bin/sh
# Apply each migration once; versions are recorded in schema_migrations by each file.
set -eu
q() { psql -v ON_ERROR_STOP=1 -tAc "$1"; }
for file in /migrations/*.sql; do
    version=$(basename "$file" .sql)
    applied=""
    if [ "$(q "SELECT 1 FROM pg_tables WHERE tablename='schema_migrations'")" = "1" ]; then
        applied=$(q "SELECT 1 FROM schema_migrations WHERE version='$version'")
    fi
    if [ "$applied" = "1" ]; then
        echo "skip $version"
    else
        echo "apply $version"
        psql -q -v ON_ERROR_STOP=1 -f "$file"
    fi
done
