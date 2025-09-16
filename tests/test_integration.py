"""Integration tests."""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch
from src.worker.main import ImageWorker
from src.models.image import Image, ImageStatus
from src.services.image_service import ImageService


class TestWorkerIntegration:
    """Test worker integration."""
    
    @pytest.mark.asyncio
    async def test_worker_processes_message_success(
        self, 
        test_db, 
        temp_storage,
        sample_image_file
    ):
        """Test that worker successfully processes image."""
        
        # Create image record
        image = Image(
            status=ImageStatus.NEW,
            original_filename="test.jpg",
            original_path=sample_image_file,
            original_size=1000
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)
        
        # Create worker
        worker = ImageWorker()
        
        # Mock RabbitMQ message
        class MockMessage:
            def __init__(self, body: bytes):
                self.body = body
                self.processed = False
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                self.processed = True
                if exc_type:
                    # Simulate message rejection on error
                    pass
            
            def process(self):
                return self
        
        message_body = json.dumps({
            "image_id": str(image.id),
            "image_path": sample_image_file
        }).encode()
        
        mock_message = MockMessage(message_body)
        
        # Process message
        with patch('src.worker.main.AsyncSessionLocal', return_value=test_db):
            await worker.process_message(mock_message)
        
        # Check that message was processed
        assert mock_message.processed
        
        # Check that image status was updated
        await test_db.refresh(image)
        assert image.status == ImageStatus.DONE
        assert image.thumbnail_100_path is not None
        assert image.thumbnail_300_path is not None
        assert image.thumbnail_1200_path is not None
    
    @pytest.mark.asyncio
    async def test_worker_handles_processing_error(
        self, 
        test_db, 
        temp_storage
    ):
        """Test that worker handles processing errors gracefully."""
        
        # Create image record with non-existent file
        image = Image(
            status=ImageStatus.NEW,
            original_filename="test.jpg",
            original_path="/nonexistent/file.jpg",
            original_size=1000
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)
        
        worker = ImageWorker()
        
        # Mock RabbitMQ message
        class MockMessage:
            def __init__(self, body: bytes):
                self.body = body
                self.processed = False
                self.rejected = False
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                self.processed = True
                if exc_type:
                    self.rejected = True
            
            def process(self):
                return self
        
        message_body = json.dumps({
            "image_id": str(image.id),
            "image_path": "/nonexistent/file.jpg"
        }).encode()
        
        mock_message = MockMessage(message_body)
        
        # Process message (should fail)
        with patch('src.worker.main.AsyncSessionLocal', return_value=test_db):
            with pytest.raises(Exception):
                await worker.process_message(mock_message)
        
        # Check that message was processed and rejected
        assert mock_message.processed
        assert mock_message.rejected
        
        # Check that image status was updated to ERROR
        await test_db.refresh(image)
        assert image.status == ImageStatus.ERROR
        assert image.error_message is not None


class TestEndToEndFlow:
    """Test end-to-end application flow."""
    
    @pytest.mark.asyncio
    async def test_full_image_processing_flow(
        self,
        client,
        test_db,
        temp_storage,
        sample_image_file,
        mock_rabbitmq
    ):
        """Test complete flow from upload to processing completion."""
        
        # 1. Upload image
        with patch('src.services.image_service.rabbitmq_service', mock_rabbitmq):
            with open(sample_image_file, 'rb') as f:
                upload_response = await client.post(
                    "/images/",
                    files={"file": ("test.jpg", f, "image/jpeg")}
                )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        image_id = upload_data["id"]
        
        # 2. Check initial status
        status_response = await client.get(f"/images/{image_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == ImageStatus.PROCESSING
        
        # 3. Simulate worker processing
        await ImageService.update_image_status(
            test_db,
            image_id,
            ImageStatus.DONE,
            thumbnail_paths={
                "100x100": f"/app/storage/thumbnails/{image_id}_100x100.jpg",
                "300x300": f"/app/storage/thumbnails/{image_id}_300x300.jpg", 
                "1200x1200": f"/app/storage/thumbnails/{image_id}_1200x1200.jpg",
            }
        )
        
        # 4. Check final status
        final_response = await client.get(f"/images/{image_id}")
        assert final_response.status_code == 200
        final_data = final_response.json()
        assert final_data["status"] == ImageStatus.DONE
        assert len(final_data["thumbnails"]) == 3
        assert all(url for url in final_data["thumbnails"].values())
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, client, mock_rabbitmq):
        """Test health check with all services."""
        
        with patch('src.api.routes.health.rabbitmq_service', mock_rabbitmq):
            response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["services"]["database"] is True
        assert data["services"]["rabbitmq"] is True
        assert "timestamp" in data
