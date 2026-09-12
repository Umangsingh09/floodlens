from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration, overridable via environment variables."""

    app_name: str = "FloodLens API"
    app_version: str = "0.1.0"
    cors_allow_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_prefix = "FLOODLENS_"


settings = Settings()
