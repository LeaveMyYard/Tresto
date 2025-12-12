from __future__ import annotations

from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    model_config = {
        "env_prefix": "TEST_",
        "case_sensitive": False,
        "extra": "ignore",
    }

