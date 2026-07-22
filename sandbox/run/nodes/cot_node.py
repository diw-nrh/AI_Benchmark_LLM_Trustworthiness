import os
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

# =============================================================================
# Load CoT System Prompt
# =============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(CURRENT_DIR, "..", "skills")

COT_PROMPT_PATH = os.path.join(SKILLS_DIR, "cot_responder", "SKILL.md")

with open(COT_PROMPT_PATH, "r", encoding="utf-8") as f:
    COT_PROMPT = f.read()


async def cot_node(state: GraphState) -> GraphState:
    """
    CoT Node — Single node ที่ทำทุกอย่างในครั้งเดียว
    
    Flow (ภายใน 1 LLM call):
    1. Qwen คิดใน <think> block:
       - เข้าใจคำถาม
       - ตรวจ jailbreak
       - ประเมินความปลอดภัย (level 1-5)
       - ตัดสินใจ ตอบ/ปฏิเสธ
    2. Qwen ตอบนอก <think> block:
       - ตอบอย่างเป็นมิตร หรือ ปฏิเสธอย่างสุภาพ
    3. strip_think_tags → ได้ final response ที่สะอาด
    """
    query = state["query"]
    query_id = state.get("query_id", "unknown")

    print(f"🧠 [{query_id}] CoT processing (single call)...")

    # --- Single LLM Call ทำทุกอย่าง ---
    raw_response = await llm_client.agenerate_text(
        system_prompt=COT_PROMPT,
        user_prompt=query,
        temperature=0.7,
        max_tokens=1024
    )
    
    # Strip <think> block → ได้แค่คำตอบที่สะอาด
    clean_response = strip_think_tags(raw_response)

    # Fallback for empty response
    if not clean_response:
        clean_response = "ขออภัย ฉันไม่สามารถประมวลผลคำขอนี้ได้ในขณะนี้"

    print(f"📤 [{query_id}] Response ready ({len(clean_response)} chars)")

    state["final_response"] = clean_response
    return state
