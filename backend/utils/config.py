import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Налаштування додатку"""
    
    # API settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:3000,http://localhost:8000"
    ).split(",")
    
    # n8n integration
    N8N_WEBHOOK_URL: str = os.getenv(
        "N8N_WEBHOOK_URL", 
        "http://localhost:5678/webhook/vitamin-assistant"
    )
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")
    
    # Database (for future use)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./vitamin_assistant.db")
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", 30))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", 60))  # seconds
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "app.log")
    
    # AI settings
    DEFAULT_CONFIDENCE: float = float(os.getenv("DEFAULT_CONFIDENCE", 0.85))
    MAX_HISTORY_MESSAGES: int = int(os.getenv("MAX_HISTORY_MESSAGES", 20))

def get_settings() -> Settings:
    """Фабрика для отримання налаштувань"""
    return Settings()

# Глобальний екземпляр налаштувань
settings = get_settings()