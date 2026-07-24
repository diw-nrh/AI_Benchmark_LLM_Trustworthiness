import os
import re
import asyncio
import json
import random
from termcolor import colored
from state import GraphState
from nodes.llm_clients import llm_client
from nodes.response_formatter_node import format_unsafe_response

# Load System Prompts
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(CURRENT_DIR, "..", "skills")
JUDGE_UNIFIED_DIR = os.path.join(SKILLS_DIR, "judge-unified")

def load_prompt(skill_name: str) -> str:
    with open(os.path.join(SKILLS_DIR, skill_name, "SKILL.md"), "r", encoding="utf-8") as f:
        return f.read()

PROMPT_UNIFIED = load_prompt("judge-unified")

# Load Examples
try:
    with open(os.path.join(JUDGE_UNIFIED_DIR, "examples.json"), "r", encoding="utf-8") as f:
        EXAMPLES = json.load(f)
except FileNotFoundError:
    EXAMPLES = []

def build_dynamic_prompt() -> str:
    """Append 1 SAFE and 1 UNSAFE random few-shot example to the base prompt."""
    prompt = PROMPT_UNIFIED
    if EXAMPLES:
        prompt += "\n\n[FEW-SHOT EXAMPLES (For Reference)]\n"
        
        safe_examples = [ex for ex in EXAMPLES if ex.get("decision") == "SAFE"]
        unsafe_examples = [ex for ex in EXAMPLES if ex.get("decision") == "UNSAFE"]
        
        selected_examples = []
        if safe_examples:
            selected_examples.append(random.choice(safe_examples))
        if unsafe_examples:
            selected_examples.append(random.choice(unsafe_examples))
            
        random.shuffle(selected_examples)
        
        for i, ex in enumerate(selected_examples):
            prompt += f"\n--- Example {i+1} ({ex['category']}) ---\n"
            prompt += f"📌 User Query: {ex['query']}\n"
            if "draft_response" in ex:
                prompt += f"📌 Draft Response: {ex['draft_response']}\n"
            prompt += f"<think>\n{ex['think']}\n</think>\n"
            prompt += f"<decision>{ex['decision']}</decision>\n"
    return prompt

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
    query_id = state.get("query_id", "Unknown")
    
    user_prompt = f"📌 User Query: {query}\n\n📌 Draft Response: {draft_response}"
    system_prompt = build_dynamic_prompt()
    
    # Run 1 unified LLM call
    decision = await call_judge(system_prompt, user_prompt)
    is_safe = (decision == "SAFE")
    
    # Logging
    final_icon = "✅" if is_safe else "⛔"
    log_msg = f"[JUDGE] Unified Decision: {decision} | Final: {final_icon}"
    print(colored(log_msg, "green" if is_safe else "red"))
    
    if is_safe:
        state["final_response"] = draft_response
    else:
        # Trigger Response Formatter
        state["final_response"] = await format_unsafe_response(query, query_id)
        
    return state
