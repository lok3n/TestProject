"""Tests for API endpoints."""

import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.image import Image, ImageStatus
from unittest.mock import patch


class TestImagesAPI:
    """Test image API endpoints."""
    
    @pytest.mark.asyncio
    async def test_upload_image_success(
        self, 
        client: AsyncClient, 
        temp_storage: str,
        sample_image_file: str,
        mock_rabbitmq
    ):
        """Test successful image upload."""
        with patch('src.services.image_service.rabbitmq_service', mock_rabbitmq):
            with open(sample_image_file, 'rb') as f:
                response = await client.post(
                    "/images/",
                    files={"file": ("test.jpg", f, "image/jpeg")}
                )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == ImageStatus.PROCESSING
        assert data["message"] == "Image uploaded successfully and queued for processing"
    
    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client: AsyncClient):
        """Test upload with invalid file type."""
        response = await client.post(
            "/images/",
            files={"file": ("test.txt", b"not an image", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "File type .txt not allowed" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_no_file(self, client: AsyncClient):
        """Test upload without file."""
        response = await client.post("/images/")
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_get_image_success(
        self, 
        client: AsyncClient, 
        test_db: AsyncSession
    ):
        """Test successful image retrieval."""
        # Create test image record
        image = Image(
            status=ImageStatus.DONE,
            original_filename="test.jpg",
            original_path="/path/to/test.jpg",
            original_size=1000,
            thumbnail_100_path="/path/to/thumb_100.jpg",
            thumbnail_300_path="/path/to/thumb_300.jpg",
            thumbnail_1200_path="/path/to/thumb_1200.jpg"
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)
        
        response = await client.get(f"/images/{image.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(image.id)
        assert data["status"] == ImageStatus.DONE
        assert "thumbnails" in data
        assert "100x100" in data["thumbnails"]
        assert "300x300" in data["thumbnails"]
        assert "1200x1200" in data["thumbnails"]
    
    @pytest.mark.asyncio
    async def test_get_image_not_found(self, client: AsyncClient):
        """Test get non-existent image."""
        response = await client.get("/images/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert response.json()["detail"] == "Image not found"
    
    @pytest.mark.asyncio
    async def test_get_image_invalid_uuid(self, client: AsyncClient):
        """Test get image with invalid UUID."""
        response = await client.get("/images/invalid-uuid")
        assert response.status_code == 404
        assert response.json()["detail"] == "Image not found"


class TestHealthAPI:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client: AsyncClient, mock_rabbitmq):
        """Test successful health check."""
        with patch('src.api.routes.health.rabbitmq_service', mock_rabbitmq):
            response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert data["services"]["database"] is True
        assert data["services"]["rabbitmq"] is True
        assert "timestamp" in data


class TestRootAPI:
    """Test root endpoint."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"
