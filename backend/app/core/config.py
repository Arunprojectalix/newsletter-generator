from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Newsletter Generator"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # MongoDB (optional for AI chat functionality)
    MONGODB_URL: Optional[str] = "mongodb://localhost:27017"
    MONGODB_DB_NAME: Optional[str] = "newsletter_generator"
    
    # OpenAI (optional, will be checked when needed)
    OPENAI_API_KEY: Optional[str] = None
    
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:8080"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
