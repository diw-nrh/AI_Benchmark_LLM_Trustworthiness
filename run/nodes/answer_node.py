import os
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

# Load System Prompts
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(CURRENT_DIR, "..", "skills")

ANSWER_PROMPT_PATH = os.path.join(SKILLS_DIR, "answer", "SKILL.md")
REFUSAL_PROMPT_PATH = os.path.join(SKILLS_DIR, "refusal", "SKILL.md")

with open(ANSWER_PROMPT_PATH, "r", encoding="utf-8") as f:
    ANSWER_PROMPT = f.read()

with open(REFUSAL_PROMPT_PATH, "r", encoding="utf-8") as f:
    REFUSAL_PROMPT = f.read()


async def answer_node(state: GraphState) -> GraphState:
    """
    Answer Node — ตอบคำถามหรือปฏิเสธ ขึ้นอยู่กับผลจาก Judge Node
    
    - ใช้ query ภาษาไทยต้นฉบับเสมอ
    - ถ้า judge_verdict="answer" → ตอบคำถามตามปกติ
    - ถ้า judge_verdict="refuse" → สร้างคำปฏิเสธ dynamic พร้อมเหตุผล
    """
    query = state["query"]             # Original Thai query
    judge_verdict = state.get("judge_verdict", "answer")
    judge_reason = state.get("judge_reason", "")
    query_id = state.get("query_id", "unknown")

    # [OLD] ใช้ is_safe จาก WildGuard
    # is_safe = state.get("is_safe", True)
    # guard_reason = state.get("guard_reason", "")

    if judge_verdict == "answer":
        # --- ตอบคำถามตามปกติ ---
        print(f"💬 [{query_id}] Generating answer for approved query...")
        raw_response = await llm_client.agenerate_text(
            system_prompt=ANSWER_PROMPT,
            user_prompt=query,
            temperature=0.7
        )
    else:
        # --- สร้างคำปฏิเสธ dynamic ---
        print(f"🚫 [{query_id}] Generating refusal for rejected query...")
        refusal_user_prompt = (
            f"คำถามจากผู้ใช้: {query}\n\n"
            f"เหตุผลที่ต้องปฏิเสธ: {judge_reason}"
        )
        raw_response = await llm_client.agenerate_text(
            system_prompt=REFUSAL_PROMPT,
            user_prompt=refusal_user_prompt,
            temperature=0.7
        )

    # Process output — strip <think> tags
    clean_response = strip_think_tags(raw_response)

    # Fallback for empty response
    if not clean_response:
        if judge_verdict == "answer":
            clean_response = "ขออภัย ฉันไม่สามารถประมวลผลคำขอนี้ได้"
        else:
            clean_response = "ขออภัย ฉันไม่สามารถช่วยเหลือในเรื่องนี้ได้ เนื่องจากคำขอนี้อาจไม่เหมาะสม"

    print(f"📤 [{query_id}] Response ready ({len(clean_response)} chars)")

    state["final_response"] = clean_response
    return state
