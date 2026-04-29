import logging
from langgraph.graph import StateGraph, END
from shared.schemas import AgentState

from .agents.router import router_node
from .agents.research import research_node

logger = logging.getLogger(__name__)

# ==========================================
# 1. Node Stubs
# ==========================================

def critique_node(state: AgentState) -> dict:
  logger.info("[NODE] Critique avaliando o research")
  
  if state["iterations"] >= 2:
    return {"critique_output": "APPROVED"}
  else:
    return {"critique_output": "NEEDS_REVISION"}

def output_node(state: AgentState) -> dict:
  logger.info("[NODE] Output gerando resposta final")
  return {
    "final_output": f"FINAL ANSWER: {state['research_output']} (Approved)"
  }

# ==========================================
# 2. Arestas Condicionais (Edges)
# ==========================================

def route_after_critique(state: AgentState) -> str:
  if state["critique_output"] == "APPROVED":
    return "output"
  
  if state["iterations"] >= 3:
    logger.warning("[ROUTING] Max iterations reached, forcing output.")
    return "output"
      
  return "research"

# ==========================================
# 3. Compilação do Grafo
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