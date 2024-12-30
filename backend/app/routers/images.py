"""Router for image generation endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_user
from ..image_generation import ImageGenerator
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["images"],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def generate_character_image(
    request: schemas.ImageGenerationRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Generate an image for a character.
    
    Args:
        request: Image generation request containing prompt and character ID.
        current_user: The authenticated user making the request.
        db: Database session.
        
    Returns:
        Dictionary containing the image URL and local path.
        
    Raises:
        HTTPException: If character not found or image generation fails.
    """
    try:
        logger.info("Starting image generation request for character %s", request.character_id)
        logger.debug("Request data: %s", request.dict())
        
        # Verify character exists and belongs to user
        character = await crud.get_character(db, request.character_id)
        if not character or character.user_id != current_user.id:
            logger.error("Character not found or does not belong to user: %s", request.character_id)
            raise HTTPException(status_code=404, detail="Character not found")
        
        logger.info("Character verified: %s", character.id)
        
        # Initialize image generator
        try:
            generator = ImageGenerator()
            logger.info("Image generator initialized")
        except Exception as e:
            logger.error("Failed to initialize image generator: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize image generator: {str(e)}"
            )
        
        try:
            # Generate image
            logger.info("Generating image with prompt: %s", request.prompt)
            image_url = await generator.generate_character_image(
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                width=request.width or 1024,
                height=request.height or 1024,
                num_inference_steps=request.num_inference_steps or 50,
                guidance_scale=request.guidance_scale or 7.5
            )
            logger.info("Image generated successfully: %s", image_url)
            
            # Save image locally
            logger.info("Saving image locally")
            local_path = await generator.save_image_locally(image_url, str(request.character_id))
            logger.info("Image saved locally: %s", local_path)
            
            # Update character with image URL
            character.image_url = local_path
            await db.commit()
            logger.info("Character updated with new image URL")
            
            return {
                "image_url": image_url,
                "local_path": local_path,
                "message": "Image generated successfully"
            }
            
        except Exception as e:
            logger.error("Failed to generate or save image: %s", str(e), exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate image: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        ) 