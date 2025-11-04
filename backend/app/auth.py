from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from . import models, database
import os
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "7edbef8aaf4735a01738e32afd795f7d639110ffae866e52e472e89efa4ee925")
if not SECRET_KEY or SECRET_KEY == "your-secret-key":
    logger.warning("Using default SECRET_KEY. This is insecure for production!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password to verify
        hashed_password: The bcrypt hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    try:
        result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        return result
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for a password.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt hashed password as a string

    Raises:
        Exception: If password hashing fails
    """
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        result = hashed.decode('utf-8')
        return result
    except Exception as e:
        logger.error("Error generating password hash")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary of data to encode in the token
        expires_delta: Optional expiration timedelta, defaults to 15 minutes

    Returns:
        Encoded JWT token as a string

    Raises:
        Exception: If token encoding fails
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error("Error generating JWT token")
        raise

async def get_user(db: AsyncSession, username: str) -> Optional[models.User]:
    """Get a user by username.

    Args:
        db: Database session
        username: Username to look up

    Returns:
        User model instance or None if not found
    """
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[models.User]:
    """Authenticate a user with username and password.

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password to verify

    Returns:
        User model instance if authentication succeeds, False otherwise
    """
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db)
) -> models.User:
    """Get the current authenticated user from JWT token.

    Args:
        token: JWT access token from the Authorization header
        db: Database session

    Returns:
        Authenticated User model instance

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and validate token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as e:
            logger.debug(f"JWT decode error: {str(e)}")
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            logger.debug("No username in token payload")
            raise credentials_exception

        user = await get_user(db, username)
        if user is None:
            logger.debug(f"User not found: {username}")
            raise credentials_exception

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {str(e)}")
        raise credentials_exception
