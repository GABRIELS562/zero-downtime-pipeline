#!/bin/bash
# Volume Setup Script for Finance Trading Application
# Creates and configures persistent data volumes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VOLUMES_DIR="$PROJECT_DIR/volumes"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Create volume directories
create_volume_directories() {
    log "Creating volume directories..."
    
    # Development volumes
    mkdir -p "$VOLUMES_DIR/postgres-dev"
    mkdir -p "$VOLUMES_DIR/redis-dev"
    mkdir -p "$VOLUMES_DIR/logs-dev"
    mkdir -p "$VOLUMES_DIR/data-dev"
    
    # Staging volumes
    mkdir -p "$VOLUMES_DIR/postgres-staging"
    mkdir -p "$VOLUMES_DIR/redis-staging"
    mkdir -p "$VOLUMES_DIR/logs-staging"
    mkdir -p "$VOLUMES_DIR/data-staging"
    
    # Production volumes (if running locally)
    mkdir -p "$VOLUMES_DIR/postgres-prod"
    mkdir -p "$VOLUMES_DIR/redis-prod"
    mkdir -p "$VOLUMES_DIR/logs-prod"
    mkdir -p "$VOLUMES_DIR/data-prod"
    
    # Monitoring volumes
    mkdir -p "$VOLUMES_DIR/prometheus-data"
    mkdir -p "$VOLUMES_DIR/grafana-data"
    mkdir -p "$VOLUMES_DIR/nginx-logs"
    
    # Backup directories
    mkdir -p "$VOLUMES_DIR/backups"
    mkdir -p "$VOLUMES_DIR/backups/database"
    mkdir -p "$VOLUMES_DIR/backups/redis"
    mkdir -p "$VOLUMES_DIR/backups/logs"
    
    log "Volume directories created successfully"
}

# Set proper permissions
set_permissions() {
    log "Setting proper permissions..."
    
    # PostgreSQL requires specific ownership
    if command -v docker &> /dev/null; then
        # Use Docker to set PostgreSQL permissions
        docker run --rm -v "$VOLUMES_DIR/postgres-dev":/data alpine chown -R 999:999 /data
        docker run --rm -v "$VOLUMES_DIR/postgres-staging":/data alpine chown -R 999:999 /data
        docker run --rm -v "$VOLUMES_DIR/postgres-prod":/data alpine chown -R 999:999 /data
    else
        warn "Docker not available, PostgreSQL volumes may need manual permission adjustment"
    fi
    
    # Redis permissions
    chmod -R 755 "$VOLUMES_DIR/redis-"*
    
    # Log directories - writable by all for development
    chmod -R 777 "$VOLUMES_DIR/logs-"*
    
    # Data directories
    chmod -R 755 "$VOLUMES_DIR/data-"*
    
    # Monitoring data
    chmod -R 755 "$VOLUMES_DIR/prometheus-data"
    chmod -R 755 "$VOLUMES_DIR/grafana-data"
    
    log "Permissions set successfully"
}

# Create volume configuration files
create_volume_configs() {
    log "Creating volume configuration files..."
    
    # PostgreSQL development configuration
    cat > "$PROJECT_DIR/config/postgresql.dev.conf" << EOF
# PostgreSQL Development Configuration
# Optimized for development with detailed logging

# Connection settings
listen_addresses = '*'
port = 5432
max_connections = 100

# Memory settings
shared_buffers = 128MB
effective_cache_size = 512MB
maintenance_work_mem = 64MB
work_mem = 4MB

# WAL settings
wal_level = replica
max_wal_size = 1GB
min_wal_size = 80MB
checkpoint_completion_target = 0.9

# Logging
log_destination = 'stderr'
log_statement = 'all'
log_duration = on
log_min_duration_statement = 100ms
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Performance monitoring
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.max = 10000
pg_stat_statements.track = all

# Development-specific settings
fsync = off
synchronous_commit = off
full_page_writes = off
EOF

    # Redis development configuration
    cat > "$PROJECT_DIR/config/redis.dev.conf" << EOF
# Redis Development Configuration
# Optimized for development with persistence

# Network
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
dbfilename dump.rdb
dir /data

# Append only file
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no

# Logging
loglevel notice
logfile ""

# Security (development only - disable for production)
protected-mode no
EOF

    log "Configuration files created successfully"
}

# Create backup scripts
create_backup_scripts() {
    log "Creating backup scripts..."
    
    # Database backup script
    cat > "$PROJECT_DIR/scripts/backup-database.sh" << 'EOF'
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
EOF

    # Redis backup script
    cat > "$PROJECT_DIR/scripts/backup-redis.sh" << 'EOF'
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
EOF

    # Make scripts executable
    chmod +x "$PROJECT_DIR/scripts/backup-database.sh"
    chmod +x "$PROJECT_DIR/scripts/backup-redis.sh"
    
    log "Backup scripts created successfully"
}

