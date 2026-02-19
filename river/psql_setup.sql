-- PostgreSQL Setup for river
-- Run these commands on your PostgreSQL server

-- 1. Create DB and User
CREATE DATABASE river_db;
CREATE USER river_user WITH PASSWORD '63Fkxo4JorzkIhS2';
GRANT ALL PRIVILEGES ON DATABASE river_db TO river_user;

-- 2. Connect to the new database (CRITICAL STEP)
\c river_db

-- 3. Grant schema permissions
GRANT ALL ON SCHEMA public TO river_user;
ALTER DATABASE river_db OWNER TO river_user;

-- 4. Exit
\q
