# AgentNext Platform

Complete AI Platform — build, route, observe, and bill LLM workflows.

## Architecture

```
User → AgentFlow (7860) → LLM Gateway (4000) → LocalLLM / Claude / OpenAI
                                  ↓
                            ObserveLLM (3150) — traces + tokens
                                  ↓
                            Billing Bridge (8090)
                                  ↓
                            Billing (3200/3201) — invoices
```

## Services

| Service | Component | Port | Purpose |
|---------|-----------|------|---------|
| **AgentFlow** | Langflow | 7860 | AI workflow builder |
| **LLM Gateway** | LiteLLM | 4000 | Unified LLM proxy, virtual keys, spend tracking |
| **ObserveLLM** | Langfuse | 3150 | LLM tracing & observability |
| **LocalLLM** | Ollama | 11434 | Local model inference |
| **Billing** | Lago | 3200/3201 | Usage-based metering & invoicing |
| **Billing Bridge** | Python | 8090 | ObserveLLM → Billing event metering |
| **Mail Server** | Stalwart | 4500 | Email (SMTP/IMAP) |
| **Database** | PostgreSQL | internal | Shared database |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/agentnxxt/platform.git
cd platform

# 2. Configure
cp .env.example .env
# Edit .env — fill in CHANGE_ME values

# 3. Deploy
docker compose up -d

# 4. Setup
# - Open AgentFlow: http://localhost:7860 (admin/admin)
# - Open ObserveLLM: http://localhost:3150 (sign up)
# - Copy ObserveLLM keys → set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env
# - Open Billing: http://localhost:3201 (sign up)
# - Create billable metrics: llm_tokens, api_calls, workflow_runs
# - Create plan + customer + subscription
# - Copy Billing API key → set LAGO_API_KEY in .env
# - Restart: docker compose up -d
```

## Billing Metrics

| Metric | Code | What it counts |
|--------|------|---------------|
| LLM Tokens | `llm_tokens` | Total input + output tokens |
| API Calls | `api_calls` | Each workflow execution |
| Workflow Runs | `workflow_runs` | Each unique workflow run |

## Project Structure

```
platform/
├── docker-compose.yaml    # Full platform stack
├── .env.example           # Environment template
├── gateway/
│   └── config.yaml        # LLM Gateway routing config
├── bridge/
│   └── bridge.py          # ObserveLLM → Billing metering
├── db/
│   └── init-databases.sh  # PostgreSQL init script
└── docs/
    └── test-results.html  # Platform test results
```

## License

MIT
