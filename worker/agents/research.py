import logging
from langchain_ollama import ChatOllama
from shared.schemas import AgentState
from ..config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a research assistant. Generate a clear, detailed and well-structured response to the user's prompt.

If this is a revision, you will receive the previous critique — address it directly.
Be objective and precise. Do not fabricate information."""

def research_node(state: AgentState) -> dict:
  model = (
    settings.TASK_MODEL
    if state["router_decision"] == "complex"
    else settings.ROUTER_MODEL
  )

  llm = ChatOllama(
    base_url=settings.OLLAMA_BASE_URL,
    model=model,
    temperature=0.7,
  )

  logger.info(
    "[RESEARCH] iteração=%s model=%s task=%s",
    state["iterations"], model, state["task_id"]
  )

  messages = [{"role": "system", "content": SYSTEM_PROMPT}]

  if state["iterations"] > 0 and state.get("critique_output"):
    messages.append({
      "role": "assistant",
      "content": state["research_output"],
    })
    messages.append({
      "role": "user",
      "content": (
        f"Your previous response received this critique:\n"
        f"{state['critique_output']}\n\n"
        f"Please revise and improve your response."
      ),
    })
  else:
    messages.append({
      "role": "user",
      "content": state["original_prompt"],
    })

  response = llm.invoke(messages)
  
  return {
    "research_output": response.content,
    "iterations": state["iterations"] + 1,
  }