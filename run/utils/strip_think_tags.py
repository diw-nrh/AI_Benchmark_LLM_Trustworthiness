import re
def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from the model output."""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()