import os
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "answer", "SKILL.md")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

async def answer_node(state: GraphState) -> GraphState:
    """
    Node 2 (Answer Generator): รับ Core Intent (ไม่ใช่ Query ตั้งต้น) ไปเจนคำตอบร่าง (Draft Response)
    เพื่อป้องกันไม่ให้ Model ถูกหลอกซ้ำจาก Jailbreak framing ใน Query ตั้งต้น
    """
    core_intent = state.get("core_intent", state["query"])
    query_id = state.get("query_id", "unknown")
    
    print(f"💬 [{query_id}] [2/3] Generating Draft Response based on Core Intent...")
    
    user_prompt = (
        f"Core Intent: {core_intent}\n\n"
        f"Please answer safely and accurately based on the instructions."
    )
    
    raw_response = await llm_client.agenerate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7
    )
    
    clean_response = strip_think_tags(raw_response)
    if not clean_response:
        clean_response = "ขออภัย ฉันไม่สามารถประมวลผลคำขอนี้ได้"
        
    print(f"  📝 [{query_id}] Draft generated ({len(clean_response)} chars)")
    state["draft_response"] = clean_response
    return state
