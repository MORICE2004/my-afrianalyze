import os
from celery import Celery

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "my_afrianalyze",
    broker=redis_url,
    backend=redis_url,
    include=["apps.api.tasks.research_tasks"]
)

# Configuration for testing
if os.environ.get("APP_ENV") == "TEST":
    celery_app.conf.update(
        task_always_eager=True,
    )
