from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import tasks, health

@asynccontextmanager
async def lifespan(app: FastAPI):
  app.state.pool = await asyncpg.create_pool(
    settings.POSTGRES_URL,
    min_size=2,
    max_size=10,
  )
  yield
  await app.state.pool.close()


app = FastAPI(
  title="agent-infra-stack",
  description="Scalable multi-agent pipeline with persistent memory and observability.",
  version="0.1.0",
  lifespan=lifespan,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/task", tags=["tasks"])
app.include_router(health.router, prefix="/health", tags=["health"])