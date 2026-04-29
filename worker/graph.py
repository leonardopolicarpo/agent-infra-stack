import logging
from langgraph.graph import StateGraph, END
from shared.schemas import AgentState

from .agents import (
  router_node,
  research_node,
  critique_node,
  route_after_critique,
  output_node
)

logger = logging.getLogger(__name__)

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