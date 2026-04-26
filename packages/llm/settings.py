"""LLM configuration loaded from environment."""

from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    google_api_key: str = ""
    gemini_model_pro: str = "gemini-1.5-pro"
    gemini_model_flash: str = "gemini-1.5-flash"
    gemini_embedding_model: str = "models/text-embedding-004"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "unmapped"
    llm_temperature: float = 0.2
    llm_max_retries: int = 3
    llm_retry_base_wait: float = 1.0
    llm_retry_max_wait: float = 30.0
    redis_url: str = "redis://localhost:6379/0"

    model_config = {"env_prefix": "", "case_sensitive": False}
