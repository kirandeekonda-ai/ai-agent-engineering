# ==============================================================================
# Lesson 1.1, 1.2, 1.3 & 2.1: FastAPI + Pydantic + CORS + Groq LLM
# ==============================================================================
# This file demonstrates:
# - Creating a FastAPI application (Lesson 1.1)
# - Using Pydantic for type-safe data structures (Lesson 1.2)
# - Enabling CORS for frontend-backend communication (Lesson 1.3)
# - Integrating Groq LLM for real AI responses (Lesson 2.1)

# ------------------------------------------------------------------------------
# STEP 1: Import FastAPI
# ------------------------------------------------------------------------------
from fastapi import FastAPI

# ------------------------------------------------------------------------------
# STEP 1.2: Import Pydantic (Lesson 1.2)
# ------------------------------------------------------------------------------
# Pydantic provides data validation and settings management using Python type hints
from pydantic import BaseModel
from datetime import datetime

# ------------------------------------------------------------------------------
# STEP 1.3: Import CORS Middleware (Lesson 1.3)
# ------------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) allows your frontend (running on one port)
# to communicate with your backend API (running on a different port).
# Without this, browsers block requests due to the "Same-Origin Policy"
from fastapi.middleware.cors import CORSMiddleware

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# STEP 1.4: Import LLM Client and Environment Variables (Lesson 2.1)
# ------------------------------------------------------------------------------
# Load environment variables from .env file (for API keys)
from dotenv import load_dotenv

# Our custom Groq client with multi-model strategy
from llm_client import get_groq_client

# Conversation manager for tracking chat history (Lesson 2.3)
from conversation_manager import conversation_manager

# Database functions for persistent storage (NEW in Lesson 4.1)
from database import save_idea, get_all_ideas, get_idea_by_id, get_idea_count

# Web research for market context (NEW in Module 7)
from web_research import get_web_research_client
from research_cache import cache_research, get_cached_research, cleanup_expired

# Load .env file
load_dotenv()

# Initialize the Groq client (will read GROQ_API_KEY from .env)
try:
    groq_client = get_groq_client()
    print("[OK] Groq client initialized successfully")
except ValueError as e:
    print(f"[WARNING] {e}")
    print("   The API will run but chat responses will be placeholder text.")
    groq_client = None

# Initialize the web research client (NEW in Module 7)
try:
    research_client = get_web_research_client()
    print("[OK] Web research client initialized")
except Exception as e:
    print(f"[WARNING] Web research disabled: {e}")
    research_client = None

# ------------------------------------------------------------------------------
# STEP 2: Define Pydantic Models (NEW in Lesson 1.2)
# ------------------------------------------------------------------------------
# Think of these as "blueprints" for your data.
# They define what fields are required, what types they should be,
# and provide automatic validation.

class ChatMessage(BaseModel):
    """
    Represents a message sent by the user to the chatbot.
    
    Fields:
        content (str): The actual message text from the user
        session_id (str | None): Optional ID to track conversation history
    
    Example JSON that would be valid:
    {
        "content": "I have an idea to automate weekly reports",
        "session_id": "user123-session456"
    }
    """
    content: str                    # Required: Must be a string
    session_id: str | None = None   # Optional: Can be None, defaults to None
    
    # EXPLANATION OF SYNTAX:
    # 'content: str' means "content must be a string and is required"
    # 'session_id: str | None = None' means:
    #   - Can be a string OR None (the | means "or")
    #   - Defaults to None if not provided
    #   - This makes it optional


class ChatResponse(BaseModel):
    """
    Represents the chatbot's response back to the user.
    
    Fields:
        message (str): The bot's reply
        session_id (str): The session this message belongs to
        timestamp (str): When the response was generated
        auto_saved (bool): Whether the idea was automatically saved (NEW in Module 5.5)
        idea_id (int | None): Database ID if auto-saved (NEW in Module 5.5)
    
    Example JSON that will be returned:
    {
        "message": "That sounds interesting! Tell me more about your idea.",
        "session_id": "user123-session456",
        "timestamp": "2026-02-08T10:42:00",
        "auto_saved": true,
        "idea_id": 42
    }
    """
    message: str        # The bot's reply text
    session_id: str     # Session identifier (now always present in response)
    timestamp: str      # When this response was created
    auto_saved: bool = False  # Was the idea automatically extracted and saved?
    idea_id: int | None = None  # Database ID if auto-saved


