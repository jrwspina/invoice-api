# Invoice Management API

[![CI/CD](https://github.com/jrwspina/invoice-api/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/jrwspina/invoice-api/actions/workflows/ci-cd.yml)

REST API for managing clients, invoices, and payments. Async Python (FastAPI, SQLAlchemy 2.0, asyncpg) on PostgreSQL, with Celery background jobs, Redis caching and rate limiting, deployed on Render with Docker, with an AWS deployment (ECS Fargate, RDS, CI/CD) documented below.

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

The test suite covers endpoints, auth, ownership, rate limiting, and cache behavior (95 tests, ~97% coverage).

## AWS Deployment

Deployed to AWS using ECR for image storage, running on ECS Fargate (app + Redis sidecar) backed by RDS PostgreSQL and fronted by an ALB. The infrastructure is fully codified in Terraform ([`infra/`](infra/)): `terraform apply` recreates the stack, `terraform destroy` removes it, so it runs on demand rather than 24/7.

### Typical request path

```
Internet -> ALB :80 -> app :8000 (ALB Security Group only) -> RDS :5432 (app Security Group only)
```

The ALB health-checks a liveness-only /health endpoint; no dependency checks, so a database outage degrades responses instead of triggering a restart cycle.

### Deployment pipeline
```
push to main -> 95 tests -> image built (Dockerfile.prod) -> tagged sha + latest -> push to ECR -> new deployment forced on the ECS service -> waits for service stability; auto-rollback on failure.
```

This repository keeps no AWS secrets; each workflow run presents a GitHub-signed identity token to AWS STS and receives temporary credentials, via an IAM role whose trust policy only accepts this repo's main branch.

### Known gaps

- IP-keyed rate limiting behind the ALB collapses all anonymous users into one bucket (the app sees the ALB's IP). Authenticated routes key on username; fix for anonymous traffic is keying on X-Forwarded-For.

- HTTP only; HTTPS deferred since it needs a domain for an ACM certificate; production would terminate TLS at the ALB with a 443 listener and redirect from 80.

- Config and credentials live as plaintext env vars in the task definition (injected via Terraform variables); production would use Secrets Manager or SSM Parameter Store.

- Backups + Multi-AZ off on RDS to keep costs minimal.

## Render Deployment

Render Blueprint (`render.yaml`) defines five services: the web app, a Celery worker, Celery beat, managed PostgreSQL, and managed Redis (Valkey). One production image serves all three process types, routed by a `MODE` env var in the entrypoint, since Render's Docker runtime has no per-service start commands. Migrations run in the entrypoint too, as the free tier has no pre-deploy hook.
