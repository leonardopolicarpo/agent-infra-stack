import httpx

from fastapi import APIRouter, FastAPI, Request
from typing import cast

from ..config import settings

router = APIRouter()

@router.get("/")
async def health(request: Request):
  app = cast(FastAPI, request.app)
  
  try:
    await app.state.pool.fetchval("SELECT 1")
    pg_status = "ok"
  except Exception:
    pg_status = "unavailable"

  try:
    async with httpx.AsyncClient() as client:
      r = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
      ollama_status = "ok" if r.status_code == 200 else "unavailable"
  except Exception:
    ollama_status = "unavailable"

  return {
    "status": "ok",
    "services": {
      "postgres": pg_status,
      "ollama": ollama_status,
    }
  }