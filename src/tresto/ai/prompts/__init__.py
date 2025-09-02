from collections.abc import Sequence
from functools import cache
from pathlib import Path

CURRENT_DIR = Path(__file__).parent


@cache
def load_prompt(name: str) -> str:
    with open(CURRENT_DIR / f"{name}.md", encoding="utf-8") as f:
        return f.read()


def system(available_secrets: Sequence[str]) -> str:
    return load_prompt("system").format(available_secrets=", ".join(available_secrets))


def codegen(current_recording_code: str) -> str:
    return load_prompt("codegen").format(current_recording_code=current_recording_code)


def create_test(available_secrets: Sequence[str]) -> str:
    return load_prompt("create_test").format(available_secrets=", ".join(available_secrets))
