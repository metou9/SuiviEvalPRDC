-- deploy/postgres/init.sql
-- (variables METABASE_DB_PASSWORD / METABASE_DB_RO_PASSWORD are provided via env;
--  the official image substitutes them using the POSTGRES_* mechanism. If your image
--  version does not, replace the :'var' placeholders with literals or use an env_file.)

-- 1. Metabase's own metadata database + owner -------------------------------
CREATE ROLE metabase_app LOGIN PASSWORD :'METABASE_DB_PASSWORD';
CREATE DATABASE metabaseappdb OWNER metabase_app;

-- 2. Read-only role the BI tool uses to read the APPLICATION database --------
CREATE ROLE metabase_ro LOGIN PASSWORD :'METABASE_DB_RO_PASSWORD';

-- Grants on the application database (run inside it):
\connect :"POSTGRES_DB"

GRANT CONNECT ON DATABASE :"POSTGRES_DB" TO metabase_ro;
GRANT USAGE ON SCHEMA public TO metabase_ro;

-- The reporting VIEWS are created later by Django migrations; the migration that
-- creates them also GRANTs SELECT to metabase_ro (see 06 §6.1). As a safety net,
-- default privileges ensure any view the app owner creates is readable:
ALTER DEFAULT PRIVILEGES FOR ROLE :"POSTGRES_USER" IN SCHEMA public
    GRANT SELECT ON TABLES TO metabase_ro;

-- IMPORTANT: metabase_ro is intentionally NOT granted SELECT on base tables.
-- Dashboards read only the v_* reporting views.
