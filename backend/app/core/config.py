from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Newsletter Generator"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # MongoDB
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "https://newsletter-generator-fronten-git-f085ca-aruns-projects-d8be8db2.vercel.app", "https://newsletter-generator-frontend.vercel.app"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
