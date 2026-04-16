from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://us.cloud.langfuse.com"
    llm_model: str = "gpt-4.1-mini"
    judge_model: str = "gpt-4.1"
    embedding_model: str = "text-embedding-3-small"
    llm_temperature: float = 0.1
    retrieval_k: int = 4
    chroma_persist_dir: str = "chroma_db"
    collection_name: str = "restoration_portfolio"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

