from celery import Celery

from src.core.config import get_settings


settings = get_settings()
celery_app = Celery(
    "file_tasks",
    broker=settings.celery_broker_url,
    backend=settings.result_backend,
)
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    task_track_started=True,
)
