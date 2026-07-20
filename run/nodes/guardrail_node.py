import os
import re
from state import GraphState
from nodes.llm_clients import llm_client

# Load System Prompt from Markdown File
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "guardrail_system_prompt.md")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from the model output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

async def guardrail_agent_node(state: GraphState) -> GraphState:
    """
    Node to act as the primary guardrail and responder.
    In Phase 1, this node handles both safety assessment and answering.
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
    
    # Fallback in case of empty response
    if not clean_response:
        clean_response = "ขออภัย ฉันไม่สามารถประมวลผลคำขอนี้ได้"

    # Update state
    state["final_response"] = clean_response
    
    # For Phase 1, we assume it's processed and ready. 
    # In Phase 2, we would parse the <think> block to determine `is_safe` and route accordingly.
    state["is_safe"] = True 
    
    return state
