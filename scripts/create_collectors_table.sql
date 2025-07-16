CREATE TABLE IF NOT EXISTS collectors (
    id SERIAL PRIMARY KEY,
    territory VARCHAR(255),
    practice VARCHAR(255),
    collector VARCHAR(255),
    march_amount NUMERIC(15,2),
    april_amount NUMERIC(15,2),
    may_amount NUMERIC(15,2),
    june_amount NUMERIC(15,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_collectors_territory ON collectors(territory);
CREATE INDEX IF NOT EXISTS idx_collectors_practice ON collectors(practice);
CREATE INDEX IF NOT EXISTS idx_collectors_collector ON collectors(collector); 