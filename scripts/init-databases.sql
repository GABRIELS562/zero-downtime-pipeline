-- Initialize databases for Zero-Downtime Pipeline applications
-- This script creates separate databases and users for each application
-- with appropriate permissions for forensic audit trails

-- Create Trading Database and User
CREATE DATABASE trading_db;
CREATE USER trading_user WITH ENCRYPTED PASSWORD 'trading_pass';
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;

-- Create Pharma Manufacturing Database and User
CREATE DATABASE pharma_db;
CREATE USER pharma_user WITH ENCRYPTED PASSWORD 'pharma_pass';
GRANT ALL PRIVILEGES ON DATABASE pharma_db TO pharma_user;

-- Create Audit Database for Forensic Evidence
CREATE DATABASE audit_db;
CREATE USER audit_user WITH ENCRYPTED PASSWORD 'audit_pass';
GRANT ALL PRIVILEGES ON DATABASE audit_db TO audit_user;

-- Switch to Trading Database
\c trading_db;

-- Trading Tables
CREATE TABLE IF NOT EXISTS trading_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    currency VARCHAR(10),
    desk VARCHAR(50),
    trader_id VARCHAR(50),
    session_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL, -- 'BUY' or 'SELL'
    quantity DECIMAL(15,2) NOT NULL,
    price DECIMAL(15,6) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    desk VARCHAR(50),
    trader_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(15,6) NOT NULL,
    volume BIGINT NOT NULL,
    bid DECIMAL(15,6),
    ask DECIMAL(15,6),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source VARCHAR(50)
);

-- Grant permissions to trading user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;

-- Switch to Pharma Database
\c pharma_db;

