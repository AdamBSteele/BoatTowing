#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE terraintracker;
    \c terraintracker;
    CREATE EXTENSION postgis;
EOSQL
