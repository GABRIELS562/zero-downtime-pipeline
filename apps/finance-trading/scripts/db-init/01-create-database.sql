-- Database Initialization Script
-- Creates the trading database with proper configuration

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE trading_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trading_db')\gexec

-- Create test database if it doesn't exist
SELECT 'CREATE DATABASE trading_db_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trading_db_test')\gexec

-- Connect to the trading database
\c trading_db

-- Create extensions for enhanced functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create custom schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS compliance;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set default search path
ALTER DATABASE trading_db SET search_path TO public, trading, compliance, monitoring;

-- Create custom types and domains
CREATE DOMAIN IF NOT EXISTS price_type AS NUMERIC(20, 8) CHECK (VALUE >= 0);
CREATE DOMAIN IF NOT EXISTS quantity_type AS NUMERIC(20, 8) CHECK (VALUE >= 0);
CREATE DOMAIN IF NOT EXISTS percentage_type AS NUMERIC(5, 4) CHECK (VALUE >= 0 AND VALUE <= 1);

-- Create audit function for SOX compliance
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (
            user_id, event_type, event_description, table_name, 
            record_id, old_values, retention_until, hash_value, created_at
        ) VALUES (
            NULLIF(current_setting('trading.current_user_id', true), '')::uuid,
            'DELETE',
            'Record deleted from ' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            OLD.id,
            to_jsonb(OLD),
            NOW() + INTERVAL '7 years',
            encode(digest(to_jsonb(OLD)::text, 'sha256'), 'hex'),
            NOW()
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (
            user_id, event_type, event_description, table_name, 
            record_id, old_values, new_values, retention_until, hash_value, created_at
        ) VALUES (
            NULLIF(current_setting('trading.current_user_id', true), '')::uuid,
            'UPDATE',
            'Record updated in ' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            NEW.id,
            to_jsonb(OLD),
            to_jsonb(NEW),
            NOW() + INTERVAL '7 years',
            encode(digest((to_jsonb(OLD)::text || to_jsonb(NEW)::text), 'sha256'), 'hex'),
            NOW()
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (
            user_id, event_type, event_description, table_name, 
            record_id, new_values, retention_until, hash_value, created_at
        ) VALUES (
            NULLIF(current_setting('trading.current_user_id', true), '')::uuid,
            'INSERT',
            'Record inserted into ' || TG_TABLE_NAME,
            TG_TABLE_NAME,
            NEW.id,
            to_jsonb(NEW),
            NOW() + INTERVAL '7 years',
            encode(digest(to_jsonb(NEW)::text, 'sha256'), 'hex'),
            NOW()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create performance optimization function
CREATE OR REPLACE FUNCTION optimize_database()
RETURNS void AS $$
BEGIN
    -- Update statistics
    ANALYZE;
    
    -- Reindex if needed
    REINDEX DATABASE trading_db;
    
    -- Vacuum analyze
    VACUUM ANALYZE;
    
    RAISE NOTICE 'Database optimization completed';
END;
$$ LANGUAGE plpgsql;

-- Create function to clean old audit logs
CREATE OR REPLACE FUNCTION cleanup_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '7 years'
    AND retention_until < NOW();
    
    RAISE NOTICE 'Audit log cleanup completed';
END;
$$ LANGUAGE plpgsql;

-- Set up database configuration for optimal performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Create roles for different access levels
CREATE ROLE IF NOT EXISTS trading_read_only;
CREATE ROLE IF NOT EXISTS trading_app_user;
CREATE ROLE IF NOT EXISTS trading_admin;

-- Grant permissions
GRANT CONNECT ON DATABASE trading_db TO trading_read_only;
GRANT USAGE ON SCHEMA public TO trading_read_only;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO trading_read_only;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO trading_read_only;

GRANT CONNECT ON DATABASE trading_db TO trading_app_user;
GRANT USAGE ON SCHEMA public TO trading_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO trading_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO trading_app_user;

GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_admin;

-- Create indexes for commonly queried columns
-- These will be recreated by the application migration scripts
-- but we include them here for immediate setup

-- Log database initialization
INSERT INTO audit_logs (
    user_id, event_type, event_description, table_name, 
    retention_until, hash_value, created_at
) VALUES (
    NULL,
    'DATABASE_INIT',
    'Database initialized with extensions and functions',
    'system',
    NOW() + INTERVAL '7 years',
    encode(digest('database_init', 'sha256'), 'hex'),
    NOW()
);

-- Create system settings table
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('database_version', '1.0.0', 'Database schema version'),
('initialized_at', NOW()::TEXT, 'Database initialization timestamp'),
('audit_enabled', 'true', 'Enable audit logging'),
('sox_compliance', 'true', 'SOX compliance enabled'),
('max_connections', '200', 'Maximum database connections'),
('maintenance_mode', 'false', 'System maintenance mode')
ON CONFLICT (setting_key) DO NOTHING;

-- Create health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details JSONB
) AS $$
BEGIN
    RETURN QUERY SELECT 
        'database_connection'::TEXT,
        'healthy'::TEXT,
        jsonb_build_object(
            'database', current_database(),
            'version', version(),
            'uptime', extract(epoch from (now() - pg_postmaster_start_time())),
            'connections', (SELECT count(*) FROM pg_stat_activity),
            'active_connections', (SELECT count(*) FROM pg_stat_activity WHERE state = 'active')
        );
END;
$$ LANGUAGE plpgsql;

COMMIT;