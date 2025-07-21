-- Add Account Territory Mapping Table to existing healthtech database
-- Run this script to add the new table without affecting existing data

-- Create staging schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS staging;

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

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_account ON staging.account_territory_mapping(account_number);
CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_rep ON staging.account_territory_mapping(sales_rep_name);
CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_territory ON staging.account_territory_mapping(territory_name);
CREATE INDEX IF NOT EXISTS idx_account_territory_mapping_active ON staging.account_territory_mapping(is_active);

-- Verify the table was created
SELECT 'Table staging.account_territory_mapping created successfully!' as status; 