class ExtractRequest(BaseModel):
    """
    Request to extract an idea from a conversation session.
    
    Fields:
        session_id (str): The session ID to extract the idea from
    
    Example JSON:
    {
        "session_id": "session-20260208110611"
    }
    """
    session_id: str


class ExtractedIdea(BaseModel):
    """
    Represents a structured idea extracted from a conversation.
    
    This is the output of the idea extraction process.
    All fields are optional (str | None) because extraction may not find all info.
    
    Example JSON:
    {
        "id": 1,
        "title": "Report Automation API",
        "description": "Build an API to automate weekly report generation...",
        "problem_solved": "Manual report creation takes 5 hours per week",
        "time_estimate": "2-3 weeks",
        "cost_estimate": "$5,000-$10,000",
        "resources_needed": ["2 backend developers", "API infrastructure"],
        "impact": "Saves 5 hours/week for 10 team members",
        "complexity": "medium"
    }
    """
    id: int | None = None  # Database ID (added after saving)
    session_id: str | None = None
    title: str | None = None
    description: str | None = None
    problem_solved: str | None = None
    time_estimate: str | None = None
    cost_estimate: str | None = None
    resources_needed: list[str] | None = None
    impact: str | None = None
    complexity: str | None = None
    domain: str | None = None
    created_at: str | None = None
    status: str | None = None
    error: str | None = None  # If extraction failed


# ------------------------------------------------------------------------------
# STEP 3: Create the Application
# ------------------------------------------------------------------------------
app = FastAPI(
    title="Idea Assistant API",
    description="API for team idea collection with Pydantic validation",
    version="1.0.0"
)


# ------------------------------------------------------------------------------
# STEP 3.1: Configure CORS Middleware (NEW in Lesson 1.3)
# ------------------------------------------------------------------------------
# This middleware allows our frontend (prototype-chat.html) to communicate
# with this backend API, even though they run on different ports/domains.
#
# WHY IS THIS NEEDED?
# By default, browsers block requests from one origin (e.g., localhost:3000)
# to another origin (e.g., localhost:8000). This is called the Same-Origin Policy.
# CORS tells the browser: "It's okay, this API accepts requests from these origins."

app.add_middleware(
    CORSMiddleware,
    # allow_origins: List of origins that can access this API
    # ["*"] means "allow ALL origins" - good for development, bad for production
    # In production, use specific domains: ["https://yourdomain.com"]
    allow_origins=["*"],
    
    # allow_credentials: Whether to allow cookies/auth headers
    # Set to True if you're using authentication
    allow_credentials=True,
    
    # allow_methods: Which HTTP methods are allowed
    # ["*"] means all methods (GET, POST, PUT, DELETE, etc.)
    # You could restrict to: ["GET", "POST"]
    allow_methods=["*"],
    
    # allow_headers: Which headers can be sent in requests
    # ["*"] means all headers - usually fine
    # Common headers: ["Content-Type", "Authorization"]
    allow_headers=["*"],
)

# SECURITY NOTE:
# For production, change allow_origins to your actual frontend domain:
# allow_origins=["https://yourdomain.com", "https://www.yourdomain.com"]


# ------------------------------------------------------------------------------
# STEP 4: Original Endpoints (from Lesson 1.1)
# ------------------------------------------------------------------------------

