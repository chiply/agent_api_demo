# Agent API Demo

## Project Overview

FastAPI-based REST API with PostgreSQL backend. Python 3.11+.

## Tech Stack

- **Framework:** FastAPI (async)
- **Database:** PostgreSQL with asyncpg driver
- **ORM:** SQLAlchemy (async sessions via `sqlalchemy.ext.asyncio`)
- **Migrations:** Alembic (configured for async)
- **Testing:** pytest with pytest-asyncio
- **Python:** 3.11+

## Project Structure

```
agent_api_demo/
├── alembic/                # Migration files
│   ├── versions/
│   └── env.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app factory
│   ├── config.py           # Settings via pydantic-settings
│   ├── database.py         # Async engine, session factory
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── routers/            # API route modules
│   └── dependencies.py     # Shared FastAPI dependencies
├── tests/
│   ├── conftest.py         # Fixtures (async client, test DB)
│   └── test_*.py
├── pyproject.toml
└── CLAUDE.md
```

## Development Strategy: TDD

Follow strict Test-Driven Development:

1. **Red** — Write a failing test first that defines the desired behavior
2. **Green** — Write the minimum code to make the test pass
3. **Refactor** — Clean up while keeping tests green

Every feature or bugfix starts with a test. Do not write implementation code without a corresponding test. Run tests after every change.

## Testing

- Use **pytest** with **pytest-asyncio** for all tests
- Use `httpx.AsyncClient` with `ASGITransport` for API integration tests
- Use a separate test database (never the development database)
- Run tests with: `pytest -xvs`
- Run a specific test: `pytest -xvs tests/test_foo.py::test_bar`

## Database Conventions

- All database operations must be async (use `AsyncSession`)
- Create migrations with: `alembic revision --autogenerate -m "description"`
- Apply migrations with: `alembic upgrade head`
- Models go in `app/models/` — one file per domain entity
- Use UUID primary keys

## API Conventions

- All route modules go in `app/routers/`
- Use Pydantic v2 schemas for request validation and response serialization
- Return appropriate HTTP status codes (201 for creation, 204 for deletion, etc.)
- Use FastAPI dependency injection for database sessions

## Observability

The project uses OpenTelemetry for traces and metrics, structured JSON logging with trace correlation, and Grafana LGTM (Loki, Grafana, Tempo, Mimir) as the backend.

Key files: `app/telemetry.py` (OTel SDK), `app/logging_config.py` (JSON logging), `app/middleware.py` (request logging), `docker-compose.observability.yml` (stack), `grafana/` (dashboards and provisioning).

### Starting the stack

```bash
docker compose -f docker-compose.observability.yml up -d
```

This starts the `grafana/otel-lgtm` all-in-one container exposing Grafana on port 3000 and OTLP receivers on ports 4317 (gRPC) and 4318 (HTTP).

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `OTEL_SERVICE_NAME` | `agent-api-demo` | Service name attached to all telemetry |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTLP collector endpoint |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | Export protocol (`http/protobuf` or `grpc`) |
| `OTEL_LOG_LEVEL` | `info` | OTel SDK internal log level |
| `OTEL_SDK_DISABLED` | `false` | Set to `true` to disable the OTel SDK entirely |
| `LOG_LEVEL` | `INFO` | Root Python log level |
| `LOG_LEVEL_<module>` | *(unset)* | Per-module log level override (e.g. `LOG_LEVEL_app.routers=DEBUG`) |

All `OTEL_*` variables are defined in `.env.example`.

### Viewing in Grafana

