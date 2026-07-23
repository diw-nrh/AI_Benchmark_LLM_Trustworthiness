import os
import re
import asyncio
from termcolor import colored
from state import GraphState
from nodes.llm_clients import llm_client
from nodes.response_formatter_node import format_unsafe_response

# Load System Prompts
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(CURRENT_DIR, "..", "skills")

def load_prompt(skill_name: str) -> str:
    with open(os.path.join(SKILLS_DIR, skill_name, "SKILL.md"), "r", encoding="utf-8") as f:
        return f.read()

PROMPT_INTENT = load_prompt("judge-intent")
PROMPT_CONTENT = load_prompt("judge-content")
PROMPT_IMPACT = load_prompt("judge-impact")

async def call_judge(system_prompt: str, user_prompt: str) -> str:
    try:
        res = await llm_client.agenerate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        match = re.search(r'<decision>(.*?)</decision>', res, re.IGNORECASE)
        if match:
            return match.group(1).strip().upper()
        return "UNSAFE"  # Default to UNSAFE if parsing fails
    except Exception as e:
        print(colored(f"[JUDGE ERROR]: {str(e)}", "red"))
        return "UNSAFE"

async def hybrid_judge_node(state: GraphState) -> GraphState:
    query = state["query"]
    draft_response = state.get("draft_response", "")
    threat_summary = state.get("threat_summary", "None")
    query_id = state.get("query_id", "Unknown")
    
    user_prompt = f"📌 Threat Summary:\n{threat_summary}\n\n📌 User Query: {query}\n\n📌 Draft Response: {draft_response}"
    
    # Run 3 LLM calls concurrently with DIFFERENT prompts
    tasks = [
        call_judge(PROMPT_INTENT, user_prompt),
        call_judge(PROMPT_CONTENT, user_prompt),
        call_judge(PROMPT_IMPACT, user_prompt)
    ]
    responses = await asyncio.gather(*tasks)
    
    intent_decision = responses[0]
    content_decision = responses[1]
    impact_decision = responses[2]
    
    unsafe_votes = responses.count("UNSAFE")
    
    # Phase 5: Majority Vote (2/3)
    is_safe = unsafe_votes < 2
    
    # Logging
    final_icon = "✅" if is_safe else "⛔"
    log_msg = f"[JUDGE] Intent: {intent_decision} | Content: {content_decision} | Impact: {impact_decision} | Final: {final_icon}"
    print(colored(log_msg, "green" if is_safe else "red"))
    
    if is_safe:
        state["final_response"] = draft_response
    else:
        # Trigger Response Formatter
        state["final_response"] = await format_unsafe_response(query, threat_summary, query_id)
        
    return state
