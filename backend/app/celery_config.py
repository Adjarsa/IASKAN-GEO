"""
Celery Configuration for IAskan
Distributed task queue for analysis pipeline
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'iaskan',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.analysis_tasks']
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit at 9 minutes
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Task routing
    task_routes={
        'app.tasks.analysis_tasks.run_full_analysis': {'queue': 'analysis'},
        'app.tasks.analysis_tasks.query_single_llm': {'queue': 'llm'},
        'app.tasks.analysis_tasks.process_analysis_results': {'queue': 'processing'},
    },
    
    # Beat scheduler for periodic tasks
    beat_schedule={
        'check-scheduled-scans': {
            'task': 'app.tasks.analysis_tasks.check_scheduled_scans_task',
            'schedule': 60.0,  # Every minute
        },
    },
)

# Optional: Configure task priority
celery_app.conf.task_default_priority = 5
celery_app.conf.task_queue_max_priority = 10
