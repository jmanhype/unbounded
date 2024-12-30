"""Router for backstory generation endpoints."""
from typing import Optional, List
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..backstory_generation import BackstoryGenerator
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console only for now
    ]
)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["backstories"],
    responses={404: {"description": "Not found"}},
)

@router.post("/{character_id}", response_model=schemas.BackstoryResponse)
async def generate_character_backstory(
    character_id: str,
    request: schemas.BackstoryGenerationRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.BackstoryResponse:
    """Generate a backstory for a character."""
    try:
        logger.info(f"Starting backstory generation request for character {character_id}")
        logger.info(f"Current user: {current_user.id} ({current_user.username})")
        logger.debug(f"Request data: {request.model_dump()}")
        
        # Verify character exists and belongs to user
        logger.debug(f"Looking up character with ID: {character_id}")
        character = await crud.get_character(db, character_id)
        
        if not character:
            logger.error(f"Character not found: {character_id}")
            raise HTTPException(status_code=404, detail="Character not found")
            
        if character.user_id != current_user.id:
            logger.error(f"Character {character_id} belongs to user {character.user_id}, not {current_user.id}")
            raise HTTPException(status_code=404, detail="Character not found")
        
        logger.info(f"Character verified: {character.id} ({character.name})")
        logger.debug(f"Character details: name={character.name}, description={character.description}")
        
        # Initialize backstory generator
        try:
            generator = BackstoryGenerator()
            logger.info("Backstory generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize backstory generator: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize backstory generator: {str(e)}"
            )
        
        try:
            # Generate backstory
            logger.info(f"Generating backstory for character: {character.name}")
            backstory = await generator.generate_backstory(
                character_name=character.name,
                character_description=character.description,
                tone=request.tone,
                length=request.length,
                themes=request.themes
            )
            logger.info("Backstory generated successfully")
            logger.debug(f"Generated backstory: {backstory}")
            
            # Save backstory to database
            try:
                db_backstory = await crud.create_character_backstory(
                    db=db,
                    character_id=character.id,
                    content=backstory["content"],
                    tone=backstory["tone"],
                    themes=backstory["themes"],
                    word_count=backstory["word_count"]
                )
                logger.info(f"Backstory saved to database: {db_backstory.id}")
                
                if not db_backstory:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to save backstory to database"
                    )
                
                # Update character's backstory field
                await crud.update_character(
                    db=db,
                    character_id=character.id,
                    character=schemas.CharacterUpdate(backstory=backstory["content"])
                )
                logger.info("Updated character's backstory field")
                
                # Create response
                response = schemas.BackstoryResponse(
                    character_id=character.id,
                    content=db_backstory.content,
                    tone=db_backstory.tone,
                    themes=db_backstory.themes or [],
                    word_count=db_backstory.word_count,
                    created_at=db_backstory.created_at
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Failed to save backstory to database: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save backstory: {str(e)}"
                )
            
        except Exception as e:
            error_msg = f"Failed to generate backstory: {str(e)}"
            logger.error("%s\n%s", error_msg, traceback.format_exc())
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error("%s\n%s", error_msg, traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/{character_id}", response_model=schemas.BackstoryResponse)
async def get_character_backstory(
    character_id: str,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> schemas.BackstoryResponse:
    """Get the most recent backstory for a character."""
    try:
        # Verify character exists and belongs to user
        character = await crud.get_character(db, character_id)
        if not character or character.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Character not found")
            
        # Get most recent backstory
        backstory = await crud.get_character_backstory(db, character_id)
        if not backstory:
            raise HTTPException(status_code=404, detail="No backstory found for character")
            
        return schemas.BackstoryResponse(
            character_id=character.id,
            content=backstory.content,
            tone=backstory.tone,
            themes=backstory.themes or [],
            word_count=backstory.word_count,
            created_at=backstory.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get character backstory: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get character backstory: {str(e)}"
        )

@router.get("/{character_id}/history", response_model=List[schemas.BackstoryResponse])
async def get_character_backstory_history(
    character_id: str,
    skip: int = 0,
    limit: int = 10,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[schemas.BackstoryResponse]:
    """Get the history of backstories for a character."""
    try:
        # Verify character exists and belongs to user
        character = await crud.get_character(db, character_id)
        if not character or character.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Character not found")
            
        # Get backstory history
        backstories = await crud.get_character_backstories(
            db,
            character_id,
            skip=skip,
            limit=limit
        )
        
        return [
            schemas.BackstoryResponse(
                character_id=character.id,
                content=b.content,
                tone=b.tone,
                themes=b.themes or [],
                word_count=b.word_count,
                created_at=b.created_at
            )
            for b in backstories
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get character backstory history: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get character backstory history: {str(e)}"
        ) 