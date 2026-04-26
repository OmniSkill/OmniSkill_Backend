"""Database-layer settings loaded from environment."""

from pydantic_settings import BaseSettings


class DataSettings(BaseSettings):
    database_url: str = "postgresql+asyncpg://unmapped:unmapped_dev@localhost:5432/unmapped"
    echo_sql: bool = False
    pool_size: int = 10
    max_overflow: int = 20

    model_config = {"env_prefix": "", "case_sensitive": False}
