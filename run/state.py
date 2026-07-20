from typing import TypedDict

class GraphState(TypedDict, total=False):
    # Core Inputs
    query_id: str
    query: str
    
    # Phase 1: Guardrail & Final Response
    # In the future (Phase 2), these fields can be populated by different agents
    is_safe: bool
    final_response: str
