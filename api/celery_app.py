# api/celery_app.py
from celery import Celery
from .config import settings

celery_app = Celery(
  "agent_infra_stack",
  broker=settings.REDIS_URL,
  backend=settings.REDIS_URL,
)

celery_app.conf.update(
  task_serializer="json",
  result_serializer="json",
  accept_content=["json"],
  timezone="UTC"
)