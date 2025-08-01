#!/bin/bash

# Database export script
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
EXPORT_DIR="database_exports"

# Create export directory
mkdir -p $EXPORT_DIR

# PostgreSQL exports
echo "Exporting PostgreSQL databases..."
pg_dump -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} -d l2_main -f "$EXPORT_DIR/l2_main_$TIMESTAMP.sql"
pg_dump -h ${POSTGRES_HOST:-localhost} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-postgres} -d langtrace -f "$EXPORT_DIR/langtrace_$TIMESTAMP.sql"

# ClickHouse export
echo "Exporting ClickHouse database..."
clickhouse-client --host ${CLICKHOUSE_HOST:-localhost} --port ${CLICKHOUSE_PORT:-9000} --user ${CLICKHOUSE_USER:-default} --password ${CLICKHOUSE_PASSWORD:-} --query "SHOW DATABASES" > "$EXPORT_DIR/clickhouse_databases_$TIMESTAMP.txt"

echo "Database exports completed in $EXPORT_DIR/"