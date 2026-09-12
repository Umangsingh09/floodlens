from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration, overridable via environment variables."""

    app_name: str = "FloodLens API"
    app_version: str = "0.1.0"
    cors_allow_origins: list[str] = ["http://localhost:5173"]
    output_dir: str = str((Path(__file__).resolve().parents[3] / "ai" / "outputs").resolve())
    risk_threshold: float = 0.7
    enable_scheduler: bool = True
    risk_refresh_interval_hours: int = 12

    class Config:
        env_file = ".env"
        env_prefix = "FLOODLENS_"
        extra = "ignore"


settings = Settings()
