from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
import uuid
from config import MODEL_PATH

class LLMClient:
    """Inference Service — Logical Microservice ที่ดูแลการ Generate ทั้งหมด"""
    
    def __init__(self):
        # Engine จะยังไม่ถูกสร้างจนกว่าจะเรียก initialize()
        self.engine = None
        self.model_name = MODEL_PATH

    def initialize(self):
        """เรียกใช้ตอน SYSTEM INITIALIZATION เท่านั้น ไม่สร้างตอน import"""
        print(f"--- SYSTEM INITIALIZATION (Inference Service) ---")
        print(f"Loading model from: {self.model_name}")
        
        engine_args = AsyncEngineArgs(
            model=self.model_name,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.9,
            max_model_len=32768,
            enforce_eager=True
        )
        
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)
        print("--- 🚀 Inference Service Initialized! ---")

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
            print(f"[ERROR] Inference Service failed: {e}")
            return ""

# Singleton instance — แต่ยังไม่โหลดโมเดล จนกว่าจะเรียก .initialize()
llm_client = LLMClient()