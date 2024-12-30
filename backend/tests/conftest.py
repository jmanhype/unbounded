"""Test configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import timedelta
import uuid
from datetime import datetime

from app.database import Base, get_db
from app.main import app
from app.auth import get_password_hash, create_access_token
from app.models import User, Character

# Use in-memory SQLite for tests
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    # Generate unique identifiers for both email and username
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"test_{unique_id}@example.com",
        "username": f"testuser_{unique_id}",
        "password_hash": get_password_hash("testpass123"),
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create a valid JWT token for the test user."""
    access_token = create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=30)
    )
    return access_token

@pytest.fixture
async def authorized_client(
    db: AsyncSession,
    auth_token: str
) -> AsyncGenerator[AsyncClient, None]:
    """Get a test client with authorization headers."""
    async def _get_test_db():
        yield db
    
    app.dependency_overrides[get_db] = _get_test_db
    
    async with AsyncClient(
        app=app,
        base_url="http://test",
        headers={"Authorization": f"Bearer {auth_token}"}
    ) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def test_character(db: AsyncSession, test_user: User) -> Character:
    """Create a test character."""
    character_data = {
        "name": "Test Character",
        "description": "A test character",
        "user_id": test_user.id,
        "personality_traits": {},
        "created_at": datetime.utcnow()
    }
    character = Character(**character_data)
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character
