"""Test configuration and fixtures."""

import asyncio
import os
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.api.main import app
from src.api.dependencies import get_db
from src.database.connection import Base
from src.config import settings
from src.services.rabbitmq_service import RabbitMQService


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestAsyncSessionLocal() as session:
        yield session
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with test database."""
    
    async def get_test_db():
        yield test_db
    
    app.dependency_overrides[get_db] = get_test_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def temp_storage() -> Generator[str, None, None]:
    """Create temporary storage directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update settings for tests
        settings.STORAGE_PATH = temp_dir
        os.makedirs(os.path.join(temp_dir, "originals"), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, "thumbnails"), exist_ok=True)
        yield temp_dir


@pytest.fixture
def sample_image_file() -> Generator[str, None, None]:
    """Create a sample image file for testing."""
    from PIL import Image
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img.save(temp_file, 'JPEG')
        temp_file.flush()
        
        yield temp_file.name
        
        # Cleanup
        try:
            os.unlink(temp_file.name)
        except OSError:
            pass


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ service for tests."""
    class MockRabbitMQService:
        async def connect(self):
            pass
        
        async def disconnect(self):
            pass
        
        async def send_image_processing_task(self, image_id: str, image_path: str):
            pass
        
        async def is_healthy(self) -> bool:
            return True
    
    return MockRabbitMQService()
