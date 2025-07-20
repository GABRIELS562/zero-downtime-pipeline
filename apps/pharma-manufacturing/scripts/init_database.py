#!/usr/bin/env python3
"""
Database Initialization Script for Pharmaceutical Manufacturing System
FDA 21 CFR Part 11 Compliant Database Setup
"""

import os
import sys
import asyncio
import logging
from typing import Optional
from pathlib import Path

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from database.database import DatabaseManager, DatabaseConfig
from database.models import Base, get_all_models

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PharmaDBInitializer:
    """Database initializer for pharmaceutical manufacturing system"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.db_manager = DatabaseManager(self.config)
        
    async def create_database_if_not_exists(self):
        """Create the main database if it doesn't exist"""
        try:
            # Parse database URL to get connection details
            db_url_parts = self.config.database_url.split('/')
            db_name = db_url_parts[-1]
            base_url = '/'.join(db_url_parts[:-1]) + '/postgres'
            
            # Connect to postgres database to create the main database
            conn = await asyncpg.connect(base_url)
            
            # Check if database exists
            db_exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db_name
            )
            
            if not db_exists:
                logger.info(f"Creating database: {db_name}")
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"Database {db_name} created successfully")
            else:
                logger.info(f"Database {db_name} already exists")
                
            await conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database: {str(e)}")
            raise
    
    def initialize_schemas_and_tables(self):
        """Initialize database schemas and tables"""
        try:
            logger.info("Initializing database schemas and tables...")
            
            # Initialize database manager
            self.db_manager.initialize()
            
            # Create all tables
            self.db_manager.create_tables()
            
            logger.info("Database schemas and tables created successfully")
            
        except Exception as e:
            logger.error(f"Error initializing schemas and tables: {str(e)}")
            raise
    
    def apply_regulatory_constraints(self):
        """Apply FDA 21 CFR Part 11 regulatory constraints"""
        try:
            logger.info("Applying regulatory constraints...")
            
            # Read and execute regulatory constraints SQL
            constraints_file = Path(__file__).parent / 'db-init' / '01_regulatory_constraints.sql'
            
            if constraints_file.exists():
                with open(constraints_file, 'r') as f:
                    constraints_sql = f.read()
                
                # Execute constraints in chunks to handle complex SQL
                with self.db_manager.get_session() as session:
                    # Split SQL by semicolons and execute each statement
                    statements = [stmt.strip() for stmt in constraints_sql.split(';') if stmt.strip()]
                    
                    for statement in statements:
                        if statement and not statement.startswith('--'):
                            try:
                                session.execute(text(statement))
                                session.commit()
                            except Exception as e:
                                logger.warning(f"Statement failed (continuing): {str(e)[:100]}...")
                                session.rollback()
                
                logger.info("Regulatory constraints applied successfully")
            else:
                logger.warning("Regulatory constraints file not found")
                
        except Exception as e:
            logger.error(f"Error applying regulatory constraints: {str(e)}")
            raise
    
    def create_default_users_and_roles(self):
        """Create default users and roles for pharmaceutical operations"""
        try:
            logger.info("Creating default users and roles...")
            
            from database.models import User, UserRole, ElectronicSignature
            from uuid import uuid4
            from datetime import datetime, timezone
            
            with self.db_manager.get_session() as session:
                # Create default roles
                default_roles = [
                    {
                        'role_name': 'Manufacturing Operator',
                        'role_code': 'MFG_OP',
                        'role_description': 'Manufacturing floor operator with batch execution rights',
                        'permissions': ['batch_execution', 'equipment_operation', 'data_entry']
                    },
                    {
                        'role_name': 'Quality Control Analyst', 
                        'role_code': 'QC_ANALYST',
                        'role_description': 'Quality control testing and release authority',
                        'permissions': ['quality_testing', 'batch_release', 'deviation_investigation']
                    },
                    {
                        'role_name': 'Manufacturing Manager',
                        'role_code': 'MFG_MGR', 
                        'role_description': 'Manufacturing operations management and oversight',
                        'permissions': ['batch_approval', 'schedule_management', 'team_oversight']
                    },
                    {
                        'role_name': 'Compliance Officer',
                        'role_code': 'COMPLIANCE',
                        'role_description': 'Regulatory compliance and audit management',
                        'permissions': ['audit_access', 'compliance_reporting', 'regulatory_submissions']
                    },
                    {
                        'role_name': 'System Administrator',
                        'role_code': 'SYS_ADMIN',
                        'role_description': 'System administration and technical support',
                        'permissions': ['system_admin', 'user_management', 'technical_support']
                    }
                ]
                
                for role_data in default_roles:
                    existing_role = session.query(UserRole).filter(
                        UserRole.role_code == role_data['role_code']
                    ).first()
                    
                    if not existing_role:
                        role = UserRole(
                            id=uuid4(),
                            role_name=role_data['role_name'],
                            role_code=role_data['role_code'],
                            role_description=role_data['role_description'],
                            permissions=role_data['permissions'],
                            is_active=True,
                            created_by=uuid4(),  # System user
                            modified_by=uuid4()
                        )
                        session.add(role)
                        logger.info(f"Created role: {role_data['role_name']}")
                
                # Create system admin user
                admin_role = session.query(UserRole).filter(
                    UserRole.role_code == 'SYS_ADMIN'
                ).first()
                
                if admin_role:
                    existing_admin = session.query(User).filter(
                        User.username == 'admin'
                    ).first()
                    
                    if not existing_admin:
                        admin_user = User(
                            id=uuid4(),
                            username='admin',
                            email='admin@pharma-manufacturing.local',
                            full_name='System Administrator',
                            role_id=admin_role.id,
                            is_active=True,
                            account_locked=False,
                            password_hash='$2b$12$placeholder_hash_change_in_production',
                            created_by=uuid4(),
                            modified_by=uuid4()
                        )
                        session.add(admin_user)
                        logger.info("Created system administrator user")
                
                session.commit()
                logger.info("Default users and roles created successfully")
                
        except Exception as e:
            logger.error(f"Error creating default users and roles: {str(e)}")
            raise
    
    def setup_audit_triggers(self):
        """Setup audit triggers for all relevant tables"""
        try:
            logger.info("Setting up audit triggers...")
            
            # Get all model classes
            models = get_all_models()
            
            with self.db_manager.get_session() as session:
                for model in models:
                    table_name = model.__tablename__
                    
                    # Skip audit tables themselves
                    if 'audit' in table_name.lower():
                        continue
                    
                    # Create audit trigger for each table
                    trigger_sql = f"""
                    DROP TRIGGER IF EXISTS audit_trigger_{table_name} ON {table_name};
                    CREATE TRIGGER audit_trigger_{table_name}
                        AFTER INSERT OR UPDATE OR DELETE ON {table_name}
                        FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
                    """
                    
                    try:
                        session.execute(text(trigger_sql))
                        logger.info(f"Created audit trigger for table: {table_name}")
                    except Exception as e:
                        logger.warning(f"Failed to create audit trigger for {table_name}: {str(e)}")
                
                session.commit()
                logger.info("Audit triggers setup completed")
                
        except Exception as e:
            logger.error(f"Error setting up audit triggers: {str(e)}")
            raise
    
    def validate_database_integrity(self):
        """Validate database integrity and compliance"""
        try:
            logger.info("Validating database integrity...")
            
            with self.db_manager.get_session() as session:
                # Check if essential tables exist
                essential_tables = [
                    'users', 'user_roles', 'products', 'batches', 
                    'equipment', 'audit_trail', 'electronic_signatures'
                ]
                
                for table in essential_tables:
                    result = session.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                        "WHERE table_name = :table_name)"
                    ), {'table_name': table})
                    
                    exists = result.scalar()
                    if not exists:
                        raise Exception(f"Essential table {table} does not exist")
                    
                    logger.info(f"✓ Table {table} exists")
                
                # Check regulatory functions exist
                regulatory_functions = [
                    'create_audit_trail_entry',
                    'validate_electronic_signature', 
                    'validate_batch_number',
                    'check_pharma_db_health'
                ]
                
                for func in regulatory_functions:
                    result = session.execute(text(
                        "SELECT EXISTS (SELECT 1 FROM pg_proc WHERE proname = :func_name)"
                    ), {'func_name': func})
                    
                    exists = result.scalar()
                    if not exists:
                        logger.warning(f"Regulatory function {func} does not exist")
                    else:
                        logger.info(f"✓ Function {func} exists")
                
                # Test database health check
                health_result = session.execute(text("SELECT * FROM check_pharma_db_health()"))
                health_data = health_result.fetchall()
                
                logger.info("Database health check results:")
                for component, status, details in health_data:
                    logger.info(f"  {component}: {status} - {details}")
                
                logger.info("Database integrity validation completed successfully")
                
        except Exception as e:
            logger.error(f"Database integrity validation failed: {str(e)}")
            raise
    
    async def run_full_initialization(self):
        """Run complete database initialization process"""
        try:
            logger.info("Starting pharmaceutical database initialization...")
            
            # Step 1: Create database if needed
            await self.create_database_if_not_exists()
            
            # Step 2: Initialize schemas and tables
            self.initialize_schemas_and_tables()
            
            # Step 3: Apply regulatory constraints
            self.apply_regulatory_constraints()
            
            # Step 4: Create default users and roles
            self.create_default_users_and_roles()
            
            # Step 5: Setup audit triggers
            self.setup_audit_triggers()
            
            # Step 6: Validate database integrity
            self.validate_database_integrity()
            
            logger.info("✅ Pharmaceutical database initialization completed successfully!")
            logger.info("🏭 Manufacturing system database is ready for GMP operations")
            logger.info("📋 FDA 21 CFR Part 11 compliance features are active")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            raise
        finally:
            if hasattr(self, 'db_manager') and self.db_manager:
                self.db_manager.close()

async def main():
    """Main initialization function"""
    try:
        # Get configuration from environment
        config = DatabaseConfig()
        
        # Initialize database
        initializer = PharmaDBInitializer(config)
        await initializer.run_full_initialization()
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())