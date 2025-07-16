-- Fix mismatched practice names in collectors table
-- Update practice names to match those in account_data table

UPDATE collectors 
SET practice = 'Center for Pain Management' 
WHERE practice = 'Center for Pain Mgmt';

UPDATE collectors 
SET practice = 'Premier Internal Medicine' 
WHERE practice = 'Premier Internal Medicine - Pulaski';

UPDATE collectors 
SET practice = 'Premier Internal Medicine' 
WHERE practice = 'Premier Internal Medicine - Shelbyville';

UPDATE collectors 
SET practice = 'Randall Pain Management' 
WHERE practice = 'Randall Pain Mgmt';

UPDATE collectors 
SET practice = 'Winfield Family Medicine' 
WHERE practice = 'Winfield Family Medical';

-- Verify the updates
SELECT practice, collector, territory FROM collectors ORDER BY practice; 