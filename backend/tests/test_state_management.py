"""Tests for state management functionality."""
from datetime import datetime, timedelta
import pytest
from typing import TYPE_CHECKING

from app.state_management import StateManager
from app.schemas import CharacterState

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from pytest_mock import MockerFixture

@pytest.fixture
def state_manager() -> StateManager:
    """Create a state manager instance."""
    return StateManager()

@pytest.fixture
def base_state() -> CharacterState:
    """Create a base character state for testing."""
    return CharacterState(
        health=100,
        energy=100,
        happiness=100,
        hunger=0,
        fatigue=0,
        stress=0,
        personality_traits={"openness": 70},
        skills={"cooking": 50},
        inventory=["book"],
        achievements=[],
        relationships={"user123": 50}
    )

def test_calculate_time_based_changes(state_manager: StateManager, base_state: CharacterState):
    """Test time-based state changes."""
    # Test 1 hour of time passing
    last_update = datetime.utcnow() - timedelta(hours=1)
    updated_state = state_manager.calculate_time_based_changes(base_state, last_update)
    
    assert updated_state.hunger == 5  # 5 points per hour
    assert updated_state.fatigue == 4  # 4 points per hour
    assert updated_state.stress == 3  # 3 points per hour
    
    # Test high needs impact on stats
    base_state.hunger = 80
    base_state.fatigue = 80
    base_state.stress = 80
    
    updated_state = state_manager.calculate_time_based_changes(base_state, last_update)
    assert updated_state.energy < 100  # Energy decreased due to high needs
    assert updated_state.happiness < 100  # Happiness decreased due to high needs

def test_apply_interaction_effects(state_manager: StateManager, base_state: CharacterState):
    """Test interaction effects on state."""
    # Test feeding interaction
    updated_state = state_manager.apply_interaction_effects(base_state, "feed")
    assert updated_state.hunger == 0  # Hunger decreased
    assert updated_state.happiness > 100  # Happiness increased
    assert updated_state.energy > 100  # Energy increased
    
    # Test resting interaction
    base_state.fatigue = 50
    updated_state = state_manager.apply_interaction_effects(base_state, "rest")
    assert updated_state.fatigue == 10  # Fatigue decreased
    assert updated_state.energy > 100  # Energy increased
    assert updated_state.stress == 0  # Stress decreased
    
    # Test partial success
    updated_state = state_manager.apply_interaction_effects(base_state, "play", success_level=0.5)
    assert updated_state.happiness == 112  # Half the normal happiness increase

def test_update_skills(state_manager: StateManager, base_state: CharacterState):
    """Test skill progression system."""
    # Test normal skill increase
    updated_state = state_manager.update_skills(base_state, "cooking", 10)
    assert updated_state.skills["cooking"] == 55  # 5 point increase (with level factor)
    
    # Test new skill
    updated_state = state_manager.update_skills(base_state, "painting", 10)
    assert "painting" in updated_state.skills
    assert updated_state.skills["painting"] == 10
    
    # Test skill cap
    base_state.skills["cooking"] = 95
    updated_state = state_manager.update_skills(base_state, "cooking", 20)
    assert updated_state.skills["cooking"] == 100  # Capped at 100

def test_update_relationships(state_manager: StateManager, base_state: CharacterState):
    """Test relationship dynamics."""
    # Test positive interaction
    updated_state = state_manager.update_relationships(base_state, "user123", 1.0)
    assert updated_state.relationships["user123"] == 60  # Increased by 10
    
    # Test negative interaction
    updated_state = state_manager.update_relationships(base_state, "user123", -0.5)
    assert updated_state.relationships["user123"] == 45  # Decreased by 5
    
    # Test new relationship
    updated_state = state_manager.update_relationships(base_state, "user456", 0.5)
    assert updated_state.relationships["user456"] == 55  # Started at 50, increased by 5

def test_check_and_award_achievements(state_manager: StateManager, base_state: CharacterState):
    """Test achievement system."""
    # Test master chef achievement
    base_state.skills["cooking"] = 90
    updated_state = state_manager.check_and_award_achievements(base_state)
    assert "master_chef" in updated_state.achievements
    
    # Test social butterfly achievement
    base_state.relationships = {
        f"user{i}": 80 for i in range(5)
    }
    updated_state = state_manager.check_and_award_achievements(base_state)
    assert "social_butterfly" in updated_state.achievements
    
    # Test well balanced achievement
    base_state.health = 70
    base_state.happiness = 70
    base_state.energy = 70
    updated_state = state_manager.check_and_award_achievements(base_state)
    assert "well_balanced" in updated_state.achievements
    
    # Test skill collector achievement
    base_state.skills = {
        f"skill{i}": 50 for i in range(5)
    }
    updated_state = state_manager.check_and_award_achievements(base_state)
    assert "skill_collector" in updated_state.achievements
    
    # Test iron will achievement
    base_state.stress = 10
    base_state.happiness = 90
    updated_state = state_manager.check_and_award_achievements(base_state)
    assert "iron_will" in updated_state.achievements 