import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List

# Force reload of .env file
load_dotenv(override=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ===========================================
    # DeepSeek API Configuration
    # ===========================================
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # ===========================================
    # OpenAI API Configuration
    # ===========================================
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-5.1"           # Primary (High Intelligence)
    OPENAI_MINI_MODEL: str = "gpt-5-mini"   # Secondary (Fast/Mini)
    
    # ===========================================
    # Translation Settings
    # ===========================================
    DEFAULT_SOURCE_LANGUAGE: str = "zh"
    DEFAULT_TARGET_LANGUAGE: str = "en"
    SUPPORTED_TARGET_LANGUAGES: List[str] = ["uz", "ru", "en"]
    
    # ===========================================
    # API Performance Settings
    # ===========================================
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.2
    
    # ===========================================
    # Summarization Settings
    # ===========================================
    ENABLE_SUMMARIZATION: bool = True
    SUMMARIZE_THRESHOLD: int = 500
    
    # ===========================================
    # Cache Settings
    # ===========================================
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 3600
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Create settings instance - this will read from .env
settings = Settings()

# Debug: Print loaded keys (masked)
def _mask_key(key: str) -> str:
    if len(key) > 10:
        return f"{key[:8]}...{key[-4:]}"
    return "NOT SET" if not key else key

print(f"[Config] DeepSeek Key: {_mask_key(settings.DEEPSEEK_API_KEY)}")
print(f"[Config] OpenAI Key: {_mask_key(settings.OPENAI_API_KEY)}")
