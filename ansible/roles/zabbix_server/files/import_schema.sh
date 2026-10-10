#!/bin/bash
# Run as postgres; never import over an existing schema.
set -eu
export PGHOST=/var/run/postgresql
export PGPORT=5432
export PGUSER=postgres
tables=$(psql -X -d zabbix -At -v ON_ERROR_STOP=1 -c "SELECT count(*) FROM pg_tables WHERE schemaname='public'")
if [ "$tables" = 0 ]; then
    schema_tmp=$(mktemp)
    trap 'rm -f "$schema_tmp"' EXIT
    gzip -dc "$1" > "$schema_tmp"
    PGOPTIONS='-c role=zabbix' psql -X -d zabbix --single-transaction -v ON_ERROR_STOP=1 -f "$schema_tmp" >/dev/null
    echo SCHEMA_IMPORTED
else
    psql -X -d zabbix -At -v ON_ERROR_STOP=1 -c 'SELECT mandatory FROM dbversion' >/dev/null
fi
