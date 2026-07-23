import os
# Ensure environment variables are loaded first from config
import config

import asyncio
import pandas as pd
import time
import sys
import nest_asyncio
from graph import app

nest_asyncio.apply()

# ==============================================================================
# 🚨 STRICT CUDA CHECK BEFORE RUNNING
# ==============================================================================
try:
    import torch
    if not torch.cuda.is_available():
        print("[FATAL ERROR] ❌ CUDA is NOT available. This program requires a GPU to run.")
        sys.exit(1)
    
    device_name = torch.cuda.get_device_name(0)
    print(f"\n[INFO] ✅ CUDA is available and working properly. Using device: {device_name}\n")
except Exception as e:
    print(f"\n[FATAL ERROR] ❌ Failed to initialize CUDA: {e}")
    sys.exit(1)
# ==============================================================================

def call_progress(i):
    """Watchdog Heartbeat to prevent competition platform timeout."""
    if os.path.exists(config.PROGRESS_LIB):
        os.system(f"{config.PROGRESS_LIB} {i}")

def initialize_system():
    """
    --- SYSTEM INITIALIZATION ---
    เรียกก่อนเริ่มประมวลผล เพื่อโหลดโมเดลลง GPU
    ใช้ Qwen3-14B-Instruct ตัวเดียว (ไม่มี WildGuard แล้ว)
    """
    print("--- SYSTEM INITIALIZATION ---")
    
    from nodes.llm_clients import llm_client
    # [OLD] from nodes.llm_clients import wildguard_client
    
    llm_client.initialize()
    # [OLD] wildguard_client.initialize()  # ไม่ใช้ WildGuard แล้ว
    
    print("--- INITIALIZATION COMPLETE ---")

async def process_single_query(inputs: dict, semaphore: asyncio.Semaphore) -> dict:
    """
    Process a single query through the LangGraph under Semaphore limits.
    """
    async with semaphore:
        print(f"⚡ Processing Query ID: {inputs['query_id']}")
        try:
            final_state = await app.ainvoke(inputs)
            
            print(f"✅ Finished Query ID: {inputs['query_id']}")
            return {
                "id": inputs["query_id"],
                "response": final_state.get("final_response", "")
            }
        except Exception as e:
            print(f"[ERROR] Pipeline failed on {inputs['query_id']}: {e}")
            return {
                "id": inputs["query_id"],
                "response": "ขออภัย เกิดข้อผิดพลาดในการประมวลผล"
            }

async def task_wrapper(inputs: dict, semaphore: asyncio.Semaphore, progress_state: dict) -> dict:
    """Wrapper to update Watchdog progress as each task completes."""
    result = await process_single_query(inputs, semaphore)
    progress_state["count"] += 1
    call_progress(progress_state["count"])
    return result

async def run_pipeline():
    print("\n============================================")
    print("       TRUSTWORTHINESS CHALLENGE (PHASE 1)    ")
    print("       Internal Sandwich Guardrail (Single Node) ")
    print("============================================\n")
    
    start_time = time.time()
    
    # 0. Initialize System (โหลดโมเดลก่อน)
    initialize_system()
    
    # 1. Load Dataset
    print(f"📥 Loading dataset from {config.DATASET_PATH}...")
    if not os.path.exists(config.DATASET_PATH):
        print(f"[ERROR] Dataset not found at: {config.DATASET_PATH}")
        # Fallback to local dataset for testing if absolute path fails
        fallback_path = os.path.join(config.PROJECT_ROOT, "dataset.csv")
        if os.path.exists(fallback_path):
            print(f"[INFO] Falling back to local dataset: {fallback_path}")
            config.DATASET_PATH = fallback_path
        else:
            sys.exit(1)
            
    df = pd.read_csv(config.DATASET_PATH)
    queries = df.to_dict(orient='records')
    
    print(f"📊 Found {len(queries)} queries. Processing {config.MAX_CONCURRENT_TASKS} concurrently...")
    
    # 2. Setup Semaphore, Progress State, and Tasks
    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_TASKS)
    progress_state = {"count": 0}
    tasks = []
    for q in queries:
        inputs = {
            "query_id": q["id"],
            "query": q["query"]
        }
        tasks.append(task_wrapper(inputs, semaphore, progress_state))
    
    # 3. Run in Parallel (Order is guaranteed to be preserved by asyncio.gather)
    results = await asyncio.gather(*tasks)
    
    # 4. Save to Submission CSV
    print(f"\n💾 Saving results to {config.RESULT_CSV_PATH}...")
    os.makedirs(os.path.dirname(config.RESULT_CSV_PATH), exist_ok=True)
    submission_df = pd.DataFrame(results)
    
    # Enforce correct column order just in case
    submission_df = submission_df[["id", "response"]]
    
    # Ensure encoding is strictly utf-8 and newlines are correct
    submission_df.to_csv(config.RESULT_CSV_PATH, index=False, encoding='utf-8', lineterminator='\n')
    
    # Final Watchdog Call
    call_progress(len(queries))
    
    total_time = time.time() - start_time
    print(f"✨ All done! Processed {len(submission_df)} records in {total_time:.2f} seconds.")

def main():
    print("⏳ หน่วงเวลา 10 วินาที เพื่อให้ระบบเก็บ Log (ตามคำแนะนำทีมงาน)...")
    time.sleep(10)
    
    # เรียก Progress ทันทีตั้งแต่เริ่ม เพื่อต่ออายุ Watchdog ไม่ให้มันตัดจบ!
    call_progress(0)
    
    try:
        asyncio.run(run_pipeline())
    except Exception as e:
        print(f"[FATAL ERROR] เกิดข้อผิดพลาดร้ายแรงระหว่างรัน Pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()