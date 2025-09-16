"""Tests for services."""

import os
import pytest
import tempfile
from PIL import Image as PILImage
from src.services.image_processor import ImageProcessor
from src.config import settings


class TestImageProcessor:
    """Test image processing service."""
    
    def test_create_thumbnails_success(self, temp_storage: str):
        """Test successful thumbnail creation."""
        # Create a test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            img = PILImage.new('RGB', (1000, 1000), color=(255, 0, 0))
            img.save(temp_file, 'JPEG')
            temp_file.flush()
            
            image_id = "test-image-id"
            
            try:
                # Process image
                thumbnails = ImageProcessor.create_thumbnails(image_id, temp_file.name)
                
                # Check that all thumbnails were created
                assert "100x100" in thumbnails
                assert "300x300" in thumbnails
                assert "1200x1200" in thumbnails
                
                # Check that thumbnail files exist
                for size, path in thumbnails.items():
                    assert os.path.exists(path)
                    
                    # Check thumbnail dimensions
                    with PILImage.open(path) as thumb:
                        expected_size = tuple(map(int, size.split('x')))
                        assert thumb.size == expected_size
                        
            finally:
                # Cleanup
                os.unlink(temp_file.name)
                for path in thumbnails.values():
                    if os.path.exists(path):
                        os.unlink(path)
    
    def test_create_thumbnails_invalid_file(self, temp_storage: str):
        """Test thumbnail creation with invalid file."""
        with pytest.raises(Exception):
            ImageProcessor.create_thumbnails("test-id", "/nonexistent/file.jpg")
    
    def test_get_image_info_success(self):
        """Test getting image information."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            img = PILImage.new('RGB', (800, 600), color=(0, 255, 0))
            img.save(temp_file, 'JPEG')
            temp_file.flush()
            
            try:
                info = ImageProcessor.get_image_info(temp_file.name)
                
                assert info is not None
                assert info["width"] == 800
                assert info["height"] == 600
                assert info["format"] == "JPEG"
                assert info["mode"] == "RGB"
                
            finally:
                os.unlink(temp_file.name)
    
    def test_get_image_info_invalid_file(self):
        """Test getting info for invalid file."""
        info = ImageProcessor.get_image_info("/nonexistent/file.jpg")
        assert info is None


class TestImageService:
    """Test image service."""
    
    @pytest.mark.asyncio
    async def test_create_image_validates_extension(self, test_db, temp_storage):
        """Test that create_image validates file extensions."""
        from fastapi import UploadFile
        from io import BytesIO
        from src.services.image_service import ImageService
        from fastapi import HTTPException
        
        # Create invalid file
        invalid_file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"not an image"),
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await ImageService.create_image(test_db, invalid_file)
        
        assert exc_info.value.status_code == 400
        assert "File type .txt not allowed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_image_invalid_uuid(self, test_db):
        """Test get_image with invalid UUID."""
        from src.services.image_service import ImageService
        
        result = await ImageService.get_image(test_db, "invalid-uuid")
        assert result is None
