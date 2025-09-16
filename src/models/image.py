"""Image model for database."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from src.database.connection import Base


class ImageStatus(str, Enum):
    """Status of image processing."""
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"


class Image(Base):
    """Image model for storing image information."""
    
    __tablename__ = "images"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True
    )
    
    status = Column(
        String(20),
        nullable=False,
        default=ImageStatus.NEW
    )
    
    original_filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    original_size = Column(Integer, nullable=True)
    
    # Thumbnail paths (JSON would be better, but keeping it simple)
    thumbnail_100_path = Column(String(500), nullable=True)
    thumbnail_300_path = Column(String(500), nullable=True)
    thumbnail_1200_path = Column(String(500), nullable=True)
    
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
