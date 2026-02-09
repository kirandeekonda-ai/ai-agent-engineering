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
    
    
    def get_session_count(self) -> int:
        """
        Get the total number of active sessions.
        
        Returns:
            int: Number of sessions currently being tracked
        
        Example:
            >>> print(manager.get_session_count())  # 5
        """
        return len(self.conversations)
    
    
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
