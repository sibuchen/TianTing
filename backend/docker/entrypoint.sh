#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -U sibuchen; do
    sleep 1
done

echo "PostgreSQL is ready!"

if ! npx --version 2>/dev/null; then
    echo "WARNING: npx not found. MCP stdio servers will not work. Rebuild the backend image: docker compose build --no-cache backend && docker compose up -d"
fi

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 2811
