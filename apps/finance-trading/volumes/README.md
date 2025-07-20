# Volumes Directory

This directory contains persistent data volumes for the Finance Trading Application.

## Structure

- `postgres-*`: PostgreSQL database data
- `redis-*`: Redis cache data  
- `logs-*`: Application logs
- `data-*`: Application data files
- `backups/`: Database and volume backups
- `prometheus-data/`: Prometheus metrics data
- `grafana-data/`: Grafana dashboard data

## Environment Suffixes

- `*-dev`: Development environment
- `*-staging`: Staging environment  
- `*-prod`: Production environment

## Backup and Restore

Use the provided scripts:
- `scripts/backup-database.sh`: Backup PostgreSQL database
- `scripts/backup-redis.sh`: Backup Redis data
- `scripts/restore-database.sh`: Restore PostgreSQL database
- `scripts/monitor-volumes.sh`: Monitor volume health and usage

## Security Notes

- Volume data contains sensitive financial information
- Ensure proper access controls in production environments
- Regular backups are essential for data protection
- Monitor disk usage to prevent storage issues
