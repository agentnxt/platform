#!/bin/bash
# Create databases for all platform services
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE agentflow;
    CREATE DATABASE gateway;
    CREATE DATABASE observellm;
EOSQL

echo "Platform databases created: agentflow, gateway, observellm"