@app.get("/")
def read_root():
    """Root endpoint - the homepage of our API."""
    return {
        "message": "Welcome to Idea Assistant API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ------------------------------------------------------------------------------
# STEP 5: Chat Endpoint with Multi-turn Conversations (Lesson 2.3)
# ------------------------------------------------------------------------------
# Now supports conversation history - the AI remembers previous messages!

@app.post("/chat")
def chat(message: ChatMessage) -> ChatResponse:
    """
    Chat endpoint with conversation memory and proactive idea validation.
    
    NEW in Module 9:
    - Detects when user describes an idea
    - Proactively researches market alternatives
    - Shares alternatives with user
    - Challenges user to differentiate
    - Only saves validated, unique ideas
    
    Args:
        message (ChatMessage): The validated message from the user
    
    Returns:
        ChatResponse: AI-generated response with session tracking
    """
    # Generate or reuse session_id
    session = message.session_id or f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Get conversation history for this session
    history = conversation_manager.get_history(session)
    
    # Get research state for this session
    research_state = conversation_manager.get_research_state(session)
    
    # Initialize response variables
    ai_response = ""
    auto_saved = False
    saved_idea_id = None
    
    if groq_client:
        try:
            # ================================================================
            # NEW FLOW: Proactive Research & Validation (Module 9)
            # ================================================================
            
            # DEBUG: Log current state
            print(f"\n{'='*60}")
            print(f"[DEBUG] Session: {session}")
            print(f"[DEBUG] Message: {message.content[:50]}...")
            print(f"[DEBUG] History length: {len(history)}")
            print(f"[DEBUG] Research state: {research_state}")
            print(f"{'='*60}\n")
            
            # Check if we're in the middle of a research/validation flow
            if research_state.get("awaiting_differentiation"):
                # User is responding to our challenge about differentiation
                print("[VALIDATION] User responding to differentiation challenge...")
                
                research_data = {"alternatives": research_state.get("alternatives", [])}
                
                # Validate their differentiation
                validation = groq_client.validate_idea_uniqueness(
                    research_state.get("idea_summary", ""),
                    research_data,
                    message.content
                )
                
                print(f"[VALIDATION] Result: {validation.get('validated')} - {validation.get('reason')}")
                
                if validation.get("validated"):
                    # Idea passed validation! Generate positive response and save
                    ai_response = groq_client.chat_with_research(
                        message.content, history, research_data, research_state
                    )
                    ai_response += f"\n\nGreat! Your idea has a clear differentiator. I'm saving it to the dashboard."
                    
                    # Add messages to history
                    conversation_manager.add_message(session, "user", message.content)
                    conversation_manager.add_message(session, "assistant", ai_response)
                    
                    # Extract and save the idea
                    current_history = conversation_manager.get_history(session)
                    extracted_data = groq_client.extract_idea(current_history)
                    
                    if 'error' not in extracted_data:
                        extracted_data['session_id'] = session
                        
                        # Enrich with research data
                        extracted_data = groq_client.enrich_with_research(extracted_data, research_data)
                        
                        # Check for duplicates before saving
                        idea_title = extracted_data.get('title', '')
                        if not conversation_manager.is_idea_saved(session, idea_title):
                            idea_id = save_idea(extracted_data)
                            conversation_manager.mark_idea_saved(session, idea_title)
                            print(f"[OK] Validated idea saved with ID: {idea_id}")
                            auto_saved = True
                            saved_idea_id = idea_id
                        else:
                            print(f"[SKIP] Idea already saved: {idea_title}")
                    
                    # Clear research state
                    conversation_manager.mark_validated(session, True)
                else:
                    # Idea needs more work
                    ai_response = f"I see, but {validation.get('reason', 'that differentiation might not be strong enough')}. "
                    ai_response += "Can you think of what else makes your idea unique or how it could be improved?"
                    
                    conversation_manager.add_message(session, "user", message.content)
                    conversation_manager.add_message(session, "assistant", ai_response)
            
            else:
                # Normal chat - but check if user is describing an idea
                idea_detection = groq_client.detect_idea_in_message(message.content, history)
                
                if idea_detection.get("is_idea") and idea_detection.get("confidence", 0) > 0.6:
                    # User is describing an idea - research it BEFORE responding
                    print(f"[AI] Idea detected: {idea_detection.get('idea_summary')}")
                    
                    idea_summary = idea_detection.get("idea_summary", message.content)
                    
                    # Check if research is needed
                    if research_client and research_client.client:
                        research_need = groq_client.classify_research_need(idea_summary)
                        print(f"[RESEARCH] Need: {research_need}")
                        
                        if research_need in ["YES", "MAYBE"]:
                            # Check cache first
                            cached = get_cached_research(idea_summary)
                            
                            if cached:
                                print("[RESEARCH] Cache hit!")
                                research_results = cached
                            else:
                                # Run Tavily search
                                print("[RESEARCH] Searching web for alternatives...")
                                research_results = research_client.search_competitors(idea_summary)
                                
                                # Cache the results
                                maturity = groq_client.classify_market_maturity(idea_summary)
                                ttl_days = research_client.get_cache_duration(maturity)
                                cache_research(idea_summary, research_results, ttl_days, maturity)
                                print(f"[RESEARCH] Cached for {ttl_days} days")
                            
                            alternatives = research_results.get("alternatives", [])
                            
                            if alternatives:
                                # Found alternatives - challenge the user
                                print(f"[RESEARCH] Found {len(alternatives)} alternatives, challenging user...")
                                
                                # Mark that we're awaiting differentiation
                                conversation_manager.mark_researched(session, alternatives)
                                conversation_manager.set_research_state(session, {
                                    "researched": True,
                                    "alternatives": alternatives,
                                    "awaiting_differentiation": True,
                                    "validated": False,
                                    "idea_summary": idea_summary
                                })
                                
                                # Generate research-aware response
                                ai_response = groq_client.chat_with_research(
                                    message.content, history, research_results, 
                                    {"awaiting_differentiation": False}  # First time showing
                                )
                                
                                conversation_manager.add_message(session, "user", message.content)
                                conversation_manager.add_message(session, "assistant", ai_response)
                            else:
                                # No alternatives found - proceed normally
                                print("[RESEARCH] No alternatives found, proceeding with normal chat")
                                ai_response = groq_client.chat(message.content, history)
                                conversation_manager.add_message(session, "user", message.content)
                                conversation_manager.add_message(session, "assistant", ai_response)
                        else:
                            # Internal/proprietary idea - skip research
                            print("[RESEARCH] Skipped (internal idea)")
                            ai_response = groq_client.chat(message.content, history)
                            conversation_manager.add_message(session, "user", message.content)
                            conversation_manager.add_message(session, "assistant", ai_response)
                    else:
                        # No research client - normal chat
                        ai_response = groq_client.chat(message.content, history)
                        conversation_manager.add_message(session, "user", message.content)
                        conversation_manager.add_message(session, "assistant", ai_response)
                else:
                    # Not an idea description - normal chat
                    ai_response = groq_client.chat(message.content, history)
                    conversation_manager.add_message(session, "user", message.content)
                    conversation_manager.add_message(session, "assistant", ai_response)
            
        except Exception as e:
            print(f"[ERROR] Chat error: {e}")
            ai_response = f"Sorry, I'm having trouble thinking right now. Error: {str(e)}"
    else:
        ai_response = "[WARNING] Groq API key not configured. Please add GROQ_API_KEY to your .env file."
    
    # Create structured response
    response = ChatResponse(
        message=ai_response,
        session_id=session,
        timestamp=datetime.now().isoformat(),
        auto_saved=auto_saved,
        idea_id=saved_idea_id
    )
    
    return response


# ------------------------------------------------------------------------------
# STEP 6: Idea Extraction Endpoint (NEW in Lesson 3.1)
# ------------------------------------------------------------------------------
# This endpoint extracts structured idea data from a conversation

@app.post("/extract", response_model=ExtractedIdea)
def extract_idea(request: ExtractRequest) -> ExtractedIdea:
    """
    Extract a structured idea from a conversation session.
    
    This uses the llama-4-scout model for better reasoning and extraction.
    The model analyzes the entire conversation and extracts:
    - Title, description, problem solved
    - Time and cost estimates
    - Resources needed
    - Impact and complexity
    
    Args:
        request (ExtractRequest): Contains the session_id to analyze
    
    Returns:
        ExtractedIdea: Structured idea data or error
    
    Try in /docs:
    - First have a conversation via /chat
    - Note the session_id from the response
    - Call /extract with that session_id
    - See the extracted structured data!
    """
    # Get conversation history
    history = conversation_manager.get_history(request.session_id)
    
    if not history:
        return ExtractedIdea(
            error=f"No conversation found for session: {request.session_id}"
        )
    
    if len(history) < 2:
        return ExtractedIdea(
            error="Not enough conversation to extract an idea. Chat more first!"
        )
    
    # Extract the idea using the LLM
    if groq_client:
        try:
            extracted_data = groq_client.extract_idea(history)
            
            # Check if extraction was successful
            if 'error' in extracted_data:
                return ExtractedIdea(**extracted_data)
            
            # Add session_id to the extracted data
            extracted_data['session_id'] = request.session_id
            
            # Save to database (NEW in Lesson 4.1)
            try:
                idea_id = save_idea(extracted_data)
                print(f"✅ Idea saved to database with ID: {idea_id}")
                extracted_data['id'] = idea_id  # Add the ID to the response
            except Exception as db_error:
                print(f"⚠️ Failed to save idea to database: {db_error}")
                # Continue anyway, return the extracted data
            
            # Convert to ExtractedIdea model
            return ExtractedIdea(**extracted_data)
            
        except Exception as e:
            return ExtractedIdea(
                error=f"Extraction failed: {str(e)}"
            )
    else:
        return ExtractedIdea(
            error="Groq client not configured. Add GROQ_API_KEY to .env file."
        )


# ------------------------------------------------------------------------------
# STEP 7: Ideas Retrieval Endpoints (NEW in Lesson 4.1)
# ------------------------------------------------------------------------------
# Get all saved ideas from the database

@app.get("/ideas")
def list_ideas(limit: int = 100, offset: int = 0):
    """
    Get all saved ideas from the database.
    
    Supports pagination with limit and offset parameters.
    
    Args:
        limit (int): Maximum number of ideas to return (default 100)
        offset (int): Number of ideas to skip for pagination (default 0)
    
    Returns:
        Dict with ideas array and metadata
    
    Try in /docs:
    - GET /ideas (all ideas)
    - GET /ideas?limit=5 (first 5 ideas)
    - GET /ideas?limit=10&offset=10 (ideas 11-20)
    """
    try:
        ideas = get_all_ideas(limit=limit, offset=offset)
        total = get_idea_count()
        
        return {
            "ideas": ideas,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    except Exception as e:
        return {
            "error": f"Failed to retrieve ideas: {str(e)}",
            "ideas": [],
            "total": 0
        }


@app.get("/ideas/{idea_id}")
def get_single_idea(idea_id: int):
    """
    Get a single idea by its ID.
    
    Args:
        idea_id (int): The idea ID from the database
    
    Returns:
        The idea object or error if not found
    
    Try in /docs:
    - GET /ideas/1 (get idea with ID 1)
    """
    try:
        idea = get_idea_by_id(idea_id)
        
        if idea:
            return idea
        else:
            return {"error": f"Idea {idea_id} not found"}
    except Exception as e:
        return {"error": f"Failed to retrieve idea: {str(e)}"}


# ------------------------------------------------------------------------------
# WHAT YOU'LL SEE IN /docs
# ------------------------------------------------------------------------------
# When you visit http://localhost:8000/docs, you'll see:
# 
# 1. The POST /chat endpoint with a "Request Body" section showing the 
#    ChatMessage structure (required: content, optional: session_id)
#
# 2. A "Response" section showing the ChatResponse structure
#
# 3. A "Try it out" button where you can test sending messages!
#
# This is all AUTO-GENERATED by FastAPI based on our Pydantic models!

# ------------------------------------------------------------------------------
# TRY THESE EXPERIMENTS
# ------------------------------------------------------------------------------
# 1. In /docs, try sending: {"content": "Test message"}
#    ✅ Should work! Returns a ChatResponse
#
# 2. Try sending: {"session_id": "abc123"}
#    ❌ Should fail! "content" is required
#    You'll get a clear error: "field required"
#
# 3. Try sending: {"content": 123}
#    ❌ Should fail! "content" must be a string
#    You'll get: "value is not a valid string"
#
# 4. Try sending: {"content": "Test", "session_id": "my-session"}
#    ✅ Should work! Returns response with your session_id

# ------------------------------------------------------------------------------
# NEXT STEPS
# ------------------------------------------------------------------------------
# In Lesson 1.3, we'll learn about CORS - making the frontend and backend
# work together so our beautiful UI can talk to this API!

