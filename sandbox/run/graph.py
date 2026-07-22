from langgraph.graph import StateGraph, END
from state import GraphState

# Old phase 1 node
# from nodes.guardrail_node import guardrail_agent_node

# Sandwich Guardrail nodes
from nodes.intent_node import intent_node
from nodes.answer_node import answer_node
from nodes.output_guard_node import output_guard_node

# Create the Graph
workflow = StateGraph(GraphState)

# Add Nodes — Sandwich Guardrail Flow
workflow.add_node("intent_extractor", intent_node)       # Node 1 (Input Guardrail): ดึง Core Intent
workflow.add_node("answer", answer_node)                 # Node 2 (Answer Generator): เจน Draft Response
workflow.add_node("output_guardrail", output_guard_node) # Node 3 (Output Guardrail): ตรวจความปลอดภัยคำตอบ

# Define Routing / Edges
# intent_extractor → answer → output_guardrail → END
workflow.set_entry_point("intent_extractor")
workflow.add_edge("intent_extractor", "answer")
workflow.add_edge("answer", "output_guardrail")
workflow.add_edge("output_guardrail", END)

# Compile the graph
app = workflow.compile()