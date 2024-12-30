"""Tests for interactions functionality."""
from datetime import datetime, timedelta
import pytest
from typing import TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

from app import crud, schemas
from app.models import Interaction, Character, User
from app.schemas import InteractionCreate
from app.state_management import StateManager

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from pytest_mock import MockerFixture

@pytest.fixture(autouse=True)
async def cleanup_db(db: AsyncSession):
    """Clean up database before and after each test."""
    # Clean up before test
    await db.execute(delete(Interaction))
    await db.execute(delete(Character))
    await db.execute(delete(User))
    await db.commit()
    
    yield
    
    # Clean up after test
    await db.execute(delete(Interaction))
    await db.execute(delete(Character))
    await db.execute(delete(User))
    await db.commit()

@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    """Create a test user."""
    user_data = schemas.UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpass123"
    )
    return await crud.create_user(db, user_data)

@pytest.fixture
async def test_character(db: AsyncSession, test_user: User) -> Character:
    """Create a test character."""
    character_data = schemas.CharacterCreate(
        name="Test Character",
        description="A test character"
    )
    return await crud.create_character(db, character=character_data, user_id=test_user.id)

@pytest.fixture
def interaction_create(test_character: Character) -> InteractionCreate:
    """Create an interaction creation schema for testing."""
    return InteractionCreate(
        character_id=test_character.id,
        interaction_type="chat",
        content="Hello, how are you?",
        sentiment_score=0.8,
        context={"location": "home", "time_of_day": "morning"},
        effects={"happiness": 5, "energy": -2}
    )

async def test_create_interaction(db: AsyncSession, interaction_create: InteractionCreate, test_user: User):
    """Test creating a new interaction."""
    interaction = await crud.create_interaction(db, interaction_create, test_user.id)
    assert interaction.character_id == interaction_create.character_id
    assert interaction.interaction_type == interaction_create.interaction_type
    assert interaction.content == interaction_create.content
    assert interaction.sentiment_score == interaction_create.sentiment_score
    assert interaction.context == interaction_create.context
    assert interaction.effects == interaction_create.effects

async def test_get_interactions_by_character(db: AsyncSession, interaction_create: InteractionCreate, test_user: User):
    """Test retrieving all interactions for a character."""
    # Create multiple interactions
    interaction1 = await crud.create_interaction(db, interaction_create, test_user.id)
    interaction2 = await crud.create_interaction(db, interaction_create, test_user.id)

    interactions = await crud.get_interactions_by_character(db, interaction_create.character_id)
    assert len(interactions) == 2
    assert all(i.character_id == interaction_create.character_id for i in interactions)

async def test_interaction_history(db: AsyncSession, interaction_create: InteractionCreate, test_user: User):
    """Test interaction history functionality."""
    # Create multiple interactions with timestamps
    for i in range(3):
        interaction = await crud.create_interaction(db, interaction_create, test_user.id)
        stmt = update(Interaction).where(Interaction.id == interaction.id).values(timestamp=datetime.utcnow())
        await db.execute(stmt)
        await db.commit()

    # Get interactions sorted by timestamp
    stmt = select(Interaction).where(
        Interaction.character_id == interaction_create.character_id
    ).order_by(Interaction.timestamp.desc()).offset(0).limit(10)
    
    result = await db.execute(stmt)
    interactions = result.scalars().all()

    assert len(interactions) == 3
    # Verify timestamps are in descending order
    for i in range(len(interactions) - 1):
        assert interactions[i].timestamp >= interactions[i + 1].timestamp

async def test_interaction_effects(db: AsyncSession, test_character: Character):
    """Test interaction effects on character state."""
    state_manager = StateManager()
    
    # Initial state
    initial_state = schemas.CharacterState(
        health=100,
        energy=80,
        happiness=70,
        hunger=60,
        fatigue=40,
        stress=30,
        last_interaction=datetime.utcnow(),
        personality_traits={},
        skills={},
        inventory=[],
        achievements=[],
        relationships={},
        location="home",
        activity=None
    )
    
    # Test feed interaction
    updated_state = state_manager.apply_interaction_effects(initial_state, "feed")
    assert updated_state.hunger == max(0, initial_state.hunger - 30)
    assert updated_state.happiness == initial_state.happiness + 5
    
    # Test rest interaction
    updated_state = state_manager.apply_interaction_effects(initial_state, "rest")
    assert updated_state.energy == min(100, initial_state.energy + 20)
    assert updated_state.fatigue == max(0, initial_state.fatigue - 15)

async def test_unauthorized_interaction(db: AsyncSession, test_character: Character, test_user: User):
    """Test unauthorized interaction attempts."""
    # Create another user and character
    other_user = await crud.create_user(db, schemas.UserCreate(
        email="other@example.com",
        username="otheruser",
        password="otherpass123"
    ))
    other_character = await crud.create_character(db, schemas.CharacterCreate(
        name="Other Character",
        description="Another test character"
    ), user_id=other_user.id)
    
    # Try to create interaction for other character
    interaction_data = InteractionCreate(
        character_id=other_character.id,
        interaction_type="chat",
        content="Unauthorized interaction",
        sentiment_score=0.8,
        context={"location": "home", "time_of_day": "morning"},
        effects={"happiness": 5, "energy": -2}
    )
    
    with pytest.raises(Exception):  # Should raise appropriate exception
        await crud.create_interaction(db, interaction_data, test_user.id)

async def test_invalid_interaction_type(db: AsyncSession, test_character: Character):
    """Test handling of invalid interaction types."""
    state_manager = StateManager()
    initial_state = schemas.CharacterState(
        health=100,
        energy=80,
        happiness=70,
        hunger=60,
        fatigue=40,
        stress=30,
        last_interaction=datetime.utcnow(),
        personality_traits={},
        skills={},
        inventory=[],
        achievements=[],
        relationships={},
        location="home",
        activity=None
    )
    
    # Try invalid interaction type
    updated_state = state_manager.apply_interaction_effects(initial_state, "invalid_type")
    # State should remain unchanged for invalid interaction type
    assert updated_state.health == initial_state.health
    assert updated_state.energy == initial_state.energy
    assert updated_state.happiness == initial_state.happiness 