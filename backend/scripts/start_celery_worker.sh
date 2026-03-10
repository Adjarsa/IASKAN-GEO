#!/bin/bash
# Celery Worker startup script for IAskan

cd /app/backend

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start Celery worker
exec celery -A app.celery_config worker --loglevel=info --concurrency=2 -Q analysis,llm,processing,celery
