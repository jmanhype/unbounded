"""Authentication router."""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from .. import crud, models, schemas
from ..database import get_db
from ..auth import create_access_token, get_current_user, verify_password

router = APIRouter(
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/signup", response_model=schemas.User)
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)) -> models.User:
    """Create a new user.
    
    Args:
        user: User creation data.
        db: Database session.
        
    Returns:
        The created user.
        
    Raises:
        HTTPException: If username already exists.
    """
    db_user = await crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return await crud.create_user(db=db, user=user)

@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Log in a user.
    
    Args:
        form_data: Form containing username and password.
        db: Database session.
        
    Returns:
        Access token and token type.
        
    Raises:
        HTTPException: If credentials are invalid.
    """
    user = await crud.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(days=30)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/test-create-user", response_model=schemas.User)
async def test_create_user(db: AsyncSession = Depends(get_db)) -> models.User:
    """Create a test user.
    
    Args:
        db: Database session.
        
    Returns:
        The created test user.
    """
    user = schemas.UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )
    return await crud.create_user(db=db, user=user)

@router.post("/test-password")
async def test_password(password: str, db: AsyncSession = Depends(get_db)) -> dict:
    """Test password hashing and verification.
    
    Args:
        password: Password to test.
        db: Database session.
        
    Returns:
        Dictionary containing test results.
    """
    user = await crud.create_user(
        db=db,
        user=schemas.UserCreate(
            username="testuser2",
            email="test2@example.com",
            password=password
        )
    )
    
    is_valid = verify_password(password, user.password_hash)
    return {
        "password": password,
        "hash": user.password_hash,
        "is_valid": is_valid
    }
