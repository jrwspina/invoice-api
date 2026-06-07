#!/bin/bash
set -e

if [ "$MODE" = "worker" ]; then
    exec celery -A app.celery worker --loglevel=INFO
elif [ "$MODE" = "beat" ]; then
    exec celery -A app.celery beat --loglevel=INFO
else
    alembic upgrade head
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi