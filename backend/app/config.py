"""Configuration settings for the application."""
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/unbounded_db"
    SECRET_KEY: str = "your_secret_key_here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OLLAMA_API_URL: str = "http://localhost:11434"
    MODEL_NAME: str = "llama2"
    REPLICATE_API_KEY: str = ""
    STABILITY_API_KEY: str = ""
    BFL_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ENVIRONMENT: str = "development"
    DEEPSEEK_API_KEY: str = ""
    AIDER_OPENAI_API_BASE: str = "https://api.deepseek.com"
    JWT_SECRET_KEY: str = ""

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

settings = get_settings() 