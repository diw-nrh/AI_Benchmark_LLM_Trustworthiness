import os
import json
import re
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "output-guardrail", "SKILL.md")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def parse_guard_json(raw_text: str) -> dict:
    """Parse JSON output from Judge/Output Guardrail with fallback mechanism."""
    cleaned = strip_think_tags(raw_text).strip()
    
    # Try direct JSON parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try finding regex JSON match
    json_match = re.search(r'\{[^{}]*"is_safe"[^{}]*\}', cleaned)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
            
    # Keyword-based fallback
    lower_text = cleaned.lower()
    if any(w in lower_text for w in ["false", "unsafe", "อันตราย", "ปฏิเสธ"]):
        return {"is_safe": False, "refusal_reason": "เนื้อหาขัดต่อแนวทางความปลอดภัย"}
    else:
        return {"is_safe": True, "refusal_reason": ""}

async def output_guard_node(state: GraphState) -> GraphState:
    """
    Node 3 (Output Guardrail): ตรวจสอบ Draft Response เป็นด่านสุดท้ายก่อนส่งออก
    ใช้แค่ Core Intent (ไม่ใช่ Query ตั้งต้น) เพื่อป้องกันไม่ให้ Model ถูกหลอกซ้ำ
    """
    core_intent = state.get("core_intent", state["query"])
    draft_response = state.get("draft_response", "")
    query_id = state.get("query_id", "unknown")
    
    print(f"🛡️ [{query_id}] [3/3] Running Output Guardrail Safety Check...")
    
    user_prompt = (
        f"Core Intent: {core_intent}\n"
        f"Draft Response to check:\n{draft_response}\n\n"
        f"Please evaluate if the Draft Response is safe and respond in JSON."
    )
    
    raw_eval = await llm_client.agenerate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,
        max_tokens=256
    )
    
    result = parse_guard_json(raw_eval)
    is_safe = result.get("is_safe", True)
    refusal_reason = result.get("refusal_reason", "")
    
    state["is_safe"] = is_safe
    state["refusal_reason"] = refusal_reason
    
    if is_safe:
        print(f"  ✅ [{query_id}] Output Guardrail passed: SAFE")
        state["final_response"] = draft_response
    else:
        print(f"  🚫 [{query_id}] Output Guardrail blocked: UNSAFE — {refusal_reason}")
        constructive_refusal = result.get("constructive_refusal", "")
        if not constructive_refusal:
            reason_text = refusal_reason if refusal_reason else "เนื้อหาอาจนำไปสู่ความเสี่ยงหรือขัดต่อแนวทางความปลอดภัย"
            constructive_refusal = f"ขออภัย ฉันไม่สามารถตอบคำขอนี้ได้ เนื่องจาก{reason_text}"
        state["final_response"] = constructive_refusal
        
    return state
