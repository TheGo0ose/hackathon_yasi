"""
Configuration module — loads settings from environment / .env file.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Telegram ────────────────────────────────────────────
    bot_token: str = "CHANGE_ME"

    # ── B2B Dashboard ───────────────────────────────────────
    dashboard_api_key: str = "hackathon-secret-key-2026"

    # ── LLM (OpenRouter) ────────────────────────────────────
    openrouter_api_key: str = "CHANGE_ME"

    # ── ML Model ────────────────────────────────────────────
    use_mock_scorer: bool = True
    model_path: str = "app/ml_inference/models/model.pkl"
    default_threshold: float = 0.5

    # ── CORS ────────────────────────────────────────────────
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Singleton — import this wherever you need settings
settings = Settings()
