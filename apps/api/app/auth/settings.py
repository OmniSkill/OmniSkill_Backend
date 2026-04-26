"""Auth configuration loaded from environment."""

from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    jwt_secret_key: str = "CHANGE-ME-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    anonymous_token_expire_hours: int = 24
    bcrypt_rounds: int = 12
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = {"env_prefix": "", "case_sensitive": False}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
