"""Database models."""
from datetime import datetime
from typing import Optional
from uuid import uuid4, UUID as UUID_TYPE
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, ForeignKey, Boolean, UUID, Index
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    characters = relationship("Character", back_populates="user", cascade="all, delete-orphan")
    game_states = relationship("GameState", back_populates="user", cascade="all, delete-orphan")

class Character(Base):
    """Character model."""
    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String)
    description = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    image_url = Column(String, nullable=True)
    personality_traits = Column(JSON, default=dict)
    backstory = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="characters")
    game_states = relationship("GameState", back_populates="character", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="character", cascade="all, delete-orphan")
    backstories = relationship("CharacterBackstory", back_populates="character", cascade="all, delete-orphan")

class GameState(Base):
    """Model for character game states."""
    __tablename__ = "game_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    health = Column(Integer, nullable=False, default=100)
    energy = Column(Integer, nullable=False, default=100)
    happiness = Column(Integer, nullable=False, default=100)
    hunger = Column(Integer, nullable=False, default=0)
    fatigue = Column(Integer, nullable=False, default=0)
    stress = Column(Integer, nullable=False, default=0)
    location = Column(String, nullable=False, default="home")
    activity = Column(String, nullable=False, default="resting")
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    character = relationship("Character", back_populates="game_states")
    user = relationship("User", back_populates="game_states")

class Interaction(Base):
    """Model for character interactions."""
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id"))
    interaction_type = Column(String)
    content = Column(String)
    sentiment_score = Column(Float)
    context = Column(JSON)
    effects = Column(JSON)
    response = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

    character = relationship("Character", back_populates="interactions")

    __table_args__ = (
        Index("ix_interactions_character_id_timestamp", "character_id", "timestamp"),
    )

class CharacterBackstory(Base):
    """Character backstory model."""
    __tablename__ = "character_backstories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    character_id = Column(UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE"))
    content = Column(String)
    tone = Column(String)
    themes = Column(JSON)
    word_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    character = relationship("Character", back_populates="backstories")
