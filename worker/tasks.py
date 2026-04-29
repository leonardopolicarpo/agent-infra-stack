import json
import logging

import psycopg

from .celery_app import celery_app
from .config import settings
from .graph import build_graph
from shared.schemas import AgentState

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
    initial_state: AgentState = {
      "task_id": task_id,
      "original_prompt": task_input.get("prompt"),
      "router_decision": None,
      "research_output": None,
      "critique_output": None,
      "final_output": None,
      "memory_context": None,
      "iterations": 0,
      "error": None
    }

    graph = build_graph()
    final_state = graph.invoke(initial_state)

    output = {
      "answer": final_state.get("final_output"),
      "iterations": final_state.get("iterations"),
      "decision": final_state.get("router_decision")
    }

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