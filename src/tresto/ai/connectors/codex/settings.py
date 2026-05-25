from __future__ import annotations

from pydantic_settings import BaseSettings


class CodexSettings(BaseSettings):
    model_config = {
        "env_prefix": "CODEX_",
        "case_sensitive": False,
        "extra": "ignore",
    }

    auth_file: str | None = None
