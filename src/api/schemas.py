"""Pydantic schemas for API."""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel
from src.models.image import ImageStatus


class ImageResponse(BaseModel):
    """Response model for image data."""
    id: str
    status: ImageStatus
    original_url: Optional[str] = None
    thumbnails: Dict[str, Optional[str]] = {}
    
    class Config:
        from_attributes = True


class ImageCreateResponse(BaseModel):
    """Response model for image creation."""
    id: str
    status: ImageStatus
    message: str
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    services: Dict[str, bool]
    timestamp: datetime
