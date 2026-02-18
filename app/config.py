from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql://mobashir@/senior_companion_db"
    
    # ChromaDB (RAG Memory)
    CHROMADB_PATH: str = "./chroma_data"
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5555
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Email (SMTP)
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    FROM_EMAIL: str
    
    # OTP
    OTP_EXPIRY_MINUTES: int = 10
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
