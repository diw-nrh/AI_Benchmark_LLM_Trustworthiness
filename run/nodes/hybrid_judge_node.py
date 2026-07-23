import os
import re
import json
import random
import asyncio
from state import GraphState
from nodes.llm_clients import llm_client

# Load System Prompt from Markdown File
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "hybrid-judge", "SKILL.md")
EXAMPLES_PATH = os.path.join(CURRENT_DIR, "..", "skills", "guardrail", "examples.json")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    BASE_SYSTEM_PROMPT = f.read()

# Load examples
EXAMPLES = []
if os.path.exists(EXAMPLES_PATH):
    with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
        EXAMPLES = json.load(f)

def build_dynamic_prompt() -> str:
    """Append 1 SAFE and 1 UNSAFE random few-shot example to the base prompt."""
    prompt = BASE_SYSTEM_PROMPT
    if EXAMPLES:
        prompt += "\n\n[FEW-SHOT EXAMPLES (For Reference)]\n"
        
        # Separate examples into SAFE and UNSAFE based on the text in 'think'
        safe_examples = [ex for ex in EXAMPLES if "(SAFE)" in ex['think']]
        unsafe_examples = [ex for ex in EXAMPLES if "(UNSAFE)" in ex['think']]
        
        selected_examples = []
        if safe_examples:
            selected_examples.append(random.choice(safe_examples))
        if unsafe_examples:
            selected_examples.append(random.choice(unsafe_examples))
            
        # Shuffle them so it's not always SAFE first
        random.shuffle(selected_examples)
        
        for i, ex in enumerate(selected_examples):
            decision = "SAFE" if "(SAFE)" in ex['think'] else "UNSAFE"
            prompt += f"\n--- Example {i+1} ({ex['category']}) ---\n"
            prompt += f"User Query: {ex['query']}\n"
            prompt += f"Draft Response: {ex['response']}\n"
            prompt += f"<think>\n{ex['think']}\n</think>\n"
            prompt += f"<decision>{decision}</decision>\n"
    return prompt

async def call_llm(system_prompt: str, user_prompt: str) -> str:
    return await llm_client.agenerate_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.7
    )

async def hybrid_judge_node(state: GraphState) -> GraphState:
    """
    Evaluates the draft_response using Self-Consistency (Majority Vote among 3 parallel calls).
    """
    query = state["query"]
    draft_response = state.get("draft_response", "")
    
    # Generate dynamic prompt
    system_prompt = build_dynamic_prompt()
    user_prompt = f"User Query: {query}\nDraft Response: {draft_response}"
    
    # Run 3 LLM calls concurrently
    tasks = [
        call_llm(system_prompt, user_prompt),
        call_llm(system_prompt, user_prompt),
        call_llm(system_prompt, user_prompt)
    ]
    responses = await asyncio.gather(*tasks)
    
    # Tally votes
    safe_votes = 0
    unsafe_votes = 0
    for res in responses:
        # Parse <decision> tags. Default to UNSAFE if missing/broken.
        match = re.search(r'<decision>(.*?)</decision>', res, re.IGNORECASE)
        if match:
            decision = match.group(1).strip().upper()
            if decision == "SAFE":
                safe_votes += 1
            else:
                unsafe_votes += 1
        else:
            # If no tags, check if SAFE is mentioned near the end
            if "SAFE" in res[-20:].upper() and "UNSAFE" not in res[-20:].upper():
                safe_votes += 1
            else:
                unsafe_votes += 1
                
    # Majority Vote
    is_safe = safe_votes > unsafe_votes
    
    if is_safe:
        state["final_response"] = draft_response
    else:
        state["final_response"] = "ขออภัย ฉันไม่สามารถช่วยเหลือในเรื่องนี้ได้"
        
    return state
