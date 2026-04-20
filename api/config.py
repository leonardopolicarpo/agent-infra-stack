from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  REDIS_URL: str = "redis://localhost:6379/0"
  OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
  ROUTER_MODEL: str = "llama3.2:3b"
  TASK_MODEL: str = "llama3.2:3b"
  POSTGRES_URL: str = "postgresql://agent:agent_pass@localhost:5432/agent_db"

settings = Settings()