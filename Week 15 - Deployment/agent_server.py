"""
Week 15: Deployment & Scaling - FastAPI Agent Server

This script demonstrates:
1. REST API wrapper for agents
2. Health checks for load balancers
3. Async request handling
4. Structured request/response models
"""
from pathlib import Path
from dotenv import load_dotenv
import os
import time
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load .env from parent directory
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# --- FASTAPI APP ---
app = FastAPI(
    title="AI Agent API",
    description="Production-ready AI agent REST API",
    version="1.0.0"
)

# --- REQUEST/RESPONSE MODELS ---
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(default="default")
    stream: bool = Field(default=False)

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    session_id: str
    tokens_used: int
    latency_ms: int

class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float

# --- STARTUP TIME ---
START_TIME = datetime.now()

# --- LLM INSTANCE ---
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.1-8b-instant",
    api_key=os.environ.get("GROQ_API_KEY")
)

# --- ENDPOINTS ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for load balancers.
    Returns server status and uptime.
    """
    uptime = (datetime.now() - START_TIME).total_seconds()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        uptime_seconds=round(uptime, 2)
    )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Sends message to AI agent and returns response.
    """
    start_time = time.time()
    
    try:
        # Generate response
        response = llm.invoke([
            SystemMessage(content="You are a helpful assistant. Be concise."),
            HumanMessage(content=request.message)
        ])
        
        answer = response.content
        
        # Calculate metrics
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_used = len(request.message.split()) + len(answer.split()) + 20
        
        return ChatResponse(
            response=answer,
            session_id=request.session_id,
            tokens_used=tokens_used,
            latency_ms=latency_ms
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint.
    Returns response as server-sent events.
    """
    async def generate():
        llm_stream = ChatGroq(
            temperature=0,
            model_name="llama-3.1-8b-instant",
            api_key=os.environ.get("GROQ_API_KEY"),
            streaming=True
        )
        
        async for chunk in llm_stream.astream([
            SystemMessage(content="Be concise."),
            HumanMessage(content=request.message)
        ]):
            if chunk.content:
                yield f"data: {chunk.content}\n\n"
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "GET - Health check",
            "/chat": "POST - Chat with agent",
            "/chat/stream": "POST - Streaming chat"
        }
    }

# --- RUN ---
if __name__ == "__main__":
    import uvicorn
    print("Starting AI Agent API server...")
    print("API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
