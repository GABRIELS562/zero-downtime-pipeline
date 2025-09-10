#!/bin/bash
# Forensic Evidence Backup Script
# Backs up evidence chain with cryptographic verification

set -e

FORENSICS_DIR="/var/forensics"
BACKUP_DIR="/backups/forensics"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REMOTE_SERVER="server2"
EC2_GATEWAY="ec2-gateway"  # Configure Tailscale name or IP

echo "=== Forensic Evidence Backup Started at $(date) ==="

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Verify evidence chain before backup
echo "Verifying evidence chain integrity..."
python3 /app/forensic_collector.py verify || {
    echo "ERROR: Evidence chain compromised! Backup aborted."
    exit 1
}

# Create backup with hash
echo "Creating evidence backup..."
tar -czf ${BACKUP_DIR}/forensics-${TIMESTAMP}.tar.gz ${FORENSICS_DIR}/

# Calculate backup hash
BACKUP_HASH=$(sha256sum ${BACKUP_DIR}/forensics-${TIMESTAMP}.tar.gz | cut -d' ' -f1)
echo "${BACKUP_HASH} forensics-${TIMESTAMP}.tar.gz" >> ${BACKUP_DIR}/checksums.txt

# Sync to Server 2 (full backup)
echo "Syncing full backup to Server 2..."
rsync -avz ${BACKUP_DIR}/ ${REMOTE_SERVER}:/forensics-replica/

# Sync critical evidence only to EC2 (last 24 hours)
echo "Syncing critical evidence to EC2..."
find ${FORENSICS_DIR}/evidence -type d -name "INC-*" -mtime -1 | while read dir; do
    rsync -avz "$dir" ${EC2_GATEWAY}:/var/forensics/critical/
done

# Database replication
echo "Replicating chain database..."
sqlite3 ${FORENSICS_DIR}/chain_of_custody.db ".backup '${BACKUP_DIR}/chain_${TIMESTAMP}.db'"
rsync -avz ${BACKUP_DIR}/chain_${TIMESTAMP}.db ${REMOTE_SERVER}:/forensics-replica/
rsync -avz ${BACKUP_DIR}/chain_${TIMESTAMP}.db ${EC2_GATEWAY}:/var/forensics/

# Clean old backups (keep 30 days)
find ${BACKUP_DIR} -type f -name "forensics-*.tar.gz" -mtime +30 -delete

echo "=== Forensic Evidence Backup Completed ==="
echo "Backup hash: ${BACKUP_HASH}"
echo "Locations:"
echo "  - Local: ${BACKUP_DIR}/forensics-${TIMESTAMP}.tar.gz"
echo "  - Server2: ${REMOTE_SERVER}:/forensics-replica/"
echo "  - EC2: ${EC2_GATEWAY}:/var/forensics/critical/"