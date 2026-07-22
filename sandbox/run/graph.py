from langgraph.graph import StateGraph, END
from state import GraphState
from nodes.cot_node import cot_node

# Create the Graph — Single Node Flow
workflow = StateGraph(GraphState)

# Add single CoT Node — ทำทุกอย่างในครั้งเดียว
workflow.add_node("cot", cot_node)

# Define Routing / Edges
# cot → END (แค่นั้น!)
workflow.set_entry_point("cot")
workflow.add_edge("cot", END)

# Compile the graph
app = workflow.compile()
