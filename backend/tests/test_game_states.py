"""Tests for game state endpoints."""
from typing import AsyncGenerator, Dict, List, TYPE_CHECKING
from uuid import UUID
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.database import get_db
from app.models import User, Character, GameState
from app.schemas import GameStateCreate, CharacterState
from app.auth import get_password_hash, create_access_token

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def test_character(db: AsyncSession, test_user: User) -> Character:
    """Create a test character."""
    character = Character(
        name="Test Character",
        description="A test character",
        user_id=test_user.id
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character

@pytest.fixture
async def test_game_state(db: AsyncSession, test_character: Character, test_user: User) -> GameState:
    """Create a test game state."""
    state_data = {
        "health": 100,
        "energy": 100,
        "happiness": 100,
        "hunger": 0,
        "fatigue": 0,
        "stress": 0,
        "last_interaction": None,
        "personality_traits": {},
        "skills": {},
        "inventory": [],
        "achievements": [],
        "relationships": {},
        "location": "home",
        "activity": None
    }
    game_state = GameState(
        character_id=test_character.id,
        user_id=test_user.id,
        state_data=state_data
    )
    db.add(game_state)
    await db.commit()
    await db.refresh(game_state)
    return game_state

async def test_create_game_state(
    authorized_client: AsyncClient,
    test_character: Character,
    test_user: User,
    db: AsyncSession
) -> None:
    """Test creating a new game state."""
    state_data = CharacterState(
        health=100,
        energy=100,
        happiness=100,
        hunger=0,
        fatigue=0,
        stress=0,
        last_interaction=None,
        personality_traits={},
        skills={},
        inventory=[],
        achievements=[],
        relationships={},
        location="home",
        activity=None
    )
    game_state = GameStateCreate(state_data=state_data)
    
    response = await authorized_client.post(
        f"/game-states/{test_character.id}",
        json=game_state.model_dump()
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["character_id"] == str(test_character.id)
    assert data["user_id"] == str(test_user.id)
    assert data["state_data"]["health"] == 100
    assert data["state_data"]["energy"] == 100

async def test_get_game_state(
    authorized_client: AsyncClient,
    test_game_state: GameState,
    test_user: User
) -> None:
    """Test getting a specific game state."""
    response = await authorized_client.get(
        f"/game-states/{test_game_state.id}"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_game_state.id)
    assert data["state_data"]["health"] == 100
    assert data["state_data"]["energy"] == 100

async def test_get_latest_game_state(
    authorized_client: AsyncClient,
    test_character: Character,
    test_game_state: GameState,
    test_user: User,
    db: AsyncSession
) -> None:
    """Test getting the latest game state."""
    # Create another game state with different values
    state_data = {
        "health": 90,
        "energy": 80,
        "happiness": 70,
        "hunger": 30,
        "fatigue": 20,
        "stress": 10,
        "last_interaction": None,
        "personality_traits": {},
        "skills": {},
        "inventory": [],
        "achievements": [],
        "relationships": {},
        "location": "home",
        "activity": None
    }
    new_game_state = GameState(
        character_id=test_character.id,
        user_id=test_user.id,
        state_data=state_data
    )
    db.add(new_game_state)
    await db.commit()
    
    response = await authorized_client.get(
        f"/game-states/character/{test_character.id}/latest"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["state_data"]["health"] == 90
    assert data["state_data"]["energy"] == 80

async def test_get_game_state_history(
    authorized_client: AsyncClient,
    test_character: Character,
    test_game_state: GameState,
    test_user: User,
    db: AsyncSession
) -> None:
    """Test getting game state history."""
    # Create multiple game states with decreasing energy values
    for energy in [90, 80, 70]:
        state_data = {
            "health": 100,
            "energy": energy,
            "happiness": 100,
            "hunger": 0,
            "fatigue": 0,
            "stress": 0,
            "last_interaction": None,
            "personality_traits": {},
            "skills": {},
            "inventory": [],
            "achievements": [],
            "relationships": {},
            "location": "home",
            "activity": None
        }
        game_state = GameState(
            character_id=test_character.id,
            user_id=test_user.id,
            state_data=state_data
        )
        db.add(game_state)
    await db.commit()
    
    response = await authorized_client.get(
        f"/game-states/character/{test_character.id}/history"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4  # Original state + 3 new states
    assert data[0]["state_data"]["energy"] == 70  # Most recent first
    assert data[1]["state_data"]["energy"] == 80
    assert data[2]["state_data"]["energy"] == 90
    assert data[3]["state_data"]["energy"] == 100  # Original state
    for state in data:
        assert state["character_id"] == str(test_character.id)

async def test_update_game_state(
    authorized_client: AsyncClient,
    test_game_state: GameState,
    test_user: User
) -> None:
    """Test updating a game state."""
    state_data = CharacterState(
        health=90,
        energy=80,
        happiness=70,
        hunger=30,
        fatigue=20,
        stress=10,
        last_interaction=None,
        personality_traits={},
        skills={},
        inventory=[],
        achievements=[],
        relationships={},
        location="home",
        activity=None
    )
    game_state = GameStateCreate(state_data=state_data)
    
    response = await authorized_client.put(
        f"/game-states/{test_game_state.id}",
        json=game_state.model_dump()
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_game_state.id)
    assert data["state_data"]["health"] == 90
    assert data["state_data"]["energy"] == 80
    assert data["state_data"]["happiness"] == 70

async def test_unauthorized_access(
    authorized_client: AsyncClient,
    test_character: Character,
    db: AsyncSession
) -> None:
    """Test unauthorized access to game states."""
    # Create another user with different token
    unauthorized_user = User(
        username="unauthorized",
        email="unauthorized@example.com",
        password_hash=get_password_hash("testpass123")
    )
    db.add(unauthorized_user)
    await db.commit()

    # Create a token for unauthorized user
    unauthorized_token = create_access_token(
        data={"sub": unauthorized_user.username},
        expires_delta=timedelta(minutes=30)
    )

    # Create an unauthorized client
    headers = {"Authorization": f"Bearer {unauthorized_token}"}
    
    # Try to access the character's game states
    response = await authorized_client.get(
        f"/game-states/character/{test_character.id}/latest",
        headers=headers
    )
    
    assert response.status_code == 403  # Not authorized
    assert response.json()["detail"] == "Not authorized to access this character"

async def test_invalid_game_state_updates(
    authorized_client: AsyncClient,
    test_game_state: GameState,
    test_user: User
) -> None:
    """Test invalid game state updates."""
    # Try to set negative health
    state_data = CharacterState(
        health=-10,  # Invalid value
        energy=80,
        happiness=70,
        hunger=30,
        fatigue=20,
        stress=10,
        last_interaction=None,
        personality_traits={},
        skills={},
        inventory=[],
        achievements=[],
        relationships={},
        location="home",
        activity=None
    )
    game_state = GameStateCreate(state_data=state_data)
    
    response = await authorized_client.put(
        f"/game-states/{test_game_state.id}",
        json=game_state.model_dump()
    )
    
    assert response.status_code == 422  # Validation error 