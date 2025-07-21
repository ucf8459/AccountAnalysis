-- Add collector and collector_cost columns to account_data table
ALTER TABLE account_data 
ADD COLUMN IF NOT EXISTS collector CHAR(1) DEFAULT 'N',
ADD COLUMN IF NOT EXISTS collector_cost DECIMAL(10,2) DEFAULT 0.00;

-- Add index for collector column
CREATE INDEX IF NOT EXISTS idx_account_data_collector ON account_data(collector);

-- Add index for collector_cost column
CREATE INDEX IF NOT EXISTS idx_account_data_collector_cost ON account_data(collector_cost); 