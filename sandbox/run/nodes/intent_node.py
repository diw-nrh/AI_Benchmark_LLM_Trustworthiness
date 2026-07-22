import os
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "intent_extractor", "SKILL.md")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

async def intent_node(state: GraphState) -> GraphState:
    """
    Node 1 (Input Guardrail): ถอดหน้ากาก/แปลงคำถาม เพื่อดึง Core Intent ออกมาจาก Query ต้นฉบับ
    """
    query = state["query"]
    query_id = state.get("query_id", "unknown")
    
    print(f"🎯 [{query_id}] [1/3] Extracting Core Intent from Query...")
    raw_intent = await llm_client.agenerate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=query,
        temperature=0.3
    )
    
    clean_intent = strip_think_tags(raw_intent)
    if not clean_intent:
        clean_intent = query  # Fallback: ถ้าสกัดไม่ได้ ให้ใช้คำถามเดิม
        
    print(f"  📌 [{query_id}] Core Intent: {clean_intent[:100]}...")
    state["core_intent"] = clean_intent
    return state
