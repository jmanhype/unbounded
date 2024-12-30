"""Database CRUD operations."""
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy import select, update, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from . import models, schemas
from uuid import UUID
import json
from .auth import get_password_hash
from datetime import datetime

logger = logging.getLogger(__name__)

async def get_user(db: AsyncSession, user_id: str) -> Optional[models.User]:
    """Get a user by ID."""
    try:
        result = await db.execute(select(models.User).filter(models.User.id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error looking up user: {e}")
        return None

async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    """Get a user by username."""
    try:
        result = await db.execute(select(models.User).filter(models.User.username == username))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error looking up user by username: {e}")
        return None

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    """Get a user by email."""
    try:
        result = await db.execute(select(models.User).filter(models.User.email == email))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error looking up user by email: {e}")
        return None

async def create_user(db: AsyncSession, user: schemas.UserCreate) -> Optional[models.User]:
    """Create a new user."""
    try:
        user_data = user.model_dump()
        password = user_data.pop('password')  # Remove password from dict
        user_data['password_hash'] = get_password_hash(password)  # Add hashed password
        db_user = models.User(**user_data)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await db.rollback()
        return None

async def get_character(db: AsyncSession, character_id: UUID) -> Optional[models.Character]:
    """Get a character by ID."""
    try:
        result = await db.execute(
            select(models.Character).filter(models.Character.id == str(character_id))
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error looking up character: {e}")
        return None

async def get_characters(db: AsyncSession, user_id: str) -> List[models.Character]:
    """Get all characters for a user."""
    try:
        result = await db.execute(
            select(models.Character).filter(models.Character.user_id == user_id)
        )
        return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error looking up characters: {e}")
        return []

async def create_character(db: AsyncSession, character: schemas.CharacterCreate, user_id: str) -> Optional[models.Character]:
    """Create a new character."""
    try:
        db_character = models.Character(**character.model_dump(), user_id=user_id)
        db.add(db_character)
        await db.commit()
        await db.refresh(db_character)
        return db_character
    except Exception as e:
        logger.error(f"Error creating character: {e}")
        await db.rollback()
        return None

async def update_character(db: AsyncSession, character_id: UUID, character: schemas.CharacterUpdate) -> Optional[models.Character]:
    """Update a character."""
    try:
        stmt = (
            update(models.Character)
            .where(models.Character.id == str(character_id))
            .values(**character.model_dump(exclude_unset=True))
        )
        await db.execute(stmt)
        await db.commit()
        
        # Fetch and return the updated character
        result = await db.execute(
            select(models.Character).filter(models.Character.id == str(character_id))
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error updating character: {e}")
        await db.rollback()
        return None

async def create_game_state(
    db: AsyncSession,
    character_id: UUID,
    user_id: UUID,
    game_state: schemas.GameStateCreate
) -> Optional[models.GameState]:
    """Create a new game state."""
    try:
        db_game_state = models.GameState(
            character_id=str(character_id),
            user_id=str(user_id),
            health=game_state.health,
            energy=game_state.energy,
            happiness=game_state.happiness,
            hunger=game_state.hunger,
            fatigue=game_state.fatigue,
            stress=game_state.stress,
            location=game_state.location,
            activity=game_state.activity,
            timestamp=datetime.utcnow()
        )
        db.add(db_game_state)
        await db.commit()
        await db.refresh(db_game_state)
        return db_game_state
    except Exception as e:
        logger.error(f"Error creating game state: {e}")
        await db.rollback()
        return None

async def get_game_state(db: AsyncSession, game_state_id: UUID) -> Optional[models.GameState]:
    """Get a game state by ID."""
    try:
        result = await db.execute(
            select(models.GameState).filter(models.GameState.id == str(game_state_id))
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error looking up game state: {e}")
        return None

async def get_latest_game_state(
    db: AsyncSession,
    character_id: UUID
) -> Optional[models.GameState]:
    """Get the latest game state for a character."""
    try:
        result = await db.execute(
            select(models.GameState)
            .filter(models.GameState.character_id == str(character_id))
            .order_by(models.GameState.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting latest game state: {e}")
        return None

async def get_game_state_history(
    db: AsyncSession,
    character_id: UUID,
    limit: int = 10
) -> List[models.GameState]:
    """Get game state history for a character."""
    try:
        result = await db.execute(
            select(models.GameState)
            .filter(models.GameState.character_id == str(character_id))
            .order_by(models.GameState.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error looking up game state history: {e}")
        return []

async def update_game_state(
    db: AsyncSession,
    game_state_id: UUID,
    game_state: schemas.GameStateCreate
) -> Optional[models.GameState]:
    """Update a game state."""
    try:
        db_game_state = await db.get(models.GameState, str(game_state_id))
        if not db_game_state:
            return None
            
        # Update fields
        db_game_state.health = game_state.health
        db_game_state.energy = game_state.energy
        db_game_state.happiness = game_state.happiness
        db_game_state.hunger = game_state.hunger
        db_game_state.fatigue = game_state.fatigue
        db_game_state.stress = game_state.stress
        db_game_state.location = game_state.location
        db_game_state.activity = game_state.activity
        db_game_state.timestamp = datetime.utcnow()
        
        await db.commit()
        await db.refresh(db_game_state)
        return db_game_state
    except Exception as e:
        logger.error(f"Error updating game state: {e}")
        await db.rollback()
        return None

async def create_interaction(
    db: AsyncSession,
    character_id: UUID,
    interaction_type: str,
    content: str,
    sentiment_score: float,
    context: Dict[str, Any],
    effects: Dict[str, Any],
    response: Dict[str, Any]
) -> Optional[models.Interaction]:
    """Create a new interaction record."""
    try:
        # Convert any datetime objects in the response to ISO format strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        response = convert_datetime(response)
        context = convert_datetime(context)
        effects = convert_datetime(effects)
        
        db_interaction = models.Interaction(
            character_id=character_id,
            interaction_type=interaction_type,
            content=content,
            sentiment_score=sentiment_score,
            context=context,
            effects=effects,
            response=response,
            timestamp=datetime.utcnow()
        )
        db.add(db_interaction)
        await db.commit()
        await db.refresh(db_interaction)
        return db_interaction
    except Exception as e:
        logger.error(f"Error creating interaction: {e}")
        await db.rollback()
        return None

async def get_character_interactions(
    db: AsyncSession,
    character_id: UUID,
    limit: int = 50
) -> List[models.Interaction]:
    """Get interactions for a character."""
    try:
        result = await db.execute(
            select(models.Interaction)
            .filter(models.Interaction.character_id == str(character_id))
            .order_by(models.Interaction.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error looking up character interactions: {e}")
        return []

async def create_character_backstory(
    db: AsyncSession,
    character_id: str,
    content: str,
    tone: str,
    themes: List[str],
    word_count: int
) -> Optional[models.CharacterBackstory]:
    """Create a character backstory."""
    try:
        db_backstory = models.CharacterBackstory(
            character_id=character_id,
            content=content,
            tone=tone,
            themes=themes,
            word_count=word_count
        )
        db.add(db_backstory)
        await db.commit()
        await db.refresh(db_backstory)
        return db_backstory
    except Exception as e:
        logger.error(f"Error creating character backstory: {e}")
        await db.rollback()
        return None

async def get_character_backstory(
    db: AsyncSession,
    character_id: str
) -> Optional[models.CharacterBackstory]:
    """Get the most recent backstory for a character."""
    try:
        result = await db.execute(
            select(models.CharacterBackstory)
            .filter(models.CharacterBackstory.character_id == character_id)
            .order_by(models.CharacterBackstory.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting character backstory: {e}")
        return None

async def get_character_backstories(
    db: AsyncSession,
    character_id: str,
    skip: int = 0,
    limit: int = 10
) -> List[models.CharacterBackstory]:
    """Get all backstories for a character."""
    try:
        result = await db.execute(
            select(models.CharacterBackstory)
            .filter(models.CharacterBackstory.character_id == character_id)
            .order_by(models.CharacterBackstory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error getting character backstories: {e}")
        return []

async def delete_character(db: AsyncSession, character_id: UUID) -> None:
    """Delete a character and all associated data."""
    # Delete associated game states
    await db.execute(
        delete(models.GameState).where(models.GameState.character_id == character_id)
    )
    
    # Delete associated backstories
    await db.execute(
        delete(models.CharacterBackstory).where(models.CharacterBackstory.character_id == character_id)
    )
    
    # Delete the character
    await db.execute(
        delete(models.Character).where(models.Character.id == character_id)
    )
    
    await db.commit()
