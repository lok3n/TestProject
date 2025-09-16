"""Image processing service for creating thumbnails."""

import os
from typing import Dict, Optional
from PIL import Image, ImageOps
from src.config import settings
from src.services.logger import get_logger

logger = get_logger(__name__)


class ImageProcessor:
    """Service for processing images and creating thumbnails."""
    
    @staticmethod
    def create_thumbnails(image_id: str, original_path: str) -> Dict[str, str]:
        """Create thumbnails for an image."""
        thumbnails = {}
        
        try:
            # Open original image
            with Image.open(original_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnails for each size
                for width, height in settings.THUMBNAIL_SIZES:
                    size_name = f"{width}x{height}"
                    
                    # Create thumbnail
                    thumbnail = img.copy()
                    
                    # Use ImageOps.fit to crop and resize maintaining aspect ratio
                    thumbnail = ImageOps.fit(
                        thumbnail, 
                        (width, height), 
                        Image.Resampling.LANCZOS
                    )
                    
                    # Generate thumbnail filename
                    thumbnail_filename = f"{image_id}_{size_name}.jpg"
                    thumbnail_path = os.path.join(
                        settings.STORAGE_PATH,
                        "thumbnails",
                        thumbnail_filename
                    )
                    
                    # Ensure thumbnails directory exists
                    os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
                    
                    # Save thumbnail with optimization
                    thumbnail.save(
                        thumbnail_path,
                        'JPEG',
                        quality=85,
                        optimize=True
                    )
                    
                    thumbnails[size_name] = thumbnail_path
                    logger.info(f"Created thumbnail {size_name} for image {image_id}")
                
                logger.info(f"Successfully created all thumbnails for image {image_id}")
                return thumbnails
                
        except Exception as e:
            logger.error(f"Failed to create thumbnails for image {image_id}: {e}")
            raise
    
    @staticmethod
    def get_image_info(image_path: str) -> Optional[Dict]:
        """Get image information."""
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode
                }
        except Exception as e:
            logger.error(f"Failed to get image info for {image_path}: {e}")
            return None
