<div align="center">

# ◈ File Exchange

### Refactored fullstack file-exchange MVP

**Layered FastAPI backend · Parallel Celery chord processing · Next.js frontend**

[![CI](https://github.com/Alpha-Oi/fullstack-test-task-solution/actions/workflows/ci.yml/badge.svg)](https://github.com/Alpha-Oi/fullstack-test-task-solution/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-22a06b.svg)](LICENSE)
[![Last commit](https://img.shields.io/github/last-commit/Alpha-Oi/fullstack-test-task-solution?color=1f6feb)](https://github.com/Alpha-Oi/fullstack-test-task-solution/commits/main)

[English](README.md) · [Русский](README.ru.md) · [Contributing](CONTRIBUTING.md) · [Conduct](CODE_OF_CONDUCT.md) · [Security](SECURITY.md)

</div>

---

A refactoring of the MVP file exchange from the original
[test task](https://github.com/sputnik-llc/fullstack-test-task). The application
uploads and stores files, checks their traits asynchronously, extracts metadata, and
raises alerts.

## What was done

- the backend is split into HTTP, application, domain, and infrastructure layers;
- the original endpoints, response models, and file-check rules are preserved;
- uploads stream in 1 MiB chunks without reading the whole file into memory;
- blocking file processing is moved off the event loop;
- database, Redis, CORS, and storage configuration is centralized;
- the Docker setup for PostgreSQL, Redis, and the frontend build is fixed;
- deleting a file cascades to its alerts;
- indexes are added for sorting files and alerts by date;
- the frontend is split into API, hooks, features, components, lib, and types;
- backend tests, frontend typecheck, and CI are added.

## Backend architecture

```text
src/
├── api/              # FastAPI routers and dependency wiring
├── services/         # file use cases and content processing
├── domain/           # domain errors and statuses
├── infrastructure/   # SQLAlchemy repositories and file storage
├── workers/          # Celery app and background tasks
├── core/             # configuration and a single DB session factory
├── models.py         # ORM models
├── schemas.py        # API schemas
└── app.py            # composition root
```

The API layer only handles HTTP. `FileService` coordinates use cases and transaction
boundaries. Repositories encapsulate SQLAlchemy queries, and `LocalFileStorage`
encapsulates disk access. The pure check and metadata-extraction functions are tested
apart from Celery and the database.

## Additional optimization

In the original implementation the background stages ran sequentially:

```text
scan → metadata → alert
```

Threat-trait checking uses data from the database, and metadata extraction reads the
stored file. These operations do not depend on each other, so the workflow is rebuilt
as a Celery chord:

```text
mark processing → (scan ‖ metadata) → finalize + alert
```

This reduces total processing latency to the slower of the two stages instead of their
sum. Redis is used both as the broker and as the result backend required for chord
synchronization. The backend and the worker also share one SQLAlchemy session factory
instead of duplicate engines and pools.

## Frontend architecture

```text
src/
├── app/              # Next.js page and layout
├── api/              # HTTP client
├── hooks/            # page state and orchestration
├── features/         # the upload user flow
├── components/       # tables and presentation components
├── lib/              # formatting and UI helpers
└── types/            # API types
```

Components do not know the API address and hold no network logic. Page state lives in
`useFileDashboard`, and the upload form is isolated as a feature.

## Running

Requires Docker with the Compose plugin.

```bash
docker compose -f docker-compose.dev.yml up --build
```

In another terminal, apply the migrations:

```bash
docker exec -it backend alembic upgrade head
```

After startup:

- frontend: <http://localhost:3000/test>
- Swagger UI: <http://localhost:8000/docs>

PostgreSQL is reachable only by services inside the Docker network on the standard
port `5432`.

## Checks

Backend:

```bash
cd backend
uv sync --group dev
uv run ruff check .
uv run pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

Tests cover CRUD and download through the API, cascade deletion of alerts, streaming
storage, the check rules, text and PDF metadata extraction, and the structure of the
parallel Celery workflow.

## Preserved business logic

- `.exe`, `.bat`, `.cmd`, `.sh`, `.js` are treated as suspicious;
- a file larger than 10 MiB needs attention;
- a mismatch between a `.pdf` extension and the MIME type needs attention;
- `line_count` and `char_count` are computed for text;
- the page count is estimated for PDFs;
- the processing result raises an `info`, `warning`, or `critical` alert.

## MVP limitations

The check is based on file traits and is not an antivirus. Local storage suits a
single node; in a distributed setup the adapter can be swapped for S3-compatible
storage without changing the HTTP or application layers. To guarantee task delivery
when the database and the broker fail at the same time, the next step would be a
transactional outbox.
