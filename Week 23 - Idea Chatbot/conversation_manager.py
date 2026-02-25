# ==============================================================================
# Conversation Manager - In-Memory Session Storage
# ==============================================================================
# This module manages conversation history for each session.
# Uses in-memory storage (will be upgraded to database in Module 4)

from typing import List, Dict, Optional


class ConversationManager:
    """
    Manages conversation history for multiple sessions.
    
    Each session has its own conversation history (list of messages).
    This is stored in memory, so it's lost when the server restarts.
    
    In Module 4, we'll upgrade this to use a database for persistence.
    """
    
    def __init__(self):
        """Initialize the conversation manager with empty storage."""
        # Dictionary mapping session_id -> list of messages
        # Format: {"session-123": [{"role": "user", "content": "..."}, ...]}
        self.conversations: Dict[str, List[Dict]] = {}
        
        # Track saved ideas per session to prevent duplicates
        self.saved_ideas: Dict[str, List[str]] = {}
        
        # Track research state per session for mid-conversation research
        # Format: {"session-123": {"researched": True, "alternatives": [...], "awaiting_differentiation": True}}
        self.research_state: Dict[str, Dict] = {}
    
    
    def get_history(self, session_id: str) -> List[Dict]:
        """
        Get the conversation history for a session.
        
        Args:
            session_id (str): The session identifier
        
        Returns:
            List[Dict]: List of messages in the conversation
                       Empty list if session doesn't exist yet
        
        Example:
            >>> manager = ConversationManager()
            >>> history = manager.get_history("session-123")
            >>> print(history)  # []
        """
        return self.conversations.get(session_id, [])
    
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to the conversation history.
        
        Args:
            session_id (str): The session identifier
            role (str): Message role ("user" or "assistant")
            content (str): The message content
        
        Example:
            >>> manager = ConversationManager()
            >>> manager.add_message("session-123", "user", "Hello!")
            >>> manager.add_message("session-123", "assistant", "Hi there!")
        """
        # Create session if it doesn't exist
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        # Add the message
        self.conversations[session_id].append({
            "role": role,
            "content": content
        })
    
    
    def clear_session(self, session_id: str):
        """
        Clear the conversation history for a session.
        
        Args:
            session_id (str): The session identifier
        
        Example:
            >>> manager.clear_session("session-123")
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.saved_ideas:
            del self.saved_ideas[session_id]
        if session_id in self.research_state:
            del self.research_state[session_id]
    
    
    def get_session_count(self) -> int:
        """
        Get the total number of active sessions.
        
        Returns:
            int: Number of sessions currently being tracked
        
        Example:
            >>> print(manager.get_session_count())  # 5
        """
        return len(self.conversations)
    
    
    # ----------------------------------
    # NEW: Duplicate Prevention Methods
    # ----------------------------------
    
    def is_idea_saved(self, session_id: str, idea_title: str) -> bool:
        """Check if an idea with this title was already saved in this session."""
        saved = self.saved_ideas.get(session_id, [])
        # Normalize for comparison
        normalized_title = idea_title.lower().strip()
        return any(t.lower().strip() == normalized_title for t in saved)
    
    
    def mark_idea_saved(self, session_id: str, idea_title: str):
        """Mark an idea as saved for this session."""
        if session_id not in self.saved_ideas:
            self.saved_ideas[session_id] = []
        self.saved_ideas[session_id].append(idea_title)
    
    
    # ----------------------------------
    # NEW: Research State Methods
    # ----------------------------------
    
    def get_research_state(self, session_id: str) -> Dict:
        """Get the research state for a session."""
        return self.research_state.get(session_id, {
            "researched": False,
            "alternatives": [],
            "awaiting_differentiation": False,
            "validated": False
        })
    
    
    def set_research_state(self, session_id: str, state: Dict):
        """Set the research state for a session."""
        self.research_state[session_id] = state
    
    
    def mark_researched(self, session_id: str, alternatives: List[Dict]):
        """Mark that research was done and we're awaiting user differentiation."""
        self.research_state[session_id] = {
            "researched": True,
            "alternatives": alternatives,
            "awaiting_differentiation": True,
            "validated": False
        }
    
    
    def mark_validated(self, session_id: str, validated: bool):
        """Mark whether the idea passed validation."""
        if session_id in self.research_state:
            self.research_state[session_id]["validated"] = validated
            self.research_state[session_id]["awaiting_differentiation"] = False
    
    
    def get_message_count(self, session_id: str) -> int:
        """
        Get the number of messages in a session.
        
        Args:
            session_id (str): The session identifier
        
        Returns:
            int: Number of messages in the session
        
        Example:
            >>> count = manager.get_message_count("session-123")
            >>> print(f"This session has {count} messages")
        """
        return len(self.conversations.get(session_id, []))


# ------------------------------------------------------------------------------
# Global instance (singleton pattern)
# ------------------------------------------------------------------------------
# We create one instance that's shared across the application
# In Module 4, this will be replaced with database queries

conversation_manager = ConversationManager()


# ------------------------------------------------------------------------------
# USAGE EXAMPLE
# ------------------------------------------------------------------------------
# from conversation_manager import conversation_manager
#
# # Add messages
# conversation_manager.add_message("session-123", "user", "Hello")
# conversation_manager.add_message("session-123", "assistant", "Hi!")
#
# # Get history
# history = conversation_manager.get_history("session-123")
# print(history)
# # [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi!"}]
