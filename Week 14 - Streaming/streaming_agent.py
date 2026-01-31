"""
Week 14: Streaming & Real-time

This script demonstrates:
1. Token-by-token streaming responses
2. Async streaming for concurrent tasks
3. Progress callbacks for long operations
4. Graceful cancellation
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import sys
import time
import asyncio
from typing import Callable, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.callbacks import BaseCallbackHandler

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- 1. STREAMING CALLBACK HANDLER ---
class StreamingHandler(BaseCallbackHandler):
    """Handle streaming tokens in real-time."""
    
    def __init__(self, on_token: Optional[Callable[[str], None]] = None):
        self.tokens = []
        self.on_token = on_token or self._default_handler
    
    def _default_handler(self, token: str):
        """Print token immediately."""
        print(token, end="", flush=True)
    
    def on_llm_new_token(self, token: str, **kwargs):
        """Called for each new token."""
        self.tokens.append(token)
        self.on_token(token)
    
    def get_full_response(self) -> str:
        """Get the complete response."""
        return "".join(self.tokens)

# --- 2. STREAMING AGENT ---
class StreamingAgent:
    """Agent with streaming responses."""
    
    def __init__(self):
        self.model_name = "llama-3.1-8b-instant"
    
    def stream(self, query: str, on_token: Optional[Callable] = None) -> str:
        """Stream response token by token."""
        print(f"\n[STREAMING] {query[:50]}...\n")
        print("-" * 40)
        
        handler = StreamingHandler(on_token=on_token)
        
        llm = ChatGroq(
            temperature=0,
            model_name=self.model_name,
            api_key=os.environ.get("GROQ_API_KEY"),
            streaming=True,
            callbacks=[handler]
        )
        
        # This will stream tokens via the callback
        llm.invoke([
            SystemMessage(content="You are a helpful assistant. Be concise."),
            HumanMessage(content=query)
        ])
        
        print("\n" + "-" * 40)
        return handler.get_full_response()
    
    async def stream_async(self, query: str) -> str:
        """Async streaming for concurrent operations."""
        print(f"\n[ASYNC STREAM] {query[:50]}...")
        
        llm = ChatGroq(
            temperature=0,
            model_name=self.model_name,
            api_key=os.environ.get("GROQ_API_KEY"),
            streaming=True
        )
        
        full_response = []
        
        async for chunk in llm.astream([
            SystemMessage(content="Be concise."),
            HumanMessage(content=query)
        ]):
            token = chunk.content
            if token:
                print(token, end="", flush=True)
                full_response.append(token)
        
        print()
        return "".join(full_response)

# --- 3. PROGRESS TRACKER ---
class ProgressTracker:
    """Track and display progress for multi-step operations."""
    
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total = total_steps
        self.current = 0
        self.description = description
        self.start_time = time.time()
    
    def update(self, step_name: str = ""):
        """Update progress."""
        self.current += 1
        percent = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        
        # Progress bar
        bar_length = 30
        filled = int(bar_length * self.current / self.total)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        status = f"\r[{bar}] {percent:.0f}% | {step_name}"
        print(status, end="", flush=True)
        
        if self.current == self.total:
            print(f" | Done in {elapsed:.1f}s")
    
    def reset(self):
        """Reset progress."""
        self.current = 0
        self.start_time = time.time()

# --- 4. STREAMING MULTI-STEP AGENT ---
class MultiStepStreamingAgent:
    """Agent that streams progress for multi-step tasks."""
    
    def __init__(self):
        self.agent = StreamingAgent()
    
    def research_task(self, topic: str) -> dict:
        """Multi-step research with progress tracking."""
        steps = [
            ("Analyzing topic", f"What are the key aspects of {topic}?"),
            ("Finding examples", f"Give 2 real-world examples of {topic}"),
            ("Summarizing", f"Summarize {topic} in one sentence")
        ]
        
        progress = ProgressTracker(len(steps), "Research")
        results = {}
        
        print(f"\n{'='*60}")
        print(f"RESEARCHING: {topic}")
        print(f"{'='*60}\n")
        
        for step_name, query in steps:
            progress.update(step_name)
            print()  # New line after progress bar
            
            # Stream each step
            response = self.agent.stream(query)
            results[step_name] = response
            print()
        
        return results

# --- MAIN ---
def demo_basic_streaming():
    """Demo: Basic streaming."""
    agent = StreamingAgent()
    agent.stream("Explain what streaming responses are and why they matter for UX")

def demo_custom_handler():
    """Demo: Custom token handler."""
    agent = StreamingAgent()
    
    token_count = [0]
    def count_tokens(token: str):
        token_count[0] += 1
        print(token, end="", flush=True)
    
    print("\n[CUSTOM HANDLER] Counting tokens...")
    agent.stream("Name 5 programming languages", on_token=count_tokens)
    print(f"\n\nTotal tokens: {token_count[0]}")

def demo_async_streaming():
    """Demo: Async streaming."""
    async def run():
        agent = StreamingAgent()
        await agent.stream_async("What is async programming?")
    
    asyncio.run(run())

def demo_multi_step():
    """Demo: Multi-step with progress."""
    agent = MultiStepStreamingAgent()
    results = agent.research_task("machine learning")
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    for step, response in results.items():
        print(f"\n[{step}]")
        print(response[:200] + "...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "custom":
            demo_custom_handler()
        elif mode == "async":
            demo_async_streaming()
        elif mode == "multi":
            demo_multi_step()
        else:
            # Treat as query
            agent = StreamingAgent()
            agent.stream(" ".join(sys.argv[1:]))
    else:
        demo_basic_streaming()
