import json
import uuid

from fastapi import APIRouter, Request, FastAPI, HTTPException
from typing import cast

from ..celery_app import celery_app
from shared.schemas import TaskInput, TaskResponse, TaskResult, TaskStatus

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

@router.get("/{task_id}", response_model=TaskResult)
async def get_task(task_id: str, request: Request):
  app = cast(FastAPI, request.app)
  pool = app.state.pool
  
  row = await pool.fetchrow(
    "SELECT * FROM tasks WHERE id = $1",
    task_id,
  )

  if not row:
    raise HTTPException(status_code=404, detail="Task not found")

  return TaskResult(
    task_id=row["id"],
    status=TaskStatus(row["status"]),
    input=TaskInput(**json.loads(row["input"])),
    output=json.loads(row["output"]) if row["output"] else None,
    error=row["error"],
    created_at=str(row["created_at"]),
    updated_at=str(row["updated_at"]),
  )