# Create restore scripts
create_restore_scripts() {
    log "Creating restore scripts..."
    
    # Database restore script
    cat > "$PROJECT_DIR/scripts/restore-database.sh" << 'EOF'
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
EOF

    chmod +x "$PROJECT_DIR/scripts/restore-database.sh"
    
    log "Restore scripts created successfully"
}

# Create volume monitoring script
create_monitoring_script() {
    log "Creating volume monitoring script..."
    
    cat > "$PROJECT_DIR/scripts/monitor-volumes.sh" << 'EOF'
#!/bin/bash
# Volume Monitoring Script

set -euo pipefail

VOLUMES_DIR="volumes"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check disk usage
check_disk_usage() {
    log "Checking disk usage for volumes..."
    
    echo "Volume Directory Sizes:"
    du -sh $VOLUMES_DIR/* | sort -hr
    
    echo ""
    echo "Available Disk Space:"
    df -h $VOLUMES_DIR
    
    # Check if any volume is using more than 80% of available space
    USAGE=$(df $VOLUMES_DIR | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$USAGE" -gt 80 ]; then
        echo "WARNING: Volume directory is using $USAGE% of available space"
    fi
}

# Check volume health
check_volume_health() {
    log "Checking volume health..."
    
    # Check PostgreSQL data directory
    if [ -d "$VOLUMES_DIR/postgres-dev/base" ]; then
        echo "✓ PostgreSQL development volume is healthy"
    else
        echo "✗ PostgreSQL development volume may be corrupted"
    fi
    
    # Check Redis data files
    if [ -f "$VOLUMES_DIR/redis-dev/dump.rdb" ] || [ -f "$VOLUMES_DIR/redis-dev/appendonly.aof" ]; then
        echo "✓ Redis development volume is healthy"
    else
        echo "✗ Redis development volume may be empty or corrupted"
    fi
    
    # Check log files
    if [ "$(find $VOLUMES_DIR/logs-dev -name "*.log" -type f | wc -l)" -gt 0 ]; then
        echo "✓ Application logs are being generated"
    else
        echo "⚠ No log files found (may be normal for new installations)"
    fi
}

# Main monitoring function
main() {
    log "Starting volume monitoring..."
    
    check_disk_usage
    echo ""
    check_volume_health
    
    log "Volume monitoring completed"
}

main
EOF

    chmod +x "$PROJECT_DIR/scripts/monitor-volumes.sh"
    
    log "Monitoring script created successfully"
}

# Create .gitignore for volumes
create_gitignore() {
    log "Creating .gitignore for volumes..."
    
    cat > "$VOLUMES_DIR/.gitignore" << EOF
# Ignore all volume data but keep the directory structure
*
!.gitignore
!README.md
EOF

    # Create README for volumes
    cat > "$VOLUMES_DIR/README.md" << EOF
# Volumes Directory

This directory contains persistent data volumes for the Finance Trading Application.

## Structure

- \`postgres-*\`: PostgreSQL database data
- \`redis-*\`: Redis cache data  
- \`logs-*\`: Application logs
- \`data-*\`: Application data files
- \`backups/\`: Database and volume backups
- \`prometheus-data/\`: Prometheus metrics data
- \`grafana-data/\`: Grafana dashboard data

## Environment Suffixes

- \`*-dev\`: Development environment
- \`*-staging\`: Staging environment  
- \`*-prod\`: Production environment

## Backup and Restore

Use the provided scripts:
- \`scripts/backup-database.sh\`: Backup PostgreSQL database
- \`scripts/backup-redis.sh\`: Backup Redis data
- \`scripts/restore-database.sh\`: Restore PostgreSQL database
- \`scripts/monitor-volumes.sh\`: Monitor volume health and usage

## Security Notes

- Volume data contains sensitive financial information
- Ensure proper access controls in production environments
- Regular backups are essential for data protection
- Monitor disk usage to prevent storage issues
EOF
    
    log "Volume documentation created successfully"
}

# Main function
main() {
    log "Setting up volumes for Finance Trading Application..."
    
    create_volume_directories
    set_permissions
    create_volume_configs
    create_backup_scripts
    create_restore_scripts
    create_monitoring_script
    create_gitignore
    
    log "Volume setup completed successfully!"
    log ""
    log "Next steps:"
    log "1. Run 'docker-compose up -d' to start the application"
    log "2. Use 'scripts/monitor-volumes.sh' to monitor volume health"
    log "3. Set up regular backups using the backup scripts"
    log "4. Review volume configurations in config/ directory"
}

# Run main function
main "$@"