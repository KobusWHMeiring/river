-- 1. Create DB and User
CREATE DATABASE river_db;
CREATE USER river_user WITH PASSWORD 'L30sPohi2OodEyu2';
GRANT ALL PRIVILEGES ON DATABASE river_db TO river_user;

-- 2. Move INTO the new database (CRITICAL)
\c river_db

-- 3. Grant the internal permissions
GRANT ALL ON SCHEMA public TO river_user;
ALTER DATABASE river_db OWNER TO river_user;
\q
