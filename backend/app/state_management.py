"""State management and transition logic for characters."""
from datetime import datetime, timedelta
from typing import Optional
import json
from . import schemas

class StateManager:
    """Manages character state transitions and updates."""

    @staticmethod
    def calculate_time_based_changes(
        current_state: schemas.CharacterState,
        last_update: datetime
    ) -> schemas.CharacterState:
        """Calculate state changes based on time passed.
        
        Args:
            current_state: Current character state
            last_update: Last time the state was updated
            
        Returns:
            Updated character state
        """
        time_passed = datetime.utcnow() - last_update
        hours_passed = time_passed.total_seconds() / 3600

        # Increase needs over time
        current_state.hunger = min(100, current_state.hunger + int(hours_passed * 5))  # 5 points per hour
        current_state.fatigue = min(100, current_state.fatigue + int(hours_passed * 4))  # 4 points per hour
        current_state.stress = min(100, current_state.stress + int(hours_passed * 3))  # 3 points per hour

        # Decrease stats based on needs
        if current_state.hunger > 70:
            current_state.energy = max(0, current_state.energy - int(hours_passed * 3))
            current_state.happiness = max(0, current_state.happiness - int(hours_passed * 2))
        
        if current_state.fatigue > 70:
            current_state.energy = max(0, current_state.energy - int(hours_passed * 4))
            current_state.happiness = max(0, current_state.happiness - int(hours_passed * 2))
        
        if current_state.stress > 70:
            current_state.happiness = max(0, current_state.happiness - int(hours_passed * 3))

        return current_state

    @staticmethod
    def apply_interaction_effects(
        current_state: schemas.CharacterState,
        interaction_type: str,
        success_level: Optional[float] = 1.0
    ) -> schemas.CharacterState:
        """Apply effects of an interaction to the character state.
        
        Args:
            current_state: Current character state
            interaction_type: Type of interaction
            success_level: How successful the interaction was (0.0 to 1.0)
            
        Returns:
            Updated character state
        """
        # Initialize attributes if they don't exist
        if not hasattr(current_state, 'skills'):
            current_state.skills = {}
        if not hasattr(current_state, 'relationships'):
            current_state.relationships = {}
        if not hasattr(current_state, 'achievements'):
            current_state.achievements = []
            
        # Update last interaction time
        current_state.last_interaction = datetime.utcnow()

        # Apply effects based on interaction type
        if interaction_type == "feed":
            current_state.hunger = max(0, current_state.hunger - 30)
            current_state.energy = min(100, current_state.energy + 10)
            current_state.happiness = min(100, current_state.happiness + 5)
        
        elif interaction_type == "rest":
            current_state.fatigue = max(0, current_state.fatigue - 40)
            current_state.energy = min(100, current_state.energy + 30)
            current_state.stress = max(0, current_state.stress - 20)
        
        elif interaction_type == "play":
            current_state.happiness = min(100, current_state.happiness + 20)
            current_state.energy = max(0, current_state.energy - 15)
            current_state.fatigue = min(100, current_state.fatigue + 10)
            current_state.stress = max(0, current_state.stress - 15)
        
        elif interaction_type == "exercise":
            current_state.health = min(100, current_state.health + 15)
            current_state.energy = max(0, current_state.energy - 25)
            current_state.fatigue = min(100, current_state.fatigue + 20)
            current_state.stress = max(0, current_state.stress - 10)
        
        elif interaction_type == "socialize":
            current_state.happiness = min(100, current_state.happiness + 15)
            current_state.energy = max(0, current_state.energy - 10)
            current_state.stress = max(0, current_state.stress - 25)
        
        elif interaction_type == "learn":
            current_state.energy = max(0, current_state.energy - 20)
            current_state.fatigue = min(100, current_state.fatigue + 15)
            current_state.stress = min(100, current_state.stress + 10)

        # Convert datetime to string for JSON serialization
        current_state.last_interaction = current_state.last_interaction.isoformat()
        return current_state

    @staticmethod
    def update_skills(
        current_state: schemas.CharacterState,
        skill_name: str,
        experience_points: int
    ) -> schemas.CharacterState:
        """Update character skills based on activities.
        
        Args:
            current_state: Current character state
            skill_name: Name of the skill to update
            experience_points: Points to add to the skill
            
        Returns:
            Updated character state
        """
        if not hasattr(current_state, 'skills'):
            current_state.skills = {}
            
        current_level = current_state.skills.get(skill_name, 0)
        # Apply diminishing returns for higher levels
        level_factor = 1.0 - (current_level / 200)  # Slower progress at higher levels
        new_level = current_level + int(experience_points * level_factor)
        new_level = min(100, new_level)  # Cap at 100
        
        current_state.skills[skill_name] = new_level
        return current_state

    @staticmethod
    def update_relationships(
        current_state: schemas.CharacterState,
        target_id: str,
        interaction_quality: float
    ) -> schemas.CharacterState:
        """Update character relationships based on interactions.
        
        Args:
            current_state: Current character state
            target_id: ID of the character or user interacted with
            interaction_quality: Quality of interaction (-1.0 to 1.0)
            
        Returns:
            Updated character state
        """
        if not hasattr(current_state, 'relationships'):
            current_state.relationships = {}
            
        current_relation = current_state.relationships.get(target_id, 50)
        change = int(interaction_quality * 5)  # Convert to -5 to +5 range
        new_relation = max(0, min(100, current_relation + change))
        
        current_state.relationships[target_id] = new_relation
        return current_state

    @staticmethod
    def check_and_award_achievements(
        current_state: schemas.CharacterState
    ) -> schemas.CharacterState:
        """Check and award achievements based on character state.
        
        Args:
            current_state: Current character state
            
        Returns:
            Updated character state with any new achievements
        """
        if not hasattr(current_state, 'achievements'):
            current_state.achievements = []
            
        achievement_conditions = {
            "master_chef": lambda s: s.skills.get("cooking", 0) >= 90,
            "social_butterfly": lambda s: len([v for v in s.relationships.values() if v >= 80]) >= 5,
            "well_balanced": lambda s: all(v >= 70 for v in [s.health, s.happiness, s.energy]),
            "skill_collector": lambda s: len([v for v in s.skills.values() if v >= 50]) >= 5,
            "iron_will": lambda s: s.stress <= 10 and s.happiness >= 90,
        }

        for achievement, condition in achievement_conditions.items():
            if achievement not in current_state.achievements and condition(current_state):
                current_state.achievements.append(achievement)

        return current_state 