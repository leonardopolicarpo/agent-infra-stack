import json
import logging

import psycopg

from .celery_app import celery_app
from .config import settings

logger = logging.getLogger(__name__)

@celery_app.task(name="worker.tasks.run_agent", bind=True, max_retries=2)
def run_agent(self, task_id: str, task_input: dict):
  conn_str = settings.POSTGRES_URL.replace("postgresql+psycopg", "postgresql")

  with psycopg.connect(conn_str) as conn:
    conn.execute(
      "UPDATE tasks SET status='running' WHERE id=%s",
      (task_id,),
    )
    conn.commit()

  try:
    output = {"answer": "worker reached — graph not implemented yet"}

    with psycopg.connect(conn_str) as conn:
      conn.execute(
        "UPDATE tasks SET status='done', output=%s WHERE id=%s",
        (json.dumps(output), task_id),
      )
      conn.commit()

  except Exception as exc:
    logger.exception("Agent failed for task %s", task_id)
    with psycopg.connect(conn_str) as conn:
      conn.execute(
        "UPDATE tasks SET status='failed', error=%s WHERE id=%s",
        (str(exc), task_id),
      )
      conn.commit()
    raise self.retry(exc=exc, countdown=5)