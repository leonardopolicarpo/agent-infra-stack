import logging
from langchain_ollama import ChatOllama
from shared.schemas import AgentState
from ..config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a strict but fair critic. Evaluate the response based on:
1. Relevance — does it directly answer the prompt?
2. Completeness — does it cover the key points?
3. Clarity — is it well-structured and easy to understand?
4. Accuracy — no vague or incorrect claims?

Reply ONLY in one of these formats:
- APPROVED
- NEEDS_REVISION: [specific and concise reason]

No extra text. Start your reply with APPROVED or NEEDS_REVISION."""

def critique_node(state: AgentState) -> dict:
  llm = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.ROUTER_MODEL,
    temperature=0,
  )

  logger.info(
    "[CRITIQUE] iteração=%s task=%s",
    state["iterations"], state["task_id"]
  )

  response = llm.invoke([
    {"role": "system", "content": SYSTEM_PROMPT},
    {
      "role": "user",
      "content": (
        f"Original prompt: {state['original_prompt']}\n\n"
        f"Response to evaluate:\n{state['research_output']}"
      ),
    },
  ])

  critique = response.content.strip()
  
  if not critique.startswith("APPROVED") and not critique.startswith("NEEDS_REVISION"):
    logger.warning("[CRITIQUE] output inesperado, forçando APPROVED: %s", critique)
    critique = "APPROVED"

  logger.info("[CRITIQUE] result=%s task=%s", critique[:50], state["task_id"])
  return {"critique_output": critique}

def route_after_critique(state: AgentState) -> str:
  if state["critique_output"].startswith("APPROVED"):
    return "output"
  if state["iterations"] >= 3:
    logger.warning("[ROUTING] Max iterations reached, forcing output. task=%s", state["task_id"])
    return "output"
  return "research"