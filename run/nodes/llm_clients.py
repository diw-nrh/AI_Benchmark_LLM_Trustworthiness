from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
import uuid
from config import Qwen_PATH, Guard_PATH


# =============================================================================
# WildGuard Prompt Template (ไม่ใช่ ChatML — ใช้ format เฉพาะของ WildGuard)
# =============================================================================
WILDGUARD_INSTRUCTION_FORMAT = """<s><|user|>
[INST] You are a classifier for analyzing interactions between humans and LLMs. Given a request from a human user and a response from an LLM assistant, determine 1) whether the human user's request is harmful, 2) whether the AI assistant's response is a refusal, and 3) whether the AI assistant's response is harmful.

Human user:
{prompt}

AI assistant:
{response}

---

Answers: [/INST]
<|assistant|>
"""


# =============================================================================
# Qwen LLM Client (vLLM Async Engine)
# =============================================================================
class LLMClient:
    """Inference Service — Logical Microservice ที่ดูแลการ Generate ทั้งหมด"""
    
    def __init__(self):
        # Engine จะยังไม่ถูกสร้างจนกว่าจะเรียก initialize()
        self.engine = None
        self.model_name = Qwen_PATH

    def initialize(self):
        """เรียกใช้ตอน SYSTEM INITIALIZATION เท่านั้น ไม่สร้างตอน import"""
        print(f"--- SYSTEM INITIALIZATION (Inference Service) ---")
        print(f"Loading Qwen from: {self.model_name}")
        
        engine_args = AsyncEngineArgs(
            model=self.model_name,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            max_model_len=32768,
            enforce_eager=True
        )
        
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        print("--- 🚀 Qwen Inference Service Initialized! ---")

    async def agenerate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        Generate text using local vLLM engine.
        We format the prompt manually to Qwen3's ChatML format.
        """
        if self.engine is None:
            raise RuntimeError("LLMClient has not been initialized! Call llm_client.initialize() first.")
        
        # Build ChatML prompt
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=0.9,
            max_tokens=1024,
            stop=["<|im_end|>", "<|endoftext|>"]
        )
        
        request_id = str(uuid.uuid4())
        try:
            # Generate output via async generator
            generator = self.engine.generate(prompt, sampling_params, request_id)
            final_output = ""
            async for request_output in generator:
                final_output = request_output.outputs[0].text
                
            return final_output.strip()
        except Exception as e:
            print(f"[ERROR] Qwen Inference failed: {e}")
            return ""


# =============================================================================
# WildGuard Client (vLLM Async Engine)
# =============================================================================
class WildGuardClient:
    """Safety Guard — ใช้ WildGuard model ตรวจสอบว่า request เป็นอันตรายหรือไม่ (vLLM)"""

    def __init__(self):
        self.engine = None
        self.model_name = Guard_PATH

    def initialize(self):
        """โหลด WildGuard model ผ่าน vLLM"""
        print(f"--- SYSTEM INITIALIZATION (WildGuard) ---")
        print(f"Loading WildGuard from: {self.model_name}")

        engine_args = AsyncEngineArgs(
            model=self.model_name,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            max_model_len=2048,
            enforce_eager=True
        )

        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        print("--- 🛡️ WildGuard Initialized! ---")

    async def aevaluate(self, prompt: str, response: str = "") -> dict:
        """
        ตรวจสอบ prompt ด้วย WildGuard (async via vLLM)
        Returns dict with keys: is_safe, raw_output, is_harmful_request
        """
        if self.engine is None:
            raise RuntimeError("WildGuardClient has not been initialized! Call wildguard_client.initialize() first.")

        # Build WildGuard prompt (ไม่ใช่ ChatML)
        model_input = WILDGUARD_INSTRUCTION_FORMAT.format(
            prompt=prompt,
            response=response
        )

        sampling_params = SamplingParams(
            temperature=0.0,  # Deterministic for classification
            max_tokens=32,
            stop=["<|end|>", "</s>"]
        )

        request_id = str(uuid.uuid4())
        try:
            generator = self.engine.generate(model_input, sampling_params, request_id)
            final_output = ""
            async for request_output in generator:
                final_output = request_output.outputs[0].text

            output_text = final_output.strip()
        except Exception as e:
            print(f"[ERROR] WildGuard inference failed: {e}")
            output_text = "Harmful request: no\nResponse refusal: no\nHarmful response: no"

        # Parse — ใช้แค่ "Harmful request" เป็นตัวตัดสินใจ
        is_harmful_request = "harmful request: yes" in output_text.lower()

        return {
            "is_safe": not is_harmful_request,
            "raw_output": output_text,
            "is_harmful_request": is_harmful_request,
        }


# =============================================================================
# Singleton instances — ยังไม่โหลดโมเดล จนกว่าจะเรียก .initialize()
# =============================================================================
llm_client = LLMClient()
wildguard_client = WildGuardClient()