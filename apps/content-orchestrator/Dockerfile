FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --quiet

# Agents package (workspace dep)
COPY packages/agents/pyproject.toml ./packages/agents/pyproject.toml
COPY packages/agents/src ./packages/agents/src

# Install dependencies
RUN uv pip install --system temporalio fastapi uvicorn[standard] httpx pydantic

# App source
COPY apps/content-orchestrator/src ./src
COPY packages/agents/src/agents ./src/agents

ENV PYTHONPATH=/app/src

EXPOSE 8200

CMD ["python", "-m", "orchestrator.main"]
