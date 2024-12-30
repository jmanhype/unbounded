"""Characters router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(
    tags=["characters"],
    responses={404: {"description": "not found"}},
)

@router.post("/", response_model=schemas.Character)
async def create_character(
    character: schemas.CharacterCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> models.Character:
    """Create a new character.
    
    Args:
        character: Character creation data.
        current_user: The authenticated user making the request.
        db: Database session.
        
    Returns:
        The created character.
    """
    return await crud.create_character(db=db, character=character, user_id=current_user.id)

@router.get("/", response_model=List[schemas.Character])
async def list_characters(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[models.Character]:
    """List all characters belonging to the current user.
    
    Args:
        current_user: The authenticated user making the request.
        db: Database session.
        
    Returns:
        List of characters.
    """
    return await crud.get_characters(db, user_id=current_user.id)

@router.get("/{character_id}", response_model=schemas.Character)
async def get_character(
    character_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> models.Character:
    """Get a specific character.
    
    Args:
        character_id: ID of the character to retrieve.
        current_user: The authenticated user making the request.
        db: Database session.
        
    Returns:
        The requested character.
        
    Raises:
        HTTPException: If character not found or doesn't belong to user.
    """
    character = await crud.get_character(db, character_id=character_id)
    if not character or character.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Character not found")
    return character

@router.put("/{character_id}", response_model=schemas.Character)
async def update_character(
    character_id: str,
    character: schemas.CharacterCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> models.Character:
    """Update a character.
    
    Args:
        character_id: ID of the character to update.
        character: Updated character data.
        current_user: The authenticated user making the request.
        db: Database session.
        
    Returns:
        The updated character.
        
    Raises:
        HTTPException: If character not found or doesn't belong to user.
    """
    db_character = await crud.get_character(db, character_id=character_id)
    if not db_character or db_character.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Character not found")
    return await crud.update_character(db=db, character_id=character_id, character=character)

@router.delete("/{character_id}")
async def delete_character(
    character_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Delete a character.
    
    Args:
        character_id: ID of the character to delete.
        current_user: The authenticated user making the request.
        db: Database session.
        
    Returns:
        Success message.
        
    Raises:
        HTTPException: If character not found or doesn't belong to user.
    """
    character = await crud.get_character(db, character_id=character_id)
    if not character or character.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Character not found")
    await crud.delete_character(db=db, character_id=character_id)
    return {"message": "Character deleted successfully"}
