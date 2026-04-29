import logging
from langgraph.graph import StateGraph, END
from shared.schemas import AgentState

from .agents.router import router_node
from .agents.research import research_node
from .agents.critique import critique_node
from .agents.output import output_node

logger = logging.getLogger(__name__)

# ==========================================
# Arestas Condicionais (Edges)
# ==========================================

def route_after_critique(state: AgentState) -> str:
  if state["critique_output"] == "APPROVED":
    return "output"
  
  if state["iterations"] >= 3:
    logger.warning("[ROUTING] Max iterations reached, forcing output.")
    return "output"
      
  return "research"

# ==========================================
# Compilação do Grafo
# ==========================================

def build_graph():
  workflow = StateGraph(AgentState)

  workflow.add_node("router", router_node)
  workflow.add_node("research", research_node)
  workflow.add_node("critique", critique_node)
  workflow.add_node("output", output_node)

  workflow.set_entry_point("router")
  workflow.add_edge("router", "research")
  workflow.add_edge("research", "critique")
  
  workflow.add_conditional_edges(
    "critique",
    route_after_critique,
    {
      "output": "output",
      "research": "research"
    }
  )
  
  workflow.add_edge("output", END)

  return workflow.compile()

# Instância global do grafo para ser importada pelo Celery
graph = build_graph()