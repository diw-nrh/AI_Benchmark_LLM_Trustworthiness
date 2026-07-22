import os
import json
import asyncio
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

# =============================================================================
# Load System Prompts for Dual Agents
# =============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(CURRENT_DIR, "..", "skills")

ANSWERABILITY_PROMPT_PATH = os.path.join(SKILLS_DIR, "answerability_agent", "SKILL.md")
SAFETY_PROMPT_PATH = os.path.join(SKILLS_DIR, "safety_agent", "SKILL.md")

with open(ANSWERABILITY_PROMPT_PATH, "r", encoding="utf-8") as f:
    ANSWERABILITY_PROMPT = f.read()

with open(SAFETY_PROMPT_PATH, "r", encoding="utf-8") as f:
    SAFETY_PROMPT = f.read()


def parse_agent_json(raw_text: str, agent_name: str) -> dict:
    """
    Parse JSON output จาก Agent — มี fallback กรณี parse ไม่ได้
    พยายามหา JSON object จาก text ก่อน ถ้าไม่ได้ก็ใช้ default
    """
    cleaned = strip_think_tags(raw_text).strip()
    
    # พยายาม parse JSON ตรงๆ ก่อน
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # พยายามหา JSON object จากใน text (กรณีมีข้อความอื่นปนมา)
    import re
    json_match = re.search(r'\{[^{}]*"decision"[^{}]*\}', cleaned)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Fallback — ดูจาก keyword ใน text
    print(f"  ⚠️ [{agent_name}] JSON parse failed, using keyword fallback. Raw: {cleaned[:200]}")
    lower_text = cleaned.lower()
    
    if agent_name == "Agent-A":
        # Agent A: ถ้า parse ไม่ได้ สันนิษฐานว่าตอบได้
        decision = "yes" if "yes" in lower_text else "no"
    else:
        # Agent B: ถ้า parse ไม่ได้ สันนิษฐานว่าปลอดภัย (err on safe)
        decision = "yes" if any(w in lower_text for w in ["อันตราย", "harmful", "unsafe", "dangerous"]) else "no"
    
    return {"decision": decision, "reason": cleaned[:200]}


async def debate_node(state: GraphState) -> GraphState:
    """
    Debate Node — เรียก Agent 2 ตัวพร้อมกัน (asyncio.gather)
    
    Agent A (Answerability): วิเคราะห์ว่าคำถามตอบได้หรือไม่
    Agent B (Safety): วิเคราะห์ว่าคำถามอันตรายหรือไม่
    
    ทั้งสองใช้ Qwen ตัวเดียวกัน แต่ต่าง system prompt
    """
    query = state["query"]
    query_id = state.get("query_id", "unknown")

    print(f"🤖 [{query_id}] Starting Dual-Agent Debate...")

    # --- เรียกทั้งสอง Agent พร้อมกัน ---
    agent_a_task = llm_client.agenerate_text(
        system_prompt=ANSWERABILITY_PROMPT,
        user_prompt=query,
        temperature=0.3,    # Low temp เพื่อ consistency
        max_tokens=256      # ไม่ต้องยาว แค่ JSON
    )
    
    agent_b_task = llm_client.agenerate_text(
        system_prompt=SAFETY_PROMPT,
        user_prompt=query,
        temperature=0.3,
        max_tokens=256
    )
    
    # รันพร้อมกัน
    raw_a, raw_b = await asyncio.gather(agent_a_task, agent_b_task)
    
    # --- Parse ผลลัพธ์ ---
    result_a = parse_agent_json(raw_a, "Agent-A")
    result_b = parse_agent_json(raw_b, "Agent-B")
    
    agent_a_decision = result_a.get("decision", "yes")
    agent_a_reason = result_a.get("reason", "")
    agent_b_decision = result_b.get("decision", "no")
    agent_b_reason = result_b.get("reason", "")
    
    print(f"  📊 [{query_id}] Agent-A (Answerability): decision={agent_a_decision}, reason={agent_a_reason[:80]}")
    print(f"  📊 [{query_id}] Agent-B (Safety):        decision={agent_b_decision}, reason={agent_b_reason[:80]}")

    # --- Update State ---
    state["agent_a_decision"] = agent_a_decision
    state["agent_a_reason"] = agent_a_reason
    state["agent_b_decision"] = agent_b_decision
    state["agent_b_reason"] = agent_b_reason

    return state
