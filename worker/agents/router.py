import logging
from langchain_ollama import ChatOllama
from shared.schemas import AgentState
from ..config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a task routing assistant. Analyze the user prompt and classify its complexity.

Reply with ONLY one of:
- simple   (direct facts, definitions, closed questions, simple calculations)
- complex  (analysis, research, multi-step reasoning, comparison)

No explanation. No punctuation. Just the word."""

def router_node(state: AgentState) -> dict:
  llm = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.ROUTER_MODEL,
    temperature=0,
  )

  response = llm.invoke([
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user",   "content": state["original_prompt"]},
  ])

  decision = response.content.strip().lower()
  if decision not in ("simple", "complex"):
    decision = "complex"

  logger.info("[ROUTER] decision=%s task=%s", decision, state["task_id"])
  return {"router_decision": decision}