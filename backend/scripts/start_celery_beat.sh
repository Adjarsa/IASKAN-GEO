#!/bin/bash
# Celery Beat scheduler startup script for IAskan

cd /app/backend

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start Celery beat
exec celery -A app.celery_config beat --loglevel=info
