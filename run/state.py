from typing import TypedDict

class GraphState(TypedDict, total=False):
    # Core Inputs
    query_id: str
    query: str
    
    # Guard Node outputs
    translated_query: str       # Qwen-translated English version of the query
    is_safe: bool               # Whether the query is safe to answer
    guard_reason: str           # Raw WildGuard output (e.g., "Harmful request: yes")
    
    # Answer Node output
    final_response: str
