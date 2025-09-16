"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.api.routes import images, health
from src.services.rabbitmq_service import rabbitmq_service
from src.services.logger import setup_logging, get_logger
from src.config import settings
import os

# Configure logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events."""
    # Startup
    logger.info("Starting image processing API")
    
    # Ensure storage directories exist
    os.makedirs(os.path.join(settings.STORAGE_PATH, "originals"), exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_PATH, "thumbnails"), exist_ok=True)
    
    # Connect to RabbitMQ
    try:
        await rabbitmq_service.connect()
        logger.info("Connected to RabbitMQ")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down image processing API")
    await rabbitmq_service.disconnect()


# Create FastAPI application
app = FastAPI(
    title="Image Processing Service",
    description="Async image processing service with thumbnails generation",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(health.router)
app.include_router(images.router)

# Mount static files if storage directory exists
if os.path.exists(settings.STORAGE_PATH):
    app.mount("/static", StaticFiles(directory=settings.STORAGE_PATH), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Image Processing Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
