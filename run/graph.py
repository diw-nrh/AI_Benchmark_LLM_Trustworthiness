from langgraph.graph import StateGraph, END
from state import GraphState

# [OLD] from nodes.guardrail_node import guard_node
from nodes.debate_node import debate_node
from nodes.judge_node import judge_node
from nodes.answer_node import answer_node

# Create the Graph
workflow = StateGraph(GraphState)

# Add Nodes — Multi-Agent Debate Flow
workflow.add_node("debate", debate_node)    # Node 1: Dual-Agent (Answerability + Safety)
workflow.add_node("judge", judge_node)      # Node 2: Judge ตัดสิน
workflow.add_node("answer", answer_node)    # Node 3: ตอบหรือปฏิเสธ

# Define Routing / Edges
# debate → judge → answer → END
workflow.set_entry_point("debate")
workflow.add_edge("debate", "judge")
workflow.add_edge("judge", "answer")
workflow.add_edge("answer", END)

# [OLD] Flow เก่า: guard → answer → END
# workflow.add_node("guard", guard_node)
# workflow.add_node("answer", answer_node)
# workflow.set_entry_point("guard")
# workflow.add_edge("guard", "answer")
# workflow.add_edge("answer", END)

# Compile the graph
app = workflow.compile()