from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "gazprom_test",
    broker=settings.celery_broker_url,
    include=["app.infrastructure.tasks"],
)

celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    task_ignore_result=True,
    task_always_eager=settings.celery_task_always_eager,
    timezone="UTC",
    enable_utc=True,
)
