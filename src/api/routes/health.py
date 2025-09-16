"""Health check routes."""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.api.dependencies import get_db
from src.api.schemas import HealthResponse
from src.services.rabbitmq_service import rabbitmq_service
from src.services.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check service health including database and RabbitMQ."""
    services = {
        "database": False,
        "rabbitmq": False
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        services["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check RabbitMQ
    try:
        services["rabbitmq"] = await rabbitmq_service.is_healthy()
    except Exception as e:
        logger.error(f"RabbitMQ health check failed: {e}")
    
    # Determine overall status
    overall_status = "healthy" if all(services.values()) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        services=services,
        timestamp=datetime.utcnow()
    )
