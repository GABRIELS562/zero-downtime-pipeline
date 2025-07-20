#!/bin/bash
# Database Backup Script

set -euo pipefail

BACKUP_DIR="volumes/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ENVIRONMENT="${1:-development}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
log "Creating database backup for $ENVIRONMENT environment..."

if [ "$ENVIRONMENT" = "development" ]; then
    COMPOSE_FILE="docker-compose.yml"
    DB_SERVICE="postgres"
else
    COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
    DB_SERVICE="postgres"
fi

# Create SQL dump
docker-compose -f "$COMPOSE_FILE" exec -T "$DB_SERVICE" pg_dump -U trading_user trading_db > "$BACKUP_DIR/trading_db_$TIMESTAMP.sql"

# Create compressed backup
gzip "$BACKUP_DIR/trading_db_$TIMESTAMP.sql"

# Create volume backup
docker run --rm -v $(pwd)/volumes/postgres-$ENVIRONMENT:/source -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres_volume_$TIMESTAMP.tar.gz -C /source .

log "Database backup completed: $BACKUP_DIR/trading_db_$TIMESTAMP.sql.gz"
log "Volume backup completed: $BACKUP_DIR/postgres_volume_$TIMESTAMP.tar.gz"

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete

log "Backup cleanup completed"
