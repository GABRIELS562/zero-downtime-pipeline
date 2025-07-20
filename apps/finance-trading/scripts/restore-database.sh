#!/bin/bash
# Database Restore Script

set -euo pipefail

BACKUP_FILE="$1"
ENVIRONMENT="${2:-development}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file> [environment]"
    exit 1
fi

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Restoring database from $BACKUP_FILE to $ENVIRONMENT environment..."

if [ "$ENVIRONMENT" = "development" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
fi

# Stop application to prevent connections
docker-compose -f "$COMPOSE_FILE" stop app

# Drop and recreate database
docker-compose -f "$COMPOSE_FILE" exec -T postgres dropdb -U trading_user trading_db || true
docker-compose -f "$COMPOSE_FILE" exec -T postgres createdb -U trading_user trading_db

# Restore from backup
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U trading_user trading_db
else
    docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U trading_user trading_db < "$BACKUP_FILE"
fi

# Restart application
docker-compose -f "$COMPOSE_FILE" start app

log "Database restore completed successfully"
