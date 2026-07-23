from langgraph.graph import StateGraph, END
from state import GraphState
from nodes.sandwich_guardrail_node import sandwich_guardrail_node

# Create the Graph
workflow = StateGraph(GraphState)

# Add Node - Single Internal Sandwich Guardrail Flow
workflow.add_node("sandwich_guardrail", sandwich_guardrail_node)

# Define Routing / Edges
workflow.set_entry_point("sandwich_guardrail")
workflow.add_edge("sandwich_guardrail", END)

# Compile the graph
app = workflow.compile()