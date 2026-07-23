from typing import TypedDict

class GraphState(TypedDict, total=False):
    query_id: str
    query: str
    threat_summary: str
    draft_response: str
    final_response: str
