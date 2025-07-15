-- Account Analysis Database Schema
-- PostgreSQL database with raw, staging, and analytics schemas

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS auth;

-- Raw Tables (unprocessed data from sources)
CREATE TABLE IF NOT EXISTS raw.qbo_transactions (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(255) UNIQUE,
    customer_name VARCHAR(255),
    account_name VARCHAR(255),
    amount NUMERIC(15,2),
    txn_date DATE,
    txn_type VARCHAR(100),
    description TEXT,
    raw_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.external_reports (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255),
    file_name VARCHAR(255),
    file_date DATE,
    file_size BIGINT,
    raw_content TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Staging Tables (cleaned and transformed data)
CREATE TABLE IF NOT EXISTS staging.transactions_cleaned (
    id SERIAL PRIMARY KEY,
    qbo_id VARCHAR(255),
    customer_id VARCHAR(255),
    account_id VARCHAR(255),
    amount NUMERIC(15,2),
    txn_date DATE,
    region VARCHAR(255),
    territory VARCHAR(255),
    sales_rep VARCHAR(255),
    product_category VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.external_data_cleaned (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(255),
    metric_name VARCHAR(255),
    metric_value NUMERIC(15,2),
    metric_date DATE,
    account_id VARCHAR(255),
    territory VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Account to Territory/Rep Mapping Table
CREATE TABLE IF NOT EXISTS staging.account_territory_mapping (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(255) UNIQUE NOT NULL,
    sales_rep_name VARCHAR(255),
    sales_rep_id VARCHAR(255),
    territory_name VARCHAR(255),
    territory_id VARCHAR(255),
    region VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- QBO OAuth Tokens Table
CREATE TABLE IF NOT EXISTS staging.qbo_tokens (
    user_id INTEGER NOT NULL,
    realm_id VARCHAR(64) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, realm_id)
);

-- Analytics Tables (aggregated data for dashboards)
CREATE TABLE IF NOT EXISTS analytics.financial_summary (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255),
    account_id VARCHAR(255),
    total_revenue NUMERIC(15,2),
    total_cogs NUMERIC(15,2),
    total_expenses NUMERIC(15,2),
    gross_profit NUMERIC(15,2),
    net_profit NUMERIC(15,2),
    period_start DATE,
    period_end DATE,
    region VARCHAR(255),
    territory VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.territory_performance (
    id SERIAL PRIMARY KEY,
    territory_name VARCHAR(255),
    total_sales NUMERIC(15,2),
    num_accounts INTEGER,
    avg_revenue_per_account NUMERIC(15,2),
    report_date DATE,
    period_type VARCHAR(50), -- daily, weekly, monthly
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics.account_kpis (
    id SERIAL PRIMARY KEY,
    account_id VARCHAR(255),
    account_name VARCHAR(255),
    revenue_per_sample NUMERIC(15,2),
    cost_of_sale NUMERIC(15,2),
    billing_per_sample NUMERIC(15,2),
    collection_rate NUMERIC(5,2), -- percentage
    territory VARCHAR(255),
    report_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Authentication and User Management
CREATE TABLE IF NOT EXISTS auth.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- finance, sales_management, sales_team
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auth.user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth.users(id),
    session_token VARCHAR(255) UNIQUE,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data Quality and Monitoring
CREATE TABLE IF NOT EXISTS staging.data_quality_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255),
    check_type VARCHAR(100),
    records_processed INTEGER,
    records_failed INTEGER,
    error_details JSONB,
    check_date TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS staging.etl_job_log (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255),
    status VARCHAR(50), -- success, failed, running
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    records_processed INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_qbo_transactions_date ON raw.qbo_transactions(txn_date);
CREATE INDEX IF NOT EXISTS idx_qbo_transactions_customer ON raw.qbo_transactions(customer_name);
CREATE INDEX IF NOT EXISTS idx_qbo_transactions_qbo_id ON raw.qbo_transactions(qbo_id);

CREATE INDEX IF NOT EXISTS idx_transactions_cleaned_date ON staging.transactions_cleaned(txn_date);
CREATE INDEX IF NOT EXISTS idx_transactions_cleaned_territory ON staging.transactions_cleaned(territory);
CREATE INDEX IF NOT EXISTS idx_transactions_cleaned_customer ON staging.transactions_cleaned(customer_id);

CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_account ON staging.account_territory_mapping(account_number);
CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_rep ON staging.account_territory_mapping(sales_rep_name);
CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_territory ON staging.account_territory_mapping(territory_name);
CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_active ON staging.account_territory_mapping(is_active);

CREATE INDEX IF NOT EXISTS idx_financial_summary_period ON analytics.financial_summary(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_financial_summary_territory ON analytics.financial_summary(territory);
CREATE INDEX IF NOT EXISTS idx_financial_summary_account ON analytics.financial_summary(account_id);

CREATE INDEX IF NOT EXISTS idx_territory_performance_date ON analytics.territory_performance(report_date);
CREATE INDEX IF NOT EXISTS idx_territory_performance_name ON analytics.territory_performance(territory_name);

CREATE INDEX IF NOT EXISTS idx_account_kpis_date ON analytics.account_kpis(report_date);
CREATE INDEX IF NOT EXISTS idx_account_kpis_account ON analytics.account_kpis(account_id);

-- Sample data for testing (optional)
INSERT INTO auth.users (username, email, password_hash, role) VALUES
('admin', 'admin@company.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJhHm2', 'finance'),
('sales_manager', 'sales@company.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJhHm2', 'sales_management'),
('sales_rep', 'rep@company.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJhHm2', 'sales_team')
ON CONFLICT (username) DO NOTHING; 