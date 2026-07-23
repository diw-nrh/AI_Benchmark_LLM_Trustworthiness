import os
import re
from state import GraphState
from nodes.llm_clients import llm_client

# Load System Prompt from Markdown File
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "guardrail", "SKILL.md")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from the model output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

async def sandwich_guardrail_node(state: GraphState) -> GraphState:
    """
    Single-node Sandwich Guardrail:
    Executes Intent Extraction -> Mental Draft -> Safety Judge internally within <think>.
    """
    query = state["query"]
    
    # Generate response from the LLM
    raw_response = await llm_client.agenerate_text(
        system_prompt=SYSTEM_PROMPT,
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
