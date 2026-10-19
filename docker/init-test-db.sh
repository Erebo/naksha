#!/bin/bash
set -e

# Create secondary test database and grant privileges
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE naksha_test;
    GRANT ALL PRIVILEGES ON DATABASE naksha_test TO "$POSTGRES_USER";
EOSQL

# Enable PostGIS in both databases
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "naksha_test" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
EOSQL
