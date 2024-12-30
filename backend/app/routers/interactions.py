"""Router for character interactions."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
import os

from .. import crud, schemas
from ..database import get_db
from ..auth import get_current_user
from ..interaction_handler import InteractionHandler

class InteractionInput(BaseModel):
    input: str

router = APIRouter()
interaction_handler = InteractionHandler()

@router.post("/characters/{character_id}/interact", response_model=schemas.Interaction)
async def create_interaction(
    character_id: UUID,
    interaction: InteractionInput,
    current_user: schemas.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new interaction with a character."""
    # Verify character exists and belongs to user
    character = await crud.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to interact with this character")

    try:
        # Process the interaction
        response_text = await interaction_handler.handle_interaction(character, interaction.input)
        
        # Create interaction record
        db_interaction = await crud.create_interaction(
            db=db,
            character_id=character_id,
            interaction_type="chat",
            content=interaction.input,
            sentiment_score=0.0,  # This should be calculated by sentiment analysis
            context={
                "location": "chat",
                "time_of_day": datetime.now().strftime("%H:%M"),
                "weather": None,
                "previous_activity": None
            },
            effects={},  # This should track any state changes
            response={
                "text": response_text,
                "emotion": "neutral",
                "action": None
            }
        )
        
        if not db_interaction:
            raise HTTPException(status_code=500, detail="Failed to create interaction")
            
        # Convert the database model to a response schema
        return schemas.Interaction(
            id=db_interaction.id,
            character_id=db_interaction.character_id,
            interaction_type=db_interaction.interaction_type,
            content=db_interaction.content,
            sentiment_score=db_interaction.sentiment_score,
            context=db_interaction.context,
            effects=db_interaction.effects,
            response=db_interaction.response,
            timestamp=db_interaction.timestamp
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/characters/{character_id}/interactions", response_model=List[schemas.Interaction])
async def get_interaction_history(
    character_id: UUID,
    current_user: schemas.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get interaction history for a character."""
    # Verify character exists and belongs to user
    character = await crud.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    if character.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this character's interactions")

    try:
        interactions = await crud.get_character_interactions(db, character_id)
        return interactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 