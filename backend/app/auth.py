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

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "7edbef8aaf4735a01738e32afd795f7d639110ffae866e52e472e89efa4ee925")
if not SECRET_KEY or SECRET_KEY == "your-secret-key":
    print("WARNING: Using default SECRET_KEY. This is insecure for production!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    print(f"\nVerifying password for user")
    print(f"Plain password: {plain_password}")
    print(f"Hashed password: {hashed_password}")
    try:
        result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    print(f"\nGenerating password hash")
    print(f"Plain password: {password}")
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        result = hashed.decode('utf-8')
        print(f"Generated hash: {result}")
        return result
    except Exception as e:
        print(f"Error generating password hash: {e}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        print(f"Generated token: {encoded_jwt}")  # Debug print
        return encoded_jwt
    except Exception as e:
        print(f"Error generating token: {e}")
        raise

async def get_user(db: AsyncSession, username: str):
    result = await db.execute(select(models.User).filter(models.User.username == username))
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"\n=== Token Validation Debug ===")
        print(f"Raw token received: {token}")
        print(f"SECRET_KEY being used: {SECRET_KEY}")
        print(f"ALGORITHM being used: {ALGORITHM}")
        
        # Decode and validate token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"Successfully decoded payload: {payload}")
        except JWTError as e:
            print(f"JWT decode error: {str(e)}")
            raise credentials_exception
            
        username: str = payload.get("sub")
        if username is None:
            print("ERROR: No username in token payload")
            raise credentials_exception
            
        print(f"Looking up user: {username}")
        user = await get_user(db, username)
        if user is None:
            print(f"ERROR: User not found: {username}")
            raise credentials_exception
            
        print(f"Authentication successful for user: {username}")
        print(f"User details: id={user.id}, username={user.username}, email={user.email}")
        return user
        
    except Exception as e:
        print(f"Unexpected error during authentication: {str(e)}")
        raise credentials_exception
