import os

# ==========================================
# ENVIRONMENT VARIABLES (MUST BE SET FIRST)
# ==========================================
os.environ["VLLM_USE_V1"] = "0"
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

# ==========================================
# ABSOLUTE PATHS FOR COMPETITION
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Model Path — ใช้ Qwen3-14B-Instruct (Full, ไม่ใช่ AWQ)
Qwen_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "../../models/Qwen3-14B-Instruct"))

# Progress Lib Path (ตามกติกา)
PROGRESS_LIB = "/benchmark_lib/progress"

# Result CSV Path (ตามกติกา)
RESULT_CSV_PATH = "/result/submission.csv"

# Dataset Path
DATASET_PATH = "/model/test/dataset.csv"

# ==========================================
# EXECUTION CONFIGURATION
# ==========================================
MAX_CONCURRENT_TASKS = 15
