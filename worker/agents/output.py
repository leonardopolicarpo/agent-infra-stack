import logging
from shared.schemas import AgentState

logger = logging.getLogger(__name__)

def output_node(state: AgentState) -> dict:
  logger.info(
    "[OUTPUT] formatando resposta final task=%s iterations=%s",
    state["task_id"], state["iterations"]
  )

  research = state["research_output"] or ""
  final = research.strip()

  return {"final_output": final}