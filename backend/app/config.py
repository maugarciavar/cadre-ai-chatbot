from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration, read from environment variables (or .env locally)."""

    allowed_origins: str = "http://localhost:5173"

    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-5.6-luna"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout_seconds: float = 30.0

    max_history_messages: int = 20
    max_message_length: int = 2000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
