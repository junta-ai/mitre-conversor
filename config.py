"""
Configuration settings for the MITRE ATT&CK Classifier API
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    API_TITLE: str = "MITRE ATT&CK Classifier API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080

    CORS_ORIGINS: list = [
        "http://localhost:5173",
        "https://mitre-mapper-front.vercel.app",
        "*",
    ]

    DATA_DIR: Path = Path("data")
    MITRE_DATA_PATH: Path = DATA_DIR / "processed" / "mitre_techniques_complete.json"
    PROCESSED_DATA_PATH: Path = DATA_DIR / "processed" / "mitre_techniques.json"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.2:1b"
    LLM_TEMPERATURE: float = 0.7
    LLM_ENABLED: bool = True

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
