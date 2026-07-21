from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.sampling_params import SamplingParams
import uuid
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import Qwen_PATH, Guard_PATH


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


# =============================================================================
# WildGuard Client (Transformers)
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


class WildGuardClient:
    """Safety Guard — ใช้ WildGuard model ตรวจสอบว่า request เป็นอันตรายหรือไม่"""

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_path = Guard_PATH

    def initialize(self):
        """โหลด WildGuard model ลง GPU"""
        print(f"--- SYSTEM INITIALIZATION (WildGuard) ---")
        print(f"Loading WildGuard from: {self.model_path}")

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        self.model.eval()
        print("--- 🛡️ WildGuard Initialized! ---")

    def evaluate(self, prompt: str, response: str = "") -> dict:
        """
        ตรวจสอบ prompt ด้วย WildGuard
        Returns dict with keys: is_safe, raw_output, is_harmful_request
        """
        if self.model is None:
            raise RuntimeError("WildGuardClient has not been initialized! Call wildguard_client.initialize() first.")

        model_input = WILDGUARD_INSTRUCTION_FORMAT.format(
            prompt=prompt,
            response=response
        )

        tokenized_input = self.tokenizer(
            [model_input],
            return_tensors="pt",
            add_special_tokens=False
        )
        # Move to same device as model
        tokenized_input = {
            k: v.to(self.model.device)
            for k, v in tokenized_input.items()
        }

        with torch.no_grad():
            result = self.model.generate(
                **tokenized_input,
                max_new_tokens=32
            )

        # Decode only newly generated tokens
        input_len = tokenized_input["input_ids"].shape[1]
        output_text = self.tokenizer.decode(
            result[0][input_len:],
            skip_special_tokens=True
        ).strip()

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