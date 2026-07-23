import os
import json
import random
from utils.strip_think_tags import strip_think_tags
from state import GraphState
from nodes.llm_clients import llm_client

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(CURRENT_DIR, "..", "skills", "intent-extractor", "SKILL.md")
EXAMPLES_PATH = os.path.join(CURRENT_DIR, "..", "skills", "intent-extractor", "examples.json")

with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    BASE_SYSTEM_PROMPT = f.read()

# Load examples
EXAMPLES = []
if os.path.exists(EXAMPLES_PATH):
    with open(EXAMPLES_PATH, "r", encoding="utf-8") as f:
        EXAMPLES = json.load(f)

def build_dynamic_prompt() -> str:
    """Append 1 SAFE and 1 UNSAFE random few-shot example to the base prompt."""
    prompt = BASE_SYSTEM_PROMPT
    if EXAMPLES:
        prompt += "\n\n[FEW-SHOT EXAMPLES (For Reference)]\n"
        
        safe_examples = [ex for ex in EXAMPLES if ex.get("decision") == "SAFE"]
        unsafe_examples = [ex for ex in EXAMPLES if ex.get("decision") == "UNSAFE"]
        
        selected_examples = []
        if safe_examples:
            selected_examples.append(random.choice(safe_examples))
        if unsafe_examples:
            selected_examples.append(random.choice(unsafe_examples))
            
        random.shuffle(selected_examples)
        
        for i, ex in enumerate(selected_examples):
            prompt += f"\n--- Example {i+1} ({ex['category']}) ---\n"
            prompt += f"User Query: {ex['query']}\n"
            prompt += f"<think>\n{ex['think']}\n</think>\n"
            prompt += f"Output: {ex['extracted_intent']}\n"
    return prompt

async def intent_node(state: GraphState) -> GraphState:
    """
    Node 1 (Input Guardrail): ถอดหน้ากาก/แปลงคำถาม เพื่อดึง Core Intent ออกมาจาก Query ต้นฉบับ
    """
    query = state["query"]
    query_id = state.get("query_id", "unknown")
    
    print(f"🎯 [{query_id}] [1/3] Extracting Core Intent from Query...")
    
    system_prompt = build_dynamic_prompt()
    raw_intent = await llm_client.agenerate_text(
        system_prompt=system_prompt,
        user_prompt=query,
        temperature=0.3
    )
    
    clean_intent = strip_think_tags(raw_intent)
    if not clean_intent:
        clean_intent = query  # Fallback: ถ้าสกัดไม่ได้ ให้ใช้คำถามเดิม
        
    print(f"  📌 [{query_id}] Core Intent: {clean_intent[:100]}...")
    state["core_intent"] = clean_intent
    return state
