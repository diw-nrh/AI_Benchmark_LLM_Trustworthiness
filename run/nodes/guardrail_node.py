import os
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client, wildguard_client

# Load System Prompt for Translation
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSLATION_PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "translation_prompt.md")

with open(TRANSLATION_PROMPT_PATH, "r", encoding="utf-8") as f:
    TRANSLATION_PROMPT = f.read()


async def guard_node(state: GraphState) -> GraphState:
    """
    Guard Node — ตรวจสอบความปลอดภัยของ query
    
    Flow:
    1. ใช้ Qwen แปล query ภาษาไทย → ภาษาอังกฤษ
    2. ส่ง English query ให้ WildGuard ตรวจ
    3. Set is_safe + guard_reason แล้วส่งต่อไป Answer Node
    """
    query = state["query"]
    query_id = state.get("query_id", "unknown")

    # --- Step 1: Translate Thai → English using Qwen ---
    print(f"🔄 [{query_id}] Translating query to English...")
    translated = await llm_client.agenerate_text(
        system_prompt=TRANSLATION_PROMPT,
        user_prompt=query,
        temperature=0.3  # Low temp for faithful translation
    )
    translated = strip_think_tags(translated).strip()

    if not translated:
        # Fallback: ถ้าแปลไม่ได้ ให้ใช้ query ต้นฉบับ
        print(f"⚠️ [{query_id}] Translation failed, using original query for guard check")
        translated = query

    print(f"📝 [{query_id}] Translated: {translated[:100]}...")

    # --- Step 2: Check with WildGuard ---
    print(f"🛡️ [{query_id}] Running WildGuard safety check...")
    guard_result = wildguard_client.evaluate(prompt=translated)

    is_safe = guard_result["is_safe"]
    raw_output = guard_result["raw_output"]

    if is_safe:
        print(f"✅ [{query_id}] SAFE — WildGuard output: {raw_output}")
    else:
        print(f"🚫 [{query_id}] UNSAFE — WildGuard output: {raw_output}")

    # --- Update State ---
    state["translated_query"] = translated
    state["is_safe"] = is_safe
    state["guard_reason"] = raw_output

    return state
