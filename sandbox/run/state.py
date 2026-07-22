from typing import TypedDict

class GraphState(TypedDict, total=False):
    # Core Inputs
    query_id: str
    query: str
    
    # Sandwich Guardrail Fields
    core_intent: str       # (Input Guardrail) วัตถุประสงค์หลักที่สกัดจากคำถาม
    draft_response: str    # (Answer Node) คำตอบร่างที่เจนออกมาก่อนตรวจ
    is_safe: bool          # (Output Guardrail) ผลการตรวจสอบความปลอดภัยของคำตอบร่าง
    refusal_reason: str    # (Output Guardrail) เหตุผลหากตรวจพบว่าคำตอบอันตราย
    final_response: str    # คำตอบสุดท้ายที่จะส่งออกไปให้ผู้ใช้