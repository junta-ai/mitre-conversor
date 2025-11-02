"""
Configuration settings for the MITRE ATT&CK Classifier API
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    API_TITLE: str = "MITRE ATT&CK Classifier API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]
    
    # Data Paths
    DATA_DIR: Path = Path("data")
    MITRE_DATA_PATH: Path = DATA_DIR / "processed" / "mitre_techniques_complete.json"  # Now includes practical situations!
    PROCESSED_DATA_PATH: Path = DATA_DIR / "processed" / "mitre_techniques.json"
    
    # RAG Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Fast and efficient
    # Alternative models:
    # - "all-mpnet-base-v2" (better quality, slower)
    # - "paraphrase-multilingual-MiniLM-L12-v2" (multilingual)
    
    # LLM Settings (Ollama)
    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.2:3b"
    LLM_TEMPERATURE: float = 0.7
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
