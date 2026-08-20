from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./shortener.db"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    REDIS_TTL_SECONDS: int = 259200
    RATE_LIMIT_PER_IP: int = 100
    RATE_LIMIT_WINDOW: int = 3600
    BASE_URL: str = "http://localhost:8000"

    class Config:
        model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.REDIS_URL =f'redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}'


@lru_cache
def get_settings() -> Settings:
    return Settings()

