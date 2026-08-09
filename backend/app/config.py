from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "PersonalityChat"
    secret_key: str = "change-me-in-production-32-chars!!"
    google_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./chat.db"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
