"""LLM configuration loaded from environment."""

from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    google_api_key: str = ""
    gemini_model_pro: str = "gemini-1.5-pro"
    gemini_model_flash: str = "gemini-1.5-flash"
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "unmapped"
    llm_temperature: float = 0.2
    llm_max_retries: int = 3

    model_config = {"env_prefix": "", "case_sensitive": False}
