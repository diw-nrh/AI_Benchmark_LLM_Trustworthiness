from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
import uuid
from config import Qwen_PATH


# =============================================================================
# Qwen LLM Client (vLLM Async Engine)
# Sandbox version — ใช้ Qwen3-14B-Instruct ตัวเดียว, 1 call per query
# =============================================================================
class LLMClient:
    """Inference Service — ใช้ Qwen ตัวเดียวทำทุกอย่างด้วย CoT"""
    
    def __init__(self):
        self.engine = None
        self.model_name = Qwen_PATH

    def initialize(self):
        """เรียกใช้ตอน SYSTEM INITIALIZATION เท่านั้น"""
        print(f"--- SYSTEM INITIALIZATION (Inference Service) ---")
        print(f"Loading Qwen from: {self.model_name}")
        
        engine_args = AsyncEngineArgs(
            model=self.model_name,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.90,
            max_model_len=8192,
            enforce_eager=True,
            dtype="bfloat16"
        )
        
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        print("--- 🚀 Qwen Inference Service Initialized! ---")

    async def agenerate_text(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """
        Generate text using local vLLM engine.
        Qwen3 ChatML format — ปล่อยให้ thinking mode ทำงานตามปกติ
        """
        if self.engine is None:
            raise RuntimeError("LLMClient has not been initialized! Call llm_client.initialize() first.")
        
        # Build ChatML prompt
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        sampling_params = SamplingParams(
            temperature=temperature,
            top_p=0.9,
            max_tokens=max_tokens,
            stop=["<|im_end|>", "<|endoftext|>"]
        )
        
        request_id = str(uuid.uuid4())
        try:
            generator = self.engine.generate(prompt, sampling_params, request_id)
            final_output = ""
            async for request_output in generator:
                final_output = request_output.outputs[0].text
                
            return final_output.strip()
        except Exception as e:
            print(f"[ERROR] Qwen Inference failed: {e}")
            return ""


# =============================================================================
# Singleton instance
# =============================================================================
llm_client = LLMClient()
