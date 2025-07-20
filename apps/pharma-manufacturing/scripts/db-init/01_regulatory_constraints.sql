-- Pharmaceutical Manufacturing Database Initialization
-- FDA 21 CFR Part 11 Regulatory Constraints and Extensions
-- =================================================================

-- Enable required PostgreSQL extensions for pharmaceutical manufacturing
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create pharmaceutical database schema
CREATE SCHEMA IF NOT EXISTS pharma_manufacturing;
CREATE SCHEMA IF NOT EXISTS pharma_audit;
CREATE SCHEMA IF NOT EXISTS pharma_compliance;

-- Set default schema
SET search_path TO pharma_manufacturing, pharma_audit, pharma_compliance, public;

-- =================================================================
-- FDA 21 CFR Part 11 Compliance Functions
-- =================================================================

-- Function to generate compliant audit trail entries
CREATE OR REPLACE FUNCTION create_audit_trail_entry(
    p_table_name VARCHAR,
    p_record_id UUID,
    p_action VARCHAR,
    p_user_id UUID,
    p_old_values JSONB DEFAULT NULL,
    p_new_values JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    audit_id UUID;
BEGIN
    INSERT INTO pharma_audit.audit_trail (
        id,
        table_name,
        record_id,
        action,
        user_id,
        old_values,
        new_values,
        timestamp,
        data_integrity_hash,
        regulatory_status
    ) VALUES (
        uuid_generate_v4(),
        p_table_name,
        p_record_id,
        p_action,
        p_user_id,
        p_old_values,
        p_new_values,
        NOW() AT TIME ZONE 'UTC',
        encode(digest(concat(p_table_name, p_record_id, p_action, p_user_id)::text, 'sha256'), 'hex'),
        'active'
    ) RETURNING id INTO audit_id;
    
    RETURN audit_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to validate electronic signatures
CREATE OR REPLACE FUNCTION validate_electronic_signature(
    p_signature_id UUID,
    p_user_id UUID,
    p_action VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    is_valid BOOLEAN := FALSE;
BEGIN
    SELECT EXISTS(
        SELECT 1 FROM electronic_signatures 
        WHERE id = p_signature_id 
        AND user_id = p_user_id 
        AND is_valid = TRUE
        AND signature_timestamp >= NOW() - INTERVAL '24 hours'
    ) INTO is_valid;
    
    RETURN is_valid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to calculate data integrity hash
CREATE OR REPLACE FUNCTION calculate_data_integrity_hash(
    p_table_name VARCHAR,
    p_record_data JSONB
) RETURNS VARCHAR AS $$
BEGIN
    RETURN encode(
        digest(
            concat(p_table_name, p_record_data::text)::text, 
            'sha256'
        ), 
        'hex'
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =================================================================
-- Regulatory Compliance Constraints
-- =================================================================

-- Batch number validation constraint
CREATE OR REPLACE FUNCTION validate_batch_number(batch_number VARCHAR) 
RETURNS BOOLEAN AS $$
BEGIN
    -- Batch numbers must follow pharmaceutical industry standards
    -- Format: 2-3 letter prefix + 6-8 digits + optional suffix
    RETURN batch_number ~ '^[A-Z]{2,3}[0-9]{6,8}[A-Z]?$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Lot number validation constraint
CREATE OR REPLACE FUNCTION validate_lot_number(lot_number VARCHAR) 
RETURNS BOOLEAN AS $$
BEGIN
    -- Lot numbers must be unique and follow GMP standards
    RETURN lot_number ~ '^[A-Z0-9]{6,20}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Equipment ID validation
CREATE OR REPLACE FUNCTION validate_equipment_id(equipment_id VARCHAR) 
RETURNS BOOLEAN AS $$
BEGIN
    -- Equipment IDs must follow naming convention
    RETURN equipment_id ~ '^EQ[0-9]{4}[A-Z]{2}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =================================================================
-- Audit Trail Triggers for All Tables
-- =================================================================

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function() 
RETURNS TRIGGER AS $$
DECLARE
    old_values JSONB;
    new_values JSONB;
    action_type VARCHAR;
BEGIN
    -- Determine action type
    IF TG_OP = 'INSERT' THEN
        action_type := 'INSERT';
        old_values := NULL;
        new_values := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        action_type := 'UPDATE';
        old_values := to_jsonb(OLD);
        new_values := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        action_type := 'DELETE';
        old_values := to_jsonb(OLD);
        new_values := NULL;
    END IF;
    
    -- Create audit trail entry
    PERFORM create_audit_trail_entry(
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        action_type,
        COALESCE(NEW.modified_by, OLD.modified_by, '00000000-0000-0000-0000-000000000000'::UUID),
        old_values,
        new_values
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =================================================================
-- Data Integrity and Validation Functions
-- =================================================================

-- Validate manufacturing date ranges
CREATE OR REPLACE FUNCTION validate_manufacturing_dates(
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE
) RETURNS BOOLEAN AS $$
BEGIN
    -- Manufacturing dates must be logical and within reasonable ranges
    RETURN start_date <= end_date 
           AND start_date >= '2020-01-01'::TIMESTAMP WITH TIME ZONE
           AND end_date <= NOW() + INTERVAL '1 year';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Validate temperature ranges for pharmaceutical products
CREATE OR REPLACE FUNCTION validate_temperature_range(
    temperature FLOAT,
    min_temp FLOAT DEFAULT -80.0,
    max_temp FLOAT DEFAULT 100.0
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN temperature BETWEEN min_temp AND max_temp;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Validate pH ranges for pharmaceutical products
CREATE OR REPLACE FUNCTION validate_ph_range(ph_value FLOAT) 
RETURNS BOOLEAN AS $$
BEGIN
    RETURN ph_value BETWEEN 0.0 AND 14.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =================================================================
-- Security and Access Control
-- =================================================================

-- Create pharmaceutical roles
DO $$
BEGIN
    -- Manufacturing Operator Role
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pharma_operator') THEN
        CREATE ROLE pharma_operator;
    END IF;
    
    -- Quality Control Analyst Role
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pharma_qc_analyst') THEN
        CREATE ROLE pharma_qc_analyst;
    END IF;
    
    -- Manufacturing Manager Role
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pharma_manager') THEN
        CREATE ROLE pharma_manager;
    END IF;
    
    -- Compliance Officer Role
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pharma_compliance') THEN
        CREATE ROLE pharma_compliance;
    END IF;
    
    -- System Administrator Role
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'pharma_admin') THEN
        CREATE ROLE pharma_admin;
    END IF;
END $$;

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA pharma_manufacturing TO pharma_operator, pharma_qc_analyst, pharma_manager, pharma_compliance, pharma_admin;
GRANT USAGE ON SCHEMA pharma_audit TO pharma_qc_analyst, pharma_manager, pharma_compliance, pharma_admin;
GRANT USAGE ON SCHEMA pharma_compliance TO pharma_compliance, pharma_admin;

-- =================================================================
-- Regulatory Compliance Views
-- =================================================================

-- View for FDA audit reports
CREATE OR REPLACE VIEW pharma_compliance.fda_audit_view AS
SELECT 
    a.id as audit_id,
    a.table_name,
    a.record_id,
    a.action,
    a.timestamp,
    u.username,
    u.full_name,
    a.old_values,
    a.new_values,
    a.data_integrity_hash,
    es.signature_meaning,
    es.signature_timestamp
FROM pharma_audit.audit_trail a
LEFT JOIN users u ON a.user_id = u.id
LEFT JOIN electronic_signatures es ON a.record_id = es.record_id
WHERE a.regulatory_status = 'active'
ORDER BY a.timestamp DESC;

-- View for GMP compliance monitoring
CREATE OR REPLACE VIEW pharma_compliance.gmp_compliance_view AS
SELECT 
    b.batch_number,
    b.manufacturing_date,
    b.batch_status,
    b.quality_status,
    p.product_name,
    COUNT(bt.id) as test_count,
    COUNT(CASE WHEN bt.test_passed = true THEN 1 END) as passed_tests,
    COUNT(CASE WHEN bt.test_passed = false THEN 1 END) as failed_tests
FROM batches b
JOIN products p ON b.product_id = p.id
LEFT JOIN batch_test_results bt ON b.id = bt.batch_id
WHERE b.is_deleted = false
GROUP BY b.id, b.batch_number, b.manufacturing_date, b.batch_status, b.quality_status, p.product_name;

-- =================================================================
-- Performance Optimization
-- =================================================================

-- Create indexes for pharmaceutical queries
CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON pharma_audit.audit_trail(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_trail_table_record ON pharma_audit.audit_trail(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_user ON pharma_audit.audit_trail(user_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_batch_product_date ON batches(product_id, manufacturing_date);
CREATE INDEX IF NOT EXISTS idx_equipment_calibration_due ON equipment(next_calibration_date) WHERE next_calibration_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_environmental_data_timestamp_location ON environmental_data(timestamp, monitoring_location_id);

-- =================================================================
-- Regulatory Data Retention Policy
-- =================================================================

-- Function to archive old audit records
CREATE OR REPLACE FUNCTION archive_old_audit_records() 
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER := 0;
    cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Archive records older than 7 years (regulatory requirement)
    cutoff_date := NOW() - INTERVAL '7 years';
    
    -- Move old records to archive table
    INSERT INTO pharma_audit.audit_trail_archive 
    SELECT * FROM pharma_audit.audit_trail 
    WHERE timestamp < cutoff_date;
    
    GET DIAGNOSTICS archived_count = ROW_COUNT;
    
    -- Delete archived records from main table
    DELETE FROM pharma_audit.audit_trail 
    WHERE timestamp < cutoff_date;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =================================================================
-- Database Health and Monitoring
-- =================================================================

-- Function to check database health for pharmaceutical operations
CREATE OR REPLACE FUNCTION check_pharma_db_health() 
RETURNS TABLE(
    component VARCHAR,
    status VARCHAR,
    details TEXT
) AS $$
BEGIN
    -- Check connection pool
    RETURN QUERY SELECT 
        'Connection Pool'::VARCHAR,
        CASE WHEN count(*) < 100 THEN 'OK' ELSE 'WARNING' END::VARCHAR,
        ('Active connections: ' || count(*))::TEXT
    FROM pg_stat_activity 
    WHERE state = 'active';
    
    -- Check audit trail integrity
    RETURN QUERY SELECT 
        'Audit Trail'::VARCHAR,
        CASE WHEN count(*) > 0 THEN 'OK' ELSE 'ERROR' END::VARCHAR,
        ('Recent audit entries: ' || count(*))::TEXT
    FROM pharma_audit.audit_trail 
    WHERE timestamp >= NOW() - INTERVAL '1 hour';
    
    -- Check batch processing status
    RETURN QUERY SELECT 
        'Batch Processing'::VARCHAR,
        CASE WHEN count(*) > 0 THEN 'OK' ELSE 'WARNING' END::VARCHAR,
        ('Active batches: ' || count(*))::TEXT
    FROM batches 
    WHERE batch_status IN ('in_progress', 'processing') 
    AND is_deleted = false;
    
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION create_audit_trail_entry TO pharma_operator, pharma_qc_analyst, pharma_manager, pharma_compliance, pharma_admin;
GRANT EXECUTE ON FUNCTION validate_electronic_signature TO pharma_operator, pharma_qc_analyst, pharma_manager, pharma_compliance, pharma_admin;
GRANT EXECUTE ON FUNCTION check_pharma_db_health TO pharma_manager, pharma_compliance, pharma_admin;

-- Set up row level security for sensitive data
ALTER TABLE electronic_signatures ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_trail ENABLE ROW LEVEL SECURITY;

-- Create policies for row level security
CREATE POLICY audit_trail_policy ON pharma_audit.audit_trail
    FOR ALL TO pharma_compliance, pharma_admin
    USING (true);

CREATE POLICY signature_policy ON electronic_signatures
    FOR ALL TO pharma_operator, pharma_qc_analyst, pharma_manager, pharma_compliance, pharma_admin
    USING (user_id = current_setting('app.current_user_id')::UUID OR pg_has_role('pharma_compliance', 'MEMBER'));

-- Final setup message
DO $$
BEGIN
    RAISE NOTICE 'Pharmaceutical Manufacturing Database initialized successfully with FDA 21 CFR Part 11 compliance features';
    RAISE NOTICE 'Regulatory constraints, audit trails, and security policies are now active';
END $$;