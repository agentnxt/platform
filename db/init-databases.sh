#!/bin/bash
# Create databases for all platform services
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE agentflow;
    CREATE DATABASE gateway;
    CREATE DATABASE observellm;
    CREATE DATABASE auth;
    CREATE DATABASE agentcrew;
    CREATE DATABASE agentskills;
EOSQL

echo "Platform databases created: agentflow, gateway, observellm, auth, agentcrew, agentskills"
