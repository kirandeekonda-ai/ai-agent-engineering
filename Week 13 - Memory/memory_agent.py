"""
Week 13: Agent Memory & Caching

This script demonstrates:
1. Conversation memory (multi-turn context)
2. Session-based persistence (across restarts)
3. Semantic caching (avoid redundant LLM calls)
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- 1. CONVERSATION MEMORY ---
@dataclass
class ConversationMemory:
    """Manages conversation history for multi-turn context."""
    
    messages: list[dict] = field(default_factory=list)
    max_messages: int = 20  # Keep last N messages
    
    def add_user_message(self, content: str):
        """Add user message to history."""
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim()
    
    def add_assistant_message(self, content: str):
        """Add assistant message to history."""
        self.messages.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._trim()
    
    def _trim(self):
        """Keep only the last max_messages."""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_langchain_messages(self) -> list[BaseMessage]:
        """Convert to LangChain message format."""
        lc_messages = []
        for msg in self.messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            else:
                lc_messages.append(AIMessage(content=msg["content"]))
        return lc_messages
    
    def clear(self):
        """Clear all messages."""
        self.messages = []

# --- 2. SESSION PERSISTENCE ---
class SessionStore:
    """Persists sessions to disk for cross-restart memory."""
    
    def __init__(self, store_dir: str = "sessions"):
        self.store_path = Path(__file__).parent / store_dir
        self.store_path.mkdir(exist_ok=True)
    
    def _session_file(self, session_id: str) -> Path:
        return self.store_path / f"{session_id}.json"
    
    def save(self, session_id: str, memory: ConversationMemory):
        """Save session to disk."""
        filepath = self._session_file(session_id)
        data = {
            "session_id": session_id,
            "messages": memory.messages,
            "saved_at": datetime.now().isoformat()
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  [SESSION] Saved to {filepath.name}")
    
    def load(self, session_id: str) -> Optional[ConversationMemory]:
        """Load session from disk."""
        filepath = self._session_file(session_id)
        if not filepath.exists():
            return None
        
        with open(filepath) as f:
            data = json.load(f)
        
        memory = ConversationMemory()
        memory.messages = data["messages"]
        print(f"  [SESSION] Loaded {len(memory.messages)} messages from {filepath.name}")
        return memory
    
    def list_sessions(self) -> list[str]:
        """List all saved sessions."""
        return [f.stem for f in self.store_path.glob("*.json")]

# --- 3. SEMANTIC CACHE ---
class SemanticCache:
    """Cache responses based on query similarity (simple hash-based)."""
    
    def __init__(self, cache_file: str = "cache.json"):
        self.cache_path = Path(__file__).parent / cache_file
        self.cache: dict[str, dict] = {}
        self.hits = 0
        self.misses = 0
        self._load()
    
    def _load(self):
        """Load cache from disk."""
        if self.cache_path.exists():
            with open(self.cache_path) as f:
                self.cache = json.load(f)
    
    def _save(self):
        """Save cache to disk."""
        with open(self.cache_path, "w") as f:
            json.dump(self.cache, f, indent=2)
    
    def _hash_query(self, query: str) -> str:
        """Create hash of normalized query."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, query: str) -> Optional[str]:
        """Get cached response if exists."""
        key = self._hash_query(query)
        if key in self.cache:
            self.hits += 1
            print(f"  [CACHE HIT] Returning cached response")
            return self.cache[key]["response"]
        self.misses += 1
        return None
    
    def set(self, query: str, response: str):
        """Cache a response."""
        key = self._hash_query(query)
        self.cache[key] = {
            "query": query,
            "response": response,
            "cached_at": datetime.now().isoformat()
        }
        self._save()
        print(f"  [CACHE SET] Response cached")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / max(total, 1) * 100, 1),
            "cache_size": len(self.cache)
        }

# --- MEMORY-ENABLED AGENT ---
class MemoryAgent:
    """Agent with conversation memory and caching."""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.session_store = SessionStore()
        self.cache = SemanticCache()
        
        # Load or create memory
        loaded = self.session_store.load(session_id)
        self.memory = loaded if loaded else ConversationMemory()
        
        self.llm = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            api_key=os.environ.get("GROQ_API_KEY")
        )
    
    def chat(self, user_input: str) -> str:
        """Process user input with memory and caching."""
        print(f"\n[USER] {user_input}")
        
        # Check cache first
        cached = self.cache.get(user_input)
        if cached:
            self.memory.add_user_message(user_input)
            self.memory.add_assistant_message(cached)
            return cached
        
        # Add to memory
        self.memory.add_user_message(user_input)
        
        # Build messages with history
        messages = [
            SystemMessage(content="You are a helpful assistant. Remember the conversation history.")
        ] + self.memory.get_langchain_messages()
        
        # Generate response
        print(f"  [MEMORY] Using {len(self.memory.messages)} messages of context")
        response = self.llm.invoke(messages)
        answer = response.content
        
        # Update memory and cache
        self.memory.add_assistant_message(answer)
        self.cache.set(user_input, answer)
        
        # Persist session
        self.session_store.save(self.session_id, self.memory)
        
        print(f"  [ASSISTANT] {answer[:60]}...")
        return answer
    
    def show_history(self):
        """Display conversation history."""
        print("\n" + "=" * 60)
        print(f"CONVERSATION HISTORY (Session: {self.session_id})")
        print("=" * 60)
        for msg in self.memory.messages:
            role = msg["role"].upper()
            content = msg["content"][:80]
            print(f"[{role}] {content}...")

# --- MAIN ---
if __name__ == "__main__":
    import sys
    
    session_id = sys.argv[1] if len(sys.argv) > 1 else "demo"
    
    print("=" * 60)
    print(f"MEMORY AGENT - Session: {session_id}")
    print("=" * 60)
    print("Commands: 'history', 'cache', 'clear', 'quit'")
    
    agent = MemoryAgent(session_id=session_id)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            elif user_input.lower() == "quit":
                break
            elif user_input.lower() == "history":
                agent.show_history()
            elif user_input.lower() == "cache":
                stats = agent.cache.get_stats()
                print(f"\nCache Stats: {stats}")
            elif user_input.lower() == "clear":
                agent.memory.clear()
                print("Memory cleared!")
            else:
                response = agent.chat(user_input)
                print(f"\nAssistant: {response}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
