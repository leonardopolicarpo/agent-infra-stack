import json
import uuid

from fastapi import APIRouter, Request, FastAPI
from typing import cast

from ..celery_app import celery_app
from shared.schemas import TaskInput, TaskResponse, TaskStatus

router = APIRouter()

@router.post("", response_model=TaskResponse, status_code=202)
async def submit_task(body: TaskInput, request: Request):
  task_id = str(uuid.uuid4())

  app = cast(FastAPI, request.app)
  pool = app.state.pool

  await pool.execute(
    """
    INSERT INTO tasks (id, status, input)
    VALUES ($1, 'pending', $2)
    """,
    task_id,
    json.dumps(body.model_dump()),
  )

  celery_app.send_task(
    "worker.tasks.run_agent",
    args=[task_id, body.model_dump()],
    task_id=task_id,
  )

  return TaskResponse(task_id=task_id, status=TaskStatus.PENDING)