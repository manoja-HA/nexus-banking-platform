-- Enable UUID extension (PostgreSQL specific)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create Customers Table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_customer_name UNIQUE (name)
);

-- Create Accounts Table
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL,  
    account_number VARCHAR(50) UNIQUE NOT NULL,
    current_balance DECIMAL(19,4) NOT NULL DEFAULT 0.00 CHECK (current_balance >= 0),
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Create index for account lookup
CREATE INDEX idx_accounts_customer_id ON accounts(customer_id);

-- Create Transfers Table
CREATE TABLE transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_account_id UUID NOT NULL,
    destination_account_id UUID NOT NULL,
    transfer_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    amount DECIMAL(19,4) NOT NULL CHECK (amount > 0),
    description VARCHAR(255),
    is_initial_deposit BOOLEAN NOT NULL DEFAULT FALSE,
    idempotency_key UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_account_id) REFERENCES accounts(id),
    FOREIGN KEY (destination_account_id) REFERENCES accounts(id),
    CONSTRAINT unique_idempotency_key UNIQUE (idempotency_key)
);

-- Create indexes for transfer lookups
CREATE INDEX idx_transfers_source ON transfers(source_account_id, created_at);
CREATE INDEX idx_transfers_destination ON transfers(destination_account_id, created_at);
CREATE INDEX idx_transfers_idempotency ON transfers(idempotency_key);


-- Add function for account version increment
CREATE OR REPLACE FUNCTION increment_account_version()
RETURNS TRIGGER AS $$
BEGIN
   IF OLD.current_balance IS DISTINCT FROM NEW.current_balance THEN
      NEW.version = OLD.version + 1;
   END IF;
   RETURN NEW;
END;

-- Add version increment trigger
CREATE TRIGGER increment_version
BEFORE UPDATE ON accounts
FOR EACH ROW
EXECUTE FUNCTION increment_account_version();

-- Seed initial customer data
INSERT INTO customers (id, name,  created_at)
VALUES 
    (uuid_generate_v4(), 'Arisha Barron',  CURRENT_TIMESTAMP),
    (uuid_generate_v4(), 'Branden Gibson', CURRENT_TIMESTAMP),
    (uuid_generate_v4(), 'Rhonda Church',  CURRENT_TIMESTAMP),
    (uuid_generate_v4(), 'Georgina Hazel',  CURRENT_TIMESTAMP);