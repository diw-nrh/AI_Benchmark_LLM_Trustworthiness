from langgraph.graph import StateGraph, END
from state import GraphState
from nodes.guardrail_node import guardrail_agent_node

# Create the Graph
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node("guardrail_agent", guardrail_agent_node)

# Define Routing / Edges
# Phase 1: Simple 1-node flow
workflow.set_entry_point("guardrail_agent")
workflow.add_edge("guardrail_agent", END)

# Compile the graph
app = workflow.compile()