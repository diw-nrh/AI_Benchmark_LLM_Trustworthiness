from langgraph.graph import StateGraph, END
from state import GraphState
from nodes.guardrail_node import guard_node
from nodes.answer_node import answer_node

# Create the Graph
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node("guard", guard_node)
workflow.add_node("answer", answer_node)

# Define Routing / Edges
# Guard → Answer → END (Answer checks is_safe internally)
workflow.set_entry_point("guard")
workflow.add_edge("guard", "answer")
workflow.add_edge("answer", END)

# Compile the graph
app = workflow.compile()