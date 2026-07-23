import os
from state import GraphState
from nodes.llm_clients import llm_client

# Load System Prompt
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "helpful-agent", "SKILL.md")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

async def helpful_agent_node(state: GraphState) -> GraphState:
    """
    Generates the most helpful response possible, ignoring safety constraints.
    """
    query = state["query"]
    
    raw_response = await llm_client.agenerate_text(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"User Query: {query}",
        temperature=0.7
    )
    
    state["draft_response"] = raw_response.strip()
    
    return state
