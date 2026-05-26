import os
from celery import Celery
import logging

logger = logging.getLogger(__name__)

# Valkey/Redis URL (e.g. redis://localhost:6379/0)
VALKEY_URL = os.getenv("VALKEY_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "app_q_tasks",
    broker=VALKEY_URL,
    backend=VALKEY_URL,
    include=["packages.research_engine.gateway"]  # We will put tasks in gateway.py or tasks.py
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    # Worker constraints to avoid OOM for heavy LLM tasks
    worker_concurrency=int(os.getenv("CELERY_CONCURRENCY", "1")), # 1 worker per GPU by default
    worker_prefetch_multiplier=1, # Don't fetch multiple tasks per worker
    task_acks_late=True, # Acknowledge only after successful completion
    task_reject_on_worker_lost=True,
)

if __name__ == '__main__':
    celery_app.start()
