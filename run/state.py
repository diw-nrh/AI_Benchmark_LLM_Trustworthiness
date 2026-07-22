from typing import TypedDict

class GraphState(TypedDict, total=False):
    # Core Inputs
    query_id: str
    query: str
    
    # [OLD] Guard Node outputs — ไม่ใช้แล้ว เปลี่ยนมาใช้ Multi-Agent Debate
    # translated_query: str       # Qwen-translated English version of the query
    # is_safe: bool               # Whether the query is safe to answer
    # guard_reason: str           # Raw WildGuard output (e.g., "Harmful request: yes")
    
    # --- NEW: Multi-Agent Debate Flow ---
    # Debate Node outputs (Agent A = Answerability, Agent B = Safety)
    agent_a_decision: str       # "yes" = ตอบได้, "no" = ตอบไม่ได้
    agent_a_reason: str         # เหตุผลจาก Agent A
    agent_b_decision: str       # "yes" = อันตราย, "no" = ไม่อันตราย
    agent_b_reason: str         # เหตุผลจาก Agent B
    
    # Judge Node outputs
    judge_verdict: str          # "answer" = ตอบ, "refuse" = ปฏิเสธ
    judge_reason: str           # เหตุผลจาก Judge
    
    # Response Node output
    final_response: str