Open [http://localhost:3000](http://localhost:3000) (no login required with the LGTM image).

- **Dashboards** — A pre-provisioned "API Overview" dashboard is available under Dashboards. It auto-loads from `grafana/dashboards/api-overview.json`.
- **Logs** — Explore > Loki. JSON logs include `trace_id` and `span_id` fields for correlation.
- **Traces** — Explore > Tempo. Search by service name or trace ID. Click a trace ID in a Loki log line to jump directly to the trace.
- **Metrics** — Explore > Mimir/Prometheus. Query OTel metrics by name (e.g. `http_server_duration`).

### Adding custom instrumentation

**Custom span:**

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def my_function():
    with tracer.start_as_current_span("my-operation") as span:
        span.set_attribute("key", "value")
        # ... your code ...
```

**Custom metric:**

```python
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
counter = meter.create_counter("my_counter", description="Counts things")

def do_work():
    counter.add(1, {"some.attribute": "value"})
```

### Health and readiness endpoints

- `GET /health` — Returns `{"status": "ok"}`. Basic liveness check.
- `GET /ready` — Checks connectivity to the OTLP collector. Returns 200 when the collector is reachable, 503 otherwise.

## Verification with curl

After implementing any API endpoint, **always verify it works against a running instance** using curl.

### Running the server

Start a development server bound to a unique port for the current worktree:

```bash
# Pick a port that doesn't conflict with other worktrees (e.g., 8000, 8001, 8002)
uvicorn app.main:app --reload --port <PORT>
```

### curl verification examples

```bash
# Health check
curl -s http://localhost:<PORT>/health | python -m json.tool

# Create a resource
curl -s -X POST http://localhost:<PORT>/resource \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}' | python -m json.tool

# List resources
curl -s http://localhost:<PORT>/resource | python -m json.tool
```

Always confirm the response status code and body match expectations before considering a feature complete.

## Worktree Isolation

This project uses **git worktrees** for parallel feature development. Each worktree must be fully isolated:

- Each worktree gets its own **database** (e.g., `agent_api_dev`, `agent_api_feature_x`)
- Each worktree runs its server on a **unique port** to avoid conflicts
- Use environment variables or `.env` files (gitignored) to configure per-worktree settings:
  - `DATABASE_URL` — unique Postgres database per worktree
  - `PORT` — unique port per worktree
- Never share a database between worktrees — migrations and test data will collide
- Run `alembic upgrade head` in each new worktree after creation

## Autonomous Execution (Ralph)

This project supports autonomous story execution via `/ralph`. When running as a Ralph subagent:

- **Quality checks**: `pytest -xvs` (must pass before committing)
- **Typecheck**: `mypy app/` (if mypy is installed)
- **TDD still applies**: write the test first, then implement
- **Curl verification**: start the server on a unique port and verify endpoints with curl before marking a story complete
- **Per-worktree database**: each subagent worktree needs its own `DATABASE_URL` — use the worktree name as the DB suffix (e.g., `agent_api_worktree_abc`)

### Design docs

Design documents live in `docs/design/` using org-mode format (dev-agent-backlog convention). Convert to Ralph prd.json files with `/design-to-prd`. After Ralph completes, run `/reconcile-ralph` to sync results back to the design doc.

## Workflow

1. Create/switch to a feature branch in a worktree
2. Write a failing test
3. Implement until the test passes
4. Run the full test suite: `pytest -xvs`
5. Start the server and verify with curl
6. Run `/review-loop` to get automated code review feedback and iterate until clean
7. Commit

## Environment Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Required .env variables

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agent_api_dev
```

## Design Doc Workflow

This project uses design docs for task management. Design docs live in `docs/design/`.

### Key Files
- `backlog.org` - Working surface for active tasks
- `docs/design/*.org` - Design documents (source of truth)
- `README.org` - Project config (prefix, categories, statuses)

### Workflow
1. Create design docs with `/backlog:new-design-doc`
2. Queue tasks with `/backlog:task-queue <id>`
3. Start work with `/backlog:task-start <id>`
4. Complete with `/backlog:task-complete <id>`

### Task ID Format
`[AAD-NNN-XX]` where:
- AAD = project prefix
- NNN = design doc number
- XX = task sequence
