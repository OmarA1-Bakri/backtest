-- Create user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'postgres') THEN
      CREATE ROLE postgres LOGIN PASSWORD 'postgres';
   END IF;
END
$do$;

-- Grant necessary privileges
ALTER ROLE postgres WITH SUPERUSER;

-- Create main database if not exists
SELECT 'CREATE DATABASE backtest'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'backtest');

-- Create test database if not exists
SELECT 'CREATE DATABASE backtest_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'backtest_test');
