from pathlib import Path
from functools import lru_cache

PROMPTS_DIR = Path(__file__).parent

@lru_cache(maxsize=10)
def load_prompt(filename: str) -> str:
    """
    Load a markdown prompt from the prompts directory.
    Uses lru_cache to prevent repeated disk I/O.
    """
    prompt_path = PROMPTS_DIR / filename
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file {filename} not found in {PROMPTS_DIR}")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
