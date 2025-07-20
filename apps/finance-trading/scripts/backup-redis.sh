#!/bin/bash
# Redis Backup Script

set -euo pipefail

BACKUP_DIR="volumes/backups/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ENVIRONMENT="${1:-development}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Creating Redis backup for $ENVIRONMENT environment..."

if [ "$ENVIRONMENT" = "development" ]; then
    COMPOSE_FILE="docker-compose.yml"
else
    COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
fi

# Force Redis to save
docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli BGSAVE

# Wait for background save to complete
sleep 5

# Create volume backup
docker run --rm -v $(pwd)/volumes/redis-$ENVIRONMENT:/source -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/redis_volume_$TIMESTAMP.tar.gz -C /source .

log "Redis backup completed: $BACKUP_DIR/redis_volume_$TIMESTAMP.tar.gz"

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

log "Backup cleanup completed"
