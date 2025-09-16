"""RabbitMQ worker for processing images."""

import asyncio
import json
from typing import Dict
import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.database.connection import AsyncSessionLocal
from src.models.image import ImageStatus
from src.services.image_service import ImageService
from src.services.image_processor import ImageProcessor
from src.services.logger import setup_logging, get_logger

# Configure logging
setup_logging()
logger = get_logger(__name__)


class ImageWorker:
    """Worker for processing images from RabbitMQ queue."""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
    
    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL
            )
            self.channel = await self.connection.channel()
            
            # Set QoS to process one message at a time
            await self.channel.set_qos(prefetch_count=1)
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.QUEUE_NAME,
                durable=True
            )
            
            logger.info("Worker connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("Worker disconnected from RabbitMQ")
    
    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """Process a single image processing message."""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                image_id = body["image_id"]
                image_path = body["image_path"]
                
                logger.info(f"Processing image {image_id}")
                
                # Get database session
                async with AsyncSessionLocal() as db:
                    # Update status to PROCESSING
                    await ImageService.update_image_status(
                        db, image_id, ImageStatus.PROCESSING
                    )
                    
                    try:
                        # Process image - create thumbnails
                        thumbnail_paths = ImageProcessor.create_thumbnails(
                            image_id, image_path
                        )
                        
                        # Update database with success
                        await ImageService.update_image_status(
                            db, 
                            image_id, 
                            ImageStatus.DONE,
                            thumbnail_paths=thumbnail_paths
                        )
                        
                        logger.info(f"Successfully processed image {image_id}")
                        
                    except Exception as e:
                        # Update database with error
                        error_message = f"Processing failed: {str(e)}"
                        await ImageService.update_image_status(
                            db,
                            image_id,
                            ImageStatus.ERROR,
                            error_message=error_message
                        )
                        
                        logger.error(f"Failed to process image {image_id}: {e}")
                        raise
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Message will be rejected and not requeued due to message.process()
                raise
    
    async def start_consuming(self) -> None:
        """Start consuming messages from the queue."""
        if not self.queue:
            await self.connect()
        
        logger.info("Starting to consume messages...")
        
        # Start consuming messages
        await self.queue.consume(self.process_message)
        
        try:
            # Keep the worker running
            await asyncio.Future()  # run forever
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.disconnect()


async def main():
    """Main worker function."""
    logger.info("Starting image processing worker")
    
    worker = ImageWorker()
    
    try:
        await worker.start_consuming()
    except Exception as e:
        logger.error(f"Worker error: {e}")
    finally:
        await worker.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
