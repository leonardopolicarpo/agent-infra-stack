from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import tasks, health

app = FastAPI(
  title="agent-infra-stack",
  description="Scalable multi-agent pipeline with persistent memory and observability.",
  version="0.1.0",
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/task", tags=["tasks"])
app.include_router(health.router, prefix="/health", tags=["health"])