#!/bin/bash
# Create databases for all platform services
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE agentflow;
    CREATE DATABASE gateway;
    CREATE DATABASE observellm;
    CREATE DATABASE auth;
    CREATE DATABASE agentcrew;
    CREATE DATABASE camunda;
    CREATE DATABASE marquez;
    CREATE DATABASE mlflow;
    CREATE DATABASE argilla;
    CREATE DATABASE temporal;
    CREATE DATABASE temporal_visibility;
    CREATE DATABASE content;
    CREATE DATABASE typebot;
    CREATE DATABASE librechat;
    CREATE DATABASE skyvern;
    CREATE DATABASE agentstudio;
EOSQL

echo "Platform databases created: agentflow, gateway, observellm, auth, agentcrew, camunda, marquez, mlflow, argilla, temporal, temporal_visibility, content, typebot, librechat, skyvern, agentstudio"
