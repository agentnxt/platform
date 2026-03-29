FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --quiet

# Agents package (workspace dep)
COPY packages/agents/pyproject.toml ./packages/agents/pyproject.toml
COPY packages/agents/src ./packages/agents/src

# App manifest
COPY apps/content-api/pyproject.toml ./pyproject.toml

# Install dependencies
RUN uv pip install --system fastapi uvicorn[standard] httpx pydantic pydantic-settings

# App source
COPY apps/content-api/src ./src
COPY packages/agents/src/agents ./src/agents

ENV PYTHONPATH=/app/src

EXPOSE 8100

CMD ["uvicorn", "content_api.main:app", "--host", "0.0.0.0", "--port", "8100"]
