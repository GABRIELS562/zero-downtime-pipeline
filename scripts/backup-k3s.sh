#!/bin/bash
# K3s Cluster Backup Script
# Backs up K3s etcd snapshots to Server 2

set -e

BACKUP_DIR="/backups/k3s"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="k3s-backup-${TIMESTAMP}"
REMOTE_SERVER="server2"  # Configure in /etc/hosts or use IP

echo "=== K3s Cluster Backup Started at $(date) ==="

# Create backup directory if not exists
mkdir -p ${BACKUP_DIR}

# Create K3s snapshot
echo "Creating K3s etcd snapshot..."
sudo k3s etcd-snapshot save --name ${BACKUP_NAME}

# Move snapshot to backup directory
sudo mv /var/lib/rancher/k3s/server/db/snapshots/${BACKUP_NAME} ${BACKUP_DIR}/

# Backup K3s configuration
echo "Backing up K3s configuration..."
sudo tar -czf ${BACKUP_DIR}/${BACKUP_NAME}-config.tar.gz \
    /etc/rancher/k3s/ \
    /var/lib/rancher/k3s/server/manifests/ \
    2>/dev/null || true

# Sync to Server 2
echo "Syncing backup to Server 2..."
rsync -avz ${BACKUP_DIR}/ ${REMOTE_SERVER}:/backups/k3s/

# Keep only last 7 days of backups
echo "Cleaning old backups..."
find ${BACKUP_DIR} -type f -name "k3s-backup-*" -mtime +7 -delete

# Create latest symlink
ln -sf ${BACKUP_DIR}/${BACKUP_NAME} ${BACKUP_DIR}/k3s-backup-LATEST

echo "=== K3s Backup Completed Successfully ==="
echo "Backup saved to: ${BACKUP_DIR}/${BACKUP_NAME}"
echo "Remote copy at: ${REMOTE_SERVER}:/backups/k3s/${BACKUP_NAME}"