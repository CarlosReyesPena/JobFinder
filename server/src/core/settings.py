# backend/core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    API_VERSION: str = "1.0.0"
    APP_NAME: str = "JobFinder"
    DEBUG: bool = True
    API_PORT: int = 8000
    DATABASE_URL: str = "sqlite:///job_application.db"

    # Tauri specific settings
    TAURI_ALLOWED_ORIGINS: list = ["tauri://localhost", "tauri://localhost-tt"]

    # React development settings
    REACT_DEV_SERVER: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()