-- Drop triggers
DROP TRIGGER IF EXISTS increment_version ON accounts;

-- Drop functions
DROP FUNCTION IF EXISTS increment_account_version();

-- Drop tables 
DROP TABLE IF EXISTS transfers;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS customers;
