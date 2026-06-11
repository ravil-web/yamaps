"""
Application configuration settings
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "EnglishKids Academy"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kids_english"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password hashing
    PASSWORD_HASH_ALGORITHM: str = "argon2"
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 4
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5
    RATE_LIMIT_LOCKOUT_MINUTES: int = 15
    RATE_LIMIT_API_PER_MINUTE: int = 60
    
    # Session
    SESSION_MAX_AGE_MINUTES: int = 30
    SESSION_INACTIVITY_TIMEOUT_MINUTES: int = 15
    
    # File storage
    MEDIA_STORAGE_TYPE: str = "local"  # local or s3
    MEDIA_UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_AUDIO_TYPES: List[str] = ["audio/mpeg", "audio/wav", "audio/ogg"]
    
    # AWS S3 (if using S3 storage)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "kids-english-app"
    
    # Email (for parent notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@englishkids.academy"
    
    # TTS (Text-to-Speech)
    TTS_PROVIDER: str = "gtts"  # gtts, google_cloud, aws_polly
    TTS_LANGUAGE: str = "en"
    TTS_SLOW: bool = False
    
    # Gamification
    XP_PER_LESSON: int = 100
    XP_PER_GAME: int = 50
    XP_PER_WORD_LEARNED: int = 10
    STREAK_BONUS_MULTIPLIER: float = 1.5
    DAILY_GOAL_XP_BONUS: int = 50
    
    # Spaced Repetition (SM-2 Algorithm)
    SM2_MIN_EASE_FACTOR: float = 1.3
    SM2_DEFAULT_EASE_FACTOR: float = 2.5
    SM2_EASY_BONUS: float = 1.3
    SM2_INTERVAL_MODIFIER: float = 1.0
    
    # Parent Dashboard
    WEEKLY_REPORT_DAY: int = 0  # Monday
    WEEKLY_REPORT_HOUR: int = 9
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
