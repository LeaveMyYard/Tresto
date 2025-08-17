from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

MAIN_PROMPT = (PROMPTS_DIR / "main.txt").read_text()