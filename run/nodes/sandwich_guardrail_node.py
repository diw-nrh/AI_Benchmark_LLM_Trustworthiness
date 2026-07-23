import os
import re
import json
import random
from state import GraphState
from nodes.llm_clients import llm_client

# Load System Prompt from Markdown File
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "guardrail", "SKILL.md")
EXAMPLES_PATH = os.path.join(CURRENT_DIR, "..", "skills", "guardrail", "examples.json")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    BASE_SYSTEM_PROMPT = f.read()

# Load examples
EXAMPLES = []
if os.path.exists(EXAMPLES_PATH):
    with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
        EXAMPLES = json.load(f)

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from the model output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def build_dynamic_prompt() -> str:
    """Append 1 SAFE and 1 UNSAFE random few-shot example to the base prompt to keep it balanced."""
    prompt = BASE_SYSTEM_PROMPT
    if EXAMPLES:
        prompt += "\n\n[FEW-SHOT EXAMPLES (For Reference)]\n"
        
        # Separate examples into SAFE (answers) and UNSAFE (refusals)
        safe_examples = [ex for ex in EXAMPLES if "ขออภัย" not in ex['response']]
        unsafe_examples = [ex for ex in EXAMPLES if "ขออภัย" in ex['response']]
        
        selected_examples = []
        if safe_examples:
            selected_examples.append(random.choice(safe_examples))
        if unsafe_examples:
            selected_examples.append(random.choice(unsafe_examples))
            
        # Shuffle them so it's not always SAFE first
        random.shuffle(selected_examples)
        
        for i, ex in enumerate(selected_examples):
            prompt += f"\n--- Example {i+1} ({ex['category']}) ---\n"
            prompt += f"User Query: {ex['query']}\n"
            prompt += f"<think>\n{ex['think']}\n</think>\n"
            prompt += f"{ex['response']}\n"
    return prompt

async def sandwich_guardrail_node(state: GraphState) -> GraphState:
    """
    Single-node Sandwich Guardrail:
    Executes Intent Extraction -> Mental Draft -> Safety Judge internally within <think>.
    """
    query = state["query"]
    
    # Generate dynamic prompt
    system_prompt = build_dynamic_prompt()
    
    # Generate response from the LLM
    raw_response = await llm_client.agenerate_text(
        system_prompt=system_prompt,
        user_prompt=query,
        temperature=0.7
    )
    
    # Process the output
    clean_response = strip_think_tags(raw_response)
    
    # Fallback in case of empty response (if it outputs ONLY a <think> block)
    if not clean_response:
        clean_response = "ขออภัย ฉันไม่สามารถประมวลผลคำขอนี้ได้"

    # Update state
    state["final_response"] = clean_response
    
    return state
