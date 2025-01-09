-- Create test database
DROP DATABASE IF EXISTS backtest_test;
CREATE DATABASE backtest_test;

-- Grant privileges to postgres user
ALTER USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE backtest_test TO postgres;

-- Connect to test database
\c backtest_test

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
