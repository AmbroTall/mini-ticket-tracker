# Mini Ticket Tracker

A small support-ticket tracker: a REST API, a PostgreSQL database and a single-page React UI.

| Layer    | Choice                                      |
| -------- | ------------------------------------------- |
| Backend  | Python 3.12, Django 5.2, Django REST Framework, gunicorn |
| Database | PostgreSQL 16                               |
| Frontend | React 18 (Vite), served by nginx in production |
| Packaging| Docker + Docker Compose                     |

## Run it (Docker)

Requires Docker with the Compose plugin.

```bash
cp .env.example .env        # optional; every value has a local default except the secret key you should change for real deployments
docker compose up --build
```

- UI: http://localhost:8080
- API: http://localhost:8000 (for example `curl localhost:8000/tickets/stats`)
- Health check: http://localhost:8000/health

Migrations run automatically when the backend container starts. Stop with `docker compose down` (add `-v` to also delete the database volume).

## Run the tests

```bash
docker compose --profile test run --rm backend-tests
```

This runs 21 API integration tests against a real PostgreSQL instance (create, list/filter/pagination, patch, stats and health).

## Run without Docker (development)

Start only the database, then the two dev servers:

```bash
docker compose up -d db

# Backend (http://localhost:8000)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py runserver
python manage.py test        # in another terminal, same env

# Frontend (http://localhost:5173, proxies /api to the backend)
cd frontend
npm ci
npm run dev
```

## API

All bodies are JSON. Statuses are `open | in_progress | closed`; priorities are `low | medium | high`.

| Method | Path                | Description |
| ------ | ------------------- | ----------- |
| POST   | `/tickets`          | Create a ticket. `title` is required (max 200 chars); `description`, `priority` (default `medium`) are optional. Returns `201`. |
| GET    | `/tickets`          | List tickets, newest first. Query: `status`, `priority`, `page` (default 1), `limit` (default 10, max 100). Returns `{count, next, previous, results}`. |
| PATCH  | `/tickets/<id>`     | Update `status` and/or `priority`. Any other field returns `400`. Returns the full ticket. |
| GET    | `/tickets/stats`    | Ticket counts by status, e.g. `{"open": 4, "in_progress": 2, "closed": 7}`. Statuses with no tickets report `0`. |
| GET    | `/health`           | Liveness/readiness probe; checks the database connection. |

Errors use DRF's standard shape, e.g. `{"title": ["This field may not be blank."]}`. An unknown status filter is a `400`, a page past the end is a `404`.

## Configuration

| Variable | Default | Notes |
| -------- | ------- | ----- |
| `DJANGO_SECRET_KEY` | none | Required unless `DJANGO_DEBUG=1`. The compose file ships a demo value; set your own. |
| `DJANGO_DEBUG` | `0` | Never enable in production. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma separated. |
| `POSTGRES_DB` / `_USER` / `_PASSWORD` / `_HOST` / `_PORT` | `tickets` / `tickets` / `tickets` / `localhost` / `5432` | Compose sets the host to `db`. |
| `WEB_CONCURRENCY` | `2` | gunicorn workers. |

## Project layout

```
backend/    Django project (config/) and the tickets app: models, serializers, filters, views, tests
frontend/   React app (src/), nginx.conf, Dockerfile
docker-compose.yml, .env.example, .github/workflows/ci.yml
```

## Decisions & Tradeoffs

I chose Django with DRF and PostgreSQL because they give validation, migrations, filtering, pagination and a proper test client with very little code, which left time for tests and packaging. PATCH is deliberately strict: it accepts only `status` and `priority` and rejects other fields with a 400 instead of silently ignoring them, and invalid filter values are errors rather than empty results. Pagination is page/limit with a cap of 100, which is simple and fine at this size, but I would move to cursor pagination for large or fast-changing data. `/tickets/stats` runs one grouped query on every call, helped by a `(status, created_at)` index; I would cache it only if it became hot. There is no authentication or per-user scoping because the brief did not ask for it, and that is the first thing I would add, along with rate limiting at the proxy. nginx proxies `/api` to the backend, so the browser stays same-origin and no CORS configuration is needed. Migrations run at container start, which is fine for a single replica; with several replicas I would run them as a separate release step. The UI refetches after each change rather than updating optimistically, and it has no component tests, because I put the testing effort into the API where the logic lives. With more time I would add Playwright end-to-end tests, OpenAPI docs, search, ticket detail and delete, structured logging and metrics.

## Assumptions

- Ticket ids are integers.
- Changing a ticket's priority from the UI is allowed in addition to its status (the API supports both).
- Tickets are never deleted, so there is no `DELETE` endpoint.
