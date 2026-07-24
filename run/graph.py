from langgraph.graph import StateGraph, END
from state import GraphState
from nodes.helpful_agent_node import helpful_agent_node
from nodes.hybrid_judge_node import hybrid_judge_node

# Create the Graph
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node("helpful_agent", helpful_agent_node)
workflow.add_node("hybrid_judge", hybrid_judge_node)

# Define Routing / Edges
workflow.set_entry_point("helpful_agent")
workflow.add_edge("helpful_agent", "hybrid_judge")
workflow.add_edge("hybrid_judge", END)

# Compile the graph
app = workflow.compile()