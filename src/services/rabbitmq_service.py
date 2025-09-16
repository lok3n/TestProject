"""RabbitMQ service for queue operations."""

import json
from typing import Optional
import aio_pika
from aio_pika.abc import AbstractRobustConnection
from src.config import settings
from src.services.logger import get_logger

logger = get_logger(__name__)


class RabbitMQService:
    """Service for RabbitMQ operations."""
    
    def __init__(self):
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel = None
        self.queue = None
    
    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL
            )
            self.channel = await self.connection.channel()
            
            # Declare queue
            self.queue = await self.channel.declare_queue(
                settings.QUEUE_NAME,
                durable=True
            )
            
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")
    
    async def send_image_processing_task(self, image_id: str, image_path: str) -> None:
        """Send image processing task to queue."""
        if not self.channel:
            await self.connect()
        
        message = {
            "image_id": image_id,
            "image_path": image_path
        }
        
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=settings.QUEUE_NAME
            )
            logger.info(f"Sent processing task for image {image_id}")
        except Exception as e:
            logger.error(f"Failed to send task for image {image_id}: {e}")
            raise
    
    async def is_healthy(self) -> bool:
        """Check if RabbitMQ connection is healthy."""
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
            return not self.connection.is_closed
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return False


# Global RabbitMQ service instance
rabbitmq_service = RabbitMQService()
