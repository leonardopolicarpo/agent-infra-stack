from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  POSTGRES_URL:        str = "postgresql+psycopg://agent:agent_pass@localhost:5432/agent_db"
  REDIS_URL:           str = "redis://localhost:6379/0"
  OLLAMA_BASE_URL:     str = "http://host.docker.internal:11434"
  QDRANT_URL:          str = "http://localhost:6333"
  ROUTER_MODEL:        str = "llama3.2:3b"
  TASK_MODEL:          str = "llama3.2:3b"
  LANGFUSE_HOST:       str = "http://localhost:3000"
  LANGFUSE_PUBLIC_KEY: str = "pk-placeholder"
  LANGFUSE_SECRET_KEY: str = "sk-placeholder"

  class Config:
    env_file = ".env"

settings = Settings()