#!/bin/bash
set -e

# Seed default crews (idempotent — skips if already present)
python /app/seed_crews.py

# Start FastAPI sidecar for MCP integration (background)
python /app/api_server.py &

# Start Streamlit (foreground)
exec streamlit run ./app/app.py \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.port 8501
