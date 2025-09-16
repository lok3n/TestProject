"""Configuration settings for the image processing service."""

import os
from typing import Optional


class Settings:
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@db:5432/images_db"
    )
    
    # RabbitMQ
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@rabbit:5672/"
    )
    QUEUE_NAME: str = "images"
    
    # Storage
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "/app/storage")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    
    # Image processing
    THUMBNAIL_SIZES: list[tuple[int, int]] = [(100, 100), (300, 300), (1200, 1200)]
    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    
    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "json"


settings = Settings()
