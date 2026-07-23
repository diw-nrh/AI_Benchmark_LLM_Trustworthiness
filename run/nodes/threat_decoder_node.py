import os
import re
from state import GraphState
from nodes.llm_clients import llm_client
from termcolor import colored

# Load the Threat Decoder Prompt
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "threat-decoder", "SKILL.md")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    THREAT_DECODER_PROMPT = f.read()

async def threat_decoder_node(state: GraphState) -> GraphState:
    query = state["query"]
    query_id = state.get("query_id", "Unknown")
    
    user_prompt = f"User Query: {query}"
    
    try:
        # Call LLM to decode the threat
        raw_response = await llm_client.agenerate_text(THREAT_DECODER_PROMPT, user_prompt)
        
        # Extract <threat_summary>
        match = re.search(r'<threat_summary>(.*?)</threat_summary>', raw_response, re.IGNORECASE | re.DOTALL)
        if match:
            threat_summary = match.group(1).strip()
        else:
            threat_summary = "- **Core Topic:** Unknown\n- **Disguise Used:** None"
            
        # Store in state
        state["threat_summary"] = threat_summary
        
        # Logging
        first_line = threat_summary.splitlines()[0] if threat_summary else "Unknown"
        print(colored(f"[DECODER] {query_id}: {first_line}", "cyan"))
        
    except Exception as e:
        print(colored(f"[DECODER ERROR] {query_id}: {str(e)}", "red"))
        state["threat_summary"] = "- **Core Topic:** Error during decoding\n- **Disguise Used:** None"
        
    return state
