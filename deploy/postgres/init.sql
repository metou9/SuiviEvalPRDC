-- deploy/postgres/init.sql
-- Version avec variables d'environnement

-- Créer les rôles avec les mots de passe du .env
\set metabase_pw `echo "$METABASE_DB_PASSWORD"`
\set metabase_ro_pw `echo "$METABASE_DB_RO_PASSWORD"`
\set postgres_db `echo "$POSTGRES_DB"`
\set postgres_user `echo "$POSTGRES_USER"`

CREATE ROLE metabase_app WITH LOGIN PASSWORD :'metabase_pw';
CREATE DATABASE metabaseappdb OWNER metabase_app;

CREATE ROLE metabase_ro WITH LOGIN PASSWORD :'metabase_ro_pw';

\connect :postgres_db

GRANT CONNECT ON DATABASE :postgres_db TO metabase_ro;
GRANT USAGE ON SCHEMA public TO metabase_ro;

ALTER DEFAULT PRIVILEGES FOR ROLE :postgres_user IN SCHEMA public
    GRANT SELECT ON TABLES TO metabase_ro;