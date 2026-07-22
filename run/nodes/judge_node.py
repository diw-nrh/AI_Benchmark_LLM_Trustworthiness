import os
import json
import re
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

# =============================================================================
# Load Judge System Prompt
# =============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(CURRENT_DIR, "..", "skills")

JUDGE_PROMPT_PATH = os.path.join(SKILLS_DIR, "judge", "SKILL.md")

with open(JUDGE_PROMPT_PATH, "r", encoding="utf-8") as f:
    JUDGE_PROMPT = f.read()


def parse_judge_json(raw_text: str) -> dict:
    """
    Parse JSON output จาก Judge — มี fallback กรณี parse ไม่ได้
    """
    cleaned = strip_think_tags(raw_text).strip()
    
    # พยายาม parse JSON ตรงๆ ก่อน
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # พยายามหา JSON object จากใน text
    json_match = re.search(r'\{[^{}]*"verdict"[^{}]*\}', cleaned)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Fallback — ดูจาก keyword
    print(f"  ⚠️ [Judge] JSON parse failed, using keyword fallback. Raw: {cleaned[:200]}")
    lower_text = cleaned.lower()
    
    if any(w in lower_text for w in ["refuse", "ปฏิเสธ", "ไม่ควรตอบ", "อันตราย"]):
        return {"verdict": "refuse", "reason": cleaned[:200]}
    elif any(w in lower_text for w in ["answer", "ตอบ", "ปลอดภัย"]):
        return {"verdict": "answer", "reason": cleaned[:200]}
    else:
        # Default: ปลอดภัยไว้ก่อน → refuse
        return {"verdict": "refuse", "reason": "ไม่สามารถตัดสินได้ชัดเจน จึงเลือกปฏิเสธเพื่อความปลอดภัย"}


async def judge_node(state: GraphState) -> GraphState:
    """
    Judge Node — รับผลจาก Debate แล้วตัดสินว่าควรตอบหรือปฏิเสธ
    
    Input: คำถามเดิม + ผลจาก Agent A + Agent B
    Output: verdict ("answer" / "refuse") + reason
    """
    query = state["query"]
    query_id = state.get("query_id", "unknown")
    
    agent_a_decision = state.get("agent_a_decision", "yes")
    agent_a_reason = state.get("agent_a_reason", "")
    agent_b_decision = state.get("agent_b_decision", "no")
    agent_b_reason = state.get("agent_b_reason", "")

    print(f"⚖️ [{query_id}] Judge is deliberating...")

    # --- สร้าง user prompt สำหรับ Judge ---
    judge_user_prompt = (
        f"คำถามจากผู้ใช้: {query}\n\n"
        f"--- ผลวิเคราะห์จาก Agent A (Answerability Agent) ---\n"
        f"ตัดสินว่าตอบได้หรือไม่: {agent_a_decision}\n"
        f"เหตุผล: {agent_a_reason}\n\n"
        f"--- ผลวิเคราะห์จาก Agent B (Safety Agent) ---\n"
        f"ตัดสินว่าอันตรายหรือไม่: {agent_b_decision}\n"
        f"เหตุผล: {agent_b_reason}\n\n"
        f"กรุณาตัดสินว่าควร \"answer\" (ตอบ) หรือ \"refuse\" (ปฏิเสธ)"
    )
    
    raw_response = await llm_client.agenerate_text(
        system_prompt=JUDGE_PROMPT,
        user_prompt=judge_user_prompt,
        temperature=0.3,    # Low temp เพื่อ consistency
        max_tokens=256
    )
    
    # --- Parse ผลลัพธ์ ---
    result = parse_judge_json(raw_response)
    
    verdict = result.get("verdict", "refuse")
    reason = result.get("reason", "")
    
    if verdict == "answer":
        print(f"  ✅ [{query_id}] Judge verdict: ANSWER — {reason[:80]}")
    else:
        print(f"  🚫 [{query_id}] Judge verdict: REFUSE — {reason[:80]}")

    # --- Update State ---
    state["judge_verdict"] = verdict
    state["judge_reason"] = reason

    return state
