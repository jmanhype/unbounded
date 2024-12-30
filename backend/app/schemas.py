"""Pydantic models for request/response validation."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator

class UserBase(BaseModel):
    """Base user model."""
    username: str
    email: EmailStr

class UserCreate(UserBase):
    """User creation model."""
    password: str

class User(UserBase):
    """User response model."""
    id: UUID
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True

class CharacterBase(BaseModel):
    """Base character model."""
    name: str
    description: str

class CharacterCreate(CharacterBase):
    """Character creation model."""
    pass

class CharacterUpdate(CharacterBase):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    personality_traits: Optional[Dict[str, Any]] = None
    backstory: Optional[str] = None

class Character(CharacterBase):
    """Character response model."""
    id: UUID
    user_id: UUID
    image_url: Optional[str] = None
    backstory: Optional[str] = None
    personality_traits: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True

class ImageGenerationRequest(BaseModel):
    """Image generation request model."""
    prompt: str
    character_id: str
    negative_prompt: Optional[str] = None
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    num_inference_steps: Optional[int] = 50
    guidance_scale: Optional[float] = 7.5

class BackstoryGenerationRequest(BaseModel):
    """Schema for backstory generation request."""
    tone: Optional[str] = "balanced"
    length: Optional[str] = "medium"
    themes: Optional[list[str]] = None

    @validator('tone')
    def validate_tone(cls, v):
        """Validate tone value."""
        allowed_tones = ["dark", "light", "balanced", "heroic", "tragic", "mysterious"]
        if v.lower() not in allowed_tones:
            raise ValueError(f"Tone must be one of: {', '.join(allowed_tones)}")
        return v.lower()

    @validator('length')
    def validate_length(cls, v):
        """Validate length value."""
        allowed_lengths = ["short", "medium", "long"]
        if v.lower() not in allowed_lengths:
            raise ValueError(f"Length must be one of: {', '.join(allowed_lengths)}")
        return v.lower()

class BackstoryResponse(BaseModel):
    """Schema for backstory response."""
    character_id: UUID
    content: str
    tone: str
    themes: list[str]
    word_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class PersonalityTrait(BaseModel):
    """Model for a single personality trait."""
    value: int = Field(default=50, ge=0, le=100)
    development_points: int = Field(default=0, ge=0)

class PersonalityTraits(BaseModel):
    """Model for character personality traits using OCEAN model."""
    openness: PersonalityTrait = Field(default_factory=PersonalityTrait)
    conscientiousness: PersonalityTrait = Field(default_factory=PersonalityTrait)
    extraversion: PersonalityTrait = Field(default_factory=PersonalityTrait)
    agreeableness: PersonalityTrait = Field(default_factory=PersonalityTrait)
    neuroticism: PersonalityTrait = Field(default_factory=PersonalityTrait)

    def calculate_trait_influence(self, interaction_type: str) -> Dict[str, float]:
        """Calculate how traits influence an interaction type."""
        influences = {}
        
        # Define trait influences for different interaction types
        influence_map = {
            "chat": {
                "extraversion": 0.3,
                "agreeableness": 0.2,
                "neuroticism": -0.1
            },
            "task": {
                "conscientiousness": 0.4,
                "openness": 0.2,
                "neuroticism": -0.2
            },
            "social": {
                "extraversion": 0.4,
                "agreeableness": 0.3,
                "openness": 0.1
            }
        }
        
        if interaction_type in influence_map:
            for trait, influence in influence_map[interaction_type].items():
                trait_value = getattr(self, trait).value
                # Scale influence based on trait value
                scaled_influence = influence * (trait_value - 50) / 50
                if abs(scaled_influence) > 0.05:  # Only include significant influences
                    influences[trait] = scaled_influence
                    
        return influences

    def update_traits(self, interaction_type: str, success_score: float) -> None:
        """Update traits based on interaction outcome."""
        # Define which traits are affected by different interaction types
        trait_effects = {
            "chat": ["extraversion", "agreeableness"],
            "task": ["conscientiousness", "openness"],
            "social": ["extraversion", "agreeableness", "openness"]
        }
        
        if interaction_type in trait_effects:
            for trait_name in trait_effects[interaction_type]:
                trait = getattr(self, trait_name)
                # Calculate development points based on success
                points = int(success_score * 10)
                trait.development_points += points
                
                # Update trait value if enough points accumulated
                if trait.development_points >= 100:
                    trait.value = min(100, trait.value + 1)
                    trait.development_points -= 100

class CharacterState(BaseModel):
    """Character state attributes."""
    health: int = 100
    energy: int = 100
    happiness: int = 100
    hunger: int = 0
    fatigue: int = 0
    stress: int = 0
    last_interaction: Optional[datetime] = None
    personality_traits: PersonalityTraits = Field(default_factory=PersonalityTraits)
    skills: Dict[str, int] = Field(default_factory=dict)
    inventory: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    relationships: Dict[str, int] = Field(default_factory=dict)
    location: str = "home"
    activity: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class GameStateBase(BaseModel):
    """Base game state model."""
    health: int = Field(default=100, ge=0, le=100)
    energy: int = Field(default=100, ge=0, le=100)
    happiness: int = Field(default=100, ge=0, le=100)
    hunger: int = Field(default=0, ge=0, le=100)
    fatigue: int = Field(default=0, ge=0, le=100)
    stress: int = Field(default=0, ge=0, le=100)
    location: str = Field(default="home")
    activity: str = Field(default="resting")

class GameStateCreate(GameStateBase):
    """Game state creation model."""
    pass

class GameStateUpdate(GameStateBase):
    """Game state update model."""
    pass

class GameState(GameStateBase):
    """Game state response model."""
    id: UUID
    character_id: UUID
    user_id: UUID
    timestamp: datetime
    state_data: CharacterState = Field(default_factory=CharacterState)

    class Config:
        """Pydantic configuration."""
        from_attributes = True

class InteractionContext(BaseModel):
    """Model for interaction context."""
    location: str
    time_of_day: str
    weather: Optional[str] = None
    previous_activity: Optional[str] = None
    nearby_characters: List[str] = Field(default_factory=list)
    available_items: List[str] = Field(default_factory=list)

class InteractionEffects(BaseModel):
    """Model for interaction effects on character state."""
    health: int = Field(default=0, ge=-10, le=10)
    energy: int = Field(default=0, ge=-10, le=10)
    happiness: int = Field(default=0, ge=-10, le=10)
    hunger: int = Field(default=0, ge=-10, le=10)
    fatigue: int = Field(default=0, ge=-10, le=10)
    stress: int = Field(default=0, ge=-10, le=10)

class InteractionBase(BaseModel):
    """Base model for interactions."""
    interaction_type: str
    content: str
    sentiment_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    context: InteractionContext
    effects: InteractionEffects

class InteractionCreate(InteractionBase):
    """Model for creating a new interaction."""
    timestamp: Optional[datetime] = None

    @validator("timestamp", pre=True, always=True)
    def set_timestamp(cls, v):
        """Set timestamp to current time if not provided."""
        return v or datetime.utcnow()

class InteractionResponse(BaseModel):
    """Model for interaction response."""
    content: str
    emotion: str = "neutral"
    action: Optional[str] = None

class Interaction(BaseModel):
    """Model for interaction response."""
    id: UUID
    character_id: UUID
    interaction_type: str
    content: str
    sentiment_score: float
    context: Dict[str, Any]
    effects: Dict[str, Any]
    response: Dict[str, Any]
    timestamp: datetime

    class Config:
        """Pydantic configuration."""
        from_attributes = True
