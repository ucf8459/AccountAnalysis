-- Create COGS Expense table
CREATE TABLE IF NOT EXISTS cogs_expense (
    id SERIAL PRIMARY KEY,
    territory VARCHAR(50) NOT NULL,
    month_year VARCHAR(20) NOT NULL,
    expense_type VARCHAR(20) NOT NULL, -- 'COGS' or 'Expense'
    amount DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_cogs_expense_territory ON cogs_expense(territory);
CREATE INDEX IF NOT EXISTS idx_cogs_expense_month_year ON cogs_expense(month_year);
CREATE INDEX IF NOT EXISTS idx_cogs_expense_type ON cogs_expense(expense_type);
CREATE INDEX IF NOT EXISTS idx_cogs_expense_territory_month ON cogs_expense(territory, month_year);

-- Add unique constraint to prevent duplicate entries
ALTER TABLE cogs_expense ADD CONSTRAINT unique_territory_month_type 
UNIQUE (territory, month_year, expense_type); 