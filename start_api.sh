#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
