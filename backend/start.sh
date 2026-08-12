#!/bin/sh

set -eu

echo "Starting AI Root Cause Investigator..."

echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: ${PORT:-8000}"

echo "Validating required configuration..."

: "${SECRET_KEY:?SECRET_KEY must be configured}"
: "${DATABASE_URL:?DATABASE_URL must be configured}"
: "${GROQ_API_KEY:?GROQ_API_KEY must be configured}"

echo "Configuration validation passed."

echo "Running database migrations..."

alembic upgrade head

echo "Database migrations completed."

echo "Starting application..."

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}"