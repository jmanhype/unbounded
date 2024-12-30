"""Service for managing character memories and states."""
from typing import Any, Dict, List, Optional
from mem0 import MemoryManager


class MemoryService:
    """Service for managing character memories using the MemoryManager."""

    def __init__(self) -> None:
        """Initialize the memory service."""
        self.memory_manager = MemoryManager()

    def store_interaction(
        self,
        character_id: str,
        interaction: Dict[str, Any]
    ) -> None:
        """
        Store an interaction for a character.

        Args:
            character_id: Unique identifier for the character
            interaction: Dictionary containing interaction details
        """
        # Convert interaction to a memory entry
        memory_entry = {
            "content": interaction.get("content", ""),
            "metadata": {
                "type": "interaction",
                "timestamp": interaction.get("timestamp", ""),
                "context": interaction.get("context", {}),
                "effects": interaction.get("effects", {}),
                "response": interaction.get("response", {})
            }
        }
        self.memory_manager.store_interaction(character_id, memory_entry)

    def get_recent_interactions(
        self,
        character_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent interactions for a character.

        Args:
            character_id: Unique identifier for the character
            limit: Maximum number of interactions to return

        Returns:
            List of recent interactions
        """
        # Get recent memories filtered by interaction type
        memories = self.memory_manager.get_recent_interactions(
            character_id,
            limit=limit
        )
        
        # Convert memories back to interaction format
        interactions = []
        for memory in memories:
            metadata = memory.get("metadata", {})
            interaction = {
                "content": memory.get("content", ""),
                "timestamp": metadata.get("timestamp", ""),
                "context": metadata.get("context", {}),
                "effects": metadata.get("effects", {}),
                "response": metadata.get("response", {})
            }
            interactions.append(interaction)
        
        return interactions

    def search_memories(
        self,
        character_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search through a character's memories.

        Args:
            character_id: Unique identifier for the character
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching interactions
        """
        return self.memory_manager.search_memories(character_id, query, limit)

    def get_character_state(
        self,
        character_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current state and history for a character.

        Returns:
            Dictionary containing current state and history, or None if not found
        """
        return self.memory_manager.get_character_state(character_id)

    def update_character_state(
        self,
        character_id: str,
        state_update: Dict[str, Any]
    ) -> None:
        """
        Update a character's state.

        Args:
            character_id: Unique identifier for the character
            state_update: Dictionary containing state updates
        """
        self.memory_manager.store_character_state(character_id, state_update)

    def clear_character_memories(self, character_id: str) -> None:
        """
        Clear all memories and state for a character.

        Args:
            character_id: Unique identifier for the character
        """
        self.memory_manager.clear_character_memories(character_id) 