"""Main application module."""
from dotenv import load_dotenv
import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, characters, images, users, backstories, game_states, interactions
from . import models
from .database import engine, Base

# Create database tables asynchronously
async def init_db():
    """Initialize database by dropping all tables and recreating them."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables dropped and recreated successfully")

# Create event handler for startup
async def start_app():
    await init_db()

app = FastAPI(title="UNBOUNDED API")

# Add startup event handler
app.add_event_handler("startup", start_app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Create static directory if it doesn't exist
os.makedirs("static/images", exist_ok=True)

# Mount static files directory for serving images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(characters.router, prefix="/characters", tags=["characters"])
app.include_router(images.router, prefix="/images", tags=["images"])
app.include_router(backstories.router, prefix="/backstories", tags=["backstories"])
app.include_router(game_states.router, prefix="/game-states", tags=["game-states"])
app.include_router(interactions.router, prefix="/interactions", tags=["interactions"])

@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {"message": "Welcome to the UNBOUNDED API"}
