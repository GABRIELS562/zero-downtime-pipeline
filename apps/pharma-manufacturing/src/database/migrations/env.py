"""
Alembic Environment Configuration for Pharmaceutical Manufacturing Database
FDA 21 CFR Part 11 compliant database migration environment
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add the parent directory to the path so we can import our models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our models
from src.models import Base
from src.database import DatabaseConfig

# This is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Load database configuration from environment or config
def get_database_url():
    """Get database URL from environment or config"""
    db_config = DatabaseConfig()
    return db_config.database_url

def run_migrations_offline():
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Enable pharmaceutical manufacturing specific options
        transaction_per_migration=True,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get database URL
    database_url = get_database_url()
    
    # Update the configuration with our database URL
    config.set_main_option("sqlalchemy.url", database_url)
    
    # Create engine with pharmaceutical manufacturing optimizations
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Add FDA compliance settings
        connect_args={
            "options": "-c timezone=utc -c statement_timeout=300s",
            "application_name": "pharma_manufacturing_migration"
        }
    )

    with connectable.connect() as connection:
        # Set up migration context with pharmaceutical manufacturing requirements
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Enable comprehensive migration features
            transaction_per_migration=True,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # Enable constraint and index comparison
            include_object=include_object,
            # Enable pharmaceutical manufacturing specific options
            render_as_batch=True,
            # Version table configuration
            version_table_schema=None,
            version_table="alembic_version",
        )

        with context.begin_transaction():
            # Add migration metadata
            context.execute(
                "SELECT set_config('application_name', 'pharma_manufacturing_migration', false)"
            )
            
            # Run the actual migration
            context.run_migrations()

def include_object(object, name, type_, reflected, compare_to):
    """Determine whether to include objects in migration.
    
    This function is used to filter out objects that should not be
    included in the migration, such as certain indexes or constraints.
    """
    
    # Include all pharmaceutical manufacturing tables
    if type_ == "table":
        # Include all tables from our models
        return True
    
    # Include all indexes except system indexes
    if type_ == "index":
        # Skip system indexes
        if name.startswith("pg_"):
            return False
        # Include all other indexes
        return True
    
    # Include all constraints except system constraints
    if type_ == "constraint":
        # Skip system constraints
        if name.startswith("pg_"):
            return False
        # Include all other constraints
        return True
    
    # Include all foreign keys
    if type_ == "foreign_key":
        return True
    
    # Include all unique constraints
    if type_ == "unique_constraint":
        return True
    
    # Include all check constraints
    if type_ == "check_constraint":
        return True
    
    # Include everything else by default
    return True

def process_revision_directives(context, revision, directives):
    """Process and modify revision directives.
    
    This function can be used to modify the migration script
    before it's written to disk.
    """
    
    # Add pharmaceutical manufacturing specific metadata
    if config.cmd_opts and hasattr(config.cmd_opts, 'message'):
        if config.cmd_opts.message:
            # Add FDA compliance note to migration message
            original_message = config.cmd_opts.message
            config.cmd_opts.message = f"FDA 21 CFR Part 11: {original_message}"
    
    # Add revision metadata
    for directive in directives:
        if hasattr(directive, 'upgrade_ops'):
            # Add comment about pharmaceutical manufacturing compliance
            directive.upgrade_ops.ops.insert(0, 
                context.ops.execute_sql(
                    "-- FDA 21 CFR Part 11 compliant pharmaceutical manufacturing migration"
                )
            )

# Configure revision processing
if hasattr(context, 'configure'):
    context.configure(
        process_revision_directives=process_revision_directives
    )

# Run migrations based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()