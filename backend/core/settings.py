from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

class Settings(BaseSettings):
    """Configuration globale de l'application"""

    # API Keys
    OPENAI_API_KEY: Optional[str] = None#os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: Optional[str] = None#os.getenv("GROQ_API_KEY", "")

    # LLM Configuration
    DEFAULT_MAX_TOKENS: int = 1024
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_PROVIDER: str = "ollama"
    DEFAULT_MAX_RETRIES: int = 3

    # Model names
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_STRUCTURED_MODEL: Optional[str] = None  # "llama3.2:3b" to enable structured output, leave None to disable
    OLLAMA_MODEL: str = "deepseek-r1:7b"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

