#!/usr/bin/env python3
"""
Simple Backup and Recovery System for Pharmaceutical Manufacturing
FDA 21 CFR Part 11 Compliant Data Protection
"""

import os
import sys
import asyncio
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBackupRecovery:
    """Simple backup and recovery system"""
    
    def __init__(self):
        self.backup_dir = Path('/tmp/pharma-backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # Database configuration
        self.db_host = os.getenv('DB_HOST', 'postgres')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.db_user = os.getenv('DB_USER', 'pharma_user')
        self.db_password = os.getenv('DB_PASSWORD', 'pharma_password')
        self.db_name = os.getenv('DB_NAME', 'pharma_manufacturing_db')
    
    async def backup_database(self, backup_name: str = None):
        """Create database backup"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        logger.info(f"Creating database backup: {backup_file}")
        
        try:
            # Create pg_dump command
            cmd = [
                'pg_dump',
                f'--host={self.db_host}',
                f'--port={self.db_port}',
                f'--username={self.db_user}',
                f'--dbname={self.db_name}',
                '--verbose',
                '--clean',
                '--create',
                f'--file={backup_file}'
            ]
            
            # Set password environment
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            # Execute backup
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode == 0:
                logger.info(f"Backup completed successfully: {backup_file}")
                return str(backup_file)
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Backup error: {str(e)}")
            return None
    
    async def restore_database(self, backup_file: str):
        """Restore database from backup"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        logger.info(f"Restoring database from: {backup_file}")
        
        try:
            cmd = [
                'psql',
                f'--host={self.db_host}',
                f'--port={self.db_port}',
                f'--username={self.db_user}',
                f'--dbname=postgres',
                f'--file={backup_file}'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode == 0:
                logger.info("Database restored successfully")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Restore error: {str(e)}")
            return False
    
    def list_backups(self):
        """List available backups"""
        backups = list(self.backup_dir.glob('*.sql'))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        logger.info(f"Found {len(backups)} backups:")
        for backup in backups:
            size = backup.stat().st_size
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            logger.info(f"  {backup.name} - {size} bytes - {mtime}")
        
        return [str(b) for b in backups]

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Pharma Backup/Recovery')
    parser.add_argument('command', choices=['backup', 'restore', 'list'])
    parser.add_argument('--name', help='Backup name')
    parser.add_argument('--file', help='Backup file path')
    
    args = parser.parse_args()
    
    backup_system = SimpleBackupRecovery()
    
    if args.command == 'backup':
        result = await backup_system.backup_database(args.name)
        if result:
            print(f"Backup created: {result}")
        else:
            print("Backup failed")
            sys.exit(1)
    
    elif args.command == 'restore':
        if not args.file:
            print("Error: --file required for restore")
            sys.exit(1)
        
        success = await backup_system.restore_database(args.file)
        if success:
            print("Restore completed")
        else:
            print("Restore failed")
            sys.exit(1)
    
    elif args.command == 'list':
        backup_system.list_backups()

if __name__ == "__main__":
    asyncio.run(main())