
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ask Sphere"
    app_env: str = "development"
    api_prefix: str = "/api/v1"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "ask_sphere"

    chroma_path: str = "./data/chroma"
    embedding_model: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    request_timeout: int = 20
    max_scrape_chars: int = 20000

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
