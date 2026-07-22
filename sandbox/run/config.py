import os

# ==========================================
# ENVIRONMENT VARIABLES (MUST BE SET FIRST)
# ==========================================
# สั่ง vLLM ให้หยุดความล้ำสมัย ปิด V1 Engine แล้วกลับไปใช้ V0 เหมือนยุค 0.7.3
os.environ["VLLM_USE_V1"] = "0"
# บังคับวิธีสร้าง Process ให้ไม่เกิด Error แดง
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

# ==========================================
# ABSOLUTE PATHS FOR COMPETITION
# ==========================================
# ถอยหลังจากไฟล์ config.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Model Path (ตามตัวอย่างที่ให้มา)
MODEL_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../../models/Qwen3-14B-Instruct"))

# Progress Lib Path (ตามกติกา)
PROGRESS_LIB = "/benchmark_lib/progress"

# Result CSV Path (ตามกติกา)
RESULT_CSV_PATH = "/result/submission.csv"

# Dataset Path (Phase 1 คือ dataset.csv, ในอนาคตอาจจะเป็น test.json ก็แก้ไขได้ที่นี่)
# เนื่องจาก Phase 1 เป็น dataset.csv ผมใช้ path เดียวกับ RESULT_CSV_PATH แต่อยู่ในโฟลเดอร์ model/test ตามตัวอย่าง
DATASET_PATH = "/model/test/dataset.csv"


# ==========================================
# EXECUTION CONFIGURATION
# ==========================================
# Concurrency limit (Semaphore) to prevent overloading the vLLM engine
# เริ่มต้นที่ 15 สำหรับ VRAM 40GB
MAX_CONCURRENT_TASKS = 15