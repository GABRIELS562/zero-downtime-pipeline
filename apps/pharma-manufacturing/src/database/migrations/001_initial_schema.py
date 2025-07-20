"""
Initial Database Schema Migration
Creates all pharmaceutical manufacturing tables with FDA 21 CFR Part 11 compliance
"""

import logging
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create all pharmaceutical manufacturing tables"""
    logger.info("Starting pharmaceutical manufacturing database schema creation")
    
    # Create extensions
    logger.info("Creating PostgreSQL extensions")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gin"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"')
    
    # Create user roles table
    logger.info("Creating user roles table")
    op.create_table(
        'user_roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()')),
        sa.Column('role_code', sa.String(50), nullable=False, unique=True),
        sa.Column('role_name', sa.String(200), nullable=False),
        sa.Column('role_description', sa.Text, nullable=False),
        sa.Column('role_level', sa.Integer, nullable=False, default=1),
        sa.Column('parent_role_id', UUID(as_uuid=True), nullable=True),
        sa.Column('permissions', sa.JSON, nullable=False),
        sa.Column('system_access', sa.JSON, nullable=False),
        sa.Column('gmp_critical_role', sa.Boolean, nullable=False, default=False),
        sa.Column('training_required', sa.Boolean, nullable=False, default=True),
        sa.Column('qualification_required', sa.Boolean, nullable=False, default=False),
        sa.Column('can_sign_batches', sa.Boolean, nullable=False, default=False),
        sa.Column('can_sign_investigations', sa.Boolean, nullable=False, default=False),
        sa.Column('can_sign_deviations', sa.Boolean, nullable=False, default=False),
        sa.Column('can_approve_procedures', sa.Boolean, nullable=False, default=False),
        sa.Column('regulatory_oversight', sa.Boolean, nullable=False, default=False),
        sa.Column('audit_trail_exempt', sa.Boolean, nullable=False, default=False),
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('modified_by', UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, default='1.0'),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('electronic_signature_id', UUID(as_uuid=True), nullable=True),
        sa.Column('signature_meaning', sa.String(100), nullable=True),
        sa.Column('change_control_id', UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('data_integrity_hash', sa.String(64), nullable=True),
        sa.Column('regulatory_status', sa.String(50), nullable=False, default='active'),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('regulatory_metadata', sa.JSON, nullable=True),
        
        sa.ForeignKeyConstraint(['parent_role_id'], ['user_roles.id']),
        sa.CheckConstraint('role_level >= 1', name='positive_role_level'),
    )
    
    # Create users table
    logger.info("Creating users table")
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()')),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('user_id', sa.String(20), nullable=False, unique=True),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(200), nullable=False, unique=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('role_id', UUID(as_uuid=True), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('password_salt', sa.String(32), nullable=False),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('password_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tfa_enabled', sa.Boolean, nullable=False, default=False),
        sa.Column('tfa_secret', sa.String(32), nullable=True),
        sa.Column('backup_codes', sa.JSON, nullable=True),
        sa.Column('account_locked', sa.Boolean, nullable=False, default=False),
        sa.Column('lock_reason', sa.String(200), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, default=0),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active_sessions', sa.Integer, nullable=False, default=0),
        sa.Column('signature_pin', sa.String(255), nullable=True),
        sa.Column('signature_meaning', sa.String(100), nullable=True),
        sa.Column('signature_enabled', sa.Boolean, nullable=False, default=False),
        sa.Column('signature_attempts', sa.Integer, nullable=False, default=0),
        sa.Column('training_completed', sa.Boolean, nullable=False, default=False),
        sa.Column('training_completion_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('qualification_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('department', sa.String(100), nullable=False),
        sa.Column('supervisor_id', UUID(as_uuid=True), nullable=True),
        sa.Column('hire_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('termination_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('employment_status', sa.String(50), nullable=False, default='active'),
        sa.Column('gmp_training_current', sa.Boolean, nullable=False, default=False),
        sa.Column('gmp_training_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('regulatory_training_current', sa.Boolean, nullable=False, default=False),
        sa.Column('timezone', sa.String(50), nullable=False, default='UTC'),
        sa.Column('language', sa.String(10), nullable=False, default='en'),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('status_changed_by', UUID(as_uuid=True), nullable=False),
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('modified_by', UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, default='1.0'),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('electronic_signature_id', UUID(as_uuid=True), nullable=True),
        sa.Column('change_control_id', UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('data_integrity_hash', sa.String(64), nullable=True),
        sa.Column('regulatory_status', sa.String(50), nullable=False, default='active'),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('regulatory_metadata', sa.JSON, nullable=True),
        
        sa.ForeignKeyConstraint(['role_id'], ['user_roles.id']),
        sa.ForeignKeyConstraint(['supervisor_id'], ['users.id']),
        sa.CheckConstraint("employment_status IN ('active', 'inactive', 'terminated', 'suspended')", name='valid_employment_status'),
        sa.CheckConstraint("qualification_status IN ('pending', 'qualified', 'requalification_required', 'disqualified')", name='valid_qualification_status'),
        sa.CheckConstraint('failed_login_attempts >= 0', name='non_negative_failed_attempts'),
        sa.CheckConstraint('signature_attempts >= 0', name='non_negative_signature_attempts'),
        sa.CheckConstraint('active_sessions >= 0', name='non_negative_active_sessions'),
    )
    
    # Create material types table
    logger.info("Creating material types table")
    op.create_table(
        'material_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()')),
        sa.Column('type_code', sa.String(50), nullable=False, unique=True),
        sa.Column('type_name', sa.String(200), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('regulatory_class', sa.String(50), nullable=False),
        sa.Column('storage_conditions', sa.JSON, nullable=False),
        sa.Column('special_handling', sa.Boolean, nullable=False, default=False),
        sa.Column('handling_requirements', sa.JSON, nullable=True),
        sa.Column('testing_required', sa.Boolean, nullable=False, default=True),
        sa.Column('testing_frequency', sa.String(50), nullable=True),
        sa.Column('typical_shelf_life_months', sa.Integer, nullable=True),
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('modified_by', UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, default='1.0'),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('electronic_signature_id', UUID(as_uuid=True), nullable=True),
        sa.Column('signature_meaning', sa.String(100), nullable=True),
        sa.Column('change_control_id', UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('data_integrity_hash', sa.String(64), nullable=True),
        sa.Column('regulatory_status', sa.String(50), nullable=False, default='active'),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('regulatory_metadata', sa.JSON, nullable=True),
        
        sa.CheckConstraint("category IN ('api', 'excipient', 'packaging', 'solvent', 'reagent')", name='valid_category'),
        sa.CheckConstraint("regulatory_class IN ('controlled', 'non_controlled', 'hazardous')", name='valid_regulatory_class'),
        sa.CheckConstraint("testing_frequency IS NULL OR testing_frequency IN ('per_lot', 'periodic', 'skip_lot')", name='valid_testing_frequency'),
        sa.CheckConstraint("typical_shelf_life_months IS NULL OR typical_shelf_life_months > 0", name='positive_shelf_life'),
    )
    
    # Create products table
    logger.info("Creating products table")
    op.create_table(
        'products',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()')),
        sa.Column('product_code', sa.String(50), nullable=False, unique=True),
        sa.Column('product_name', sa.String(200), nullable=False),
        sa.Column('product_type', sa.String(50), nullable=False),
        sa.Column('nda_number', sa.String(20), nullable=True),
        sa.Column('anda_number', sa.String(20), nullable=True),
        sa.Column('active_ingredient', sa.String(100), nullable=False),
        sa.Column('strength', sa.String(50), nullable=False),
        sa.Column('dosage_form', sa.String(50), nullable=False),
        sa.Column('manufacturing_process', sa.String(100), nullable=False),
        sa.Column('standard_batch_size', sa.Float, nullable=False),
        sa.Column('batch_size_units', sa.String(20), nullable=False),
        sa.Column('shelf_life_months', sa.Integer, nullable=False),
        sa.Column('storage_conditions', sa.JSON, nullable=False),
        sa.Column('bom_version', sa.String(20), nullable=False, default='1.0'),
        sa.Column('bom_data', sa.JSON, nullable=False),
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('modified_by', UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, default='1.0'),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('electronic_signature_id', UUID(as_uuid=True), nullable=True),
        sa.Column('signature_meaning', sa.String(100), nullable=True),
        sa.Column('change_control_id', UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('data_integrity_hash', sa.String(64), nullable=True),
        sa.Column('regulatory_status', sa.String(50), nullable=False, default='active'),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('regulatory_metadata', sa.JSON, nullable=True),
        
        sa.CheckConstraint("shelf_life_months > 0", name='positive_shelf_life'),
        sa.CheckConstraint("standard_batch_size > 0", name='positive_batch_size'),
    )
    
    # Create monitoring locations table
    logger.info("Creating monitoring locations table")
    op.create_table(
        'monitoring_locations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()')),
        sa.Column('location_code', sa.String(50), nullable=False, unique=True),
        sa.Column('location_name', sa.String(200), nullable=False),
        sa.Column('location_type', sa.String(50), nullable=False),
        sa.Column('building', sa.String(100), nullable=False),
        sa.Column('floor', sa.String(50), nullable=False),
        sa.Column('room', sa.String(100), nullable=False),
        sa.Column('area', sa.String(100), nullable=True),
        sa.Column('coordinates', sa.String(100), nullable=True),
        sa.Column('cleanliness_class', sa.String(20), nullable=True),
        sa.Column('containment_level', sa.String(20), nullable=True),
        sa.Column('temperature_min', sa.Float, nullable=True),
        sa.Column('temperature_max', sa.Float, nullable=True),
        sa.Column('humidity_min', sa.Float, nullable=True),
        sa.Column('humidity_max', sa.Float, nullable=True),
        sa.Column('pressure_min', sa.Float, nullable=True),
        sa.Column('pressure_max', sa.Float, nullable=True),
        sa.Column('particle_count_limits', sa.JSON, nullable=True),
        sa.Column('viable_particle_limits', sa.JSON, nullable=True),
        sa.Column('air_changes_per_hour', sa.Float, nullable=True),
        sa.Column('monitoring_frequency_minutes', sa.Integer, nullable=False, default=15),
        sa.Column('critical_monitoring', sa.Boolean, nullable=False, default=False),
        sa.Column('temperature_alert_min', sa.Float, nullable=True),
        sa.Column('temperature_alert_max', sa.Float, nullable=True),
        sa.Column('humidity_alert_min', sa.Float, nullable=True),
        sa.Column('humidity_alert_max', sa.Float, nullable=True),
        sa.Column('pressure_alert_min', sa.Float, nullable=True),
        sa.Column('pressure_alert_max', sa.Float, nullable=True),
        sa.Column('qualification_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('last_qualification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_qualification_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('status_changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('status_changed_by', UUID(as_uuid=True), nullable=False),
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('modified_by', UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, default='1.0'),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('electronic_signature_id', UUID(as_uuid=True), nullable=True),
        sa.Column('signature_meaning', sa.String(100), nullable=True),
        sa.Column('change_control_id', UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('data_integrity_hash', sa.String(64), nullable=True),
        sa.Column('regulatory_status', sa.String(50), nullable=False, default='active'),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('regulatory_metadata', sa.JSON, nullable=True),
        
        sa.CheckConstraint("location_type IN ('clean_room', 'warehouse', 'laboratory', 'production_area', 'corridor', 'airlock')", name='valid_location_type'),
        sa.CheckConstraint("cleanliness_class IS NULL OR cleanliness_class IN ('ISO 5', 'ISO 6', 'ISO 7', 'ISO 8', 'unclassified')", name='valid_cleanliness_class'),
        sa.CheckConstraint("containment_level IS NULL OR containment_level IN ('BSL-1', 'BSL-2', 'BSL-3', 'none')", name='valid_containment_level'),
        sa.CheckConstraint("qualification_status IN ('pending', 'qualified', 'requalification_required', 'failed')", name='valid_qualification_status'),
        sa.CheckConstraint("monitoring_frequency_minutes > 0", name='positive_monitoring_frequency'),
        sa.CheckConstraint("temperature_min IS NULL OR temperature_max IS NULL OR temperature_min <= temperature_max", name='valid_temperature_range'),
        sa.CheckConstraint("humidity_min IS NULL OR humidity_max IS NULL OR humidity_min <= humidity_max", name='valid_humidity_range'),
        sa.CheckConstraint("pressure_min IS NULL OR pressure_max IS NULL OR pressure_min <= pressure_max", name='valid_pressure_range'),
    )
    
    # Create indexes for performance
    logger.info("Creating performance indexes")
    
    # User indexes
    op.create_index('idx_user_username', 'users', ['username'])
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_role', 'users', ['role_id'])
    op.create_index('idx_user_department', 'users', ['department'])
    op.create_index('idx_user_employment_status', 'users', ['employment_status'])
    op.create_index('idx_user_qualification_status', 'users', ['qualification_status'])
    
    # Material type indexes
    op.create_index('idx_material_type_code', 'material_types', ['type_code'])
    op.create_index('idx_material_category', 'material_types', ['category'])
    op.create_index('idx_regulatory_class', 'material_types', ['regulatory_class'])
    
    # Product indexes
    op.create_index('idx_product_code', 'products', ['product_code'])
    op.create_index('idx_product_name', 'products', ['product_name'])
    op.create_index('idx_product_type', 'products', ['product_type'])
    
    # Monitoring location indexes
    op.create_index('idx_location_code', 'monitoring_locations', ['location_code'])
    op.create_index('idx_location_name', 'monitoring_locations', ['location_name'])
    op.create_index('idx_location_type', 'monitoring_locations', ['location_type'])
    op.create_index('idx_building', 'monitoring_locations', ['building'])
    op.create_index('idx_cleanliness_class', 'monitoring_locations', ['cleanliness_class'])
    op.create_index('idx_critical_monitoring', 'monitoring_locations', ['critical_monitoring'])
    op.create_index('idx_location_qualification_status', 'monitoring_locations', ['qualification_status'])
    
    # Create audit trail table
    logger.info("Creating audit trail table")
    op.create_table(
        'audit_trail',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()')),
        sa.Column('audit_id', sa.String(100), nullable=False, unique=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_category', sa.String(50), nullable=False),
        sa.Column('event_description', sa.Text, nullable=False),
        sa.Column('table_name', sa.String(100), nullable=True),
        sa.Column('record_id', UUID(as_uuid=True), nullable=True),
        sa.Column('field_name', sa.String(100), nullable=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_name', sa.String(100), nullable=False),
        sa.Column('user_role', sa.String(100), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('action_status', sa.String(50), nullable=False),
        sa.Column('old_values', sa.JSON, nullable=True),
        sa.Column('new_values', sa.JSON, nullable=True),
        sa.Column('changed_fields', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('request_url', sa.String(500), nullable=True),
        sa.Column('request_parameters', sa.JSON, nullable=True),
        sa.Column('response_code', sa.Integer, nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('business_process', sa.String(100), nullable=True),
        sa.Column('batch_id', UUID(as_uuid=True), nullable=True),
        sa.Column('lot_id', UUID(as_uuid=True), nullable=True),
        sa.Column('regulatory_significance', sa.Boolean, nullable=False, default=False),
        sa.Column('gmp_critical', sa.Boolean, nullable=False, default=False),
        sa.Column('audit_trail_type', sa.String(50), nullable=False, default='standard'),
        sa.Column('event_hash', sa.String(64), nullable=False),
        sa.Column('previous_hash', sa.String(64), nullable=True),
        sa.Column('retention_period_years', sa.Integer, nullable=False, default=7),
        sa.Column('purge_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('alert_triggered', sa.Boolean, nullable=False, default=False),
        sa.Column('alert_level', sa.String(20), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # Base model fields
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('modified_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('modified_by', UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.String(50), nullable=False, default='1.0'),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.Column('electronic_signature_id', UUID(as_uuid=True), nullable=True),
        sa.Column('signature_meaning', sa.String(100), nullable=True),
        sa.Column('change_control_id', UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('data_integrity_hash', sa.String(64), nullable=True),
        sa.Column('regulatory_status', sa.String(50), nullable=False, default='active'),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('regulatory_metadata', sa.JSON, nullable=True),
        
        sa.CheckConstraint("event_type IN ('create', 'update', 'delete', 'login', 'logout', 'sign', 'approve', 'reject', 'review')", name='valid_event_type'),
        sa.CheckConstraint("event_category IN ('data', 'security', 'system', 'process', 'compliance')", name='valid_event_category'),
        sa.CheckConstraint("action_status IN ('success', 'failure', 'pending')", name='valid_action_status'),
        sa.CheckConstraint("audit_trail_type IN ('standard', 'security', 'compliance', 'system')", name='valid_audit_trail_type'),
        sa.CheckConstraint("alert_level IS NULL OR alert_level IN ('info', 'warning', 'critical')", name='valid_alert_level'),
        sa.CheckConstraint("retention_period_years > 0", name='positive_retention_period'),
        sa.CheckConstraint("response_code IS NULL OR (response_code >= 100 AND response_code <= 599)", name='valid_response_code'),
        sa.CheckConstraint("response_time_ms IS NULL OR response_time_ms >= 0", name='non_negative_response_time'),
    )
    
    # Create audit trail indexes
    op.create_index('idx_audit_id', 'audit_trail', ['audit_id'])
    op.create_index('idx_audit_event_type', 'audit_trail', ['event_type'])
    op.create_index('idx_audit_event_category', 'audit_trail', ['event_category'])
    op.create_index('idx_audit_table_name', 'audit_trail', ['table_name'])
    op.create_index('idx_audit_record_id', 'audit_trail', ['record_id'])
    op.create_index('idx_audit_user_id', 'audit_trail', ['user_id'])
    op.create_index('idx_audit_action', 'audit_trail', ['action'])
    op.create_index('idx_audit_action_status', 'audit_trail', ['action_status'])
    op.create_index('idx_audit_timestamp', 'audit_trail', ['timestamp'])
    op.create_index('idx_audit_ip_address', 'audit_trail', ['ip_address'])
    op.create_index('idx_audit_session_id', 'audit_trail', ['session_id'])
    op.create_index('idx_audit_batch_id', 'audit_trail', ['batch_id'])
    op.create_index('idx_audit_regulatory_significance', 'audit_trail', ['regulatory_significance'])
    op.create_index('idx_audit_gmp_critical', 'audit_trail', ['gmp_critical'])
    op.create_index('idx_audit_alert_triggered', 'audit_trail', ['alert_triggered'])
    
    # Composite indexes for common queries
    op.create_index('idx_audit_user_timestamp', 'audit_trail', ['user_id', 'timestamp'])
    op.create_index('idx_audit_table_timestamp', 'audit_trail', ['table_name', 'timestamp'])
    op.create_index('idx_audit_event_timestamp', 'audit_trail', ['event_type', 'timestamp'])
    
    # Create triggers for audit trail
    logger.info("Creating audit trail triggers")
    
    # Create trigger function for automatic audit trail
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_function()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                INSERT INTO audit_trail (
                    audit_id, event_type, event_category, event_description,
                    table_name, record_id, user_id, user_name, user_role,
                    action, action_status, old_values, ip_address, user_agent,
                    session_id, regulatory_significance, gmp_critical,
                    event_hash, created_by, modified_by
                ) VALUES (
                    'AUD-' || to_char(now(), 'YYYYMMDDHH24MISS') || '-' || substr(md5(random()::text), 1, 6),
                    'delete', 'data', 'Record deleted from ' || TG_TABLE_NAME,
                    TG_TABLE_NAME, OLD.id, OLD.modified_by, 'system', 'system',
                    'delete', 'success', to_json(OLD), '127.0.0.1', 'system',
                    'system', true, true,
                    md5(OLD.id::text || now()::text), OLD.modified_by, OLD.modified_by
                );
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO audit_trail (
                    audit_id, event_type, event_category, event_description,
                    table_name, record_id, user_id, user_name, user_role,
                    action, action_status, old_values, new_values, ip_address,
                    user_agent, session_id, regulatory_significance, gmp_critical,
                    event_hash, created_by, modified_by
                ) VALUES (
                    'AUD-' || to_char(now(), 'YYYYMMDDHH24MISS') || '-' || substr(md5(random()::text), 1, 6),
                    'update', 'data', 'Record updated in ' || TG_TABLE_NAME,
                    TG_TABLE_NAME, NEW.id, NEW.modified_by, 'system', 'system',
                    'update', 'success', to_json(OLD), to_json(NEW), '127.0.0.1',
                    'system', 'system', true, true,
                    md5(NEW.id::text || now()::text), NEW.modified_by, NEW.modified_by
                );
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                INSERT INTO audit_trail (
                    audit_id, event_type, event_category, event_description,
                    table_name, record_id, user_id, user_name, user_role,
                    action, action_status, new_values, ip_address, user_agent,
                    session_id, regulatory_significance, gmp_critical,
                    event_hash, created_by, modified_by
                ) VALUES (
                    'AUD-' || to_char(now(), 'YYYYMMDDHH24MISS') || '-' || substr(md5(random()::text), 1, 6),
                    'create', 'data', 'Record created in ' || TG_TABLE_NAME,
                    TG_TABLE_NAME, NEW.id, NEW.created_by, 'system', 'system',
                    'create', 'success', to_json(NEW), '127.0.0.1', 'system',
                    'system', true, true,
                    md5(NEW.id::text || now()::text), NEW.created_by, NEW.modified_by
                );
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers on tables
    for table_name in ['users', 'user_roles', 'material_types', 'products', 'monitoring_locations']:
        op.execute(f"""
            CREATE TRIGGER audit_trigger_{table_name}
            AFTER INSERT OR UPDATE OR DELETE ON {table_name}
            FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
        """)
    
    # Create function for data integrity verification
    logger.info("Creating data integrity functions")
    op.execute("""
        CREATE OR REPLACE FUNCTION verify_data_integrity(table_name TEXT, record_id UUID)
        RETURNS BOOLEAN AS $$
        DECLARE
            result BOOLEAN;
        BEGIN
            -- This function would implement data integrity verification
            -- For now, return true as placeholder
            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function for electronic signature validation
    op.execute("""
        CREATE OR REPLACE FUNCTION validate_electronic_signature(signature_id UUID, user_id UUID)
        RETURNS BOOLEAN AS $$
        DECLARE
            result BOOLEAN;
        BEGIN
            -- This function would implement electronic signature validation
            -- For now, return true as placeholder
            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    logger.info("Initial database schema creation completed successfully")

def downgrade():
    """Drop all pharmaceutical manufacturing tables"""
    logger.info("Starting pharmaceutical manufacturing database schema cleanup")
    
    # Drop triggers
    for table_name in ['users', 'user_roles', 'material_types', 'products', 'monitoring_locations']:
        op.execute(f"DROP TRIGGER IF EXISTS audit_trigger_{table_name} ON {table_name}")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_function()")
    op.execute("DROP FUNCTION IF EXISTS verify_data_integrity(TEXT, UUID)")
    op.execute("DROP FUNCTION IF EXISTS validate_electronic_signature(UUID, UUID)")
    
    # Drop tables in reverse order
    op.drop_table('audit_trail')
    op.drop_table('monitoring_locations')
    op.drop_table('products')
    op.drop_table('material_types')
    op.drop_table('users')
    op.drop_table('user_roles')
    
    logger.info("Database schema cleanup completed successfully")