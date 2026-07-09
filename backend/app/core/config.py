from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables.
    """
    PROJECT_NAME: str = "AI-First CRM – HCP Interaction Module"
    API_VERSION: str = "v1"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"

    # LLM Settings
    GROQ_API_KEY: str = ""
    DEFAULT_MODEL: str = "llama-3.3-70b-versatile"
    LANGGRAPH_ENABLED: bool = True
    MODEL_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 4096

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
