# Invoice Management API

[![CI/CD](https://github.com/jrwspina/invoice-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/jrwspina/invoice-api/actions/workflows/ci-cd.yml)

REST API for managing clients, invoices, and payments. Async Python (FastAPI, SQLAlchemy 2.0, asyncpg) on PostgreSQL, with Celery background jobs, Redis caching and rate limiting, deployed on Render with Docker.

Live at **https://invoice-api-1ck2.onrender.com/docs**

## What it does

Authenticated users manage their own clients and invoices: line items, payments, status transitions (draft, sent, paid, overdue), with invoice totals computed dynamically and overdue detection running on a schedule. Auth is JWT (OAuth2 password flow) with ownership checks on every resource. Single-resource reads are cached in Redis (cache-aside, invalidated on writes), all endpoints are rate-limited (per-IP on auth and registration, per-user elsewhere), and list endpoints use bounded, deterministic pagination.

```
Client ──> FastAPI (async) ──> PostgreSQL
              │   └──> Redis (cache / rate limits)
              └──> Celery ──> Redis (broker) ──> worker / beat
```

## Running locally

Requires Docker, Docker Compose, and Python 3.12 for the host-side steps. The supporting services (PostgreSQL, Redis, Celery worker/beat, Mailpit) run in Docker; the web app runs on the host with uvicorn for fast reload.

Initial setup:

```bash
cp .env.example .env
python3.12 -m venv .venv          # Windows: py -3.12 -m venv .venv
source .venv/bin/activate         # Windows: .venv/Scripts/activate
pip install -r requirements-dev.txt
```

Then edit `.env`: set `SECRET_KEY` to a generated value (`openssl rand -hex 32`). Other defaults work as-is for local development.

Start the supporting services:

```bash
docker compose up -d --build
```

Run migrations against the local database:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

API at `http://localhost:8000/docs`, Mailpit (local email capture) at `http://localhost:8025`.

Tests:

```bash
docker compose up -d db test-db redis
pytest --cov
```

The test suite covers endpoints, auth, ownership, rate limiting, and cache behavior (94 tests, ~97% coverage).

## Deployment

Render Blueprint (`render.yaml`) defines five services: the web app, a Celery worker, Celery beat, managed PostgreSQL, and managed Redis (Valkey). One production image serves all three process types, routed by a `MODE` env var in the entrypoint, since Render's Docker runtime has no per-service start commands. Migrations run in the entrypoint too, as the free tier has no pre-deploy hook.
