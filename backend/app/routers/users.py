from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, models, schemas
from ..auth import get_current_user, get_password_hash
from ..database import get_db

router = APIRouter(
    tags=["users"]
)

@router.post("/", response_model=schemas.User)
async def create_user(
    user: schemas.UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> models.User:
    """
    Create a new user.
    
    Args:
        user: User creation data
        db: Database session
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If username already exists
    """
    db_user = await crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await crud.create_user(db=db, user=user)

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> models.User:
    """
    Get current user information.
    
    Args:
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        The current user
    """
    return current_user 