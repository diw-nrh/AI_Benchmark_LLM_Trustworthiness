import os
from nodes.llm_clients import llm_client
from termcolor import colored

# Load the Response Formatter Prompt
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "response-formatter", "SKILL.md")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    FORMATTER_PROMPT = f.read()

async def format_unsafe_response(query: str, threat_summary: str, query_id: str = "Unknown") -> str:
    """Called when the Judge panel votes UNSAFE. Generates a constructive refusal."""
    print(colored(f"[FORMATTER] {query_id}: Generating constructive refusal...", "magenta"))
    
    user_prompt = f"📌 Threat Summary:\n{threat_summary}\n\n📌 User Query: {query}"
    
    try:
        # Call LLM
        raw_response = await llm_client.agenerate_text(FORMATTER_PROMPT, user_prompt)
        
        # Strip <think> tags from output if present
        import re
        final_response = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.IGNORECASE | re.DOTALL).strip()
        return final_response
        
    except Exception as e:
        print(colored(f"[FORMATTER ERROR] {query_id}: {str(e)}", "red"))
        return "ขออภัย ฉันไม่สามารถให้ข้อมูลในเรื่องนี้ได้ เนื่องจากอาจขัดต่อความปลอดภัยหรือกฎหมายที่เกี่ยวข้องครับ"
