"""
Database Migration Scripts
Alembic integration for database schema versioning and migration
"""

import os
import asyncio
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic import context
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from alembic.runtime.environment import EnvironmentContext

from src.database.models import Base
from src.database.connection import get_database_url

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata

def get_alembic_config():
    """Get Alembic configuration"""
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "src/database/migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", get_database_url())
    return alembic_cfg

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    """Run migrations with connection"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Run migrations in 'online' mode."""
    from sqlalchemy.ext.asyncio import create_async_engine
    
    connectable = create_async_engine(
        get_database_url(),
        poolclass=pool.NullPool,
        echo=False
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

class MigrationManager:
    """Database migration management"""
    
    def __init__(self):
        self.alembic_cfg = get_alembic_config()
        self.script_dir = ScriptDirectory.from_config(self.alembic_cfg)
    
    async def create_migration(self, message: str, auto_generate: bool = True):
        """Create a new migration"""
        from alembic.command import revision
        
        try:
            if auto_generate:
                revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                revision(self.alembic_cfg, message=message)
            print(f"Migration created: {message}")
        except Exception as e:
            print(f"Error creating migration: {e}")
            raise
    
    async def upgrade_database(self, revision: str = "head"):
        """Upgrade database to specific revision"""
        from alembic.command import upgrade
        
        try:
            upgrade(self.alembic_cfg, revision)
            print(f"Database upgraded to: {revision}")
        except Exception as e:
            print(f"Error upgrading database: {e}")
            raise
    
    async def downgrade_database(self, revision: str):
        """Downgrade database to specific revision"""
        from alembic.command import downgrade
        
        try:
            downgrade(self.alembic_cfg, revision)
            print(f"Database downgraded to: {revision}")
        except Exception as e:
            print(f"Error downgrading database: {e}")
            raise
    
    def get_current_revision(self):
        """Get current database revision"""
        from alembic.command import current
        
        try:
            return current(self.alembic_cfg)
        except Exception as e:
            print(f"Error getting current revision: {e}")
            return None
    
    def get_migration_history(self):
        """Get migration history"""
        from alembic.command import history
        
        try:
            return history(self.alembic_cfg)
        except Exception as e:
            print(f"Error getting migration history: {e}")
            return None
    
    async def initialize_database(self):
        """Initialize database with all tables"""
        from sqlalchemy.ext.asyncio import create_async_engine
        
        engine = create_async_engine(get_database_url())
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("Database initialized with all tables")
        
        await engine.dispose()
    
    async def drop_all_tables(self):
        """Drop all tables (use with caution)"""
        from sqlalchemy.ext.asyncio import create_async_engine
        
        engine = create_async_engine(get_database_url())
        
        async with engine.begin() as conn:
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            print("All tables dropped")
        
        await engine.dispose()

# Migration templates
INITIAL_MIGRATION_TEMPLATE = '''"""Initial migration

Revision ID: {revision}
Revises: {down_revision}
Create Date: {create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = {revision!r}
down_revision = {down_revision!r}
branch_labels = {branch_labels!r}
depends_on = {depends_on!r}

def upgrade():
    # Create ENUM types
    op.execute("CREATE TYPE order_side_enum AS ENUM ('BUY', 'SELL')")
    op.execute("CREATE TYPE order_type_enum AS ENUM ('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT')")
    op.execute("CREATE TYPE order_status_enum AS ENUM ('PENDING', 'PARTIALLY_FILLED', 'FILLED', 'CANCELLED', 'REJECTED', 'EXPIRED')")
    op.execute("CREATE TYPE time_in_force_enum AS ENUM ('GTC', 'IOC', 'FOK', 'DAY')")
    op.execute("CREATE TYPE account_type_enum AS ENUM ('TRADING', 'DEMO', 'PAPER', 'MARGIN')")
    op.execute("CREATE TYPE asset_class_enum AS ENUM ('EQUITY', 'OPTION', 'FUTURE', 'FOREX', 'CRYPTO', 'COMMODITY')")
    op.execute("CREATE TYPE transaction_type_enum AS ENUM ('TRADE', 'DEPOSIT', 'WITHDRAWAL', 'DIVIDEND', 'INTEREST', 'FEE')")
    
    # Create tables
    {create_tables}
    
    # Create indexes
    {create_indexes}
    
    # Create triggers
    {create_triggers}

def downgrade():
    # Drop tables
    {drop_tables}
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS order_side_enum")
    op.execute("DROP TYPE IF EXISTS order_type_enum")
    op.execute("DROP TYPE IF EXISTS order_status_enum")
    op.execute("DROP TYPE IF EXISTS time_in_force_enum")
    op.execute("DROP TYPE IF EXISTS account_type_enum")
    op.execute("DROP TYPE IF EXISTS asset_class_enum")
    op.execute("DROP TYPE IF EXISTS transaction_type_enum")
'''

# Utility functions for migration management
async def create_initial_migration():
    """Create initial migration with all tables"""
    migration_manager = MigrationManager()
    await migration_manager.create_migration("Initial migration - create all tables")

async def upgrade_to_latest():
    """Upgrade database to latest revision"""
    migration_manager = MigrationManager()
    await migration_manager.upgrade_database()

async def reset_database():
    """Reset database (drop all tables and recreate)"""
    migration_manager = MigrationManager()
    await migration_manager.drop_all_tables()
    await migration_manager.initialize_database()

# CLI commands for migration management
async def main():
    """Main migration CLI"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations.py <command> [args]")
        print("Commands:")
        print("  init - Initialize database")
        print("  upgrade [revision] - Upgrade database")
        print("  downgrade <revision> - Downgrade database")
        print("  create <message> - Create new migration")
        print("  current - Show current revision")
        print("  history - Show migration history")
        print("  reset - Reset database (drop all tables)")
        return
    
    command = sys.argv[1]
    migration_manager = MigrationManager()
    
    try:
        if command == "init":
            await migration_manager.initialize_database()
        
        elif command == "upgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            await migration_manager.upgrade_database(revision)
        
        elif command == "downgrade":
            if len(sys.argv) < 3:
                print("Error: downgrade requires revision argument")
                return
            revision = sys.argv[2]
            await migration_manager.downgrade_database(revision)
        
        elif command == "create":
            if len(sys.argv) < 3:
                print("Error: create requires message argument")
                return
            message = " ".join(sys.argv[2:])
            await migration_manager.create_migration(message)
        
        elif command == "current":
            current = migration_manager.get_current_revision()
            print(f"Current revision: {current}")
        
        elif command == "history":
            history = migration_manager.get_migration_history()
            print(f"Migration history: {history}")
        
        elif command == "reset":
            confirm = input("Are you sure you want to reset the database? (y/N): ")
            if confirm.lower() == 'y':
                await reset_database()
            else:
                print("Reset cancelled")
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error executing command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

# Context configuration
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())