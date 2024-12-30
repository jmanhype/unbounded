"""Handler for character interactions using Ollama."""
from typing import Dict, Any, Optional
import httpx
import json
from datetime import datetime
import logging
from uuid import UUID

from . import schemas
from .config import settings
from .services.memory_service import MemoryService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class InteractionHandler:
    """Handles character interactions and generates responses using Ollama."""

    def __init__(self):
        """Initialize the interaction handler."""
        self.ollama_url = f"{settings.OLLAMA_API_URL}/api/generate"
        self.model = settings.MODEL_NAME
        self.memory_service = MemoryService()
        logger.info(f"Initialized InteractionHandler with URL: {self.ollama_url} and model: {self.model}")

    def store_interaction(
        self,
        character_id: str,
        interaction: Dict[str, Any]
    ) -> None:
        """
        Store an interaction in memory.

        Args:
            character_id: Unique identifier for the character
            interaction: Dictionary containing interaction details
        """
        self.memory_service.store_interaction(character_id, interaction)

    async def generate_response(
        self,
        character: schemas.Character,
        game_state: schemas.GameState,
        interaction: schemas.InteractionCreate
    ) -> Dict[str, Any]:
        """Generate a response to an interaction using Ollama."""
        try:
            # Convert state_data to CharacterState if it's a dict
            if isinstance(game_state.state_data, dict):
                state_data = schemas.CharacterState.model_validate(game_state.state_data)
            else:
                state_data = game_state.state_data
            
            # Build context for the prompt
            context = self._build_context(character, state_data, interaction)
            logger.debug(f"Built context: {json.dumps(context, indent=2)}")
            
            # Calculate personality influence on the interaction
            personality_influence = self._calculate_personality_influence(
                state_data.personality_traits,
                interaction.interaction_type
            )
            logger.debug(f"Calculated personality influence: {personality_influence}")
            
            # Generate the prompt
            prompt = self._build_prompt(context, personality_influence)
            logger.debug(f"Generated prompt: {prompt}")
            
            # Call Ollama API
            logger.info("Making request to Ollama API...")
            async with httpx.AsyncClient() as client:
                request_data = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
                logger.debug(f"Request data: {json.dumps(request_data, indent=2)}")
                
                response = await client.post(
                    self.ollama_url,
                    json=request_data,
                    timeout=30.0  # Add timeout
                )
                response.raise_for_status()
                result = response.json()
                logger.debug(f"Ollama API response: {json.dumps(result, indent=2)}")

            # Parse and structure the response
            response_text = result["response"]
            parsed_response = self._parse_response(response_text)
            logger.debug(f"Parsed response: {json.dumps(parsed_response, indent=2)}")
            
            # Calculate interaction success and update personality traits
            success_score = self._calculate_interaction_success(parsed_response)
            self._update_personality_traits(
                state_data.personality_traits,
                interaction.interaction_type,
                success_score
            )
            
            # Convert personality traits to dictionary
            personality_changes = {}
            if hasattr(state_data.personality_traits, "dict"):
                personality_changes = state_data.personality_traits.dict()
            
            return {
                "content": parsed_response["content"],
                "emotion": parsed_response.get("emotion", "neutral"),
                "action": parsed_response.get("action", None),
                "effects": parsed_response.get("effects", {}),
                "personality_changes": personality_changes,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Log the full error with traceback
            logger.exception("Error generating response")
            return {
                "content": "I'm not sure how to respond to that right now.",
                "emotion": "confused",
                "personality_changes": {},
                "timestamp": datetime.utcnow().isoformat()
            }

    def _build_context(
        self,
        character: schemas.Character,
        state_data: schemas.CharacterState,
        interaction: schemas.InteractionCreate
    ) -> Dict[str, Any]:
        """Build context for the interaction."""
        return {
            "character": {
                "name": character.name,
                "description": character.description,
                "backstory": getattr(character, "backstory", "") or ""
            },
            "current_state": {
                "health": state_data.health,
                "energy": state_data.energy,
                "happiness": state_data.happiness,
                "hunger": state_data.hunger,
                "fatigue": state_data.fatigue,
                "stress": state_data.stress,
                "location": state_data.location,
                "activity": state_data.activity,
                "personality_traits": state_data.personality_traits.model_dump()
            },
            "interaction": {
                "type": interaction.interaction_type,
                "content": interaction.content,
                "context": interaction.context.model_dump(),
                "timestamp": interaction.timestamp.isoformat() if interaction.timestamp else datetime.utcnow().isoformat()
            }
        }

    def _calculate_personality_influence(
        self,
        personality_traits: schemas.PersonalityTraits,
        interaction_type: str
    ) -> Dict[str, float]:
        """Calculate how personality traits influence the interaction."""
        return personality_traits.calculate_trait_influence(interaction_type)

    def _calculate_interaction_success(self, response: Dict[str, Any]) -> float:
        """Calculate the success score of an interaction."""
        emotion_scores = {
            "happy": 1.0,
            "content": 0.8,
            "neutral": 0.5,
            "confused": 0.3,
            "sad": 0.2,
            "angry": 0.1
        }
        
        emotion = response.get("emotion", "neutral").lower()
        emotion_score = emotion_scores.get(emotion, 0.5)
        
        effects = response.get("effects", {})
        effect_score = sum(
            1 if v > 0 else 0.5 if v == 0 else 0
            for v in effects.values()
        ) / max(len(effects), 1)
        
        return (emotion_score + effect_score) / 2

    def _update_personality_traits(
        self,
        personality_traits: schemas.PersonalityTraits,
        interaction_type: str,
        success_score: float
    ) -> None:
        """Update personality traits based on interaction outcome."""
        personality_traits.update_traits(interaction_type, success_score)

    def _build_prompt(self, context: Dict[str, Any], personality_influence: Dict[str, float]) -> str:
        """Build the prompt for Ollama."""
        personality_traits = context['current_state']['personality_traits']
        personality_desc = f"""Personality Traits:
- Openness: {personality_traits['openness']['value']}/100 (Imagination, Creativity, Curiosity)
- Conscientiousness: {personality_traits['conscientiousness']['value']}/100 (Organization, Responsibility)
- Extraversion: {personality_traits['extraversion']['value']}/100 (Sociability, Energy, Assertiveness)
- Agreeableness: {personality_traits['agreeableness']['value']}/100 (Cooperation, Compassion)
- Neuroticism: {personality_traits['neuroticism']['value']}/100 (Emotional Stability, Stress Response)

Your personality influences this interaction in the following ways:
{self._format_personality_influences(personality_influence)}"""

        return f"""You are {context['character']['name']}, a character with the following traits and current state:

Description: {context['character']['description']}
Backstory: {context['character']['backstory']}

{personality_desc}

Current State:
- Health: {context['current_state']['health']}
- Energy: {context['current_state']['energy']}
- Happiness: {context['current_state']['happiness']}
- Hunger: {context['current_state']['hunger']}
- Fatigue: {context['current_state']['fatigue']}
- Stress: {context['current_state']['stress']}
- Location: {context['current_state']['location']}
- Current Activity: {context['current_state']['activity']}

A user is interacting with you:
Interaction Type: {context['interaction']['type']}
Content: {context['interaction']['content']}
Time: {context['interaction']['context']['time_of_day']}
Location: {context['interaction']['context']['location']}

Respond to this interaction in character, considering your personality traits, their influences on this interaction, your current state, and the context. Include your emotional response and any actions you take.

Format your response as JSON with the following structure:
{{
    "content": "Your response text",
    "emotion": "Your emotional state",
    "action": "Any action you take",
    "effects": {{
        "health": change_value,
        "energy": change_value,
        "happiness": change_value,
        "hunger": change_value,
        "fatigue": change_value,
        "stress": change_value
    }}
}}"""

    def _format_personality_influences(self, influences: Dict[str, float]) -> str:
        """Format personality influences for the prompt."""
        if not influences:
            return "No significant personality influences for this interaction type."
            
        formatted = []
        for trait, influence in influences.items():
            if influence > 0:
                formatted.append(f"- Your high {trait} makes you more effective (+{influence:.1%})")
            elif influence < 0:
                formatted.append(f"- Your high {trait} makes this more challenging ({influence:.1%})")
                
        return "\n".join(formatted) if formatted else "Personality has neutral influence on this interaction."

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the response from Ollama into structured data."""
        try:
            logger.debug(f"Attempting to parse response text: {response_text}")
            
            # If the response is already a dictionary, return it
            if isinstance(response_text, dict):
                return response_text
                
            # Try to find JSON in the response text
            try:
                # First try to parse the entire response as JSON
                parsed = json.loads(response_text)
                if isinstance(parsed, dict) and "content" in parsed:
                    return parsed
            except json.JSONDecodeError:
                # If that fails, try to find JSON in the text
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx + 1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and "content" in parsed:
                            return parsed
                    except json.JSONDecodeError:
                        pass
            
            # If no valid JSON found, wrap the text in our format
            return {
                "content": response_text.strip(),
                "emotion": "neutral",
                "action": None,
                "effects": {
                    "health": 0,
                    "energy": 0,
                    "happiness": 0,
                    "hunger": 0,
                    "fatigue": 0,
                    "stress": 0
                }
            }
            
        except Exception as e:
            logger.exception("Unexpected error parsing response")
            return {
                "content": "I'm having trouble processing that right now.",
                "emotion": "confused",
                "action": None,
                "effects": {
                    "health": 0,
                    "energy": 0,
                    "happiness": 0,
                    "hunger": 0,
                    "fatigue": 0,
                    "stress": 0
                }
            }

    async def handle_interaction(
        self,
        character: schemas.Character,
        input_text: str
    ) -> str:
        """
        Handle an interaction with a character.

        Args:
            character: The character to interact with
            input_text: The user's input text

        Returns:
            The character's response text
        """
        try:
            # Get recent interactions from memory
            recent_interactions = self.memory_service.get_recent_interactions(str(character.id))
            
            # Create interaction context
            interaction = schemas.InteractionCreate(
                interaction_type="chat",
                content=input_text,
                context=schemas.InteractionContext(
                    location="chat",
                    time_of_day=datetime.now().strftime("%H:%M")
                ),
                effects=schemas.InteractionEffects(),
                timestamp=datetime.utcnow()
            )
            
            # Get current game state
            game_state = schemas.GameState(
                id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                character_id=character.id,
                user_id=UUID('00000000-0000-0000-0000-000000000000'),  # Placeholder
                timestamp=datetime.utcnow(),
                health=100,
                energy=100,
                happiness=100,
                hunger=0,
                fatigue=0,
                stress=0,
                location="chat",
                activity="chatting"
            )
            
            # Generate response
            response = await self.generate_response(character, game_state, interaction)
            
            # Store interaction in memory
            self.memory_service.store_interaction(
                str(character.id),
                {
                    "type": "chat",
                    "user_input": input_text,
                    "response": response["content"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": {
                        "recent_interactions": recent_interactions
                    }
                }
            )
            
            return response["content"]
            
        except Exception as e:
            logger.exception("Error handling interaction")
            return "I apologize, but I'm having trouble processing that right now." 