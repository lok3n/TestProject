"""Image routes for FastAPI."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_db
from src.api.schemas import ImageResponse, ImageCreateResponse
from src.services.image_service import ImageService
from src.models.image import ImageStatus
from src.services.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/", response_model=ImageCreateResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process image."""
    try:
        image = await ImageService.create_image(db, file)
        
        return ImageCreateResponse(
            id=str(image.id),
            status=image.status,
            message="Image uploaded successfully and queued for processing"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading image: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get image information by ID."""
    image = await ImageService.get_image(db, image_id)
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Build thumbnail URLs
    thumbnails = {}
    if image.thumbnail_100_path:
        thumbnails["100x100"] = f"/static/thumbnails/{image_id}_100x100.jpg"
    if image.thumbnail_300_path:
        thumbnails["300x300"] = f"/static/thumbnails/{image_id}_300x300.jpg"
    if image.thumbnail_1200_path:
        thumbnails["1200x1200"] = f"/static/thumbnails/{image_id}_1200x1200.jpg"
    
    return ImageResponse(
        id=str(image.id),
        status=image.status,
        original_url=f"/static/originals/{image.original_filename}" if image.status == ImageStatus.DONE else None,
        thumbnails=thumbnails
    )
