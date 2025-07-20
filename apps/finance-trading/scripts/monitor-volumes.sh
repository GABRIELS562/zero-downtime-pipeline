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
