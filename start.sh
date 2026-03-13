#!/bin/bash

# IAskan - Railway Startup Script
# This script determines which service to start based on the SERVICE environment variable

set -e

SERVICE=${SERVICE:-"backend"}

echo "Starting IAskan service: $SERVICE"

case "$SERVICE" in
  "backend")
    echo "Starting FastAPI backend..."
    cd backend
    python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}
    ;;
  "frontend")
    echo "Starting React frontend..."
    cd frontend
    yarn start
    ;;
  "celery-worker")
    echo "Starting Celery worker..."
    cd backend
    celery -A app.core.celery_app worker --loglevel=info
    ;;
  "celery-beat")
    echo "Starting Celery beat scheduler..."
    cd backend
    celery -A app.core.celery_app beat --loglevel=info
    ;;
  *)
    echo "Unknown service: $SERVICE"
    echo "Available services: backend, frontend, celery-worker, celery-beat"
    exit 1
    ;;
esac
