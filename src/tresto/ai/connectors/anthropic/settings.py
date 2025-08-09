from __future__ import annotations

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class AnthropicSettings(BaseSettings):
    model_config = {
        "env_prefix": "ANTHROPIC_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    api_key: SecretStr | None = Field(default=None, description="API key for ANTHROPIC")
