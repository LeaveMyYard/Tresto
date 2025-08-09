from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class OpenAISettings(BaseSettings):
    model_config = {
        "env_prefix": "OPENAI_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    api_key: SecretStr | None = Field(default=None, description="API key for OPENAI")
