import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.modules.logger import pipeline_logger


class OpenSearchSettings(BaseModel):
    user: str
    password: str
    host: str
    port: int
    scheme: str = "https"
    pool_size: int = 10


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AIDR Bastion"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    OS: Optional[OpenSearchSettings] = None
    PIPELINE_CONFIG: dict = Field(default_factory=dict)

    SIMILARITY_PROMPT_INDEX: str = "similarity-prompt-index"

    SIMILARITY_NOTIFY_THRESHOLD: float = 0.7
    SIMILARITY_BLOCK_THRESHOLD: float = 0.87

    # Vector Backend Settings
    VECTOR_BACKEND: str = "auto"  # auto, qdrant, opensearch

    # Qdrant Settings
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: Optional[str] = None

    CORS_ORIGINS: list[str] = Field(default=["*"], env="CORS_ORIGINS", description="List of allowed origins for CORS")

    EMBEDDINGS_MODEL: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = None

    ML_PIPELINE_PATH: Optional[str] = None


def load_pipeline_config() -> dict:
    """
    Loads pipeline configuration from config.json file.
    Returns raw configuration without instantiating pipelines to avoid circular imports.
    """
    config_path = Path("config.json")
    loaded_config = {}

    if not config_path.exists():
        return loaded_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        pipeline_logger.error(f"Error reading config.json: {e}")
        return loaded_config


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached instance of settings.
    Used to avoid reading .env file multiple times.
    """
    settings = Settings()
    settings.PIPELINE_CONFIG = load_pipeline_config()
    return settings