-- Pharma Manufacturing Tables
CREATE TABLE IF NOT EXISTS manufacturing_lines (
    id SERIAL PRIMARY KEY,
    line_id VARCHAR(50) UNIQUE NOT NULL,
    line_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    capacity_units_per_hour INTEGER,
    efficiency_threshold DECIMAL(5,2) DEFAULT 98.0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL,
    line_id VARCHAR(50) REFERENCES manufacturing_lines(line_id),
    sensor_type VARCHAR(50) NOT NULL, -- 'temperature', 'pressure', 'humidity'
    value DECIMAL(10,3) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    min_threshold DECIMAL(10,3),
    max_threshold DECIMAL(10,3),
    is_critical BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'normal',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS batch_records (
    id SERIAL PRIMARY KEY,
    batch_id VARCHAR(100) UNIQUE NOT NULL,
    line_id VARCHAR(50) REFERENCES manufacturing_lines(line_id),
    product_code VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    planned_quantity INTEGER,
    actual_quantity INTEGER,
    efficiency_percent DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    integrity_score DECIMAL(5,2) DEFAULT 100.0,
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS compliance_records (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR(50) NOT NULL, -- 'FDA_21_CFR_11', 'GMP', 'AUDIT'
    reference_id VARCHAR(100) NOT NULL,
    validation_status VARCHAR(20) DEFAULT 'pending',
    digital_signature TEXT,
    validator_id VARCHAR(50),
    validation_timestamp TIMESTAMP WITH TIME ZONE,
    retention_until DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert sample manufacturing line
INSERT INTO manufacturing_lines (line_id, line_name, location, capacity_units_per_hour) 
VALUES ('LINE-001-PHARMA-PROD', 'Primary Production Line', 'Building A - Floor 2', 1000);

-- Grant permissions to pharma user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pharma_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pharma_user;

-- Switch to Audit Database
\c audit_db;

-- Audit and Forensic Tables
CREATE TABLE IF NOT EXISTS deployment_audits (
    id SERIAL PRIMARY KEY,
    deployment_id VARCHAR(100) UNIQUE NOT NULL,
    application VARCHAR(50) NOT NULL,
    environment VARCHAR(20) NOT NULL,
    version VARCHAR(50),
    git_commit VARCHAR(40),
    initiated_by VARCHAR(100),
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL, -- 'in_progress', 'success', 'failed', 'rolled_back'
    risk_score INTEGER,
    risk_level VARCHAR(20),
    approval_required BOOLEAN DEFAULT false,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP WITH TIME ZONE,
    rollback_reason TEXT,
    evidence_location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'vulnerability_scan', 'compliance_check', 'access_attempt'
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    source_ip INET,
    user_id VARCHAR(100),
    resource VARCHAR(200),
    action VARCHAR(100),
    result VARCHAR(50),
    details JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    investigated BOOLEAN DEFAULT false,
    investigator VARCHAR(100),
    investigation_notes TEXT
);

CREATE TABLE IF NOT EXISTS compliance_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    compliance_type VARCHAR(50) NOT NULL, -- 'FDA_21_CFR_11', 'SOX', 'SECURITY'
    event_description TEXT NOT NULL,
    affected_system VARCHAR(100),
    compliance_status VARCHAR(20), -- 'compliant', 'non_compliant', 'pending'
    remediation_required BOOLEAN DEFAULT false,
    remediation_notes TEXT,
    validator VARCHAR(100),
    validation_timestamp TIMESTAMP WITH TIME ZONE,
    retention_period INTERVAL DEFAULT '7 years',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS business_metrics (
    id SERIAL PRIMARY KEY,
    metric_id VARCHAR(100) NOT NULL,
    application VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'revenue', 'efficiency', 'latency', 'success_rate'
    metric_value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(20),
    baseline_value DECIMAL(15,6),
    threshold_value DECIMAL(15,6),
    impact_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    deployment_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_deployment_audits_application ON deployment_audits(application);
CREATE INDEX idx_deployment_audits_status ON deployment_audits(status);
CREATE INDEX idx_deployment_audits_initiated_at ON deployment_audits(initiated_at);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_timestamp ON security_events(timestamp);
CREATE INDEX idx_compliance_events_type ON compliance_events(compliance_type);
CREATE INDEX idx_business_metrics_application ON business_metrics(application);
CREATE INDEX idx_business_metrics_timestamp ON business_metrics(timestamp);

-- Grant permissions to audit user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO audit_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO audit_user;

-- Insert sample data for development/testing
INSERT INTO deployment_audits (
    deployment_id, application, environment, version, git_commit, 
    initiated_by, status, risk_score, risk_level
) VALUES 
    ('deploy-001', 'finance-trading', 'development', '1.0.0', 'abc123def456', 'developer@company.com', 'success', 25, 'low'),
    ('deploy-002', 'pharma-manufacturing', 'development', '1.0.0', 'def456ghi789', 'developer@company.com', 'success', 35, 'medium');

INSERT INTO compliance_events (
    event_id, compliance_type, event_description, affected_system, compliance_status, validator
) VALUES 
    ('comp-001', 'FDA_21_CFR_11', 'Electronic records validation completed', 'pharma-manufacturing', 'compliant', 'compliance-engine'),
    ('comp-002', 'SOX', 'Financial controls validation completed', 'finance-trading', 'compliant', 'compliance-engine');

-- Back to main postgres database for final setup
\c postgres;

-- Create read-only forensic analyst role
CREATE ROLE forensic_analyst WITH LOGIN PASSWORD 'forensic_pass';
GRANT CONNECT ON DATABASE audit_db TO forensic_analyst;
\c audit_db;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO forensic_analyst;

-- Create monitoring role for Prometheus/Grafana
\c postgres;
CREATE ROLE monitoring_user WITH LOGIN PASSWORD 'monitoring_pass';
GRANT CONNECT ON DATABASE trading_db TO monitoring_user;
GRANT CONNECT ON DATABASE pharma_db TO monitoring_user;
GRANT CONNECT ON DATABASE audit_db TO monitoring_user;

\c trading_db;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;

\c pharma_db;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;

\c audit_db;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring_user;