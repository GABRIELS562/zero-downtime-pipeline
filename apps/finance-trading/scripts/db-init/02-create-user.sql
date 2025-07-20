-- User Creation Script
-- Creates database users with appropriate permissions

-- Create application user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'trading_user') THEN
        CREATE USER trading_user WITH 
            PASSWORD 'trading_password'
            CREATEDB
            NOSUPERUSER
            NOCREATEROLE;
    END IF;
END
$$;

-- Create read-only user for reporting
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'trading_readonly') THEN
        CREATE USER trading_readonly WITH 
            PASSWORD 'readonly_password'
            NOCREATEDB
            NOSUPERUSER
            NOCREATEROLE;
    END IF;
END
$$;

-- Create admin user for maintenance
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'trading_admin') THEN
        CREATE USER trading_admin WITH 
            PASSWORD 'admin_password'
            CREATEDB
            NOSUPERUSER
            CREATEROLE;
    END IF;
END
$$;

-- Grant permissions to trading_user
GRANT CONNECT ON DATABASE trading_db TO trading_user;
GRANT USAGE ON SCHEMA public TO trading_user;
GRANT CREATE ON SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO trading_user;

-- Grant permissions to trading_readonly
GRANT CONNECT ON DATABASE trading_db TO trading_readonly;
GRANT USAGE ON SCHEMA public TO trading_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO trading_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO trading_readonly;

-- Grant permissions to trading_admin
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO trading_admin;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO trading_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO trading_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO trading_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO trading_readonly;

-- Create security policies for row-level security (if needed)
-- These can be enabled per table as needed

-- Log user creation
INSERT INTO audit_logs (
    user_id, event_type, event_description, table_name, 
    retention_until, hash_value, created_at
) VALUES (
    NULL,
    'USER_MANAGEMENT',
    'Database users created and configured',
    'system',
    NOW() + INTERVAL '7 years',
    encode(digest('user_creation', 'sha256'), 'hex'),
    NOW()
);

COMMIT;