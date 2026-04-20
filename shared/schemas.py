"""
shared/schemas.py

Contracts shared between the API and Worker services.
Changing anything here affects both — treat this as a public interface.

Sections:
  - Enums
  - API contracts  (TaskInput, TaskResponse, TaskResult)
  - Agent state    (AgentState — used by LangGraph graph nodes)
"""
from __future__ import annotations

from enum import Enum
from typing import Any, TypedDict
from uuid import UUID

from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
  PENDING = "pending"
  RUNNING = "running"
  DONE    = "done"
  FAILED  = "failed"

class TaskInput(BaseModel):
  """Payload sent by the client to POST /task."""

  prompt: str = Field(..., min_length=1, max_length=8000)

  router_model: str | None = None
  task_model:   str | None = None

class TaskResponse(BaseModel):
  """Immediate response from POST /task — returned before processing starts."""

  task_id: UUID
  status:  TaskStatus = TaskStatus.PENDING

class TaskResult(BaseModel):
  """"Response from GET /task/{id} — includes status and result when done."""

  task_id:    UUID
  status:     TaskStatus
  input:      TaskInput
  output:     dict[str, Any] | None = None
  error:      str | None = None
  created_at: str
  updated_at: str

class AgentState(TypedDict):
  """
  Internal state of the LangGraph graph.

  Each node reads from and writes to this structure.
  The PostgresSaver checkpoints it automatically after every step
  meaning the agent can resume exactly where it left off after a crash.

  Router decision values: "simple" | "complex"
  """

  task_id:         str
  original_prompt: str
  router_decision: str | None
  research_output: str | None
  critique_output: str | None
  final_output:    str | None
  memory_context:  str | None
  iterations:      int
  error:           str | None