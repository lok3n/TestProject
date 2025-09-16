"""Service for image operations."""

import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.image import Image, ImageStatus
from src.services.rabbitmq_service import rabbitmq_service
from src.config import settings
from src.services.logger import get_logger

logger = get_logger(__name__)


class ImageService:
    """Service for image operations."""
    
    @staticmethod
    async def create_image(
        db: AsyncSession,
        file: UploadFile
    ) -> Image:
        """Create new image record and save file."""
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"File type {file_ext} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Check file size
        file.file.seek(0, 2)  # Go to end of file
        file_size = file.file.tell()
        file.file.seek(0)  # Go back to beginning
        
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Generate unique filename
        image_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{image_id}{file_extension}"
        file_path = os.path.join(settings.STORAGE_PATH, "originals", filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.error(f"Failed to save file {filename}: {e}")
            raise HTTPException(status_code=500, detail="Failed to save file")
        
        # Create database record
        image = Image(
            id=uuid.UUID(image_id),
            status=ImageStatus.NEW,
            original_filename=file.filename,
            original_path=file_path,
            original_size=file_size
        )
        
        db.add(image)
        await db.commit()
        await db.refresh(image)
        
        # Send task to queue
        try:
            await rabbitmq_service.send_image_processing_task(image_id, file_path)
            
            # Update status to PROCESSING
            image.status = ImageStatus.PROCESSING
            await db.commit()
            await db.refresh(image)
            
        except Exception as e:
            logger.error(f"Failed to send processing task for image {image_id}: {e}")
            # Keep status as NEW so it can be retried later
        
        return image
    
    @staticmethod
    async def get_image(
        db: AsyncSession,
        image_id: str
    ) -> Optional[Image]:
        """Get image by ID."""
        try:
            uuid_obj = uuid.UUID(image_id)
        except ValueError:
            return None
        
        result = await db.execute(
            select(Image).where(Image.id == uuid_obj)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_image_status(
        db: AsyncSession,
        image_id: str,
        status: ImageStatus,
        thumbnail_paths: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> Optional[Image]:
        """Update image status and thumbnail paths."""
        try:
            uuid_obj = uuid.UUID(image_id)
        except ValueError:
            return None
        
        result = await db.execute(
            select(Image).where(Image.id == uuid_obj)
        )
        image = result.scalar_one_or_none()
        
        if not image:
            return None
        
        image.status = status
        
        if error_message:
            image.error_message = error_message
        
        if thumbnail_paths:
            image.thumbnail_100_path = thumbnail_paths.get("100x100")
            image.thumbnail_300_path = thumbnail_paths.get("300x300")
            image.thumbnail_1200_path = thumbnail_paths.get("1200x1200")
        
        await db.commit()
        await db.refresh(image)
        
        return image
