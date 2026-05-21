import os
from typing import List, Optional

import yaml
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    PROJECT_NAME: str = "MedAssist AI"
    APP_VERSION: str = "1.0.0"
    API_STR: str = "/api/v1"
    API: str = "/api/v1"
    PROMPTS: dict = {}

    MODEL_PRICING: dict = {
        "gpt-4o": {
            "input_cost_per_1k_tokens": 0.005,
            "output_cost_per_1k_tokens": 0.015,
        },
        "gpt-4o-mini": {
            "input_cost_per_1k_tokens": 0.00015,
            "output_cost_per_1k_tokens": 0.0006,
        },
        "gpt-3.5-turbo": {
            "input_cost_per_1k_tokens": 0.0005,
            "output_cost_per_1k_tokens": 0.0015,
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_prompts()

    def _load_prompts(self):
        prompts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
        self.PROMPTS = {}
        if os.path.exists(prompts_dir) and os.path.isdir(prompts_dir):
            for filename in os.listdir(prompts_dir):
                if filename.endswith(".yml") or filename.endswith(".yaml"):
                    file_path = os.path.join(prompts_dir, filename)
                    with open(file_path, "r") as f:
                        prompt_data = yaml.safe_load(f)
                        if prompt_data:
                            self.PROMPTS.update(prompt_data)
        else:
            print(f"WARNING: Prompts directory not found at {prompts_dir}")

    API_ROOT_PATH: str = os.getenv("API_ROOT_PATH", "/")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "")
    DATABASE_URI: str = os.getenv("DATABASE_URI", "sqlite:///./db.sqlite3")
    DEFAULT_LOCALE: Optional[str] = os.getenv("DEFAULT_LOCALE", None)

    cors_origins_str: Optional[str] = os.getenv("CORS_ALLOWED_ORIGINS", None)
    BACKEND_CORS_ORIGINS: List[str] = (
        [origin.strip() for origin in cors_origins_str.split(",")] if cors_origins_str else ["*"]
    )

    SQLALCHEMY_LOGGING: bool = os.getenv("SQLALCHEMY_LOGGING", "False").lower() == "true"


configs = Config()
