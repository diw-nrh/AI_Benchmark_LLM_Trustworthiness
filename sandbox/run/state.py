from typing import TypedDict

class GraphState(TypedDict, total=False):
    # Core Inputs
    query_id: str
    query: str
    
    # Single CoT Node output — ทำทุกอย่างในครั้งเดียว
    final_response: str
