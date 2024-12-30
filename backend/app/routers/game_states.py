"""Router for game state operations."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from .. import crud, schemas
from ..auth import get_current_user
from ..models import User

router = APIRouter(
    tags=["game-states"],
    responses={404: {"description": "Not found"}},
)

@router.post("/{character_id}", response_model=schemas.GameState)
async def create_game_state(
    character_id: UUID,
    game_state: schemas.GameStateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new game state for a character."""
    character = await crud.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this character")
    
    return await crud.create_game_state(db=db, character_id=character_id, user_id=current_user.id, game_state=game_state)

@router.get("/{game_state_id}", response_model=schemas.GameState)
async def get_game_state(
    game_state_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific game state."""
    game_state = await crud.get_game_state(db, game_state_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game state not found")
    if game_state.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this game state")
    return game_state

@router.get("/character/{character_id}/latest", response_model=schemas.GameState)
async def get_latest_game_state(
    character_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest game state for a character."""
    character = await crud.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this character")
    
    game_state = await crud.get_latest_game_state(db, character_id)
    if not game_state:
        raise HTTPException(status_code=404, detail="No game state found for this character")
    return game_state

@router.get("/character/{character_id}/history", response_model=List[schemas.GameState])
async def get_game_state_history(
    character_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the game state history for a character."""
    character = await crud.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this character")
    
    return await crud.get_game_state_history(db, character_id)

@router.put("/characters/{character_id}/state", response_model=schemas.GameState)
async def update_game_state(
    character_id: UUID,
    game_state: schemas.GameStateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update or create a game state for a character."""
    # Verify character exists and belongs to user
    character = await crud.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this character")
    
    # Get existing game state or create new one
    existing_state = await crud.get_latest_game_state(db, character_id)
    if existing_state:
        return await crud.update_game_state(db=db, game_state_id=existing_state.id, game_state=game_state)
    else:
        return await crud.create_game_state(db=db, character_id=character_id, user_id=current_user.id, game_state=game_state) 