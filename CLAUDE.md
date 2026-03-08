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

## CI/CD

### GitHub Actions

- **test.yml** — Runs `pytest -xvs` on every push/PR to `main`
- **release-please.yml** — Automates version bumps and changelog generation

### Branch Protection (`main`)

- Direct pushes blocked (admin bypass available)
- PRs require 1 approving review, conversation resolution, and `test` status check
- Force pushes and branch deletion are blocked

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) — release-please uses these to determine version bumps and generate changelogs:

- `feat:` — new feature (minor version bump)
- `fix:` — bug fix (patch version bump)
- `chore:` — maintenance (no version bump)
- `ci:` — CI changes (no version bump)
- `docs:` — documentation (no version bump)
- `refactor:` — refactoring (no version bump)
- `test:` — test changes (no version bump)
- Add `!` after the type for breaking changes: `feat!:` (major version bump)

### Release Process

1. Merge PRs to `main` with conventional commit messages
2. release-please automatically creates/updates a release PR
3. Merging the release PR creates a GitHub release and tags the version

## Workflow

1. Create/switch to a feature branch
2. Write a failing test
3. Implement until the test passes
4. Run the full test suite: `pytest -xvs`
5. Start the server and verify with curl
6. Run `/review-loop` to get automated code review feedback and iterate until clean
7. Commit with conventional commit message
8. Push and open a PR to `main`

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
